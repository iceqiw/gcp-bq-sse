from . import server
import argparse
import os


def main():
    """Main entry point for the package."""
    parser = argparse.ArgumentParser(description="Run MCP SSE-based server")
    parser.add_argument("--project", help="BigQuery project", required=False)
    parser.add_argument("--location", help="BigQuery location", required=False)
    parser.add_argument("--key-file", help="BigQuery Service Account", required=False)
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8080, help="Port to listen on")
    args = parser.parse_args()

    # Get values from environment variables if not provided as arguments
    project = args.project or os.environ.get("BIGQUERY_PROJECT")
    location = args.location or os.environ.get("BIGQUERY_LOCATION")
    key_file = args.key_file or os.environ.get("BIGQUERY_KEY_FILE")
    host = args.host
    port = args.port
    server.main(project, location, key_file, host, port)
