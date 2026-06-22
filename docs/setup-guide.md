# Phase 1 Setup Guide — step by step

Goal of Phase 1: a live repo, an agreed Maestro Case schema, and a mock API
that responds. No real agent logic yet. By the end you can run the full case
flow against deterministic mock data.

## Prerequisites

- Python 3.11+   (`python --version`)
- Node.js 18+    (`node --version`) — needed for the UiPath CLI
- Git + a GitHub account
- A UiPath Automation Cloud (Labs) account — request access NOW, it can lag

## Step 1 — Create the repo

```bash
mkdir vendorshield-ai && cd vendorshield-ai
git init
# unzip the provided scaffold here, or recreate the structure below
```

## Step 2 — Folder structure

```bash
mkdir -p api/routes api/models
mkdir -p external-agents/research-agent external-agents/financial-agent
mkdir -p uipath/maestro-case docs data/sample-vendors
touch api/__init__.py api/routes/__init__.py api/models/__init__.py
```

## Step 3 — Python environment + mock API

```bash
cd api
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cd ..
```

## Step 4 — Environment variables

```bash
cp .env.example .env
# Fill in keys you have. Phase 1 runs fully on mock data, so blanks are fine.
# Keep MOCK_MODE=true for now.
```

## Step 5 — Run and verify the API

```bash
uvicorn api.main:app --reload --port 8000
```

In another terminal:

```bash
curl localhost:8000/health
# {"status":"ok","phase":1,"mode":"mock"}

curl -X POST localhost:8000/api/risk/score \
  -H 'Content-Type: application/json' \
  -d '{"vendor_id":"V001","research_signals":["breach","lawsuit"],"compliance_gaps":["SOC2 expired"]}'
```

Or open http://localhost:8000/docs and click "Try it out" on any endpoint.

## Step 6 — UiPath CLI

```bash
npm install -g @uipath/cli
uipath auth login         # opens browser; needs Labs access
```

If Labs access has not landed yet, skip this step and keep building the
external agents (Phase 2/3) in parallel — they have no UiPath dependency.

## Step 7 — Agree the Maestro Case schema

Open `uipath/maestro-case/case-schema.md`. Walk the team through the fields,
stages, SLAs, and transition rules. This is the contract everything else is
built against — lock it before writing agent logic. Phase 1 only implements
stages 1–4 (Intake → Assessment → RiskScoring → Review).

## Step 8 — Commit and push

```bash
git add .
git commit -m "Phase 1: foundation - scaffold, mock API, case schema"
gh repo create vendorshield-ai --public --source=. --push
# or: create the repo on github.com and `git remote add origin ... && git push -u origin main`
```

## Phase 1 exit checklist

- [ ] `curl localhost:8000/health` returns ok
- [ ] All 5 endpoints respond from `/docs`
- [ ] `.env.example` committed (NOT `.env`)
- [ ] Case schema reviewed and agreed by the team
- [ ] Repo pushed to GitHub with MIT license
- [ ] UiPath CLI authenticated (or Labs access requested if pending)

Next: Phase 2 (Intake Agent + Document Understanding) and Phase 3 (real
LangChain research agent behind the `/api/research/assess` endpoint).
