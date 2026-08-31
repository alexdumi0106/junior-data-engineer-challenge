DROP TABLE IF EXISTS orders_clean;

CREATE TABLE orders_clean AS

WITH unique_orders AS (
    SELECT DISTINCT *
    FROM orders_raw
),

customer_ids AS (
    SELECT
        customer_email,
        MAX(customer_id) AS customer_id
    FROM unique_orders
    WHERE customer_id IS NOT NULL
    GROUP BY customer_email
),

product_categories AS (
    SELECT
        product_name,
        MAX(category) AS category
    FROM unique_orders
    WHERE category IS NOT NULL
    GROUP BY product_name
),

cleaned_orders AS (
    SELECT
        o.order_id,

        COALESCE(
            o.customer_id,
            c.customer_id
        )::BIGINT AS customer_id,

        LOWER(TRIM(o.customer_email)) AS customer_email,

        CASE
            WHEN o.order_ts ~ '^\d+$'
                THEN TO_TIMESTAMP(o.order_ts::BIGINT)

            WHEN o.order_ts ~ '^\d{2}/\d{2}/\d{4}'
                THEN TO_TIMESTAMP(
                    o.order_ts,
                    'DD/MM/YYYY HH24:MI'
                )

            ELSE o.order_ts::TIMESTAMP
        END AS order_ts,

        LOWER(TRIM(o.status)) AS status,
        LOWER(TRIM(o.channel)) AS channel,

        TRIM(o.sku) AS sku,
        TRIM(o.product_name) AS product_name,

        COALESCE(
            o.category,
            pc.category
        ) AS category,

        o.qty::INTEGER AS qty,
        o.unit_price::NUMERIC(12, 2) AS unit_price,

        UPPER(TRIM(o.currency)) AS currency,
        UPPER(TRIM(o.country)) AS country,

        o.fx_reference_date::DATE AS fx_reference_date

    FROM unique_orders o

    LEFT JOIN customer_ids c
        ON o.customer_email = c.customer_email

    LEFT JOIN product_categories pc
        ON o.product_name = pc.product_name
)

SELECT *
FROM cleaned_orders
WHERE customer_id IS NOT NULL
  AND qty > 0
  AND unit_price >= 0
  AND unit_price <> 999999;