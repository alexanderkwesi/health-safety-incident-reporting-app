import sys
from pathlib import Path

from fastapi.testclient import TestClient


PROJECT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from database import DB_PATH, initialise_database  # noqa: E402
from main import app  # noqa: E402


def setup_function():
    if DB_PATH.exists():
        DB_PATH.unlink()
    initialise_database()


def test_create_and_list_incident():
    with TestClient(app) as client:
        response = client.post(
            "/api/incidents",
            json={
                "title": "Unprotected edge spotted on level three",
                "incident_type": "hazard",
                "severity": "high",
                "location": "Level 3 stair core",
                "reported_by": "Test User",
                "assigned_to": "Site Manager",
                "description": "Temporary edge protection was missing from an active working area.",
                "immediate_action": "Area isolated and supervisor notified.",
                "occurred_at": "2026-06-13T10:00:00Z",
            },
        )

        assert response.status_code == 201
        incident = response.json()
        assert incident["reference"].startswith("HS-")
        assert incident["status"] == "open"

        list_response = client.get("/api/incidents?severity=high")
        assert list_response.status_code == 200
        assert len(list_response.json()["incidents"]) == 1


def test_corrective_action_moves_incident_to_action_required():
    with TestClient(app) as client:
        incident = client.post(
            "/api/incidents",
            json={
                "title": "Damaged access ladder removed from use",
                "incident_type": "incident",
                "severity": "medium",
                "location": "Plant room",
                "reported_by": "Test User",
                "description": "A damaged ladder was found before use during routine checks.",
                "occurred_at": "2026-06-13T10:00:00Z",
            },
        ).json()

        response = client.post(
            f"/api/incidents/{incident['id']}/actions",
            json={
                "owner": "Facilities Lead",
                "action": "Replace ladder and brief team on pre-use inspections.",
                "due_date": "2026-06-20",
            },
        )

        assert response.status_code == 201
        assert response.json()["incident"]["status"] == "action_required"
        assert response.json()["incident"]["corrective_actions"][0]["status"] == "open"
