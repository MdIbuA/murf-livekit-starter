"""
analytics_api.py — Day 8: Call Analytics REST API for Kisan Mitra
Runs on port 8002. Zero PII exposed.

Endpoints:
  GET /health               → {status, service}
  GET /stats                → aggregate call metrics
  GET /stats/daily          → per-day breakdown (last 7 days)
  GET /calls                → recent call history (last 50, PII-free)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional

from src import db

app = FastAPI(
    title="Kisan Mitra — Call Analytics API",
    description="Call outcome statistics for the Kisan Mitra AI farming voice agent. No PII.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    db.init_db()


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/health", tags=["System"])
def health():
    return {"status": "ok", "service": "kisan-mitra-analytics"}


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

@app.get("/stats", tags=["Analytics"])
def get_stats():
    """
    Returns aggregate call statistics.
    Fields: total, success, failed, incomplete, success_rate (%),
            avg_duration_seconds, escalated_count, today_total, today_success
    """
    return db.get_call_stats()


@app.get("/stats/daily", tags=["Analytics"])
def get_daily_stats(days: int = Query(default=7, ge=1, le=30)):
    """
    Returns per-day call counts for the last N days (default 7).
    Each entry: {date, total, success, failed}
    """
    return {"days": days, "data": db.get_daily_stats(days=days)}


# ---------------------------------------------------------------------------
# Call history (PII-free)
# ---------------------------------------------------------------------------

@app.get("/calls", tags=["Analytics"])
def list_calls(limit: int = Query(default=50, ge=1, le=200)):
    """
    Returns recent call logs — newest first, capped at `limit`.
    PII-safe: no farmer names, no transcripts, no phone numbers.
    session_id is shown in truncated form for reference only.
    """
    raw = db.list_call_logs(limit=limit)

    # Truncate session_id for display (no private room names)
    safe = []
    for r in raw:
        safe.append({
            "id":               r.get("id"),
            "session_ref":      (r.get("session_id") or "")[:12] + "…",
            "channel":          r.get("channel", "browser"),
            "language":         r.get("language", "Tamil"),
            "started_at":       r.get("started_at"),
            "ended_at":         r.get("ended_at"),
            "duration_seconds": r.get("duration_seconds"),
            "outcome":          r.get("outcome", "incomplete"),
            "failure_type":     r.get("failure_type", "none"),
            "topics_discussed": r.get("topics_discussed", ""),
            "tools_called":     r.get("tools_called", ""),
            "escalated":        bool(r.get("escalated", 0)),
        })
    return {"count": len(safe), "calls": safe}
