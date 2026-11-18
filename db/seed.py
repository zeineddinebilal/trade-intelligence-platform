"""
Demo seeder.

EVERYTHING SEEDED HERE IS FICTIONAL ILLUSTRATIVE DATA used to show the dashboard working on first boot.
No investigation, satellite reading, price move or URL below is real. Titles and headlines are prefixed
with "[DEMO]" and links point at example.org so nobody mistakes them for genuine intelligence.
Set AUTO_SEED_DEMO=false to start with an empty database.
"""
import json
from pathlib import Path
from sqlalchemy.orm import Session
from db.models import (
    AuditLog,
    ExecutiveBrief,
    MultiModalEvidence,
    RawSignal,
    SatelliteMetadata,
    StakeholderConfig,
    VerificationResult,
)

DEMO_NOTE = "FICTIONAL DEMO DATA - not real intelligence."


def seed_initial_data(db: Session) -> None:
    """Seeds the default Ministry stakeholder profile and two clearly-labelled demo briefs on first boot."""
    existing_cfg = db.query(StakeholderConfig).first()
    if existing_cfg:
        return

    cfg_path = Path(__file__).resolve().parent.parent / "config" / "stakeholder_example.json"
    cfg_data = json.loads(cfg_path.read_text(encoding="utf-8"))

    stakeholder = StakeholderConfig(
        stakeholder_code=cfg_data["stakeholder_code"],
        ministry_name=cfg_data["ministry_name"],
        priority_sectors=cfg_data["priority_sectors"],
        key_counterpart_markets=cfg_data["key_counterpart_markets"],
        bilateral_goals=cfg_data["bilateral_goals"],
        risk_tolerance=cfg_data["risk_tolerance"],
        min_confidence_for_escalation=cfg_data["min_confidence_for_escalation"],
    )
    db.add(stakeholder)
    db.commit()

    # Demo 1: Hypothetical US shrimp investigation + aquaculture pond telemetry
    sig1 = RawSignal(
        title="[DEMO] Hypothetical US Inquiry into Imported Frozen Warmwater Shrimp Pricing + Supplier Harvest Contraction",
        raw_content=(
            f"{DEMO_NOTE} Scenario: regulatory docket filings and two trade desks report a DOJ Antitrust "
            "and USITC preliminary inquiry into pricing and antibiotic compliance among two dominant "
            "incumbent suppliers of HS 030617 frozen warmwater shrimp into the United States. Satellite "
            "pond monitoring shows a 19.4% drop in stocked pond surface ratio in the affected export zone."
        ),
        feed_source="[DEMO] Docket + EO Alert",
        commodity="Frozen Warmwater Shrimp & Prawns",
        hs_chapter="0306",
        affected_market="United States",
        precursor_type="DOJ_PRICING_INVESTIGATION_AND_SUPPLY_CONTRACTION",
        prob_30d=0.68,
        prob_90d=0.84,
        source_links=[
            {
                "url": "https://example.org/demo/shrimp-docket",
                "title": "[DEMO] Docket Reference - Frozen Warmwater Shrimp Supply Review",
                "timestamp": "2026-11-17T14:20:00Z",
            },
            {
                "url": "https://example.org/demo/aquaculture-ndwi-alert",
                "title": "[DEMO] Coastal Pond NDWI Anomaly Report",
                "timestamp": "2026-11-18T06:00:00Z",
            },
        ],
        implication_summary="[DEMO] US buyers would face a 90-day supplier diversification window favoring bio-secure alternative exporters.",
        preliminary_confidence=0.86,
        status="SYNTHESIZED",
    )
    db.add(sig1)
    db.commit()
    db.refresh(sig1)

    db.add(
        MultiModalEvidence(
            signal_id=sig1.id,
            modality="DOCUMENT_IMAGE",
            mime_type="image/svg+xml",
            uri_or_path="data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='480' height='220'><rect width='100%' height='100%' fill='%230f172a'/><text x='24' y='40' fill='%23f59e0b' font-family='monospace' font-size='14'>[DEMO - FICTIONAL]</text><text x='24' y='70' fill='%2338bdf8' font-family='monospace' font-size='15'>DOCKET EXTRACT: HS 0306.17 IMPORT COMPLIANCE</text><text x='24' y='105' fill='%23e2e8f0' font-family='monospace' font-size='13'>Subpoena Scope: Spot/Contract Price Floor Coordination</text><text x='24' y='135' fill='%2394a3b8' font-family='monospace' font-size='12'>US Annual Import Baseline: USD 6.42B | Affected Share: 38.4%</text></svg>",
            caption="[DEMO] Illustrative Regulatory Filing Extract (HS 0306.17)",
        )
    )

    db.add(
        SatelliteMetadata(
            signal_id=sig1.id,
            provider="[DEMO] Sentinel-2 L2A",
            region_name="[DEMO] Incumbent Supplier Coastal Aquaculture Delta",
            bbox=[79.82, 14.10, 82.45, 16.95],
            metric_type="ACTIVE_POND_NDWI_SURFACE_RATIO",
            metric_value=0.61,
            baseline_delta_pct=-19.4,
            cloud_cover_pct=7.4,
            imagery_confidence=0.89,
            preview_image_url=None,
        )
    )

    db.add(
        VerificationResult(
            signal_id=sig1.id,
            core_claims=[
                "US authorities initiated pricing and compliance scrutiny covering 38.4% of US frozen shrimp imports.",
                "Incumbent supplier active aquaculture pond stocking fell 19.4% vs 5-year seasonal baseline.",
            ],
            verified_status="Confirmed",
            confidence=0.88,
            key_evidence=[
                "[DEMO] Docket notice corroborated by two trade law bulletins and customs volume dips (-11% MoM).",
                "[DEMO] NDWI water-index imagery (7.4% cloud cover) shows a 19.4% reduction in active aerated ponds.",
            ],
            multimodal_evaluation="[DEMO] In this scenario, both the docket chart and the pond telemetry independently corroborate supply tightening.",
            remaining_uncertainties=[
                "Exact timing of preliminary countervailing/antitrust tariff deposits (estimated 45-75 days)."
            ],
            recommendation="Escalate",
        )
    )

    brief1 = ExecutiveBrief(
        signal_id=sig1.id,
        stakeholder_code=stakeholder.stakeholder_code,
        headline="[DEMO] US Shrimp Supply Disruption Opens $180M–$320M Market-Entry Window for Certified Aquaculture Exporters",
        alignment_score=94,
        priority_level="CRITICAL",
        matching_strategic_elements=[
            "Priority Sector #1: Shrimp & Prawns (HS 0306, weight 1.0)",
            "Key Counterpart Market: United States",
            "Bilateral Goal: Expand certified aquaculture & food re-export share in US retail chains",
        ],
        alignment_rationale="Direct hit on top-weighted HS 0306 sector and tier-1 counterpart market (US) with high verification confidence (0.88).",
        what_changed="[DEMO] Regulatory pricing/compliance scrutiny in the United States coincides with a 19.4% contraction in active aquaculture pond stocking across the primary incumbent supplier belt.",
        quantified_window="USD 180M–320M addressable quarterly procurement reallocation over the next 30–90 days as US retail chains hedge supplier compliance risk.",
        strategic_alignment_section="Directly advances the Ministry's non-oil aquaculture export expansion goal into the US market under full veterinary traceability standards.",
        recommended_next_steps={
            "diplomatic": [
                "Instruct Commercial Attaché in Washington D.C. to brief USDA/FDA counterparts on national residue-free aquaculture certification.",
                "Request fast-track facility listing equivalence for top 5 national shrimp processors.",
            ],
            "commercial": [
                "Convene national aquaculture exporters and cold-chain logistics operators within 7 days to lock 40ft reefer slots.",
                "Target top 10 US supermarket seafood procurement desks seeking diversified Q1–Q2 supply contracts.",
            ],
            "monitoring": [
                "Track bi-weekly pond restocking indices and the USITC preliminary determination calendar.",
            ],
        },
        risks_and_mitigations=[
            {
                "risk": "Broadening of US import inspection holds to all third-country transshipments.",
                "mitigation": "Enforce batch-level Certificate of Origin and veterinary health attestations on every shipment.",
            },
            {
                "risk": "Reefer container rate spike on East Coast US lanes.",
                "mitigation": "Pre-book volume commitments via national port & carrier partnerships.",
            },
        ],
        confidence_score=0.88,
        main_uncertainties=[
            "Scope of final DOJ/USITC remedies expected in 60–90 days.",
        ],
        provenance=[
            {
                "source": "[DEMO] Regulatory Docket Filing HS 0306.17",
                "modality": "DOCUMENT_IMAGE + TEXT",
                "timestamp": "2026-11-17T14:20:00Z",
                "verification_note": "Illustrative only.",
            },
            {
                "source": "[DEMO] Sentinel-2 L2A Coastal Aquaculture Telemetry",
                "modality": "SATELLITE_IMAGERY",
                "timestamp": "2026-11-18T06:00:00Z",
                "verification_note": "Illustrative only: NDWI pond ratio -19.4% vs 5-yr baseline.",
            },
        ],
        markdown_brief=(
            "> **FICTIONAL DEMO BRIEF** — shows the format only; not real intelligence.\n\n"
            "### Executive Trade Opportunity Brief: US Shrimp Supply Reallocation (HS 0306)\n\n"
            "**1. What Changed & Why It Matters Now**\n"
            "US regulatory scrutiny into imported warmwater shrimp pricing and antibiotic compliance has converged with a **19.4% contraction** in active pond stocking in the dominant supplier region.\n\n"
            "**2. Quantified Opportunity Window**\n"
            "- **Addressable Volume**: USD 180M–320M over a **30-to-90 day** contract re-tendering window.\n\n"
            "**3. Strategic Alignment (Score: 94/100 — CRITICAL)**\n"
            "Matches Priority #1 commodity (**HS 0306 Shrimp & Prawns**) and Tier-1 counterpart (**United States**).\n\n"
            "**4. Recommended Next Steps**\n"
            "- **Diplomatic**: Mobilize Washington Commercial Attaché to highlight national traceability protocols with FDA/NOAA.\n"
            "- **Commercial**: Coordinate top national aquaculture exporters to pitch Q1/Q2 supply agreements to US retail chains.\n"
            "- **Monitoring**: Maintain pond monitoring and docket tracking.\n\n"
            "**5. Key Risks & Mitigations**\n"
            "- *Transshipment scrutiny*: Require strict batch-level origin certificates to prevent anti-circumvention holds."
        ),
        requires_human_review=True,
        review_status="PENDING_HUMAN_REVIEW",
    )
    db.add(brief1)

    # Demo 2: Hypothetical dairy drought NDVI signal (HS 0402)
    sig2 = RawSignal(
        title="[DEMO] Hypothetical Pasture NDVI Deficit (-24.7%) in Southern Hemisphere Dairy Basin",
        raw_content=(
            f"{DEMO_NOTE} Scenario: vegetation health indices across temperate dairy export pastures "
            "show a -24.7% NDVI anomaly alongside a 6.8% Skim Milk Powder (HS 0402) futures uptick."
        ),
        feed_source="[DEMO] Ag-Monitor + Price Feed",
        commodity="Milk & Cream Powders (Dairy)",
        hs_chapter="0401-0406",
        affected_market="China",
        precursor_type="SATELLITE_DROUGHT_YIELD_PRECURSOR",
        prob_30d=0.62,
        prob_90d=0.79,
        source_links=[
            {
                "url": "https://example.org/demo/pasture-ndvi-bulletin",
                "title": "[DEMO] Pasture NDVI Deficit Bulletin",
                "timestamp": "2026-11-18T03:30:00Z",
            }
        ],
        implication_summary="[DEMO] Forward dairy import prices into Asia/MENA could rise 8-14% in 60 days.",
        preliminary_confidence=0.81,
        status="SYNTHESIZED",
    )
    db.add(sig2)
    db.commit()
    db.refresh(sig2)

    db.add(
        SatelliteMetadata(
            signal_id=sig2.id,
            provider="[DEMO] Landsat-9 / Sentinel-2 HLS",
            region_name="[DEMO] Primary Southern Dairy Export Pastureland",
            bbox=[172.10, -43.90, 176.80, -37.50],
            metric_type="PASTURE_NDVI_ANOMALY",
            metric_value=0.42,
            baseline_delta_pct=-24.7,
            cloud_cover_pct=4.5,
            imagery_confidence=0.92,
            preview_image_url=None,
        )
    )

    db.add(
        VerificationResult(
            signal_id=sig2.id,
            core_claims=[
                "Pasture forage NDVI dropped 24.7% below seasonal norm across key dairy export districts.",
                "Skim Milk Powder forward contracts rose 6.8% over two consecutive auctions.",
            ],
            verified_status="Partially Corroborated",
            confidence=0.82,
            key_evidence=[
                "[DEMO] NDVI composite (4.5% cloud cover) shows widespread soil moisture stress.",
                "[DEMO] Auction settlement data shows upward forward price curve inflection.",
            ],
            multimodal_evaluation="[DEMO] In this scenario, the NDVI deficit corroborates early milk-solids output deceleration ahead of official statistics.",
            remaining_uncertainties=["Late-season rainfall could partially moderate Q1 output loss."],
            recommendation="Escalate",
        )
    )

    brief2 = ExecutiveBrief(
        signal_id=sig2.id,
        stakeholder_code=stakeholder.stakeholder_code,
        headline="[DEMO] Satellite-Detected Dairy Pasture Deficit Signals 60-Day Import Hedging & Regional Re-Export Opportunity",
        alignment_score=86,
        priority_level="HIGH",
        matching_strategic_elements=[
            "Priority Sector #2: Milk, Cream & Dairy Concentrates (HS 0401-0406, weight 0.95)",
            "Bilateral Goal: Secure resilient dairy import corridors insulated from regional drought shocks",
        ],
        alignment_rationale="High strategic match on food-security dairy corridor resilience and regional dairy processing re-exports.",
        what_changed="[DEMO] Imagery detected a -24.7% pasture NDVI anomaly in a major dairy export basin, alongside a 6.8% rise in forward powder prices.",
        quantified_window="45–75 day window to lock Q1/Q2 milk powder supply contracts before a projected 8%–14% spot price rise.",
        strategic_alignment_section="Protects domestic food-price stability while positioning national dairy processors to supply regional buyers from buffered inventory.",
        recommended_next_steps={
            "diplomatic": [
                "Engage EU and US agricultural trade counselors on standby tariff-rate quota allocations for dairy concentrates."
            ],
            "commercial": [
                "Advise national food-reserve and dairy reconstitution plants to evaluate 90-day forward procurement contracts."
            ],
            "monitoring": [
                "Monitor 16-day NDVI recovery composites and bi-weekly auction volumes."
            ],
        },
        risks_and_mitigations=[
            {
                "risk": "Unexpected December precipitation softens price rally.",
                "mitigation": "Use staggered 60% fixed + 40% indexed procurement tranches.",
            }
        ],
        confidence_score=0.82,
        main_uncertainties=["December meteorological anomaly trajectory."],
        provenance=[
            {
                "source": "[DEMO] Landsat-9 / Sentinel-2 Harmonized NDVI",
                "modality": "SATELLITE_IMAGERY",
                "timestamp": "2026-11-18T03:30:00Z",
                "verification_note": "Illustrative only.",
            }
        ],
        markdown_brief=(
            "> **FICTIONAL DEMO BRIEF** — shows the format only; not real intelligence.\n\n"
            "### Executive Trade Brief: Dairy Supply Precursor & Forward Hedging Window (HS 0402)\n\n"
            "**1. Precursor Detected**\n"
            "Pasture monitoring reveals a **-24.7% forage deficit** in a tier-1 dairy export basin, ahead of official production downgrades.\n\n"
            "**2. Quantified Window**\n"
            "45–75 day procurement lead-time before an estimated **8%–14%** tightening in milk powder export prices.\n\n"
            "**3. Recommended Actions**\n"
            "- **Commercial**: Evaluate Q1 forward supply tranches with EU/US suppliers.\n"
            "- **Diplomatic**: Activate bilateral food-corridor consultation clauses."
        ),
        requires_human_review=True,
        review_status="APPROVED",
        reviewed_by="[DEMO] Director of Trade Intelligence",
        review_notes="[DEMO] Seeded approval to show the approved state.",
    )
    db.add(brief2)
    db.commit()

    db.add(
        AuditLog(
            actor="SYSTEM:Bootstrapper",
            action="INITIAL_DEMO_SEED_COMPLETED",
            entity_type="StakeholderConfig",
            entity_id=stakeholder.id,
            details={"seeded_briefs": 2, "note": DEMO_NOTE},
        )
    )
    db.commit()
