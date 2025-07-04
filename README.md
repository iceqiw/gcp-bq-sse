# MCP BigQuery SSE Server

A Model Context Protocol (MCP) server that provides BigQuery database access through Server-Sent Events (SSE). This server allows you to query BigQuery tables, list datasets, describe table schemas, and export results to CSV files.

## 🚀 Features

- **Query Execution**: Execute BigQuery SQL queries and get results
- **Table Management**: List all tables and describe table schemas
- **Dataset Filtering**: Filter tables by specific datasets for focused exploration
- **CSV Export**: Save query results to CSV files with timestamps
- **Authentication**: Support for both service account keys and Application Default Credentials (ADC)
- **SSE Support**: Real-time communication through Server-Sent Events
- **Logging**: Comprehensive logging for debugging and monitoring

## 📋 Prerequisites

- Python 3.13+
- Google Cloud Project with BigQuery enabled
- GCP authentication (service account key or ADC)
- uv package manager

## 🔧 Installation

1. **Clone the repository:**

```bash
git clone <repository-url>
cd mcp-bq-sse
```

2. **Install dependencies:**

```bash
uv sync
```

3. **Set up authentication (choose one):**

   **Option A: Service Account Key**

   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/service-account-key.json"
   ```

   **Option B: Application Default Credentials**

   ```bash
   # Install gcloud CLI if not already installed
   brew install --cask google-cloud-sdk

   # Authenticate with your Google account
   gcloud auth application-default login
   ```

## 🚀 Usage

### Starting the Server

```bash
# Start the SSE server (default: localhost:8080)
uv run mcp-bq-sse

# Custom host and port
uv run mcp-bq-sse --host 127.0.0.1 --port 8080

# With specific GCP project and location
uv run mcp-bq-sse --project project-name-xxxxx --location loc-xxxxxx

# Full configuration example
uv run mcp-bq-sse --project my-gcp-project --location us-central1 --host 0.0.0.0 --port 8080
```

### VS Code Configuration

Create or update on your project `.vscode/mcp.json`:

```json
{
  "servers": {
    "sse": {
      "url": "http://localhost:8080/sse"
    }
  }
}
```

**Note:** Make sure your MCP server is running on port 8080 (default) before VS Code tries to connect. The URL should match your server's host and port configuration.

## 🔍 Available MCP Tools

### 1. **List Tables**

```python
# Lists all tables in the BigQuery project
mcp_sse_list-tables()

# Filter tables by specific dataset
mcp_sse_list-tables(datasets_filter="my_dataset")

# Example: Get tables from specific datasets
mcp_sse_list-tables(datasets_filter="analytics_data")
mcp_sse_list-tables(datasets_filter="marketing_analytics")
```

### 2. **Describe Table**

```python
# Get table schema and DDL
mcp_sse_describe-table(table_name="dataset.table_name")
```

### 3. **Execute Query**

```python
# Execute a SELECT query
mcp_sse_execute-query(query="SELECT * FROM dataset.table_name LIMIT 10")
```

### 4. **Save to CSV**

```python
# Execute query and save to specific CSV file
mcp_sse_save-csv-file(
    query="SELECT * FROM dataset.table_name",
    file_path="/path/to/output.csv"
)

# Execute query and save to auto-generated timestamped CSV
mcp_sse_save-csv-auto(
    query="SELECT * FROM dataset.table_name",
    base_name="my_export",
    directory="/path/to/output/dir"
)

# Save last query results to CSV (without re-running)
mcp_sse_save-last-results-csv(file_path="/path/to/output.csv")
```

## 🏗️ Project Structure

```
mcp-bq-sse/
├── src/
│   └── mcp_bq_sse/
│       ├── __init__.py          # Package initialization
│       ├── server.py            # MCP SSE server implementation
│       └── bigqueryOp.py        # BigQuery operations and authentication
├── .vscode/
│   └── mcp.json                 # VS Code MCP configuration
├── pyproject.toml               # Project dependencies and configuration
├── uv.lock                      # Lock file for dependencies
└── README.md                    # This file
```

## 🔐 Authentication

### Service Account Key

1. Create a service account in Google Cloud Console
2. Download the JSON key file
3. Set the environment variable:
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="/path/to/key.json"
   ```

### Application Default Credentials (ADC)

The server automatically uses ADC when no service account key is provided:

```python
# In bigqueryOp.py - automatic fallback to ADC
credentials, project_id = default.default(
    scopes=["https://www.googleapis.com/auth/cloud-platform"]
)
```

## 📊 Example Usage

### Basic Query

```python
# List all tables
tables = mcp_sse_list-tables()
print(f"Found {len(tables)} tables")

# Filter tables by dataset
analytics_tables = mcp_sse_list-tables(datasets_filter="analytics_data")
print(f"Found {len(analytics_tables)} tables in analytics dataset")

# Get table schema
schema = mcp_sse_describe-table(table_name="my_dataset.my_table")

# Execute query
results = mcp_sse_execute-query(
    query="SELECT column1, column2 FROM my_dataset.my_table LIMIT 100"
)
```

### Export to CSV

```python
# Direct export with custom filename
mcp_sse_save-csv-file(
    query="SELECT * FROM campaign_data WHERE date >= '2024-01-01'",
    file_path="/exports/campaign_data_2024.csv"
)

# Auto-generated timestamped export
mcp_sse_save-csv-auto(
    query="SELECT * FROM performance_data",
    base_name="performance_export",
    directory="/exports"
)
# Creates: /exports/performance_export_20240709_143022.csv
```

### Dataset Filtering

The server now supports filtering tables by dataset, which is particularly useful for large projects with many datasets:

```python
# Get all tables from a specific dataset
analytics_tables = mcp_sse_list-tables(datasets_filter="analytics_data")

# Examples of what you might get:
# ['analytics_data.user_events', 
#  'analytics_data.page_views',
#  'analytics_data.conversion_metrics', ...]

# Useful for exploring specific business domains
marketing_tables = mcp_sse_list-tables(datasets_filter="marketing_analytics")
finance_tables = mcp_sse_list-tables(datasets_filter="finance_reporting")
sales_tables = mcp_sse_list-tables(datasets_filter="sales_data")

# Then query specific tables from the filtered results
user_data = mcp_sse_execute-query(
    query="SELECT * FROM analytics_data.user_events LIMIT 10"
)
```


## 🔧 Configuration

### Environment Variables

| Variable                         | Description                 | Default                |
| -------------------------------- | --------------------------- | ---------------------- |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to service account key | None (uses ADC)        |
| `GOOGLE_CLOUD_PROJECT`           | GCP project ID              | Auto-detected from ADC |
| `GOOGLE_CLOUD_LOCATION`          | BigQuery location/region    | `US`                   |

### Server Options

| Option       | Description                       | Default                |
| ------------ | --------------------------------- | ---------------------- |
| `--host`     | Host to bind to                   | `0.0.0.0`              |
| `--port`     | Port to listen on                 | `8080`                 |
| `--project`  | GCP project ID                    | Auto-detected from ADC |
| `--location` | BigQuery location/region          | `US`                   |
| `--key-file` | BigQuery service account key file | `xxx.json`             |

## 📝 Logging

Logs are written to both:

- **stdout**: For real-time monitoring
- **File**: `/tmp/mcp_bigquery_server.log`

Log levels:

- `DEBUG`: Query execution details
- `INFO`: Server startup and authentication
- `WARNING`: Fallback scenarios
- `ERROR`: Authentication and query errors

## 🛠️ Development

### Running Tests

```bash
# Install development dependencies
uv sync --dev

# Format code
uv run ruff format src/
uv run black src/

# Sort imports
uv run isort src/

# Lint code
uv run ruff check src/
```

### Building

```bash
# Build the package
uv build

# Install in development mode
uv sync --dev
```

## 🔍 Troubleshooting

### Common Issues

1. **Authentication Error**

   ```
   Error: 403 Caller does not have required permission
   ```

   **Solution**: Ensure your service account has `roles/bigquery.user` and `roles/serviceusage.serviceUsageConsumer`

2. **Module Not Found**

   ```
   ModuleNotFoundError: No module named 'mcp_bq_sse'
   ```

   **Solution**: Run `uv sync` to install dependencies

3. **Server Not Starting**
   ```
   Error: Failed to spawn: mcp-bq-sse
   ```
   **Solution**: Check that the package is properly installed with `uv sync`

### Debug Mode

Start the server with debug logging:

```bash
# Check logs
tail -f /tmp/mcp_bigquery_server.log

# Or monitor in real-time
uv run mcp-bq-sse --port 8080 | tee debug.log

# With specific project and location
uv run mcp-bq-sse --project project-name-xxxxx --location loc-xxxxxx | tee debug.log
```

## 📚 API Reference

### BigQueryDatabase Class

```python
class BigQueryDatabase:
    def __init__(self, project: str, location: str, key_file: Optional[str])
    def execute_query(self, query: str, params: dict = None) -> list[dict]
    def list_tables(self, datasets_filter: Optional[str] = None) -> list[str]
    def describe_table(self, table_name: str) -> list[dict]
    def save_query_to_csv_file(self, query: str, file_path: str) -> str
    def save_last_results_to_csv_file(self, file_path: str) -> str
```

### MCP Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `list-tables` | List all tables in BigQuery project | `datasets_filter` (optional): Filter by dataset name |
| `describe-table` | Get table schema and DDL | `table_name` (required): Full table name (dataset.table) |
| `execute-query` | Execute SELECT query | `query` (required): SQL query to execute |
| `save-csv-file` | Execute query and save to CSV | `query` (required), `file_path` (required) |
| `save-csv-auto` | Execute query and save to timestamped CSV | `query` (required), `directory` (optional), `base_name` (optional) |
| `save-last-results-csv` | Save last query results to CSV | `file_path` (required) |

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and formatting
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:

- Check the troubleshooting section above
- Review the logs at `/tmp/mcp_bigquery_server.log`
- Create an issue in the repository

---

**Happy querying! 🚀**
