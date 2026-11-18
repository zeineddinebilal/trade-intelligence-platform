from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from agents.predictive_signal import run_predictive_signal_agent
from agents.fact_checker import run_multimodal_fact_checker
from agents.strategy_alignment import run_strategy_alignment_agent
from agents.opportunity_synthesis import run_opportunity_synthesis_agent
from config.settings import settings
from db.models import (
    AuditLog,
    ExecutiveBrief,
    MultiModalEvidence,
    RawSignal,
    SatelliteMetadata,
    StakeholderConfig,
    VerificationResult,
)
from ingestion.feeds import fetch_macro_and_trade_context
from ingestion.satellite import enrich_agricultural_satellite_metrics


def log_audit(db: Session, actor: str, action: str, entity_type: str, entity_id: int, details: Dict[str, Any]) -> None:
    entry = AuditLog(
        actor=actor,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details,
    )
    db.add(entry)
    db.commit()


def process_incoming_signal_pipeline(
    db: Session,
    title: str,
    raw_content: str,
    feed_source: str,
    source_links: List[Dict[str, str]],
    stakeholder_code: str,
    evidence_inputs: Optional[List[Dict[str, Any]]] = None,
    satellite_inputs: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    End-to-end multi-agent pipeline:
    1. Persist Raw Signal + Multi-Modal & Satellite attachments
    2. Predictive Signal Agent
    3. Mandatory Multi-Modal Fact-Checker Gate
    4. Strategy Alignment Agent
    5. Opportunity Synthesis (thinking_level='high') + Human Review Gate
    """
    stakeholder = db.query(StakeholderConfig).filter_by(stakeholder_code=stakeholder_code).first()
    if not stakeholder:
        raise ValueError(f"Stakeholder config '{stakeholder_code}' not found.")

    evidence_inputs = evidence_inputs or []
    satellite_inputs = satellite_inputs or []

    # 1. Persist Raw Signal
    raw_signal = RawSignal(
        title=title,
        raw_content=raw_content,
        feed_source=feed_source,
        source_links=source_links,
        status="PROCESSING",
    )
    db.add(raw_signal)
    db.commit()
    db.refresh(raw_signal)

    try:
        return _run_agents(db, raw_signal, stakeholder, title, raw_content, feed_source,
                           source_links, evidence_inputs, satellite_inputs)
    except Exception as exc:
        db.rollback()
        raw_signal.status = "FAILED"
        db.commit()
        log_audit(db, "SYSTEM:Orchestrator", "PIPELINE_FAILED", "RawSignal", raw_signal.id,
                  {"error": str(exc)[:500]})
        raise


def _run_agents(
    db: Session,
    raw_signal: RawSignal,
    stakeholder: StakeholderConfig,
    title: str,
    raw_content: str,
    feed_source: str,
    source_links: List[Dict[str, str]],
    evidence_inputs: List[Dict[str, Any]],
    satellite_inputs: List[Dict[str, Any]],
) -> Dict[str, Any]:
    for ev in evidence_inputs:
        db.add(
            MultiModalEvidence(
                signal_id=raw_signal.id,
                modality=ev.get("modality", "DOCUMENT_IMAGE"),
                mime_type=ev.get("mime_type", "image/png"),
                uri_or_path=ev["uri_or_path"],
                caption=ev.get("caption", ""),
            )
        )

    # Auto-enrich agricultural signals with satellite metrics if none were explicitly provided.
    # NOTE: until a real EO connector is wired in, these are SIMULATED placeholders (clearly labelled).
    if not satellite_inputs:
        satellite_inputs = enrich_agricultural_satellite_metrics(raw_content)

    for sat in satellite_inputs:
        db.add(
            SatelliteMetadata(
                signal_id=raw_signal.id,
                provider=sat.get("provider", "Sentinel-2"),
                region_name=sat["region_name"],
                bbox=sat.get("bbox", [0.0, 0.0, 0.0, 0.0]),
                metric_type=sat["metric_type"],
                metric_value=sat["metric_value"],
                baseline_delta_pct=sat["baseline_delta_pct"],
                cloud_cover_pct=sat.get("cloud_cover_pct", 6.5),
                imagery_confidence=sat.get("imagery_confidence", 0.88),
                preview_image_url=sat.get("preview_image_url"),
            )
        )
    db.commit()

    log_audit(db, "SYSTEM:Ingestion", "SIGNAL_INGESTED", "RawSignal", raw_signal.id, {"feed_source": feed_source})

    # 2. Predictive Signal Detection
    pred_output = run_predictive_signal_agent(
        {
            "title": title,
            "raw_content": raw_content,
            "feed_source": feed_source,
            "source_links": source_links,
            "satellite_telemetry": satellite_inputs,
        }
    )

    raw_signal.commodity = pred_output.commodity
    raw_signal.hs_chapter = pred_output.hs_chapter
    raw_signal.affected_market = pred_output.affected_market
    raw_signal.precursor_type = pred_output.precursor_type
    raw_signal.prob_30d = pred_output.estimated_probability_30d
    raw_signal.prob_90d = pred_output.estimated_probability_90d
    raw_signal.implication_summary = pred_output.implication_for_exporter
    raw_signal.preliminary_confidence = pred_output.preliminary_confidence
    db.commit()

    # 3. Mandatory Multi-Modal Fact-Checker Gate
    macro_context = fetch_macro_and_trade_context(pred_output.hs_chapter, pred_output.affected_market)
    fact_output = run_multimodal_fact_checker(
        signal=pred_output,
        raw_content=raw_content,
        evidence_items=evidence_inputs,
        satellite_observations=satellite_inputs,
        corroborating_context=macro_context,
    )

    verification_record = VerificationResult(
        signal_id=raw_signal.id,
        core_claims=fact_output.core_claims,
        verified_status=fact_output.verified_status,
        confidence=fact_output.confidence,
        key_evidence=fact_output.key_evidence,
        multimodal_evaluation=fact_output.multimodal_evaluation,
        remaining_uncertainties=fact_output.remaining_uncertainties,
        recommendation=fact_output.recommendation,
    )
    db.add(verification_record)
    db.commit()

    log_audit(
        db,
        "AGENT:MultiModalFactChecker",
        "SIGNAL_VERIFIED",
        "VerificationResult",
        verification_record.id,
        {"verified_status": fact_output.verified_status, "recommendation": fact_output.recommendation},
    )

    # Gate check: Do not synthesize executive briefs for discarded or contradicted rumors
    if fact_output.recommendation == "Discard" or fact_output.verified_status == "Contradicted":
        raw_signal.status = "DISCARDED_BY_FACT_CHECK"
        db.commit()
        return {
            "signal_id": raw_signal.id,
            "status": raw_signal.status,
            "verification": fact_output.model_dump(),
            "brief_id": None,
        }

    # 4. Stakeholder Strategy Alignment
    stakeholder_dict = {
        "stakeholder_code": stakeholder.stakeholder_code,
        "ministry_name": stakeholder.ministry_name,
        "priority_sectors": stakeholder.priority_sectors,
        "key_counterpart_markets": stakeholder.key_counterpart_markets,
        "bilateral_goals": stakeholder.bilateral_goals,
        "risk_tolerance": stakeholder.risk_tolerance,
    }
    alignment_output = run_strategy_alignment_agent(stakeholder_dict, pred_output, fact_output)

    # 5. Opportunity Synthesis (thinking_level = "high")
    synthesis_output = run_opportunity_synthesis_agent(
        stakeholder_profile=stakeholder_dict,
        signal=pred_output,
        verification=fact_output,
        alignment=alignment_output,
        market_context=macro_context,
        satellite_observations=satellite_inputs,
    )

    # Human Review Gate: high-materiality OR low-confidence items always need a human.
    needs_human_gate = (
        alignment_output.alignment_score >= settings.human_review_threshold
        or alignment_output.recommended_priority_level in ("CRITICAL", "HIGH")
        or fact_output.confidence < (stakeholder.min_confidence_for_escalation or 0.65)
    )

    brief = ExecutiveBrief(
        signal_id=raw_signal.id,
        stakeholder_code=stakeholder.stakeholder_code,
        headline=synthesis_output.headline,
        alignment_score=alignment_output.alignment_score,
        priority_level=alignment_output.recommended_priority_level,
        matching_strategic_elements=alignment_output.matching_strategic_elements,
        alignment_rationale=alignment_output.rationale,
        what_changed=synthesis_output.what_changed_and_why_now,
        quantified_window=synthesis_output.quantified_opportunity_window,
        strategic_alignment_section=synthesis_output.strategic_alignment_summary,
        recommended_next_steps=synthesis_output.recommended_next_steps.model_dump(),
        risks_and_mitigations=[r.model_dump() for r in synthesis_output.key_risks_and_mitigations],
        confidence_score=synthesis_output.confidence_score,
        main_uncertainties=synthesis_output.main_uncertainties,
        provenance=[p.model_dump() for p in synthesis_output.provenance],
        markdown_brief=synthesis_output.markdown_brief,
        requires_human_review=needs_human_gate,
        review_status="PENDING_HUMAN_REVIEW" if needs_human_gate else "APPROVED",
    )
    raw_signal.status = "SYNTHESIZED"
    db.add(brief)
    db.commit()
    db.refresh(brief)

    log_audit(
        db,
        "AGENT:OpportunitySynthesis",
        "BRIEF_GENERATED",
        "ExecutiveBrief",
        brief.id,
        {
            "alignment_score": brief.alignment_score,
            "priority_level": brief.priority_level,
            "review_status": brief.review_status,
        },
    )

    return {
        "signal_id": raw_signal.id,
        "status": raw_signal.status,
        "brief_id": brief.id,
        "review_status": brief.review_status,
        "alignment_score": brief.alignment_score,
    }
