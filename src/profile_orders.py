import pandas as pd

from inspect_orders import get_orders


def main():
    df = get_orders()

    print("DATASET OVERVIEW")
    print(f"Rows: {len(df)}")
    print(f"Columns: {len(df.columns)}")

    print("\nMISSING VALUES")
    print(df.isna().sum())

    print("\n DUPLICATES")
    print(df.duplicated().sum())

    print("\n UNIQUE VALUES")
    for column in ["status", "channel", "category", "currency", "country"]:
        print(f"\n{column}:")
        print(df[column].value_counts(dropna=False).to_string())

    print("\n NUMERIC COLUMNS")
    print(df[["customer_id", "qty", "unit_price"]].describe())

    print("\n INVALID NUMERIC VALUES")
    print("qty <= 0:", (df["qty"] <= 0).sum())
    print("unit_price < 0:", (df["unit_price"] < 0).sum())

    print("\n TIMESTAMP SAMPLES")
    print(df["order_ts"].head(20).to_string(index=False))

    print("\n FX DATE RANGE")
    fx_dates = pd.to_datetime(df["fx_reference_date"], errors="coerce")
    print("Earliest:", fx_dates.min())
    print("Latest:", fx_dates.max())
    print("Invalid dates:", fx_dates.isna().sum())

    print("\n CUSTOMER IDs")
    print("Missing:", df["customer_id"].isna().sum())

    non_integer_customer_ids = (
        df["customer_id"].dropna() % 1 != 0
    ).sum()

    print("Non-integer IDs:", non_integer_customer_ids)

    print("\n INVALID QUANTITIES")
    print(
        df.loc[
            df["qty"] <= 0,
            ["order_id", "sku", "product_name", "category", "qty", "unit_price", "status"]
        ].head(30).to_string(index=False)
    )

    print("\n SUSPICIOUSLY HIGH PRICES")
    print(
        df.nlargest(20, "unit_price")[
            ["order_id", "sku", "product_name", "category", "qty",
             "unit_price", "currency", "status"]
        ].to_string(index=False)
    )

    print("\n MISSING CUSTOMER IDS")
    print(
        df.loc[
            df["customer_id"].isna(),
            ["order_id", "customer_id", "customer_email", "status"]
        ].head(20).to_string(index=False)
    )

    print("\n MISSING CATEGORIES")
    print(
        df.loc[
            df["category"].isna(),
            ["sku", "product_name", "category"]
        ].drop_duplicates().to_string(index=False)
    )

    print("\n DUPLICATE SAMPLES")
    duplicates = df[df.duplicated(keep=False)].sort_values("order_id")
    print(duplicates.head(30).to_string(index=False))

    print("\n ORDER TIMESTAMP FORMATS")
    numeric_timestamps = df["order_ts"].astype(str).str.fullmatch(r"\d+")
    print("ISO-like timestamps:", (~numeric_timestamps).sum())
    print("Numeric timestamps:", numeric_timestamps.sum())

    print("\nNumeric timestamp examples:")
    print(
        df.loc[numeric_timestamps, ["order_id", "order_ts"]]
        .head(20)
        .to_string(index=False)
    )

    print("\n EMAIL AND CUSTOMER ID CHECK")

    email_id_counts = (
        df.dropna(subset=["customer_id"])
        .groupby("customer_email")["customer_id"]
        .nunique()
    )

    print(
        "Emails mapped to multiple customer IDs:",
        (email_id_counts > 1).sum()
    )

    print("\n RECOVERING MISSING CUSTOMER IDS")

    email_to_customer = (
        df.dropna(subset=["customer_id"])
        .groupby("customer_email")["customer_id"]
        .first()
    )

    missing_customers = df[df["customer_id"].isna()]

    recoverable_customers = (
        missing_customers["customer_email"]
        .isin(email_to_customer.index)
        .sum()
    )

    print("Missing customer IDs:", len(missing_customers))
    print("Recoverable from email:", recoverable_customers)

    print("\n PRODUCT AND CATEGORY CHECK")

    product_categories = (
        df.dropna(subset=["category"])
        .groupby("product_name")["category"]
        .nunique()
    )

    print(
        "Products mapped to multiple categories:",
        (product_categories > 1).sum()
    )

    print("\n MISSING CATEGORIES RECOVERY")

    product_to_category = (
        df.dropna(subset=["category"])
        .groupby("product_name")["category"]
        .first()
    )

    missing_categories = df[df["category"].isna()]

    recoverable_categories = (
        missing_categories["product_name"]
        .isin(product_to_category.index)
        .sum()
    )

    print("Missing categories:", len(missing_categories))
    print("Recoverable from product name:", recoverable_categories)

    print("\n QUANTITY DISTRIBUTION")
    print(
        df["qty"]
        .value_counts()
        .sort_index()
        .to_string()
    )

    print("\n PRICE 999999 COUNT")
    print((df["unit_price"] == 999999).sum())


if __name__ == "__main__":
    main()