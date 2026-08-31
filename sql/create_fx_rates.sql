CREATE TABLE IF NOT EXISTS fx_rates (
    rate_date DATE NOT NULL,
    base_currency VARCHAR(3) NOT NULL,
    quote_currency VARCHAR(3) NOT NULL,
    rate NUMERIC(18, 8) NOT NULL,
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY (
        rate_date,
        base_currency,
        quote_currency
    ),

    CHECK (rate > 0),

    CHECK (
        LENGTH(base_currency) = 3
        AND LENGTH(quote_currency) = 3
    )
);