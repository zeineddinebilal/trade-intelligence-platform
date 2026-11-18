from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from agents.client import carbon_client
from agents.orchestrator import log_audit, process_incoming_signal_pipeline
from db.database import get_db
from db.models import AuditLog, ExecutiveBrief, RawSignal, StakeholderConfig

router = APIRouter(prefix="/api", tags=["Trade Intelligence API"])


class EvidenceInputModel(BaseModel):
    modality: str = "DOCUMENT_IMAGE"
    mime_type: str = "image/png"
    uri_or_path: str = Field(max_length=10_000_000)
    caption: str = ""


class SatelliteInputModel(BaseModel):
    provider: str = "Sentinel-2"
    region_name: str
    bbox: List[float] = Field(default_factory=lambda: [0.0, 0.0, 0.0, 0.0])
    metric_type: str
    metric_value: float
    baseline_delta_pct: float
    cloud_cover_pct: float = 5.0
    imagery_confidence: float = 0.88
    preview_image_url: Optional[str] = None


class IngestSignalRequest(BaseModel):
    title: str = Field(max_length=300)
    raw_content: str = Field(max_length=200_000)
    feed_source: str = Field(default="Manual Intelligence Submission", max_length=120)
    source_links: List[Dict[str, str]] = Field(default_factory=list)
    stakeholder_code: str = "MOFA-GULF-DEMO"
    evidence_inputs: List[EvidenceInputModel] = Field(default_factory=list, max_length=10)
    satellite_inputs: List[SatelliteInputModel] = Field(default_factory=list, max_length=20)


class StakeholderUpdateRequest(BaseModel):
    stakeholder_code: str = "MOFA-GULF-DEMO"
    ministry_name: str
    priority_sectors: List[Dict[str, Any]]
    key_counterpart_markets: List[str]
    bilateral_goals: List[str]
    risk_tolerance: str = "MODERATE"
    min_confidence_for_escalation: float = Field(default=0.65, ge=0.0, le=1.0)


class HumanReviewDecisionRequest(BaseModel):
    decision: Literal["APPROVED", "REJECTED"]
    reviewer_name: str = Field(min_length=1, max_length=120)
    notes: str = ""


@router.get("/stakeholder/{stakeholder_code}")
def get_stakeholder_config(stakeholder_code: str, db: Session = Depends(get_db)):
    cfg = db.query(StakeholderConfig).filter_by(stakeholder_code=stakeholder_code).first()
    if not cfg:
        raise HTTPException(status_code=404, detail="Stakeholder configuration not found")
    return {
        "stakeholder_code": cfg.stakeholder_code,
        "ministry_name": cfg.ministry_name,
        "priority_sectors": cfg.priority_sectors,
        "key_counterpart_markets": cfg.key_counterpart_markets,
        "bilateral_goals": cfg.bilateral_goals,
        "risk_tolerance": cfg.risk_tolerance,
        "min_confidence_for_escalation": cfg.min_confidence_for_escalation,
        "gemini_live_configured": carbon_client.is_configured,
    }


@router.put("/stakeholder")
def upsert_stakeholder_config(payload: StakeholderUpdateRequest, db: Session = Depends(get_db)):
    cfg = db.query(StakeholderConfig).filter_by(stakeholder_code=payload.stakeholder_code).first()
    if not cfg:
        cfg = StakeholderConfig(stakeholder_code=payload.stakeholder_code)
        db.add(cfg)

    cfg.ministry_name = payload.ministry_name
    cfg.priority_sectors = payload.priority_sectors
    cfg.key_counterpart_markets = payload.key_counterpart_markets
    cfg.bilateral_goals = payload.bilateral_goals
    cfg.risk_tolerance = payload.risk_tolerance
    cfg.min_confidence_for_escalation = payload.min_confidence_for_escalation
    db.commit()
    db.refresh(cfg)

    log_audit(
        db,
        actor="USER:MinistryAdmin",
        action="STAKEHOLDER_CONFIG_UPDATED",
        entity_type="StakeholderConfig",
        entity_id=cfg.id,
        details={"stakeholder_code": cfg.stakeholder_code, "risk_tolerance": cfg.risk_tolerance},
    )
    return {"status": "updated", "stakeholder_code": cfg.stakeholder_code}


@router.get("/briefs")
def list_prioritized_briefs(stakeholder_code: str = "MOFA-GULF-DEMO", db: Session = Depends(get_db)):
    briefs = (
        db.query(ExecutiveBrief)
        .filter_by(stakeholder_code=stakeholder_code)
        .order_by(ExecutiveBrief.alignment_score.desc(), ExecutiveBrief.created_at.desc())
        .all()
    )
    results = []
    for b in briefs:
        sig = b.signal
        ver = sig.verification if sig else None
        results.append(
            {
                "id": b.id,
                "signal_id": b.signal_id,
                "headline": b.headline,
                "alignment_score": b.alignment_score,
                "priority_level": b.priority_level,
                "matching_strategic_elements": b.matching_strategic_elements,
                "alignment_rationale": b.alignment_rationale,
                "what_changed": b.what_changed,
                "quantified_window": b.quantified_window,
                "recommended_next_steps": b.recommended_next_steps,
                "risks_and_mitigations": b.risks_and_mitigations,
                "confidence_score": b.confidence_score,
                "main_uncertainties": b.main_uncertainties,
                "provenance": b.provenance,
                "markdown_brief": b.markdown_brief,
                "review_status": b.review_status,
                "reviewed_by": b.reviewed_by,
                "review_notes": b.review_notes,
                "created_at": b.created_at.isoformat() if b.created_at else None,
                "signal": {
                    "commodity": sig.commodity if sig else None,
                    "hs_chapter": sig.hs_chapter if sig else None,
                    "affected_market": sig.affected_market if sig else None,
                    "precursor_type": sig.precursor_type if sig else None,
                    "prob_30d": sig.prob_30d if sig else None,
                    "prob_90d": sig.prob_90d if sig else None,
                    "source_links": sig.source_links if sig else [],
                },
                "verification": {
                    "verified_status": ver.verified_status if ver else "Unverified",
                    "confidence": ver.confidence if ver else 0.0,
                    "multimodal_evaluation": ver.multimodal_evaluation if ver else "",
                    "key_evidence": ver.key_evidence if ver else [],
                },
                "evidence_items": [
                    {
                        "modality": e.modality,
                        "mime_type": e.mime_type,
                        "uri_or_path": e.uri_or_path,
                        "caption": e.caption,
                    }
                    for e in (sig.evidence_items if sig else [])
                ],
                "satellite_observations": [
                    {
                        "provider": s.provider,
                        "region_name": s.region_name,
                        "metric_type": s.metric_type,
                        "metric_value": s.metric_value,
                        "baseline_delta_pct": s.baseline_delta_pct,
                        "cloud_cover_pct": s.cloud_cover_pct,
                        "imagery_confidence": s.imagery_confidence,
                    }
                    for s in (sig.satellite_observations if sig else [])
                ],
            }
        )
    return results


@router.get("/signals")
def list_raw_signals(db: Session = Depends(get_db)):
    signals = db.query(RawSignal).order_by(RawSignal.detected_at.desc()).limit(50).all()
    return [
        {
            "id": s.id,
            "title": s.title,
            "feed_source": s.feed_source,
            "commodity": s.commodity,
            "hs_chapter": s.hs_chapter,
            "affected_market": s.affected_market,
            "prob_30d": s.prob_30d,
            "prob_90d": s.prob_90d,
            "status": s.status,
            "detected_at": s.detected_at.isoformat() if s.detected_at else None,
        }
        for s in signals
    ]


@router.post("/signals/ingest")
def ingest_and_analyze_signal(payload: IngestSignalRequest, db: Session = Depends(get_db)):
    if not carbon_client.is_configured:
        raise HTTPException(
            status_code=503,
            detail="GEMINI_API_KEY is not configured on the server. Set GEMINI_API_KEY to run live agent orchestration.",
        )
    try:
        return process_incoming_signal_pipeline(
            db=db,
            title=payload.title,
            raw_content=payload.raw_content,
            feed_source=payload.feed_source,
            source_links=payload.source_links,
            stakeholder_code=payload.stakeholder_code,
            evidence_inputs=[e.model_dump() for e in payload.evidence_inputs],
            satellite_inputs=[s.model_dump() for s in payload.satellite_inputs],
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Pipeline failed: {exc}") from exc


@router.post("/briefs/{brief_id}/review")
def submit_human_review(brief_id: int, payload: HumanReviewDecisionRequest, db: Session = Depends(get_db)):
    brief = db.query(ExecutiveBrief).filter_by(id=brief_id).first()
    if not brief:
        raise HTTPException(status_code=404, detail="Brief not found")

    brief.review_status = payload.decision
    brief.reviewed_by = payload.reviewer_name
    brief.review_notes = payload.notes
    brief.reviewed_at = datetime.now(timezone.utc)
    db.commit()

    log_audit(
        db,
        actor=f"HUMAN_REVIEWER:{payload.reviewer_name}",
        action=f"BRIEF_{payload.decision}",
        entity_type="ExecutiveBrief",
        entity_id=brief.id,
        details={"notes": payload.notes},
    )
    return {"status": "ok", "brief_id": brief.id, "review_status": brief.review_status}


@router.get("/audit-logs")
def get_audit_trail(db: Session = Depends(get_db)):
    logs = db.query(AuditLog).order_by(AuditLog.created_at.desc(), AuditLog.id.desc()).limit(40).all()
    return [
        {
            "id": entry.id,
            "actor": entry.actor,
            "action": entry.action,
            "entity_type": entry.entity_type,
            "entity_id": entry.entity_id,
            "details": entry.details,
            "created_at": entry.created_at.isoformat() if entry.created_at else None,
        }
        for entry in logs
    ]
