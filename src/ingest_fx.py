import os
from datetime import date

import requests
from dotenv import load_dotenv
from sqlalchemy import create_engine, text


FX_API_URL = "https://api.frankfurter.app"
BASE_CURRENCY = "EUR"
QUOTE_CURRENCY = "RON"


def get_required_date_range(engine):
    """Get the date range needed for FX conversion."""

    query = text("""
        SELECT
            MIN(fx_reference_date) AS min_date,
            MAX(fx_reference_date) AS max_date
        FROM orders_clean
        WHERE currency <> 'EUR';
    """)

    with engine.connect() as connection:
        result = connection.execute(query).mappings().one()

    return result["min_date"], result["max_date"]


def fetch_fx_rates(start_date, end_date):
    """Get the available EUR/RON rates for the required period."""

    today = date.today()
    effective_end_date = min(end_date, today)

    if start_date > effective_end_date:
        return {}

    url = (
        f"{FX_API_URL}/{start_date}..{effective_end_date}"
        f"?from={BASE_CURRENCY}&to={QUOTE_CURRENCY}"
    )

    response = requests.get(url, timeout=30)
    response.raise_for_status()

    payload = response.json()

    return payload.get("rates", {})


def save_fx_rates(engine, rates):
    """Save FX rates and update existing ones if needed."""

    query = text("""
        INSERT INTO fx_rates (
            rate_date,
            base_currency,
            quote_currency,
            rate,
            fetched_at
        )
        VALUES (
            :rate_date,
            :base_currency,
            :quote_currency,
            :rate,
            NOW()
        )
        ON CONFLICT (
            rate_date,
            base_currency,
            quote_currency
        )
        DO UPDATE SET
            rate = EXCLUDED.rate,
            fetched_at = NOW();
    """)

    rows = []

    for rate_date, currencies in rates.items():
        if QUOTE_CURRENCY not in currencies:
            continue

        rows.append(
            {
                "rate_date": rate_date,
                "base_currency": BASE_CURRENCY,
                "quote_currency": QUOTE_CURRENCY,
                "rate": currencies[QUOTE_CURRENCY],
            }
        )

    if not rows:
        print("No FX rates found!.")
        return

    with engine.begin() as connection:
        connection.execute(query, rows)

    print(f"Loaded {len(rows)} FX rates.")


def main():
    load_dotenv()

    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise ValueError("DATABASE_URL is not set.")

    engine = create_engine(database_url)

    start_date, end_date = get_required_date_range(engine)

    if start_date is None or end_date is None:
        print("No non-EUR orders require FX conversion.")
        return

    print(f"Required FX range: {start_date} to {end_date}")

    rates = fetch_fx_rates(start_date, end_date)

    print(f"Available FX dates returned by API: {len(rates)}")

    save_fx_rates(engine, rates)


if __name__ == "__main__":
    main()