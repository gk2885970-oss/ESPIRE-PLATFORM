from connect import engine

from sqlalchemy.orm import sessionmaker

SessionLocal = sessionmaker(autoflush=False, autocommit=False,bind=engine)
