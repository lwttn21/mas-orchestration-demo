from mcp.server.fastmcp import FastMCP
from starlette.responses import JSONResponse
from loguru import logger
import sys

logger.remove()
logger.add(sys.stderr, level="INFO")

mcp = FastMCP(
    name="text_server",
    host="127.0.0.1",
    port=3002,
    streamable_http_path="/mcp",
)


@mcp.tool()
async def word_count(text: str) -> dict:
    """Zählt die Anzahl der Wörter in einem Text."""
    count = len(text.split())
    logger.info(f"word_count({text!r}) = {count}")
    return {"count": count, "operation": "word_count"}


@mcp.tool()
async def reverse(text: str) -> dict:
    """Dreht einen Text um (Zeichen in umgekehrter Reihenfolge)."""
    reversed_text = text[::-1]
    logger.info(f"reverse({text!r}) = {reversed_text!r}")
    return {"reversed": reversed_text, "operation": "reverse"}


@mcp.tool()
async def uppercase(text: str) -> dict:
    """Konvertiert einen Text in Großbuchstaben."""
    result = text.upper()
    logger.info(f"uppercase({text!r}) = {result!r}")
    return {"uppercase": result, "operation": "uppercase"}


@mcp.custom_route("/health", methods=["GET"])
async def health(_):
    return JSONResponse({"status": "ok", "server": "text_server"})


if __name__ == "__main__":
    logger.info("Starting text_server on http://127.0.0.1:3002/mcp")
    mcp.run(transport="streamable-http")
