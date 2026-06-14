from __future__ import annotations

from datetime import datetime, timedelta

from database import connect, initialise_database
from main import create_reference


seed_incidents = [
    {
        "title": "Trailing cable identified near temporary welfare unit",
        "incident_type": "hazard",
        "severity": "medium",
        "status": "action_required",
        "location": "North compound",
        "reported_by": "A. Davies",
        "assigned_to": "Site Manager",
        "description": "A trailing power cable was found crossing a pedestrian route near the welfare unit entrance.",
        "immediate_action": "Cable route isolated and temporary matting installed.",
        "occurred_at": datetime.utcnow() - timedelta(days=1, hours=3),
        "actions": [
            {
                "owner": "Site Manager",
                "action": "Install overhead cable protection and update pedestrian route inspection checklist.",
                "due_date": datetime.utcnow().date() + timedelta(days=3),
                "status": "in_progress",
            }
        ],
    },
    {
        "title": "Near miss during telehandler reversing movement",
        "incident_type": "near_miss",
        "severity": "high",
        "status": "investigating",
        "location": "Loading bay B",
        "reported_by": "M. Khan",
        "assigned_to": "Logistics Lead",
        "description": "A pedestrian entered the vehicle exclusion zone while a telehandler was reversing with materials.",
        "immediate_action": "Work stopped and banksman briefed the team before movement restarted.",
        "occurred_at": datetime.utcnow() - timedelta(days=2),
        "actions": [],
    },
    {
        "title": "Minor hand cut while opening packaging",
        "incident_type": "incident",
        "severity": "low",
        "status": "closed",
        "location": "Fit-out area level 2",
        "reported_by": "J. Smith",
        "assigned_to": "Supervisor",
        "description": "Operative sustained a minor cut while opening packaging with an unsuitable blade.",
        "immediate_action": "First aid provided and safer cutting tool issued.",
        "occurred_at": datetime.utcnow() - timedelta(days=8),
        "actions": [
            {
                "owner": "Supervisor",
                "action": "Complete toolbox talk on safe opening of packaged materials.",
                "due_date": datetime.utcnow().date() - timedelta(days=4),
                "status": "complete",
            }
        ],
    },
]


def seed() -> None:
    initialise_database()
    with connect() as db:
        existing = db.execute("SELECT COUNT(*) AS total FROM incidents").fetchone()["total"]
        if existing:
            print("Seed skipped because incidents already exist.")
            return

        for incident in seed_incidents:
            reference = create_reference(db)
            cursor = db.execute(
                """
                INSERT INTO incidents (
                    reference, title, incident_type, severity, status, location,
                    reported_by, assigned_to, description, immediate_action, occurred_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    reference,
                    incident["title"],
                    incident["incident_type"],
                    incident["severity"],
                    incident["status"],
                    incident["location"],
                    incident["reported_by"],
                    incident["assigned_to"],
                    incident["description"],
                    incident["immediate_action"],
                    incident["occurred_at"].isoformat(),
                ),
            )

            for action in incident["actions"]:
                completed_at = datetime.utcnow().isoformat() if action["status"] == "complete" else None
                db.execute(
                    """
                    INSERT INTO corrective_actions (
                        incident_id, owner, action, due_date, status, completed_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        cursor.lastrowid,
                        action["owner"],
                        action["action"],
                        action["due_date"].isoformat(),
                        action["status"],
                        completed_at,
                    ),
                )

        db.commit()
    print("Seed data created.")


if __name__ == "__main__":
    seed()

