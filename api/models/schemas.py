"""Request/response schemas for the VendorShield API.

These mirror the contract in the project spec exactly so that the UiPath
API Workflows can be wired against them while the real agent logic is still
being built. In Phase 1 the endpoints return deterministic mock data.
"""
from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel, Field


# ---------- Research agent ----------
class ResearchRequest(BaseModel):
    vendor_name: str
    vendor_domain: Optional[str] = None
    vendor_id: str


class NewsItem(BaseModel):
    title: str
    url: str
    published: str
    sentiment: float = Field(ge=-1.0, le=1.0)


class ResearchResponse(BaseModel):
    vendor_id: str
    risk_signals: list[str]
    sentiment_score: float = Field(ge=-1.0, le=1.0)
    news_items: list[NewsItem]
    sanctions_hits: list[str]


# ---------- Financial agent ----------
class FinancialRequest(BaseModel):
    vendor_name: str
    vendor_id: str
    duns_number: Optional[str] = None


class FinancialResponse(BaseModel):
    vendor_id: str
    credit_score: int = Field(ge=0, le=100)
    financial_health: Literal["strong", "stable", "weak", "distressed"]
    revenue_trend: Literal["growing", "flat", "declining"]
    bankruptcy_risk: float = Field(ge=0.0, le=1.0)


# ---------- Risk scoring agent ----------
class RiskRequest(BaseModel):
    vendor_id: str
    research_signals: list[str] = []
    compliance_gaps: list[str] = []
    financial_data: Optional[FinancialResponse] = None


class DimensionScores(BaseModel):
    security: int = Field(ge=0, le=100)
    compliance: int = Field(ge=0, le=100)
    financial: int = Field(ge=0, le=100)
    operational: int = Field(ge=0, le=100)
    esg: int = Field(ge=0, le=100)


class RiskResponse(BaseModel):
    vendor_id: str
    overall_score: int = Field(ge=0, le=100)
    dimension_scores: DimensionScores
    confidence: int = Field(ge=0, le=100)
    classification: Literal["Low", "Medium", "High", "Critical"]


# ---------- Case lookup ----------
class CaseResponse(BaseModel):
    case_id: str
    vendor_id: str
    stage: str
    sla_status: Literal["on_track", "at_risk", "breached"]
    findings: list[str]
    decisions: list[str]


# ---------- Monitoring ----------
class MonitoringRequest(BaseModel):
    vendor_id: str


class MonitoringResponse(BaseModel):
    vendor_id: str
    alerts: list[str]
    risk_delta: int
    requires_reopen: bool
