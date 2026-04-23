from langgraph.checkpoint.memory import MemorySaver
from langgraph_supervisor import create_supervisor

from demo_mas.processors.query_processor import QueryProcessor
from demo_mas.common.prompts import (
    MATH_AGENT_SOLO_PROMPT,
    TEXT_AGENT_SOLO_PROMPT,
    SUPERVISOR_PROMPT,
)
from demo_mas.common.setup import get_llm
from demo_mas.tools.math_tools import create_math_tools
from demo_mas.tools.text_tools import create_text_tools
from demo_mas.agents.agent_builder import build_agent


class SupervisorProcessor(QueryProcessor):
    """Supervisor-Muster: dedizierter Koordinator-Agent delegiert dynamisch an Fach-Agenten."""

    def _initialize_agent_tools(self):
        self.math_tools = create_math_tools(self.session_map["math_server"])
        self.text_tools = create_text_tools(self.session_map["text_server"])

    def _compile_graph(self):
        math_agent = build_agent("math_agent", self.math_tools, MATH_AGENT_SOLO_PROMPT)
        text_agent = build_agent("text_agent", self.text_tools, TEXT_AGENT_SOLO_PROMPT)

        workflow = create_supervisor(
            agents=[math_agent, text_agent],
            model=get_llm(),
            prompt=SUPERVISOR_PROMPT,
            output_mode="full_history",
        )
        self.app = workflow.compile(checkpointer=MemorySaver())
