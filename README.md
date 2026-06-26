# VendorShield AI

Agentic third-party vendor risk management platform. Each vendor assessment
runs through 5 AI agents (Claude + Tavily) orchestrated via UiPath Maestro.

## Status: Production-ready local pipeline + UiPath Maestro Case deployed

- [x] 5 AI agents running (ports 8000-8004)
- [x] Full pipeline: vendor name → risk report in ~90 seconds
- [x] UiPath Maestro Case published (6 stages, SLAs, exit conditions)
- [x] End-to-end demo script

## Quick start

```bash
# 1. Clone and set up environment
git clone https://github.com/vtbatar-dotcom/vendorshield-ai
cd vendorshield-ai
cp .env.example .env   # fill in ANTHROPIC_API_KEY and TAVILY_API_KEY

# 2. Install deps for each agent
cd api && python3.11 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && cd ..
cd external-agents/research-agent && python3.11 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && cd ../..
cd external-agents/compliance-agent && python3.11 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && cd ../..
cd external-agents/financial-agent && python3.11 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && cd ../..
cd external-agents/remediation-agent && python3.11 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && cd ../..

# 3. Start all agents (5 terminals) or use start.sh
bash start.sh

# 4. Run demo
python3 demo.py "Acme Cloud Inc" High
python3 demo.py "Microsoft" High
```

## Architecture
## Agents

| Port | Agent | Framework | Purpose |
|------|-------|-----------|---------|
| 8000 | Main API + Risk Scoring | FastAPI | Bridge + weighted scoring |
| 8001 | Research Agent | Anthropic SDK + Tavily | OSINT, news, sanctions |
| 8002 | Compliance Agent | Anthropic SDK | Cert gap analysis |
| 8003 | Financial Agent | Anthropic SDK | Analyst+reviewer pattern |
| 8004 | Remediation Agent | Anthropic SDK | Task generation |

## Risk Scoring Model

| Dimension | Weight | Signals |
|-----------|--------|---------|
| Security | 30% | breach, hack, ransomware, vulnerability |
| Compliance | 25% | missing/expired certs, fines, violations |
| Financial | 20% | bankruptcy risk, credit score, revenue trend |
| Operational | 15% | outage, downtime, dependency risk |
| ESG | 10% | scandal, corruption, discrimination |

Classification: Low (0-25) → Medium (26-50) → High (51-75) → Critical (76-100)

## UiPath Maestro

Case published to `nobmajhrqfjf/DefaultTenant` with 6 stages:
Intake → Automated Assessment → Risk Scoring → Human Review → Decision → Continuous Monitoring

See `uipath/maestro-case/` for the case schema and `uipath/deploy.sh` for deployment.

## Environment Variables
## Repo Layout
