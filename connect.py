from sqlalchemy import create_engine,text

database_url = postgresql://espire_database_user:BPoJBnY1X91Q03lHy7fnHseTBLgvpJmA@dpg-d722n2kr85hc73co85p0-a/espire_database
engine = create_engine(database_url,echo=True)
print(f"Connecting to URL {engine.dialect.name}")



# with engine.connect() as conn:
#     conn.execute(text("DROP SCHEMA public CASCADE;"))
#     conn.execute(text("CREATE SCHEMA public;"))
