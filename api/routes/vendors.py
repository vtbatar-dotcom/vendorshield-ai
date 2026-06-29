"""Vendor case store — SQLite-backed.

Stores the last full assessment result per vendor_id.
POST /api/vendors/{vendor_id}/store — save a result
GET  /api/vendors/{vendor_id}/case  — retrieve it
"""
from __future__ import annotations
import sqlite3, json, os
from pathlib import Path
from fastapi import APIRouter, HTTPException
from api.models.schemas import CaseResponse

router = APIRouter(prefix="/api/vendors", tags=["vendors"])

DB_PATH = Path(os.getenv("DATABASE_URL", "").replace("sqlite:///", "")) or Path("vendorshield.db")
if str(DB_PATH).startswith("postgresql"):
    DB_PATH = Path("vendorshield.db")


def get_db() -> sqlite3.Connection:
    db = sqlite3.connect("vendorshield.db")
    db.execute("""
        CREATE TABLE IF NOT EXISTS vendor_cases (
            vendor_id TEXT PRIMARY KEY,
            stage TEXT,
            overall_score INTEGER,
            classification TEXT,
            findings TEXT,
            decisions TEXT,
            sla_status TEXT,
            updated_at TEXT
        )
    """)
    db.commit()
    return db


@router.get("/{vendor_id}/case", response_model=CaseResponse)
def get_case(vendor_id: str) -> CaseResponse:
    db = get_db()
    row = db.execute(
        "SELECT * FROM vendor_cases WHERE vendor_id = ?", (vendor_id,)
    ).fetchone()
    db.close()

    if not row:
        raise HTTPException(status_code=404, detail=f"No case found for vendor {vendor_id}")

    return CaseResponse(
        case_id=f"CASE-{row[0]}",
        vendor_id=row[0],
        stage=row[1] or "Assessment",
        sla_status=row[6] or "on_track",
        findings=json.loads(row[4] or "[]"),
        decisions=json.loads(row[5] or "[]"),
    )


@router.post("/{vendor_id}/store")
def store_case(vendor_id: str, payload: dict) -> dict:
    """Store assessment result. Called by orchestrator after full assessment."""
    from datetime import datetime
    db = get_db()
    db.execute("""
        INSERT OR REPLACE INTO vendor_cases
        (vendor_id, stage, overall_score, classification, findings, decisions, sla_status, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        vendor_id,
        payload.get("stage", "Assessment"),
        payload.get("overall_score", 0),
        payload.get("classification", "Unknown"),
        json.dumps(payload.get("findings", [])),
        json.dumps(payload.get("decisions", [])),
        payload.get("sla_status", "on_track"),
        datetime.utcnow().isoformat()
    ))
    db.commit()
    db.close()
    return {"status": "stored", "vendor_id": vendor_id}
