# VendorShield AI

Agentic third-party vendor risk management platform. Submit a vendor name and get a complete risk assessment in ~90 seconds — powered by Claude AI agents orchestrated via UiPath Maestro.

**Problem:** Manual vendor risk assessments take 4–6 weeks per vendor. Risk signals are scattered across 20+ sources. No continuous monitoring exists.

**Solution:** 5 specialized AI agents running in parallel, producing a scored risk report with remediation tasks and executive summary.

## Demo

```bash
python3 demo.py "Acme Cloud Inc" High   # high-risk vendor
python3 demo.py "Microsoft" High         # lower-risk vendor
```

Sample output:
Overall Score:  55/100  ███████████░░░░░░░░░

Classification: 🟠 High

Decision:       CONDITIONAL_APPROVE

Routing:        HUMAN_REVIEW → Action Center

Confidence:     100%
## Architecture
Vendor name + tier

│

▼

┌───────────────────────────────────────┐

│         Orchestrator (port 8000)       │

│    POST /api/assess/full               │

│                                       │

│  ┌─────────┐ ┌──────────┐ ┌────────┐ │

│  │Research │ │Compliance│ │Finance │ │  ← parallel

│  │  8001   │ │   8002   │ │  8003  │ │

│  └─────────┘ └──────────┘ └────────┘ │

│              │                        │

│        Risk Scoring                   │

│    (weighted 5-dimension model)        │

│              │                        │

│        Remediation 8004               │

│    (tasks + executive summary)         │

└───────────────────────────────────────┘

    │

▼

Full risk report

UiPath Maestro case updated
## Prerequisites

- Python 3.11+ — `brew install python@3.11`
- Anthropic API key — https://console.anthropic.com/api-keys
- Tavily API key (free tier) — https://tavily.com
- UiPath Automation Cloud account — https://cloud.uipath.com (optional, for Maestro)

## Installation

**Step 1 — Clone the repo:**
```bash
git clone https://github.com/vtbatar-dotcom/vendorshield-ai
cd vendorshield-ai
```

**Step 2 — Set up environment variables:**
```bash
cp .env.example .env
```
Edit `.env` and fill in:
ANTHROPIC_API_KEY=sk-ant-...

TAVILY_API_KEY=tvly-...
**Step 3 — Install dependencies for each agent:**
```bash
# Main API
cd api
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
deactivate
cd ..

# Research Agent
cd external-agents/research-agent
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
deactivate
cd ../..

# Compliance Agent
cd external-agents/compliance-agent
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
deactivate
cd ../..

# Financial Agent
cd external-agents/financial-agent
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
deactivate
cd ../..

# Remediation Agent
cd external-agents/remediation-agent
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
deactivate
cd ../..

# Intake Agent
cd external-agents/intake-agent
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
deactivate
cd ../..
```

**Step 4 — Start all agents:**

Option A — single command (background):
```bash
bash start.sh
```

Option B — one terminal per agent (recommended for development):
```bash
# Terminal 1 — Main API
cd api && source .venv/bin/activate
uvicorn api.main:app --port 8000

# Terminal 2 — Research Agent
cd external-agents/research-agent && source .venv/bin/activate
uvicorn main:app --port 8001

# Terminal 3 — Compliance Agent
cd external-agents/compliance-agent && source .venv/bin/activate
uvicorn main:app --port 8002

# Terminal 4 — Financial Agent
cd external-agents/financial-agent && source .venv/bin/activate
.venv/bin/uvicorn main:app --port 8003

# Terminal 5 — Remediation Agent
cd external-agents/remediation-agent && source .venv/bin/activate
.venv/bin/uvicorn main:app --port 8004
```

**Step 5 — Verify all agents are running:**
```bash
curl localhost:8000/health
curl localhost:8001/health
curl localhost:8002/health
curl localhost:8003/health
curl localhost:8004/health
```
All should return `{"status":"ok",...}`

**Step 6 — Run the demo:**
```bash
python3 demo.py "Acme Cloud Inc" High
python3 demo.py "Microsoft" High
```

## Agents

| Port | Agent | Framework | Purpose |
|------|-------|-----------|---------|
| 8000 | Main API + Risk Scoring | FastAPI | Bridge + weighted scoring + orchestrator |
| 8001 | Research Agent | Anthropic SDK + Tavily | OSINT, web search, news, sanctions |
| 8002 | Compliance Agent | Anthropic SDK | Cert gap analysis + Claude summary |
| 8003 | Financial Agent | Anthropic SDK | Analyst+reviewer pattern over financial DB |
| 8004 | Remediation Agent | Anthropic SDK | Task generation + executive summary |
| 8005 | Intake Agent | FastAPI | Vendor tier classification |

## Risk Scoring Model

| Dimension | Weight | Key signals |
|-----------|--------|-------------|
| Security | 30% | breach, hack, ransomware, vulnerability, attack |
| Compliance | 25% | missing/expired certs, FTC fines, GDPR violations |
| Financial | 20% | bankruptcy risk, credit score, revenue trend |
| Operational | 15% | outage, downtime, supply chain risk |
| ESG | 10% | scandal, corruption, discrimination |

Classification thresholds:
- **Low** (0–25) → auto-approve, standard monitoring
- **Medium** (26–50) → auto-approve, enhanced monitoring
- **High** (51–75) → human review required
- **Critical** (76–100) → immediate escalation

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Service status + agent map |
| `/api/assess/full` | POST | Full pipeline — all agents in parallel |
| `/api/risk/score` | POST | Risk scoring only |
| `/api/vendors/{id}/case` | GET | Retrieve stored case |
| `/api/vendors/{id}/store` | POST | Store assessment result |
| `/api/monitoring/check` | POST | Run monitoring scan |
| `localhost:8001/assess` | POST | Research agent (real Claude + Tavily) |
| `localhost:8002/assess` | POST | Compliance agent |
| `localhost:8003/assess` | POST | Financial agent |
| `localhost:8004/remediate` | POST | Remediation agent |
| `localhost:8005/intake` | POST | Intake + tier classification |

Interactive API docs: http://localhost:8000/docs

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | ✅ Yes | Claude API key |
| `TAVILY_API_KEY` | ✅ Yes | Web search API key |
| `DATABASE_URL` | No | SQLite path (default: vendorshield.db) |
| `MOCK_MODE` | No | Set true to use mock data |

## Running Tests

```bash
# Unit tests (risk scoring model)
python3 tests/test_risk_scoring.py

# Smoke tests (all agents — requires all agents running)
python3 tests/test_agents_smoke.py
```

Expected: 9/9 unit tests, 11/11 smoke tests.

## UiPath Maestro

Case published to `nobmajhrqfjf/DefaultTenant` with 6 stages and tasks wired:

| Stage | SLA | Task |
|-------|-----|------|
| Intake | 4h | Collect vendor information |
| Automated Assessment | 24h | POST /api/assess/full |
| Risk Scoring | 1h | POST /api/risk/score |
| Human Review | 48h | Risk analyst decision form |
| Decision | 24h | Generate remediation plan + record decision |
| Continuous Monitoring | — | Daily POST /api/monitoring/check |

To redeploy:
```bash
export PATH="$HOME/.nvm/versions/node/v20.20.2/bin:$PATH"
uip login
cd uipath/maestro-case
uip maestro case pack VendorRiskAssessment dist --version 1.0.0
# Upload dist/*.nupkg via cloud.uipath.com → Orchestrator → Packages
```

## Docker

```bash
docker compose up
```

Runs all 6 services. Requires `.env` file with API keys.

## Repo Layout
api/                          Main API + risk scoring + orchestrator

routes/

risk.py                   Weighted 5-dimension scoring model

orchestrator.py           Full pipeline coordinator

vendors.py                SQLite-backed case store

monitoring.py             Real monitoring (calls research agent)

external-agents/

research-agent/             Claude + Tavily OSINT (port 8001)

compliance-agent/           Cert gap analysis (port 8002)

financial-agent/            Financial health, analyst+reviewer (port 8003)

remediation-agent/          Action plan generation (port 8004)

intake-agent/               Vendor tier classification (port 8005)

uipath/

maestro-case/               Maestro Case schema + published .nupkg

api-workflows/              API Workflow definitions

agents/intake-agent/        Action Center human review task template

coded-agents/risk-scoring/  Notes on converting to UiPath Coded Agent

tests/

test_risk_scoring.py        9 unit tests for the scoring model

test_agents_smoke.py        11 smoke tests for all agents

demo.py                       End-to-end demo script

start.sh                      Start all agents in background

package.sh                    Clean zip (excludes .env and .venv)

docker-compose.yml            All 6 services containerized
## Known Limitations

- Financial data uses a 3-vendor mock DB (Microsoft, Acme, Globex). Real D&B API integration is documented but not wired.
- Document Understanding for SOC2/ISO PDF parsing requires a UiPath DU license.
- The financial agent uses a hand-rolled analyst+reviewer pattern rather than the CrewAI framework specified in the original design — functionally equivalent.
- Continuous monitoring runs on-demand (no scheduler). Add APScheduler or a UiPath Orchestrator schedule to automate daily scans.

## License

MIT
