from langgraph.prebuilt import create_react_agent
from langchain_core.tools import BaseTool

from demo_mas.common.setup import get_llm


def build_agent(name: str, tools: list[BaseTool], prompt: str):
    llm = get_llm()
    return create_react_agent(
        model=llm,
        tools=tools,
        prompt=prompt,
        name=name,
    )
