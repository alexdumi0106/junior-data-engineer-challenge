CREATE TABLE IF NOT EXISTS customer_spend_eur (
    customer_id BIGINT PRIMARY KEY,
    total_spent_eur NUMERIC(18, 2) NOT NULL,
    refreshed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

TRUNCATE TABLE customer_spend_eur;

INSERT INTO customer_spend_eur (
    customer_id,
    total_spent_eur,
    refreshed_at
)

WITH all_spend AS (

    -- for EUR orders I don't need a conversion
    SELECT
        o.customer_id,
        ROUND(o.qty * o.unit_price, 2) AS amount_eur
    FROM orders_clean o
    WHERE o.status = 'completed'
      AND o.currency = 'EUR'

    UNION ALL

    -- for RON orders, I convert only when the FX date is currently available
    SELECT
        o.customer_id,
        ROUND(
            (o.qty * o.unit_price) /
            (
                SELECT f.rate
                FROM fx_rates f
                WHERE f.base_currency = 'EUR'
                  AND f.quote_currency = 'RON'
                  AND f.rate_date <= o.fx_reference_date
                ORDER BY f.rate_date DESC
                LIMIT 1
            ),
            2
        ) AS amount_eur
    FROM orders_clean o
    WHERE o.status = 'completed'
      AND o.currency = 'RON'
      AND o.fx_reference_date <= (
          SELECT MAX(rate_date)
          FROM fx_rates
          WHERE base_currency = 'EUR'
            AND quote_currency = 'RON'
      )
)

SELECT
    customer_id,
    ROUND(SUM(amount_eur), 2) AS total_spent_eur,
    NOW() AS refreshed_at
FROM all_spend
GROUP BY customer_id;