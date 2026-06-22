"""VendorShield AI - FastAPI backend (Phase 1 mock).

Bridge layer that UiPath API Workflows call. In Phase 1 every endpoint returns
deterministic mock data so the Maestro case flow can be wired end-to-end before
the real agents (LangChain / CrewAI / Coded Agent) exist.

Run:  uvicorn api.main:app --reload --port 8000
Docs: http://localhost:8000/docs
"""
from fastapi import FastAPI

from api.routes import research, financial, risk, vendors, monitoring

app = FastAPI(
    title="VendorShield AI API",
    version="0.1.0",
    description="Bridge between UiPath Maestro and the external risk agents.",
)

app.include_router(research.router)
app.include_router(financial.router)
app.include_router(risk.router)
app.include_router(vendors.router)
app.include_router(monitoring.router)


@app.get("/health", tags=["meta"])
def health() -> dict:
    return {"status": "ok", "phase": 1, "mode": "mock"}
