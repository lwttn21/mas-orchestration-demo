from mcp.server.fastmcp import FastMCP
from starlette.responses import JSONResponse
from loguru import logger
import sys

logger.remove()
logger.add(sys.stderr, level="INFO")

mcp = FastMCP(
    name="math_server",
    host="127.0.0.1",
    port=3001,
    streamable_http_path="/mcp",
)


@mcp.tool()
async def add(a: float, b: float) -> dict:
    """Addiert zwei Zahlen und gibt das Ergebnis zurück."""
    result = a + b
    logger.info(f"add({a}, {b}) = {result}")
    return {"result": result, "operation": "add"}


@mcp.tool()
async def multiply(a: float, b: float) -> dict:
    """Multipliziert zwei Zahlen."""
    result = a * b
    logger.info(f"multiply({a}, {b}) = {result}")
    return {"result": result, "operation": "multiply"}


@mcp.tool()
async def power(base: float, exponent: float) -> dict:
    """Berechnet base hoch exponent."""
    result = base ** exponent
    return {"result": result, "operation": "power"}


@mcp.custom_route("/health", methods=["GET"])
async def health(_):
    return JSONResponse({"status": "ok", "server": "math_server"})


if __name__ == "__main__":
    logger.info("Starting math_server on http://127.0.0.1:3001/mcp")
    mcp.run(transport="streamable-http")
