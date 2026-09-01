# Junior Data Engineer Challenge

## Project overview
This project implements a small data pipeline for processing order data.

The pipeline loads raw order data into PostgreSQL, cleans data quality issues, retrieves EUR/RON exchange rates from a public API, and calculates customer spending and sales values in EUR.

The main steps are:
1. Load the raw orders into the database;
2. Clean inconsistent or invalid data;
3. Retrieve the FX rates needed for currency conversion;
4. Calculate the total spend per customer in EUR;
5. Calculate sales by country for Books and Electronics;
6. Run the pipeline automatically every day using GitHub Actions.

PostgreSQL is hosted in Supabase, while Python and SQL are used for data ingestion, transformation, and aggregation.

## Project structure
The project is organized as follows:

```
junior-data-engineer-challenge/
│
├── src/
│   ├── ingest_orders.py
│   ├── inspect_orders.py
│   ├── profile_orders.py
│   ├── ingest_fx.py
│   ├── test_connection.py
│   └── pipeline.py
│
├── sql/
│   ├── clean_orders.sql
│   ├── create_fx_rates.sql
│   ├── customer_spend.sql
│   └── country_category_sales.sql
│
├── .github/
│   └── workflows/
│       └── daily_pipeline.yml
│
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md

The src folder contains the Python scripts used for data ingestion, data inspection, FX rate retrieval, and pipeline execution.

The sql folder contains the SQL transformations used to clean the orders and calculate the required results.

The GitHub Actions workflow is stored in .github/workflows and is used to run the pipeline automatically every day.
```

## Cleaning data
The raw order data contains several data quality issues, so I added a cleaning step before using the data for calculations.

The main cleaning steps are:
- remove exact duplicate rows;
- recover missing `customer_id` values using the customer email when a known mapping exists;
- recover missing categories using the product name;
- convert the different timestamp formats into a consistent PostgreSQL timestamp;
- normalize text fields such as email, status, currency, and country;
- remove rows with missing customer IDs that could not be recovered;
- remove orders with invalid quantities (`qty <= 0`);
- remove negative prices and the suspicious `999999` price value.

The cleaned data is stored in the `orders_clean` table and is then used by the rest of the pipeline.

## FX rate conversion
The dataset contains orders both in EUR and RON. EUR orders do not require conversion, while RON orders are converted to EUR using exchange rates retrieved from the Frankfurter API.

The pipeline first checks the range of `fx_reference_date` values required by the orders and requests the available EUR/RON rates for that period.

If there is no exchange rate for the exact reference date, the latest available rate on or before `fx_reference_date` is used. This also handles weekends and other days when a new exchange rate is not available.

Future dates are not requested from the API. As new exchange rates become available, the daily pipeline retrieves them and more orders can be included in the calculations.

The retrieved rates are stored in the `fx_rates` table. Existing rates are updated when necessary, so running the FX ingestion multiple times does not create duplicate records.

## Customer spend
The `customer_spend_eur` table contains the total amount spent by each customer in EUR.

Only orders with the `completed` status are included in the sum. EUR orders are used directly, while RON orders are converted using the available FX rate.

After the currency conversion, the amounts are grouped by `customer_id` and summed to calculate `total_spent_eur`.

The table is refreshed each time the pipeline runs, so the results are updated when new FX rates become available.

## Country and category sales
The `country_category_sales` calculation is used to identify countries where the combined sales for Books and Electronics exceed the 40.000 EUR.

Only completed orders from the `Books` and `Electronics` categories are included. EUR orders are used directly, while RON orders are converted to EUR using the same FX conversion logic as in the customer spend calculation.

The EUR and converted RON amounts are combined and grouped by country. Only countries with total sales greater than 40.000 EUR are included in the final result.

The result is refreshed whenever the pipeline runs, allowing the values to change as new FX rates become available.

## Automation
The pipeline is automated using GitHub Actions.

The workflow can be started manually from GitHub using `workflow_dispatch`, and it is also scheduled to run once per day. (16:00 UTC) A later daily run was chosen so that the exchange rates for the current day are more likely to be available before the pipeline starts.

The scheduled workflow runs the following steps:
- checks out the repository;
- sets up Python;
- installs the dependencies from `requirements.txt`;
- runs `src/pipeline.py`.

The database connection string is stored securely as the `DATABASE_URL` GitHub repository secret and is passed to the pipeline as an environment variable.

The daily run loads the latest raw orders, rebuilds the cleaned orders table, refreshes the available FX rates, and then recalculates the customer spend and country/category sales tables.

## How to run the project

1. Clone the repository and open the project folder:

```bash
git clone <repository-url>
cd junior-data-engineer-challenge
```

2. Create a virtual environment:

```bash
python -m venv .venv
```

3. Activate the virtual environment.

On Windows:

```bash
.venv\Scripts\activate
```

4. Install the required dependencies:

```bash
pip install -r requirements.txt
```

5. Create a `.env` file in the project root based on `.env.example` and add the PostgreSQL connection string:

```env
DATABASE_URL=your_database_connection_string
```

6. Test the database connection:

```bash
python src/test_connection.py
```

7. If needed, the source data can be inspected before running the pipeline:

```bash
python src/inspect_orders.py
python src/profile_orders.py
```

8. Run the full pipeline:

```bash
python src/pipeline.py
```

The pipeline loads the raw orders, cleans the data, retrieves the required FX rates, and then refreshes the customer spend and country/category sales results.

The pipeline can also be run automatically through the GitHub Actions workflow configured in `.github/workflows/daily_pipeline.yml`.

## Assumptions and decisions
During the data cleaning and transformation process, I made a few decisions based on the issues found in the source data:

- Only orders with the `completed` status are used for the spend and sales calculations. Test and refunded orders are not included.

- Exact duplicate rows are removed before further processing.

- Missing `customer_id` values are recovered using `customer_email` when the same email already has a known customer ID in the dataset. Rows where the customer ID cannot be recovered are excluded.

- If a product has a missing category, I use the category found for the same product in other rows of the dataset.

- Orders with quantities less than or equal to zero are treated as invalid and are removed.

- Negative prices are treated as invalid. The `999999` price value is also excluded because it was identified as a suspicious value during the initial data inspection.

- Different order timestamp formats are converted into a consistent PostgreSQL timestamp format.

- EUR orders do not require currency conversion and RON orders are converted to EUR using EUR/RON exchange rates.

- When an FX rate is not available for the exact `fx_reference_date`, the latest available rate on or before that date is used. This is useful for weekends or other dates without a published rate.

- Future FX dates are not requested from the API. Orders that depend on rates that are not available yet (future dates) can be included in later daily runs once the required rates become available.

These decisions were based on the initial inspection of the dataset using `inspect_orders.py` and `profile_orders.py`.

## Writeup

### Data issues found in `orders_raw`
During the initial inspection of `orders_raw`, I found several data quality issues that could affect the final calculations.

The dataset contained duplicate rows, so I removed them before applying any further transformations.

Some rows had missing `customer_id` values. I checked whether the same `customer_email` appeared in other rows with a known customer ID. When a consistent mapping existed, I used that value to recover the missing ID. Rows where the customer ID could not be recovered were excluded because customer-level spending cannot be calculated reliably without an identifier.

Some product categories were also missing. I checked whether the same `product_name` appeared elsewhere with a known category and used that category when possible. This allowed me to recover missing values without assigning categories arbitrarily.

The `order_ts` column contained more than one timestamp format, including numeric timestamps and regular date-time strings. I converted these formats into a consistent PostgreSQL timestamp so they could be handled in the same way.

I also found invalid numeric values. Orders with `qty <= 0` were excluded because they do not represent valid sales quantities. Negative prices were excluded as well. The value `999999` appeared as a suspicious price value during the profiling step, so I treated it as invalid and removed those rows from the cleaned dataset.

Text fields such as email, status, channel, currency, and country were normalized to reduce inconsistencies caused by casing or extra spaces.

These decisions were based on the patterns observed during the inspection and profiling steps rather than on assumptions made before looking at the data.

### Monitoring in production

The pipeline currently runs through GitHub Actions, where each execution has a visible success or failure status and the logs can be used to identify which step failed.

In a production environment, I would not rely only on manually checking the GitHub Actions page. I would configure notifications for failed workflow runs, for example by sending an email or a Slack/Teams alert when the daily job fails.

I would also monitor whether the pipeline actually completed its expected updates. The result tables contain a `refreshed_at` timestamp, so this could be checked to detect cases where the pipeline has not refreshed the data within the expected daily interval.

I would monitor a few basic data quality metrics as well, such as the number of processed rows, missing values, rejected rows, and the number of FX rates retrieved. Unexpected changes in these values could indicate a problem even when the job itself finishes successfully.

For a larger production system, these checks could be connected to a monitoring and alerting service so that failures or unusual results generate an automatic notification.

### AI usage

I used ChatGPT as a support tool while working on this challenge. I mainly used it to discuss the project structure, clarify concepts and troubleshoot errors.

I used the guidance that matched the requirements and the patterns I observed in the dataset. For example, AI helped me reason through the FX rate fallback logic and the structure of the daily pipeline.

I did not use any suggestions without checking them. I inspected the source data with my own profiling scripts, tested the SQL transformations in PostgreSQL, ran the pipeline locally, and tested the final workflow in GitHub Actions. When something did not work or did not match the project, I changed it. For example, I fixed implementation errors found during testing, and changed the GitHub Actions Python version after identifying a dependency compatibility issue.

The final decisions about data cleaning and transformation were based on the actual dataset and the results of these tests made by me. AI was used as an assistant for guidance and debugging. 