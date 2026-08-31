CREATE TABLE IF NOT EXISTS country_category_sales (
    country VARCHAR(2) PRIMARY KEY,
    total_sales_eur NUMERIC(18, 2) NOT NULL,
    refreshed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

TRUNCATE TABLE country_category_sales;

INSERT INTO country_category_sales (
    country,
    total_sales_eur,
    refreshed_at
)

WITH eur_sales AS (
    SELECT
        country,
        ROUND(SUM(qty * unit_price), 2) AS sales_eur
    FROM orders_clean
    WHERE status = 'completed'
      AND category IN ('Books', 'Electronics')
      AND currency = 'EUR'
    GROUP BY country
),

ron_sales AS (
    SELECT
        o.country,
        ROUND(
            SUM(
                (o.qty * o.unit_price) /
                (
                    SELECT f.rate
                    FROM fx_rates f
                    WHERE f.base_currency = 'EUR'
                      AND f.quote_currency = 'RON'
                      AND f.rate_date <= o.fx_reference_date
                    ORDER BY f.rate_date DESC
                    LIMIT 1
                )
            ),
            2
        ) AS sales_eur
    FROM orders_clean o
    WHERE o.status = 'completed'
      AND o.category IN ('Books', 'Electronics')
      AND o.currency = 'RON'
      AND o.fx_reference_date <= (
          SELECT MAX(rate_date)
          FROM fx_rates
          WHERE base_currency = 'EUR'
            AND quote_currency = 'RON'
      )
    GROUP BY o.country
),

sales_by_country AS (
    SELECT
        e.country,
        ROUND(
            e.sales_eur + COALESCE(r.sales_eur, 0),
            2
        ) AS total_sales_eur
    FROM eur_sales e
    LEFT JOIN ron_sales r
        ON e.country = r.country
)

SELECT
    country,
    total_sales_eur,
    NOW() AS refreshed_at
FROM sales_by_country
WHERE total_sales_eur > 40000
ORDER BY total_sales_eur DESC;