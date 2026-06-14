from __future__ import annotations

import csv
import io
from datetime import date, datetime
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

try:
    from .database import connect, initialise_database, row_to_dict
except ImportError:
    from database import connect, initialise_database, row_to_dict


IncidentType = Literal["incident", "near_miss", "hazard", "observation"]
Severity = Literal["low", "medium", "high", "critical"]
IncidentStatus = Literal["open", "investigating", "action_required", "closed"]
ActionStatus = Literal["open", "in_progress", "complete"]


class IncidentCreate(BaseModel):
    title: str = Field(min_length=3, max_length=120)
    incident_type: IncidentType
    severity: Severity
    location: str = Field(min_length=2, max_length=120)
    reported_by: str = Field(min_length=2, max_length=80)
    assigned_to: str | None = Field(default=None, max_length=80)
    description: str = Field(min_length=10, max_length=2000)
    immediate_action: str | None = Field(default=None, max_length=1000)
    occurred_at: datetime


class IncidentUpdate(BaseModel):
    severity: Severity | None = None
    status: IncidentStatus | None = None
    assigned_to: str | None = Field(default=None, max_length=80)
    immediate_action: str | None = Field(default=None, max_length=1000)


class CorrectiveActionCreate(BaseModel):
    owner: str = Field(min_length=2, max_length=80)
    action: str = Field(min_length=5, max_length=1000)
    due_date: date


class CorrectiveActionUpdate(BaseModel):
    status: ActionStatus


app = FastAPI(title="SafetyHub Incident Reporting API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = Path(__file__).resolve().parents[1] / "frontend"
app.mount("/assets", StaticFiles(directory=FRONTEND_DIR), name="assets")


@app.on_event("startup")
def startup() -> None:
    initialise_database()


def create_reference(db) -> str:
    year = datetime.utcnow().year
    count = db.execute(
        "SELECT COUNT(*) AS total FROM incidents WHERE reference LIKE ?",
        (f"HS-{year}-%",),
    ).fetchone()["total"]
    return f"HS-{year}-{count + 1:04d}"


def get_incident_or_404(incident_id: int) -> dict:
    with connect() as db:
        incident = row_to_dict(
            db.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,)).fetchone()
        )
        if not incident:
            raise HTTPException(status_code=404, detail="Incident not found")

        actions = db.execute(
            "SELECT * FROM corrective_actions WHERE incident_id = ? ORDER BY due_date ASC",
            (incident_id,),
        ).fetchall()
        incident["corrective_actions"] = [dict(action) for action in actions]
        return incident


@app.get("/")
def index() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/api/health")
def health_check() -> dict:
    return {"status": "ok", "service": "SafetyHub Incident Reporting"}


@app.get("/api/incidents")
def list_incidents(
    status: IncidentStatus | None = None,
    severity: Severity | None = None,
    search: str | None = None,
) -> dict:
    clauses: list[str] = []
    params: list[str] = []

    if status:
        clauses.append("status = ?")
        params.append(status)
    if severity:
        clauses.append("severity = ?")
        params.append(severity)
    if search:
        clauses.append("(title LIKE ? OR location LIKE ? OR reference LIKE ?)")
        term = f"%{search}%"
        params.extend([term, term, term])

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""

    with connect() as db:
        rows = db.execute(
            f"""
            SELECT i.*,
                COUNT(a.id) AS action_count,
                SUM(CASE WHEN a.status != 'complete' THEN 1 ELSE 0 END) AS open_action_count
            FROM incidents i
            LEFT JOIN corrective_actions a ON a.incident_id = i.id
            {where}
            GROUP BY i.id
            ORDER BY i.created_at DESC
            """,
            params,
        ).fetchall()
        return {"incidents": [dict(row) for row in rows]}


@app.post("/api/incidents", status_code=201)
def create_incident(payload: IncidentCreate) -> dict:
    with connect() as db:
        reference = create_reference(db)
        cursor = db.execute(
            """
            INSERT INTO incidents (
                reference, title, incident_type, severity, status, location,
                reported_by, assigned_to, description, immediate_action, occurred_at
            )
            VALUES (?, ?, ?, ?, 'open', ?, ?, ?, ?, ?, ?)
            """,
            (
                reference,
                payload.title,
                payload.incident_type,
                payload.severity,
                payload.location,
                payload.reported_by,
                payload.assigned_to,
                payload.description,
                payload.immediate_action,
                payload.occurred_at.isoformat(),
            ),
        )
        db.commit()
        return get_incident_or_404(cursor.lastrowid)


@app.get("/api/incidents/{incident_id}")
def get_incident(incident_id: int) -> dict:
    return get_incident_or_404(incident_id)


@app.patch("/api/incidents/{incident_id}")
def update_incident(incident_id: int, payload: IncidentUpdate) -> dict:
    existing = get_incident_or_404(incident_id)
    updates = payload.model_dump(exclude_unset=True)

    if not updates:
        return existing

    assignments = ", ".join([f"{field} = ?" for field in updates])
    values = list(updates.values()) + [datetime.utcnow().isoformat(), incident_id]

    with connect() as db:
        db.execute(
            f"UPDATE incidents SET {assignments}, updated_at = ? WHERE id = ?",
            values,
        )
        db.commit()

    return get_incident_or_404(incident_id)


@app.post("/api/incidents/{incident_id}/actions", status_code=201)
def add_corrective_action(incident_id: int, payload: CorrectiveActionCreate) -> dict:
    get_incident_or_404(incident_id)

    with connect() as db:
        cursor = db.execute(
            """
            INSERT INTO corrective_actions (incident_id, owner, action, due_date)
            VALUES (?, ?, ?, ?)
            """,
            (incident_id, payload.owner, payload.action, payload.due_date.isoformat()),
        )
        db.execute(
            "UPDATE incidents SET status = 'action_required', updated_at = ? WHERE id = ?",
            (datetime.utcnow().isoformat(), incident_id),
        )
        db.commit()
        action = row_to_dict(
            db.execute("SELECT * FROM corrective_actions WHERE id = ?", (cursor.lastrowid,)).fetchone()
        )
        return {"action": action, "incident": get_incident_or_404(incident_id)}


@app.patch("/api/actions/{action_id}")
def update_corrective_action(action_id: int, payload: CorrectiveActionUpdate) -> dict:
    completed_at = datetime.utcnow().isoformat() if payload.status == "complete" else None

    with connect() as db:
        action = db.execute("SELECT * FROM corrective_actions WHERE id = ?", (action_id,)).fetchone()
        if not action:
            raise HTTPException(status_code=404, detail="Corrective action not found")

        db.execute(
            "UPDATE corrective_actions SET status = ?, completed_at = ? WHERE id = ?",
            (payload.status, completed_at, action_id),
        )
        db.commit()
        return {"incident": get_incident_or_404(action["incident_id"])}


@app.get("/api/dashboard")
def dashboard() -> dict:
    with connect() as db:
        total = db.execute("SELECT COUNT(*) AS total FROM incidents").fetchone()["total"]
        open_total = db.execute(
            "SELECT COUNT(*) AS total FROM incidents WHERE status != 'closed'"
        ).fetchone()["total"]
        critical_total = db.execute(
            "SELECT COUNT(*) AS total FROM incidents WHERE severity = 'critical'"
        ).fetchone()["total"]
        overdue_actions = db.execute(
            """
            SELECT COUNT(*) AS total FROM corrective_actions
            WHERE status != 'complete' AND due_date < DATE('now')
            """
        ).fetchone()["total"]
        by_type = db.execute(
            "SELECT incident_type, COUNT(*) AS total FROM incidents GROUP BY incident_type"
        ).fetchall()
        by_status = db.execute(
            "SELECT status, COUNT(*) AS total FROM incidents GROUP BY status"
        ).fetchall()

    return {
        "total_incidents": total,
        "open_incidents": open_total,
        "critical_incidents": critical_total,
        "overdue_actions": overdue_actions,
        "by_type": [dict(row) for row in by_type],
        "by_status": [dict(row) for row in by_status],
    }


@app.get("/api/export/incidents.csv")
def export_incidents_csv() -> Response:
    with connect() as db:
        rows = db.execute(
            """
            SELECT reference, title, incident_type, severity, status, location,
                reported_by, assigned_to, occurred_at, created_at
            FROM incidents
            ORDER BY created_at DESC
            """
        ).fetchall()

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=list(rows[0].keys()) if rows else ["reference"])
    writer.writeheader()
    for row in rows:
        writer.writerow(dict(row))

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=safetyhub-incidents.csv"},
    )
