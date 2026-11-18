import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_ci.db")
os.environ.setdefault("GEMINI_API_KEY", "dummy_ci_key")
os.environ.setdefault("AUTO_SEED_DEMO", "true")

from fastapi.testclient import TestClient  # noqa: E402
from api.main import app  # noqa: E402
from agents.schemas import FactCheckOutput, OpportunitySynthesisOutput  # noqa: E402


def test_healthz_and_seeded_briefs():
    with TestClient(app) as client:
        health = client.get("/healthz")
        assert health.status_code == 200
        assert health.json()["status"] == "healthy"

        briefs = client.get("/api/briefs?stakeholder_code=MOFA-GULF-DEMO")
        assert briefs.status_code == 200
        data = briefs.json()
        assert len(data) >= 2
        assert data[0]["alignment_score"] >= data[1]["alignment_score"]
        assert all(b["headline"].startswith("[DEMO]") for b in data)


def test_dashboard_served():
    with TestClient(app) as client:
        assert client.get("/").status_code == 200
        assert client.get("/static/app.js").status_code == 200


def test_ingest_without_key_returns_503():
    with TestClient(app) as client:
        resp = client.post("/api/signals/ingest", json={"title": "t", "raw_content": "c"})
        assert resp.status_code == 503


def test_review_requires_valid_decision_and_reviewer():
    with TestClient(app) as client:
        bad = client.post("/api/briefs/1/review", json={"decision": "MAYBE", "reviewer_name": "x"})
        assert bad.status_code == 422
        no_name = client.post("/api/briefs/1/review", json={"decision": "APPROVED", "reviewer_name": ""})
        assert no_name.status_code == 422
        ok = client.post("/api/briefs/1/review", json={"decision": "APPROVED", "reviewer_name": "Test Officer"})
        assert ok.status_code == 200
        logs = client.get("/api/audit-logs").json()
        assert any(entry["action"] == "BRIEF_APPROVED" for entry in logs)


def test_agent_schemas_are_valid():
    for schema in (FactCheckOutput, OpportunitySynthesisOutput):
        assert "properties" in schema.model_json_schema()
