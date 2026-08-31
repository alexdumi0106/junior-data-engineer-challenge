import requests
import pandas as pd


ORDERS_API_URL = (
    "https://jzozteoirwfczccltcdr.supabase.co/rest/v1/orders_raw"
    "?apikey=sb_publishable_Xwjiw--qkKcbMuSbKd6I2w_wN9mpNTv"
)


def get_orders() -> pd.DataFrame:
    response = requests.get(ORDERS_API_URL, timeout=30)
    response.raise_for_status()

    return pd.DataFrame(response.json())


def main():
    orders = get_orders()

    print(f"Number of rows: {len(orders)}")
    print(f"Number of columns: {len(orders.columns)}")

    print("\nColumns:")
    print(orders.columns.tolist())

    print("\nFirst 5 rows:")
    print(orders.head().to_string(index=False))

    print("\nData types:")
    print(orders.dtypes)


if __name__ == "__main__":
    main()