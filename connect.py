import os
from sqlalchemy import create_engine

# Get database URL from environment variable (Render / Replit Secrets)
database_url = os.environ.get("DATABASE_URL")

# Fallback (agar environment variable set nahi hai)
if not database_url:
    database_url = "postgresql://espire_database_user:BPoJBnY1X91Q03lHy7fnHseTBLgvpJmA@dpg-d722n2kr85hc73co85p0-a/espire_database?sslmode=require"

# Fix postgres:// issue (some platforms use this format)
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

# Create SQLAlchemy engine
engine = create_engine(
    database_url,
    echo=True,
    pool_pre_ping=True
)

print(f"Connecting to database using: {engine.dialect.name}")
