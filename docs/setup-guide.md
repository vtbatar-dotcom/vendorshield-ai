# VendorShield AI — Setup Guide

## Prerequisites

- Python 3.11+ (`/opt/homebrew/bin/python3.11` on Mac)
- Node.js 20+ with nvm
- Anthropic API key (console.anthropic.com)
- Tavily API key (tavily.com)
- UiPath Automation Cloud account (cloud.uipath.com)

## Step 1 — Clone and configure

```bash
git clone https://github.com/vtbatar-dotcom/vendorshield-ai
cd vendorshield-ai
cp .env.example .env
# Edit .env and fill in:
#   ANTHROPIC_API_KEY=sk-ant-...
#   TAVILY_API_KEY=tvly-...
```

## Step 2 — Install dependencies

Each agent has its own venv. Run once:

```bash
for agent in api external-agents/research-agent external-agents/compliance-agent external-agents/financial-agent external-agents/remediation-agent; do
  cd $agent
  /opt/homebrew/bin/python3.11 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt -q
  deactivate
  cd -
done
```

## Step 3 — Start all agents

Option A — one terminal per agent (recommended for dev):
```bash
# Terminal 1
cd api && source .venv/bin/activate && uvicorn api.main:app --port 8000

# Terminal 2
cd external-agents/research-agent && source .venv/bin/activate && uvicorn main:app --port 8001

# Terminal 3
cd external-agents/compliance-agent && source .venv/bin/activate && uvicorn main:app --port 8002

# Terminal 4
cd external-agents/financial-agent && source .venv/bin/activate && .venv/bin/uvicorn main:app --port 8003

# Terminal 5
cd external-agents/remediation-agent && source .venv/bin/activate && .venv/bin/uvicorn main:app --port 8004
```

Option B — background (for demo):
```bash
bash start.sh
```

## Step 4 — Verify all agents

```bash
curl localhost:8000/health
curl localhost:8001/health
curl localhost:8002/health
curl localhost:8003/health
curl localhost:8004/health
```

All should return `{"status":"ok",...}`

## Step 5 — Run demo

```bash
python3 demo.py "Acme Cloud Inc" High    # high-risk vendor
python3 demo.py "Microsoft" High          # lower-risk vendor
```

## Step 6 — UiPath Maestro

The Maestro Case is already published to `nobmajhrqfjf/DefaultTenant`.

To redeploy:
```bash
export PATH="$HOME/.nvm/versions/node/v20.20.2/bin:$PATH"
uip login
cd uipath/maestro-case
uip maestro case pack VendorRiskAssessment dist --version 1.0.0
# Then upload dist/*.nupkg via cloud.uipath.com → Orchestrator → Packages
```

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| /health | GET | Service status |
| /api/assess/full | POST | Full pipeline (all agents) |
| /api/risk/score | POST | Risk scoring only |
| /api/vendors/{id}/case | GET | Case lookup |
| localhost:8001/assess | POST | Research agent (real) |
| localhost:8002/assess | POST | Compliance agent (real) |
| localhost:8003/assess | POST | Financial agent (real) |
| localhost:8004/remediate | POST | Remediation agent (real) |

## Troubleshooting

**Port already in use:**
```bash
lsof -ti:8000 | xargs kill -9
```

**Wrong Python version (must be 3.11+):**
```bash
which uvicorn  # must show .venv/bin/uvicorn, not system path
source .venv/bin/activate
```

**macOS permissions error with --reload:**
```bash
# Drop --reload flag — macOS restricts filesystem watching in Documents folder
uvicorn main:app --port 8001   # no --reload
```
