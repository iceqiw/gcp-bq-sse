import csv
import logging
import os
from datetime import datetime
from typing import Any, Optional

from google.cloud import bigquery
from google.oauth2 import service_account

# Set up logging to both stdout and file
logger = logging.getLogger("mcp_bigquery_server")
handler_stdout = logging.StreamHandler()
handler_file = logging.FileHandler("/tmp/mcp_bigquery_server.log")

# Set format for both handlers
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler_stdout.setFormatter(formatter)
handler_file.setFormatter(formatter)

# Add both handlers to logger
logger.addHandler(handler_stdout)
logger.addHandler(handler_file)

# Set overall logging level
logger.setLevel(logging.DEBUG)

logger.info("Starting MCP BigQuery Server")


class BigQueryDatabase:
    def __init__(
        self,
        project: str,
        location: str,
        key_file: Optional[str],
        datasets_filter: list[str],
    ):
        """Initialize a BigQuery database client"""
        logger.info(
            f"Initializing BigQuery client for project: {project}, location: {location}, key_file: {key_file}"
        )
        if not project:
            raise ValueError("Project is required")
        if not location:
            raise ValueError("Location is required")

        credentials: service_account.Credentials | None = None
        if key_file:
            try:
                credentials_path = key_file
                credentials = service_account.Credentials.from_service_account_file(
                    credentials_path,
                    scopes=["https://www.googleapis.com/auth/cloud-platform"],
                )
            except Exception as e:
                logger.error(f"Error loading service account credentials: {e}")
                raise ValueError(f"Invalid key file: {e}")

        self.client = bigquery.Client(
            credentials=credentials, project=project, location=location
        )
        self.datasets_filter = datasets_filter
        self.last_query_results = None  # Store last query results for CSV conversion

    def execute_query(
        self, query: str, params: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Execute a SQL query and return results as a list of dictionaries"""
        logger.debug(f"Executing query: {query}")
        try:
            if params:
                job = self.client.query(
                    query, job_config=bigquery.QueryJobConfig(query_parameters=params)
                )
            else:
                job = self.client.query(query)

            results = job.result()
            rows = [dict(row.items()) for row in results]

            # Store the last query results for potential CSV conversion
            self.last_query_results = {"rows": rows, "schema": results.schema}

            logger.debug(f"Query returned {len(rows)} rows")
            return rows
        except Exception as e:
            logger.error(f"Database error executing query: {e}")
            raise

    def list_tables(self) -> list[str]:
        """List all tables in the BigQuery database"""
        logger.debug("Listing all tables")

        if self.datasets_filter:
            datasets = [
                self.client.dataset(dataset) for dataset in self.datasets_filter
            ]
        else:
            datasets = list(self.client.list_datasets())

        logger.debug(f"Found {len(datasets)} datasets")

        tables = []
        for dataset in datasets:
            dataset_tables = self.client.list_tables(dataset.dataset_id)
            tables.extend(
                [f"{dataset.dataset_id}.{table.table_id}" for table in dataset_tables]
            )

        logger.debug(f"Found {len(tables)} tables")
        return tables

    def describe_table(self, table_name: str) -> list[dict[str, Any]]:
        """Describe a table in the BigQuery database"""
        logger.debug(f"Describing table: {table_name}")

        parts = table_name.split(".")
        if len(parts) != 2 and len(parts) != 3:
            raise ValueError(f"Invalid table name: {table_name}")

        dataset_id = ".".join(parts[:-1])
        table_id = parts[-1]

        query = f"""
            SELECT ddl
            FROM {dataset_id}.INFORMATION_SCHEMA.TABLES
            WHERE table_name = @table_name;
        """
        return self.execute_query(
            query,
            params=[
                bigquery.ScalarQueryParameter("table_name", "STRING", table_id),
            ],
        )

    def save_query_to_csv_file(
        self, query: str, file_path: str, params: dict[str, Any] | None = None
    ) -> str:
        """Execute a SQL query and save results to a CSV file"""
        logger.debug(f"Executing query and saving to CSV file: {file_path}")
        try:
            if params:
                job = self.client.query(
                    query, job_config=bigquery.QueryJobConfig(query_parameters=params)
                )
            else:
                job = self.client.query(query)

            results = job.result()

            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # Write to CSV file
            with open(file_path, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)

                # Write headers
                if results.schema:
                    headers = [field.name for field in results.schema]
                    writer.writerow(headers)

                # Write data rows
                row_count = 0
                for row in results:
                    writer.writerow(list(row.values()))
                    row_count += 1

            logger.debug(
                f"Query results saved to CSV file: {file_path} with {row_count} rows"
            )
            return f"Successfully saved {row_count} rows to {file_path}"
        except Exception as e:
            logger.error(f"Error saving query to CSV file: {e}")
            raise

    def save_last_results_to_csv_file(self, file_path: str) -> str:
        """Save the last query results to a CSV file"""
        if not self.last_query_results:
            raise ValueError(
                "No previous query results available. Execute a query first."
            )

        logger.debug(f"Saving last query results to CSV file: {file_path}")
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # Write to CSV file
            with open(file_path, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)

                # Write headers
                if self.last_query_results["schema"]:
                    headers = [
                        field.name for field in self.last_query_results["schema"]
                    ]
                    writer.writerow(headers)

                # Write data rows
                row_count = 0
                for row in self.last_query_results["rows"]:
                    writer.writerow(list(row.values()))
                    row_count += 1

            logger.debug(
                f"Last query results saved to CSV file: {file_path} with {row_count} rows"
            )
            return f"Successfully saved {row_count} rows to {file_path}"
        except Exception as e:
            logger.error(f"Error saving last results to CSV file: {e}")
            raise

    def generate_csv_filename(self, base_name: str = "bigquery_export") -> str:
        """Generate a timestamped CSV filename"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{base_name}_{timestamp}.csv"
