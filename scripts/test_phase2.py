"""Ad-hoc Test für Phase 2: ClientSessionGroup → math_server → add-Tool."""
import asyncio
from contextlib import AsyncExitStack
from datetime import timedelta

from loguru import logger
from mcp.client.session_group import ClientSessionGroup, StreamableHttpParameters

from demo_mas.tools.math_tools import create_math_tools


async def main():
    params = StreamableHttpParameters(
        url="http://127.0.0.1:3001/mcp",
        timeout=timedelta(seconds=60),
        sse_read_timeout=300.0,
    )

    async with AsyncExitStack() as stack:
        group = ClientSessionGroup()
        await stack.enter_async_context(group)

        session = await group.connect_to_server(params)
        logger.info("Connected to math_server")

        tools = create_math_tools(session)
        logger.info(f"Wrapped tools: {[t.name for t in tools]}")
        for t in tools:
            logger.info(f"  {t.name}: {t.description}")

        result = await session.call_tool("add", {"a": 7, "b": 5})
        raw = result.content[0].text
        logger.info(f"Direct call: add(7, 5) → {raw}")

        result2 = await session.call_tool("multiply", {"a": 6, "b": 9})
        logger.info(f"Direct call: multiply(6, 9) → {result2.content[0].text}")


if __name__ == "__main__":
    asyncio.run(main())
