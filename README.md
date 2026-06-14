# SafetyHub Incident Reporting App

SafetyHub is a portfolio full stack app for recording construction health and safety incidents, hazards, near misses, corrective actions, and dashboard metrics.

The project is designed to show practical software development skills for internal business systems: clean CRUD flows, validation, reporting, workflow states, SQLite persistence, and a usable dashboard-style interface.

## Features

- Incident, hazard, near-miss, and observation reporting
- Severity and status workflow
- Corrective action tracking with owners and due dates
- Dashboard metrics for open incidents, critical incidents, and overdue actions
- Search and status filtering
- CSV export for incident registers
- Seed data for demo walkthroughs
- FastAPI backend with Pydantic validation
- Plain HTML, CSS, and JavaScript frontend

## Tech Stack

- Python
- FastAPI
- Pydantic
- SQLite
- HTML
- CSS
- JavaScript

## Run Locally

Create and activate a virtual environment, then install dependencies:

```bash
pip install -r requirements.txt
```

Seed the database:

```bash
cd backend
python seed.py
```

Start the app:

```bash
uvicorn main:app --reload
```

Open:

```text
http://127.0.0.1:8000
```

## API Endpoints

- `GET /api/dashboard`
- `GET /api/incidents`
- `POST /api/incidents`
- `GET /api/incidents/{incident_id}`
- `PATCH /api/incidents/{incident_id}`
- `POST /api/incidents/{incident_id}/actions`
- `PATCH /api/actions/{action_id}`
- `GET /api/export/incidents.csv`

## Portfolio Talking Points

This project demonstrates:

- Designing a small domain model for a real business workflow
- Building a REST API with validation and clear endpoint boundaries
- Persisting data using SQLite with foreign-key relationships
- Creating dashboard metrics from operational data
- Building a responsive frontend without relying on heavy UI templates
- Adding reporting/export functionality expected in business software

## Future Improvements

- Role-based access for admin, reporter, investigator, and reviewer users
- File/photo evidence uploads
- Email notifications for overdue corrective actions
- PDF incident reports
- Audit log for status and severity changes
- Automated test coverage for all workflow transitions

