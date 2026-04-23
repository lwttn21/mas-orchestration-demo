import argparse
import asyncio

from langchain_core.messages import AIMessage

from demo_mas.common.utils import get_server_params
from demo_mas.processors.linear_processor import LinearProcessor
from demo_mas.processors.supervisor_processor import SupervisorProcessor
from demo_mas.processors.swarm_processor import SwarmProcessor


PROCESSORS = {
    "linear": LinearProcessor,
    "supervisor": SupervisorProcessor,
    "swarm": SwarmProcessor,
}


async def main(query: str, processor_name: str):
    processor_cls = PROCESSORS[processor_name]
    configs = get_server_params()

    async with processor_cls(configs) as processor:
        final_state = None
        async for state in processor.aprocess_query(query):
            final_state = state

    messages = final_state["messages"]

    def _is_real_answer(m):
        if not isinstance(m, AIMessage) or not m.content:
            return False
        return not m.content.startswith("Transferring back to ")

    answer = next(
        (m.content for m in reversed(messages) if _is_real_answer(m)),
        "(keine Antwort)",
    )

    print("\n=== ANTWORT ===")
    print(answer)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Demo-MAS CLI")
    parser.add_argument("query", nargs="?", default="Was ist 12 * 7?", help="Anfrage an das MAS")
    parser.add_argument(
        "--processor",
        choices=list(PROCESSORS.keys()),
        default="linear",
        help="Orchestrierungsmuster (linear|supervisor|swarm)",
    )
    args = parser.parse_args()

    asyncio.run(main(args.query, args.processor))
