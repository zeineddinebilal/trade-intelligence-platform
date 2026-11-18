from typing import List, Literal
from pydantic import BaseModel, Field


class SourceLink(BaseModel):
    url: str
    title: str
    timestamp: str


class PredictiveSignalOutput(BaseModel):
    commodity: str = Field(description="Commodity name, e.g., Frozen Warmwater Shrimp or Skim Milk Powder")
    hs_chapter: str = Field(description="HS code: 2-digit chapter (e.g., 03) or 4-digit heading (e.g., 0306)")
    affected_market: str = Field(description="Importing country or bloc altering or reviewing arrangements")
    precursor_type: str = Field(description="e.g., DOJ_ANTITRUST_INVESTIGATION, SATELLITE_YIELD_SHOCK, COUNTERVAILING_DUTY_FILING")
    estimated_probability_30d: float = Field(ge=0.0, le=1.0)
    estimated_probability_90d: float = Field(ge=0.0, le=1.0)
    source_links: List[SourceLink]
    implication_for_exporter: str = Field(description="One-sentence actionable implication for an exporting country")
    preliminary_confidence: float = Field(ge=0.0, le=1.0)


class FactCheckOutput(BaseModel):
    core_claims: List[str]
    verified_status: Literal["Confirmed", "Partially Corroborated", "Unverified", "Contradicted"]
    confidence: float = Field(ge=0.0, le=1.0)
    key_evidence: List[str] = Field(description="Primary filings, customs metrics, and multi-modal evidence items")
    multimodal_evaluation: str = Field(description="Explicit evaluation of attached satellite imagery, charts, or scanned filings")
    remaining_uncertainties: List[str]
    recommendation: Literal["Escalate", "Monitor", "Discard"]


class StrategyAlignmentOutput(BaseModel):
    alignment_score: int = Field(ge=0, le=100)
    matching_strategic_elements: List[str]
    rationale: str
    recommended_priority_level: Literal["CRITICAL", "HIGH", "MEDIUM", "WATCH"]


class RecommendedActions(BaseModel):
    diplomatic: List[str]
    commercial: List[str]
    monitoring: List[str]


class RiskMitigationItem(BaseModel):
    risk: str
    mitigation: str


class ProvenanceEntry(BaseModel):
    source: str
    modality: str
    timestamp: str
    verification_note: str


class OpportunitySynthesisOutput(BaseModel):
    headline: str
    what_changed_and_why_now: str
    quantified_opportunity_window: str
    strategic_alignment_summary: str
    recommended_next_steps: RecommendedActions
    key_risks_and_mitigations: List[RiskMitigationItem]
    confidence_score: float = Field(ge=0.0, le=1.0)
    main_uncertainties: List[str]
    provenance: List[ProvenanceEntry]
    markdown_brief: str = Field(description="Complete, executive-ready Markdown brief <= 600 words")
