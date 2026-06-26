# VendorShield AI — Agent Architecture

## Agent Overview

| Agent | Port | Framework | LLM | Purpose |
|---|---|---|---|---|
| Main API | 8000 | FastAPI | — | Bridge + Risk Scoring |
| Research Agent | 8001 | Anthropic SDK + Tavily | claude-sonnet-4-6 | OSINT, news, sanctions |
| Compliance Agent | 8002 | Anthropic SDK | claude-sonnet-4-6 | Cert gap analysis |
| Financial Agent | 8003 | Anthropic SDK | claude-sonnet-4-6 | Analyst+reviewer pattern |
| Remediation Agent | 8004 | Anthropic SDK | claude-sonnet-4-6 | Task generation |

## Pipeline Flow

Vendor input → Research (8001) + Compliance (8002) + Financial (8003) [parallel]
→ Risk Scoring (8000) → Remediation (8004) → Full report

## Key Endpoints

- POST /api/assess/full — runs full pipeline in one call
- POST /api/risk/score — weighted 5-dimension scoring
- POST localhost:8001/assess — real research agent
- POST localhost:8002/assess — compliance gap analysis
- POST localhost:8003/assess — financial health (analyst+reviewer)
- POST localhost:8004/remediate — remediation task generation

## Risk Scoring Model

Dimensions and weights:
  Security:    30% — breach/attack/vulnerability signals
  Compliance:  25% — missing/expired certs, regulatory violations
  Financial:   20% — bankruptcy risk, credit score, revenue trend
  Operational: 15% — outage/downtime/dependency signals
  ESG:         10% — scandal/corruption/discrimination signals

Classification thresholds:
  0-25:   Low      → auto-approve, standard monitoring
  26-50:  Medium   → auto-approve, enhanced monitoring
  51-75:  High     → human review required
  76-100: Critical → immediate escalation

## Starting All Agents

  bash start.sh

## Running Demo

  python3 demo.py "Acme Cloud Inc" High
  python3 demo.py "Microsoft" High
