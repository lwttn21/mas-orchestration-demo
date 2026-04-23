from langgraph.checkpoint.memory import MemorySaver
from langgraph_swarm import create_swarm, create_handoff_tool

from demo_mas.processors.base import QueryProcessor
from demo_mas.common.prompts import (
    MATH_AGENT_SWARM_PROMPT,
    TEXT_AGENT_SWARM_PROMPT,
)
from demo_mas.tools.math_tools import create_math_tools
from demo_mas.tools.text_tools import create_text_tools
from demo_mas.agents.agent_builder import build_agent


class SwarmProcessor(QueryProcessor):
    """Swarm-Muster: Agenten reichen sich die Kontrolle via Handoff-Tools direkt weiter — ohne zentralen Koordinator."""

    def _initialize_agent_tools(self):
        self.math_tools = create_math_tools(self.session_map["math_server"])
        self.text_tools = create_text_tools(self.session_map["text_server"])

    def _compile_graph(self):
        transfer_to_text = create_handoff_tool(
            agent_name="text_agent",
            description="Übergib die Kontrolle an den Text-Agent für Text-Operationen (word_count, reverse, uppercase).",
        )
        transfer_to_math = create_handoff_tool(
            agent_name="math_agent",
            description="Übergib die Kontrolle an den Math-Agent für Rechenoperationen (add, multiply, power).",
        )

        math_agent = build_agent(
            "math_agent",
            self.math_tools + [transfer_to_text],
            MATH_AGENT_SWARM_PROMPT,
        )
        text_agent = build_agent(
            "text_agent",
            self.text_tools + [transfer_to_math],
            TEXT_AGENT_SWARM_PROMPT,
        )

        workflow = create_swarm(
            agents=[math_agent, text_agent],
            default_active_agent="math_agent",
        )
        self.app = workflow.compile(checkpointer=MemorySaver())
