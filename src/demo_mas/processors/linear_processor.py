from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from demo_mas.processors.base import QueryProcessor
from demo_mas.common.schema import AppState
from demo_mas.common.prompts import MATH_AGENT_PROMPT
from demo_mas.tools.math_tools import create_math_tools
from demo_mas.agents.agent_builder import build_agent


class LinearProcessor(QueryProcessor):
    """Eine-Agent-Pipeline: Query → Math-Agent → Antwort."""

    def _initialize_agent_tools(self):
        math_session = self.session_map["math_server"]
        self.math_tools = create_math_tools(math_session)

    def _compile_graph(self):
        math_agent = build_agent("math_agent", self.math_tools, MATH_AGENT_PROMPT)

        builder = StateGraph(AppState)
        builder.add_node("math_agent", math_agent)
        builder.add_edge(START, "math_agent")
        builder.add_edge("math_agent", END)

        self.app = builder.compile(checkpointer=MemorySaver())
