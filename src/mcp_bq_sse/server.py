import uvicorn
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.routing import Mount, Route
from typing import Any
import os
import mcp.types as types
from mcp.server import Server
from typing import Any

# Initialize FastMCP server for Weather tools (SSE)
from .bigqueryOp import BigQueryDatabase


def create_starlette_app(db_project, db_location, db_key_file) -> Starlette:
    """Create a Starlette application that can server the provied mcp server with SSE."""

    sse = SseServerTransport("/messages/")
    server = Server("bigquery-manager")
    db = BigQueryDatabase(db_project, db_location, db_key_file)

    @server.list_tools()
    async def handle_list_tools() -> list[types.Tool]:
        """List available tools"""
        return [
            types.Tool(
                name="execute-query",
                description="Execute a SELECT query on the BigQuery database",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "SELECT SQL query to execute using BigQuery dialect",
                        },
                    },
                    "required": ["query"],
                },
            ),
            types.Tool(
                name="list-tables",
                description="List all tables in the BigQuery database",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "datasets_filter": {
                            "type": "string",
                            "description": "Optional filter for datasets (e.g., 'my_dataset')",
                        }
                    },
                },
            ),
            types.Tool(
                name="describe-table",
                description="Get the schema information for a specific table",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "table_name": {
                            "type": "string",
                            "description": "Name of the table to describe (e.g. my_dataset.my_table)",
                        },
                    },
                    "required": ["table_name"],
                },
            ),
            types.Tool(
                name="save-csv-file",
                description="Execute a SELECT query and save results to a CSV file",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "SELECT SQL query to execute and save as CSV",
                        },
                        "file_path": {
                            "type": "string",
                            "description": "Path where to save the CSV file (e.g., /path/to/data.csv)",
                        },
                    },
                    "required": ["query", "file_path"],
                },
            ),
            types.Tool(
                name="save-last-results-csv",
                description="Save the last query results to a CSV file without re-running the query",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path where to save the CSV file (e.g., /path/to/data.csv)",
                        },
                    },
                    "required": ["file_path"],
                },
            ),
            types.Tool(
                name="save-csv-auto",
                description="Execute a SELECT query and save results to an auto-generated CSV file with timestamp",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "SELECT SQL query to execute and save as CSV",
                        },
                        "directory": {
                            "type": "string",
                            "description": "Directory where to save the CSV file (default: current directory)",
                        },
                        "base_name": {
                            "type": "string",
                            "description": "Base name for the CSV file (default: 'bigquery_export')",
                        },
                    },
                    "required": ["query"],
                },
            ),
        ]

    @server.call_tool()
    async def handle_call_tool(
        name: str, arguments: dict[str, Any] | None
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        """Handle tool execution requests"""
        try:
            if name == "list-tables":
                results = db.list_tables(arguments["datasets_filter"])
                return [types.TextContent(type="text", text=str(results))]

            elif name == "describe-table":
                if not arguments or "table_name" not in arguments:
                    raise ValueError("Missing table_name argument")
                results = db.describe_table(arguments["table_name"])
                return [types.TextContent(type="text", text=str(results))]

            elif name == "save-csv-file":
                if (
                    not arguments
                    or "query" not in arguments
                    or "file_path" not in arguments
                ):
                    raise ValueError("Missing query or file_path argument")
                result = db.save_query_to_csv_file(
                    arguments["query"], arguments["file_path"]
                )
                return [types.TextContent(type="text", text=result)]

            elif name == "save-last-results-csv":
                if not arguments or "file_path" not in arguments:
                    raise ValueError("Missing file_path argument")
                result = db.save_last_results_to_csv_file(arguments["file_path"])
                return [types.TextContent(type="text", text=result)]

            elif name == "save-csv-auto":
                if not arguments or "query" not in arguments:
                    raise ValueError("Missing query argument")

                directory = arguments.get("directory", ".")
                base_name = arguments.get("base_name", "bigquery_export")
                filename = db.generate_csv_filename(base_name)
                file_path = os.path.join(directory, filename)

                result = db.save_query_to_csv_file(arguments["query"], file_path)
                return [types.TextContent(type="text", text=result)]

            elif name == "execute-query":
                if not arguments or "query" not in arguments:
                    raise ValueError("Missing query argument")
                results = db.execute_query(arguments["query"])
                return [types.TextContent(type="text", text=str(results))]

            else:
                raise ValueError(f"Unknown tool: {name}")
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error: {str(e)}")]

    async def handle_sse(request: Request) -> None:
        async with sse.connect_sse(
            request.scope,
            request.receive,
            request._send,  # noqa: SLF001
        ) as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options(),
            )

    return Starlette(
        debug=True,
        routes=[
            Route("/sse", endpoint=handle_sse),
            Mount("/messages/", app=sse.handle_post_message),
        ],
    )


def main(
    db_project: str = None,
    db_location: str = None,
    db_key_file: str = None,
    host: str = "localhost",
    port: int = 8080,
) -> None:
    """Main entry point to run the MCP SSE server."""
    starlette_app = create_starlette_app(db_project, db_location, db_key_file)

    uvicorn.run(starlette_app, host=host, port=port)
