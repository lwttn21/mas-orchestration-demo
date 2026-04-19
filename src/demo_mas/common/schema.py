from typing import TypedDict, Annotated, Any
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AppState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    result: Any
    query: str
