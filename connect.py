import os
from sqlalchemy import create_engine

database_url = os.environ.get(
    "DATABASE_URL",
    "postgresql://espire_database_user:BPoJBnY1X91Q03lHy7fnHseTBLgvpJmA@dpg-d722n2kr85hc73co85p0-a/espire_database"
)

if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

engine = create_engine(database_url, echo=True)
print(f"Connecting to: {engine.dialect.name}")
