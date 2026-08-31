import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text


load_dotenv()

database_url = os.getenv("DATABASE_URL")

if not database_url:
    raise ValueError("DATABASE_URL is not set in the .env file.")

engine = create_engine(database_url)

try:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1;"))
        print("Database connection successful!")
        print("Test query result:", result.scalar())
except Exception as exc:
    print("Database connection failed.")
    print(exc)