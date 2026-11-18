from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Float, Text, Boolean, DateTime, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from db.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class StakeholderConfig(Base):
    __tablename__ = "stakeholder_configs"

    id = Column(Integer, primary_key=True, index=True)
    stakeholder_code = Column(String(64), unique=True, nullable=False, index=True)
    ministry_name = Column(String(255), nullable=False)
    priority_sectors = Column(JSON, nullable=False, default=list)
    key_counterpart_markets = Column(JSON, nullable=False, default=list)
    bilateral_goals = Column(JSON, nullable=False, default=list)
    risk_tolerance = Column(String(32), nullable=False, default="MODERATE")
    min_confidence_for_escalation = Column(Float, nullable=False, default=0.65)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class RawSignal(Base):
    __tablename__ = "raw_signals"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(300), nullable=False)
    raw_content = Column(Text, nullable=False)
    feed_source = Column(String(120), nullable=False)
    commodity = Column(String(120), nullable=True, index=True)
    hs_chapter = Column(String(32), nullable=True, index=True)
    affected_market = Column(String(120), nullable=True, index=True)
    precursor_type = Column(String(120), nullable=True)
    prob_30d = Column(Float, nullable=True)
    prob_90d = Column(Float, nullable=True)
    source_links = Column(JSON, nullable=False, default=list)
    implication_summary = Column(Text, nullable=True)
    preliminary_confidence = Column(Float, nullable=True)
    status = Column(String(48), nullable=False, default="INGESTED")
    detected_at = Column(DateTime(timezone=True), default=utcnow)

    evidence_items = relationship("MultiModalEvidence", back_populates="signal", cascade="all, delete-orphan")
    satellite_observations = relationship("SatelliteMetadata", back_populates="signal", cascade="all, delete-orphan")
    verification = relationship("VerificationResult", back_populates="signal", uselist=False, cascade="all, delete-orphan")
    briefs = relationship("ExecutiveBrief", back_populates="signal", cascade="all, delete-orphan")


class MultiModalEvidence(Base):
    __tablename__ = "multimodal_evidence"

    id = Column(Integer, primary_key=True, index=True)
    signal_id = Column(Integer, ForeignKey("raw_signals.id", ondelete="CASCADE"), nullable=False)
    modality = Column(String(48), nullable=False)  # DOCUMENT_IMAGE, CHART, SATELLITE_IMAGE, PHOTO
    mime_type = Column(String(64), nullable=False, default="image/png")
    uri_or_path = Column(Text, nullable=False)
    caption = Column(Text, nullable=True)
    sha256_hash = Column(String(64), nullable=True)
    captured_at = Column(DateTime(timezone=True), default=utcnow)

    signal = relationship("RawSignal", back_populates="evidence_items")


class SatelliteMetadata(Base):
    __tablename__ = "satellite_metadata"

    id = Column(Integer, primary_key=True, index=True)
    signal_id = Column(Integer, ForeignKey("raw_signals.id", ondelete="CASCADE"), nullable=False)
    provider = Column(String(64), nullable=False)  # Sentinel-2, PlanetScope, Landsat-9
    region_name = Column(String(160), nullable=False)
    bbox = Column(JSON, nullable=False)  # [min_lon, min_lat, max_lon, max_lat]
    metric_type = Column(String(64), nullable=False)  # NDVI_ANOMALY, AQUACULTURE_POND_TURBIDITY, FLOOD_EXTENT
    metric_value = Column(Float, nullable=False)
    baseline_delta_pct = Column(Float, nullable=False)
    cloud_cover_pct = Column(Float, nullable=False, default=5.0)
    imagery_confidence = Column(Float, nullable=False, default=0.85)
    preview_image_url = Column(Text, nullable=True)
    acquired_at = Column(DateTime(timezone=True), default=utcnow)

    signal = relationship("RawSignal", back_populates="satellite_observations")


class VerificationResult(Base):
    __tablename__ = "verification_results"

    id = Column(Integer, primary_key=True, index=True)
    signal_id = Column(Integer, ForeignKey("raw_signals.id", ondelete="CASCADE"), unique=True, nullable=False)
    core_claims = Column(JSON, nullable=False, default=list)
    verified_status = Column(String(48), nullable=False)  # Confirmed, Partially Corroborated, Unverified, Contradicted
    confidence = Column(Float, nullable=False)
    key_evidence = Column(JSON, nullable=False, default=list)
    multimodal_evaluation = Column(Text, nullable=False)
    remaining_uncertainties = Column(JSON, nullable=False, default=list)
    recommendation = Column(String(32), nullable=False)  # Escalate, Monitor, Discard
    verified_at = Column(DateTime(timezone=True), default=utcnow)

    signal = relationship("RawSignal", back_populates="verification")


class ExecutiveBrief(Base):
    __tablename__ = "executive_briefs"

    id = Column(Integer, primary_key=True, index=True)
    signal_id = Column(Integer, ForeignKey("raw_signals.id", ondelete="CASCADE"), nullable=False)
    stakeholder_code = Column(String(64), nullable=False, index=True)
    headline = Column(String(300), nullable=False)
    alignment_score = Column(Integer, nullable=False, index=True)
    priority_level = Column(String(32), nullable=False)  # CRITICAL, HIGH, MEDIUM, WATCH
    matching_strategic_elements = Column(JSON, nullable=False, default=list)
    alignment_rationale = Column(Text, nullable=False)
    what_changed = Column(Text, nullable=False)
    quantified_window = Column(Text, nullable=False)
    strategic_alignment_section = Column(Text, nullable=False)
    recommended_next_steps = Column(JSON, nullable=False, default=dict)
    risks_and_mitigations = Column(JSON, nullable=False, default=list)
    confidence_score = Column(Float, nullable=False)
    main_uncertainties = Column(JSON, nullable=False, default=list)
    provenance = Column(JSON, nullable=False, default=list)
    markdown_brief = Column(Text, nullable=False)

    # Governance & Human Review Gate
    requires_human_review = Column(Boolean, nullable=False, default=True)
    review_status = Column(String(48), nullable=False, default="PENDING_HUMAN_REVIEW")  # PENDING_HUMAN_REVIEW, APPROVED, REJECTED
    reviewed_by = Column(String(120), nullable=True)
    review_notes = Column(Text, nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    signal = relationship("RawSignal", back_populates="briefs")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    actor = Column(String(120), nullable=False)  # SYSTEM:FactChecker or USER:director@mofa.gov
    action = Column(String(120), nullable=False)
    entity_type = Column(String(64), nullable=False)
    entity_id = Column(Integer, nullable=False)
    details = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), default=utcnow)
