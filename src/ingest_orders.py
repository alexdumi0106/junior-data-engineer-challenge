import os

import pandas as pd
import requests
from dotenv import load_dotenv
from sqlalchemy import create_engine, text


ORDERS_API_URL = (
    "https://jzozteoirwfczccltcdr.supabase.co/rest/v1/orders_raw"
    "?apikey=sb_publishable_Xwjiw--qkKcbMuSbKd6I2w_wN9mpNTv"
)


def fetch_orders() -> pd.DataFrame:
    """Get the raw orders from the API."""
    response = requests.get(ORDERS_API_URL, timeout=30)
    response.raise_for_status()

    data = response.json()

    if not isinstance(data, list):
        raise ValueError("Unexpected API response: expected a list of orders.")

    return pd.DataFrame(data)


def load_orders(df: pd.DataFrame) -> None:
    """Save the raw orders to PostgreSQL."""
    load_dotenv()

    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise ValueError("DATABASE_URL is not set.")

    engine = create_engine(database_url)

    df.to_sql(
        name="orders_raw",
        con=engine,
        if_exists="replace",
        index=False,
        method="multi",
        chunksize=1000,
    )

    with engine.connect() as connection:
        row_count = connection.execute(
            text("SELECT COUNT(*) FROM orders_raw")
        ).scalar_one()

    if row_count != len(df):
        raise RuntimeError(
            f"Row count validation failed: source={len(df)}, database={row_count}"
        )

    print(f"Loaded {row_count} rows into orders_raw.")


def main():
    orders = fetch_orders()

    print(f"Fetched {len(orders)} rows from the source API.")

    load_orders(orders)


if __name__ == "__main__":
    main()