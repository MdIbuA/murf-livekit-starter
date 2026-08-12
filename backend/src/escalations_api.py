"""
Day 7 — Kisan Mitra Escalations Dashboard API
==============================================
Tiny FastAPI service that exposes escalation records from the SQLite database.
Run separately on port 8001:

    uvicorn src.escalations_api:app --port 8001 --reload

Endpoints:
  GET  /escalations                  — list all (or filter by ?status=open)
  GET  /escalations/{reference_id}   — fetch single escalation
  PATCH /escalations/{reference_id}  — update status
  GET  /health                       — health check
"""

import os
import sys

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src import db

app = FastAPI(
    title="Kisan Mitra — Escalations Dashboard API",
    description="Human escalation requests from the Kisan Mitra voice agent",
    version="1.0.0",
)

# Allow the local HTML dashboard to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)


class StatusUpdate(BaseModel):
    status: str  # 'open' | 'in_progress' | 'resolved'


@app.get("/health")
def health():
    return {"status": "ok", "service": "kisan-mitra-escalations"}


@app.get("/escalations")
def list_escalations(status: str = Query(default=None, description="Filter by status: open | in_progress | resolved")):
    """Return all escalation records, newest first. Optionally filter by status."""
    try:
        records = db.list_escalations(status=status)
        return {"count": len(records), "escalations": records}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/escalations/{reference_id}")
def get_escalation(reference_id: str):
    """Fetch a single escalation by reference ID (e.g. KM-20260812-0001)."""
    record = db.get_escalation(reference_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Escalation '{reference_id}' not found")
    return record


@app.patch("/escalations/{reference_id}")
def update_status(reference_id: str, body: StatusUpdate):
    """Update the status of an escalation (open → in_progress → resolved)."""
    try:
        updated = db.update_escalation_status(reference_id, body.status)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if not updated:
        raise HTTPException(status_code=404, detail=f"Escalation '{reference_id}' not found")
    return updated


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.escalations_api:app", host="0.0.0.0", port=8001, reload=True)
