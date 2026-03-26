# Espire Platform

An e-sports tournament management platform for FreeFire Max, providing a REST API for team registration, match performance tracking, community posts, and admin management.

## Architecture

- **Backend:** FastAPI (Python) with Uvicorn/Gunicorn ASGI server
- **Database:** PostgreSQL (Replit built-in), managed via SQLAlchemy ORM
- **Authentication:** JWT-based (python-jose) with Argon2 password hashing (passlib)
- **Migrations:** Alembic (schema auto-created on startup via SQLAlchemy metadata)

## Project Structure

| File | Purpose |
|------|---------|
| `endpoints.py` | Main FastAPI app, all routes and middleware |
| `sql_models.py` | SQLAlchemy table definitions |
| `pydantic_model.py` | Pydantic request/response schemas and settings |
| `database.py` | DB session and schema initialization |
| `connect.py` | SQLAlchemy engine creation (uses `DATABASE_URL` env var) |
| `admin.json` | Seed data for initial admin accounts |
| `important.env` | Local env config (SECRET_KEY, ALGORITHM, Expire_Time) |

## Running the App

The workflow runs:
```
uvicorn endpoints:espire --host 0.0.0.0 --port 5000 --reload
```

## Key API Routes

- `POST /registerTeam` — Register a new team
- `POST /loginTeam` — Team login (returns JWT)
- `POST /loginAdmin` — Admin login (returns JWT)
- `GET /teamProfile` — View team profile (auth required)
- `POST /createTeamMatch` — Create a match (admin only)
- `POST /createMatchPerformance` — Record match performance (admin only)
- `POST /community/createPost` — Create community post from match results (admin only)
- `GET /community/posts` — List all community posts
- `POST /community/{post_id}/team_comment` — Add comment (team auth)
- `GET /docs` — Interactive API docs (Swagger UI)

## Environment Variables

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string (set by Replit) |
| `SECRET_KEY` | JWT signing key (from important.env) |
| `ALGORITHM` | JWT algorithm, default HS256 |
| `Expire_Time` | Token expiry in minutes, default 30 |

## Deployment

Configured for autoscale deployment using:
```
gunicorn --bind=0.0.0.0:5000 --reuse-port --worker-class=uvicorn.workers.UvicornWorker endpoints:espire
```
