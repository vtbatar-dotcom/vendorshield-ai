from fastapi import FastAPI
from api.routes import research, financial, risk, vendors, monitoring, orchestrator

app = FastAPI(
    title="VendorShield AI API",
    version="0.9.0",
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
    return {
        "status": "ok",
        "version": "0.9.0",
        "agents": {
            "main_api": "port 8000",
            "research": "port 8001 (Claude + Tavily)",
            "compliance": "port 8002 (Claude)",
            "financial": "port 8003 (Claude analyst+reviewer)",
            "remediation": "port 8004 (Claude)"
        },
        "note": "Mock endpoints on /api/research and /api/financial are for contract documentation only. Use ports 8001/8003 for real agents."
    }
