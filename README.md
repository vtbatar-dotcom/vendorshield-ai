# VendorShield AI

Agentic third-party risk management platform. Each vendor is a dynamic case
in UiPath Maestro, assessed by specialized agents (LangChain research, CrewAI
financial, UiPath coded risk-scoring) with human-in-the-loop review.

## Status: Phase 1 — Foundation

- [x] Repo + MIT license + structure
- [x] Python project scaffold
- [x] `.env.example` with all required keys
- [x] Mock FastAPI backend (all 5 endpoints respond)
- [x] Maestro Case schema designed (`uipath/maestro-case/case-schema.md`)
- [ ] UiPath CLI authenticated (needs Labs access)

## Quick start (mock API)

```bash
cd api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cd ..
cp .env.example .env
uvicorn api.main:app --reload --port 8000
```

Open http://localhost:8000/docs for the interactive API.

## Repo layout

```
api/                 FastAPI bridge layer (mock in Phase 1)
external-agents/     LangChain (research) + CrewAI (financial) agents
uipath/              Maestro case, Agent Builder, coded agents, API workflows
data/sample-vendors/ Deterministic demo vendors (V001 flagged, V002 clean)
docs/                Setup guide and architecture notes
```

See `docs/setup-guide.md` for the full step-by-step.
