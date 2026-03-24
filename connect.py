from sqlalchemy import create_engine,text

database_url = "postgresql://postgres:Rau80nsql@localhost:5432/espire"
engine = create_engine(database_url,echo=True)
print(f"Connecting to URL {engine.dialect.name}")



# with engine.connect() as conn:
#     conn.execute(text("DROP SCHEMA public CASCADE;"))
#     conn.execute(text("CREATE SCHEMA public;"))