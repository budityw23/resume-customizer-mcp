"""
Resume Customizer MCP Server.

Main entry point for the MCP server that provides resume customization tools.
"""

import asyncio
import json
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from resume_customizer.config import get_config
from resume_customizer.mcp.handlers import TOOL_HANDLERS
from resume_customizer.mcp.tools import ALL_TOOLS
from resume_customizer.utils.logger import get_logger, setup_logger

# Initialize logger
logger = get_logger(__name__)


def create_server() -> Server:
    """
    Create and configure the MCP server instance.

    Returns:
        Configured MCP Server instance
    """
    # Load configuration
    try:
        config = get_config()
        setup_logger(
            name="resume_customizer", level=config.log_level, log_file=None  # Log to console only
        )
        logger.info("Configuration loaded successfully")
    except Exception as e:
        # If config fails, set up basic logging
        setup_logger(name="resume_customizer", level="INFO")
        logger.warning(f"Failed to load configuration: {e}. Using defaults.")

    # Create server instance
    server = Server("resume_customizer")
    logger.info("MCP Server instance created: resume_customizer")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """
        List all available tools.

        Returns:
            List of Tool definitions
        """
        logger.debug(f"Listing {len(ALL_TOOLS)} available tools")
        return ALL_TOOLS

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        """
        Handle tool execution requests.

        Args:
            name: Name of the tool to execute
            arguments: Arguments for the tool

        Returns:
            List of TextContent with tool results

        Raises:
            ValueError: If tool name is not recognized
        """
        logger.info(f"Tool called: {name} with arguments: {arguments}")

        # Get the handler for this tool
        handler = TOOL_HANDLERS.get(name)
        if not handler:
            error_msg = f"Unknown tool: {name}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        try:
            # Execute the handler
            result = handler(arguments)

            # Format result as JSON text
            result_json = json.dumps(result, indent=2, ensure_ascii=False)
            logger.info(f"Tool {name} executed successfully")

            return [TextContent(type="text", text=result_json)]

        except Exception as e:
            error_msg = f"Error executing tool {name}: {str(e)}"
            logger.error(error_msg, exc_info=True)

            # Return error as JSON
            error_result = {
                "status": "error",
                "error": str(e),
                "tool": name,
            }
            return [TextContent(type="text", text=json.dumps(error_result, indent=2))]

    return server


async def main() -> None:
    """
    Main entry point for the MCP server.

    Starts the server with stdio transport and runs until interrupted.
    """
    logger.info("Starting Resume Customizer MCP Server...")

    try:
        # Create server
        server = create_server()

        # Run with stdio transport
        async with stdio_server() as (read_stream, write_stream):
            logger.info("Server running with stdio transport")
            logger.info("Ready to receive requests from MCP clients")

            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options(),
            )

    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        raise
    finally:
        logger.info("Resume Customizer MCP Server stopped")


def run() -> None:
    """
    Synchronous entry point for running the server.

    This function is called when the module is executed directly.
    """
    asyncio.run(main())


if __name__ == "__main__":
    run()
