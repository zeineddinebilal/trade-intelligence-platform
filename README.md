# Real-Time Multi-Modal Trade Opportunity Intelligence Platform

A real-time international trade opportunity intelligence system built for foreign ministries and national trade authorities (e.g., MOFA UAE, MOFA Saudi Arabia, Ministry of Economy). Powered by the **Google Gen AI SDK** (`gemini-4-carbon`) with configurable `thinking_level` controls, multi-modal document/satellite verification, dynamic strategy alignment, and human-in-the-loop governance.

> **Status: MVP.** The AI agents, database, API, dashboard and review gate are functional. The live data
> connectors (`ingestion/feeds.py`, `ingestion/satellite.py`) are **stubs that return labelled placeholder
> data** — see [Known limitations](#known-limitations). The two briefs seeded on first boot are **fictional demo data**.

## Architecture Overview

```text
Open-source & Structured Feeds
(News, X, DOJ/Competition Filings, UN Comtrade, Freight/FX, Satellite NDVI)
        │
        ▼
[1] Predictive Signal Agent (gemini-4-carbon, thinking_level="medium")
    Detects early precursors (investigations, tariff shifts, crop/aquaculture stress)
        │
        ▼
[2] Multi-Modal Fact-Checker Agent (gemini-4-carbon, thinking_level="high")
    Cross-checks claims against primary filings, images, charts & satellite metadata
        │
        ▼
[3] Strategy Alignment Agent (gemini-4-carbon, thinking_level="low")
    Weights verified opportunities (0-100) against Ministry sectors, HS codes & bilateral goals
        │
        ▼
[4] Opportunity Synthesis Agent (gemini-4-carbon, thinking_level="high")
    Generates ≤600-word executive brief + structured JSON provenance
        │
        ▼
Stakeholder Dashboard + Human Review Gate + Audit Log
```

## Key Capabilities

- **Predictive early warning** — detects competition investigations, tariff shifts, freight anomalies and production shocks.
- **Mandatory multi-modal verification** — evaluates text alongside attached images/charts and satellite NDVI/NDWI telemetry. Signals the fact-checker marks *Discard* or *Contradicted* never become briefs.
- **Dynamic stakeholder configuration** — re-weight priorities per ministry (HS codes, counterpart markets, risk tolerance, bilateral goals) from the dashboard, no code changes.
- **Governance & auditability** — high-materiality or low-confidence briefs enter `PENDING_HUMAN_REVIEW`; every AI and human action is written to `audit_logs`. The system takes no autonomous external actions.

## Repository Layout

```text
agents/      Gemini client wrapper, prompts, schemas, the 4 agents, and the orchestrator
api/         FastAPI app (main.py) and REST endpoints (routes.py)
config/      Settings + example ministry configuration
dashboard/   Single-page stakeholder dashboard (served by FastAPI)
db/          SQLAlchemy engine, ORM models, reference SQL schema, demo seeder
ingestion/   Connector stubs for trade/freight/FX feeds and satellite EO
tests/       Smoke tests run in CI
```

## Environment Variables

Copy `.env.example` to `.env` and configure:

| Variable | Required | Description |
|---|---|---|
| `GEMINI_API_KEY` | Yes (for live runs) | Gemini API key with access to `gemini-4-carbon` (paid tier — the model has no free tier). Without it the dashboard still runs with demo data, but the pipeline is disabled. |
| `GEMINI_MODEL` | No | Defaults to `gemini-4-carbon`. |
| `DATABASE_URL` | No | PostgreSQL connection string. Defaults to local SQLite (`sqlite:///./trade_intel.db`) for zero-config local testing. |
| `HUMAN_REVIEW_THRESHOLD` | No | Alignment score (0–100, default 70) at or above which human review is mandatory. |
| `AUTO_SEED_DEMO` | No | Seed the example ministry config and two fictional demo briefs on first boot. Default `true`. |
| `DASHBOARD_PASSWORD` | Strongly recommended in production | If set, the dashboard and API (except `/healthz`) require a browser login with this password (any username). |

## Running Locally

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env and set GEMINI_API_KEY=your_key_here

uvicorn api.main:app --reload --port 8000
```

Open **http://localhost:8000** for the dashboard (prioritized briefs, multi-modal/satellite provenance, live pipeline runs, approve/reject). Interactive API docs are at **http://localhost:8000/docs**.

Run the tests with `pytest -v`.

## API Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/healthz` | Health check (used by Render) |
| GET | `/api/stakeholder/{code}` | Read a ministry configuration |
| PUT | `/api/stakeholder` | Create/update a ministry configuration |
| GET | `/api/briefs?stakeholder_code=…` | Prioritized briefs with evidence & provenance |
| GET | `/api/signals` | Latest 50 raw signals |
| POST | `/api/signals/ingest` | Run the full 4-agent pipeline on a new signal |
| POST | `/api/briefs/{id}/review` | Record a human APPROVED / REJECTED decision |
| GET | `/api/audit-logs` | Latest 40 audit entries |

## Deploying to Render (automatic deploys from GitHub)

1. Push this repository to GitHub.
2. In the [Render dashboard](https://dashboard.render.com), click **New + → Blueprint**.
3. Connect your GitHub account and select this repository.
4. Render detects `render.yaml` and provisions:
   - a managed PostgreSQL 16 database (`trade-intel-db`)
   - a Python web service (`trade-intel-platform`) serving the API and the dashboard
5. When prompted, enter the secrets `GEMINI_API_KEY` and `DASHBOARD_PASSWORD`.
6. Click **Apply**. Render builds the service and redeploys on every push to `main`.

`render.yaml` uses paid plans (`starter` web service, `basic-256mb` Postgres). For a throwaway test you can change both to `free` — the service will sleep when idle and Render's free databases expire after a limited period.

## Known Limitations

- **Live data connectors are stubs.** `ingestion/feeds.py` (Comtrade/freight/FX) and `ingestion/satellite.py` (Sentinel/Landsat) return fixed placeholder values tagged `"data_status": "SIMULATED_PLACEHOLDER"`. The agents are instructed never to treat these as evidence, and the dashboard labels them `[SIMULATED]`. Replace them with real connectors (e.g., UN Comtrade API, Copernicus Data Space / Sentinel Hub) before relying on any output.
- **Authentication is a single shared password.** Reviewer names are typed in, not tied to accounts. Before real ministry use, add per-user SSO so approvals are attributable.
- **The pipeline runs synchronously** inside the request (can take 1–2 minutes). For volume, move it to a background worker/queue.
- **Schema changes** are applied with `create_all` (no migrations). Add Alembic before the schema evolves in production.
