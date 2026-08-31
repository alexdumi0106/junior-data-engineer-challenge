import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

from ingest_fx import main as refresh_fx_rates

def run_sql_file(engine, file_path: Path):
    sql = file_path.read_text(encoding="utf-8")

    with engine.begin() as connection:
        connection.execute(text(sql))

def main():
    print("Starting daily data pipeline...")

    try:
        load_dotenv()

        database_url = os.getenv("DATABASE_URL")

        if not database_url:
            raise ValueError("DATABASE_URL is not set.")

        engine = create_engine(database_url)

        project_root = Path(__file__).resolve().parent.parent
        sql_dir = project_root / "sql"

        print("Step 1: Refresh FX rates")
        refresh_fx_rates()

        print("Step 2: Refresh customer spend")
        run_sql_file(
            engine,
            sql_dir / "customer_spend.sql"
        )

        print("Step 3: Refresh country/category sales")
        run_sql_file(
            engine,
            sql_dir / "country_category_sales.sql"
        )

        print("Pipeline finished successfully.")

    except Exception as exc:
        print(f"Pipeline failed: {exc}")
        raise


if __name__ == "__main__":
    main()