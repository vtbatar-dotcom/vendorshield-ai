"""Canonical request/response schemas for VendorShield API.

These match exactly what the live endpoints accept and return.
"""
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel


class ResearchRequest(BaseModel):
    vendor_name: str
    vendor_domain: Optional[str] = None
    vendor_id: str


class FinancialRequest(BaseModel):
    vendor_name: str
    vendor_id: str
    duns_number: Optional[str] = None


class NewsItem(BaseModel):
    title: str
    url: str
    published: str
    sentiment: float


class FinancialData(BaseModel):
    vendor_id: str
    credit_score: int
    financial_health: str
    revenue_trend: str
    bankruptcy_risk: float


class RiskRequest(BaseModel):
    vendor_id: str
    research_signals: list[str] = []
    news_items: list[NewsItem] = []
    sentiment_score: float = 0.0
    compliance_gaps: list[str] = []
    financial_data: Optional[FinancialData] = None
    sanctions_hits: list[str] = []


class DimensionScores(BaseModel):
    security: int
    compliance: int
    financial: int
    operational: int
    esg: int


class RiskResponse(BaseModel):
    vendor_id: str
    overall_score: int
    dimension_scores: DimensionScores
    confidence: int
    classification: str
    routing: str
    flags: list[str]


class MonitoringRequest(BaseModel):
    vendor_id: str


class MonitoringResponse(BaseModel):
    vendor_id: str
    alerts: list[str]
    risk_delta: int
    requires_reopen: bool


class CaseResponse(BaseModel):
    case_id: str
    vendor_id: str
    stage: str
    sla_status: str
    findings: list[str]
    decisions: list[str]
