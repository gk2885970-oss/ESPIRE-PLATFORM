import os
from sqlalchemy import create_engine

database_url = os.environ.get("DATABASE_URL")

engine = create_engine(
    database_url,
    echo=True,
    pool_pre_ping=True  # connection stable rakhega
)

print(f"Connecting to: {engine.dialect.name}")
