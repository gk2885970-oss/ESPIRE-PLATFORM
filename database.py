from connect import engine
from sqlalchemy.orm import sessionmaker
from sql_models import Base

Base.metadata.create_all(bind=engine)

SessionLocal = sessionmaker(autoflush=False, autocommit=False, bind=engine)
