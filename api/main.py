from fastapi import FastAPI
from api.routes import research, financial, risk, vendors, monitoring, orchestrator

app = FastAPI(
    title="VendorShield AI API",
    version="0.2.0",
    description="Bridge between UiPath Maestro and the external risk agents.",
)

app.include_router(research.router)
app.include_router(financial.router)
app.include_router(risk.router)
app.include_router(vendors.router)
app.include_router(monitoring.router)
app.include_router(orchestrator.router)

@app.get("/health", tags=["meta"])
def health() -> dict:
    return {"status": "ok", "phase": 2, "mode": "live", "agents": 4}
