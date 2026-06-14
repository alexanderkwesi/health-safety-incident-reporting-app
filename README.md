# SafetyHub Incident Reporting App

SafetyHub is a portfolio full stack app for recording construction health and safety incidents, hazards, near misses, corrective actions, and dashboard metrics.

The project is designed to show practical software development skills for internal business systems: CRUD workflows, validation, JWT authentication, SQL persistence, dashboard reporting, Dockerised delivery, and automated tests.

## Features

- Incident, hazard, near-miss, and observation reporting
- Severity and status workflow
- Corrective action tracking with owners and due dates
- Dashboard metrics for open incidents, critical incidents, and overdue actions
- Search and status filtering
- CSV export for incident registers
- JWT login for protected write actions
- SQLite for quick local development
- PostgreSQL support through `DATABASE_URL`
- Docker Compose setup for FastAPI and PostgreSQL
- GitHub Actions workflow for automated API tests

## Tech Stack

- Python
- FastAPI
- Pydantic
- SQLAlchemy
- SQLite
- PostgreSQL
- JWT authentication
- Docker
- GitHub Actions
- HTML
- CSS
- JavaScript

## Run Locally

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the app with local SQLite:

```bash
python -m uvicorn backend.main:app --reload
```

Open:

```text
http://127.0.0.1:8000
```

Demo login:

```text
Username: admin
Password: SafetyHub123!
```

Optional seed data:

```bash
python backend/seed.py
```

## Run With Docker And PostgreSQL

Start the API and PostgreSQL:

```bash
docker compose up --build
```

The app runs at:

```text
http://127.0.0.1:8000
```

The Compose stack sets:

```text
DATABASE_URL=postgresql://safetyhub:safetyhub@db:5432/safetyhub
```

## API Endpoints

- `GET /api/health`
- `POST /api/auth/login`
- `GET /api/dashboard`
- `GET /api/incidents`
- `POST /api/incidents` requires bearer token
- `GET /api/incidents/{incident_id}`
- `PATCH /api/incidents/{incident_id}` requires bearer token
- `POST /api/incidents/{incident_id}/actions` requires bearer token
- `PATCH /api/actions/{action_id}` requires bearer token
- `GET /api/export/incidents.csv`

## Automated Tests

Run locally:

```bash
python -m pytest
```

GitHub Actions runs the same test command on pushes and pull requests that touch this project.

## Portfolio Talking Points

This project demonstrates:

- Designing a small domain model for a real business workflow
- Building a REST API with validation and clear endpoint boundaries
- Persisting data with SQLAlchemy and supporting SQLite/PostgreSQL
- Implementing JWT login and protected write endpoints
- Packaging a FastAPI app with Docker and Docker Compose
- Adding CI coverage with GitHub Actions
- Creating dashboard metrics from operational data
- Building a responsive frontend without relying on heavy UI templates
- Adding reporting/export functionality expected in business software

## Future Improvements

- Granular role permissions for admin, reporter, investigator, and reviewer users
- React and TypeScript frontend version
- File/photo evidence uploads
- Email notifications for overdue corrective actions
- PDF incident reports
- Audit log for status and severity changes
