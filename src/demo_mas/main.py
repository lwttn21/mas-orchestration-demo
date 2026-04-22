import asyncio
import sys

from demo_mas.common.utils import get_server_params
from demo_mas.processors.linear_processor import LinearProcessor


async def main(query: str):
    configs = get_server_params()
    async with LinearProcessor(configs) as processor:
        final_state = None
        async for state in processor.aprocess_query(query):
            final_state = state

        answer = next(
            (m.content for m in reversed(final_state["messages"]) if m.content),
            "(keine Antwort)",
        )
        print("\n=== ANTWORT ===")
        print(answer)


if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else "Was ist 12 * 7?"
    asyncio.run(main(query))
