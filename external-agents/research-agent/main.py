from __future__ import annotations
import os
from dotenv import load_dotenv
load_dotenv(dotenv_path="../../.env")
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from agent import run_research

app = FastAPI(title="VendorShield Research Agent", version="0.2.0")

class ResearchRequest(BaseModel):
    vendor_name: str
    vendor_domain: str | None = None
    vendor_id: str

class NewsItem(BaseModel):
    title: str
    url: str
    published: str
    sentiment: float

class ResearchResponse(BaseModel):
    vendor_id: str
    risk_signals: list[str]
    sentiment_score: float
    news_items: list[NewsItem]
    sanctions_hits: list[str]

@app.get("/health")
def health():
    return {"status": "ok", "agent": "research", "llm": "claude-sonnet-4-6"}

@app.post("/assess", response_model=ResearchResponse)
def assess(req: ResearchRequest) -> ResearchResponse:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not set")
    if not os.environ.get("TAVILY_API_KEY"):
        raise HTTPException(status_code=500, detail="TAVILY_API_KEY not set")
    result = run_research(req.vendor_name, req.vendor_domain)
    news_items = [NewsItem(title=n.get("title",""), url=n.get("url",""), published=n.get("published",""), sentiment=float(n.get("sentiment",0.0))) for n in result.get("news_items",[])]
    return ResearchResponse(vendor_id=req.vendor_id, risk_signals=result.get("risk_signals",[]), sentiment_score=float(result.get("sentiment_score",0.0)), news_items=news_items, sanctions_hits=result.get("sanctions_hits",[]))
