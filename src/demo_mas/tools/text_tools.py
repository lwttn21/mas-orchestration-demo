import json
from typing import List
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
from langchain.tools import ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command
from mcp.client.session import ClientSession

from .tool_registry import ToolFactory


def create_text_tools(session: ClientSession) -> List[BaseTool]:
    """Erzeugt session-gebundene Text-Tools. Session wird via Closure erfasst."""
    factory = ToolFactory(session)

    class TextArg(BaseModel):
        text: str = Field(..., description="Der zu verarbeitende Text")

    @factory.register("word_count", "Zählt die Anzahl der Wörter in einem Text.", TextArg)
    async def word_count(text: str, runtime: ToolRuntime = None) -> Command:
        result = await session.call_tool("word_count", {"text": text})
        raw = result.content[0].text
        parsed = json.loads(raw) if raw else {}
        return Command(update={
            "messages": [ToolMessage(
                content=raw,
                tool_call_id=runtime.tool_call_id,
                name="word_count",
            )],
            "result": parsed,
        })

    @factory.register("reverse", "Dreht einen Text um (Zeichen rückwärts).", TextArg)
    async def reverse(text: str, runtime: ToolRuntime = None) -> Command:
        result = await session.call_tool("reverse", {"text": text})
        raw = result.content[0].text
        parsed = json.loads(raw) if raw else {}
        return Command(update={
            "messages": [ToolMessage(
                content=raw,
                tool_call_id=runtime.tool_call_id,
                name="reverse",
            )],
            "result": parsed,
        })

    @factory.register("uppercase", "Konvertiert einen Text in Großbuchstaben.", TextArg)
    async def uppercase(text: str, runtime: ToolRuntime = None) -> Command:
        result = await session.call_tool("uppercase", {"text": text})
        raw = result.content[0].text
        parsed = json.loads(raw) if raw else {}
        return Command(update={
            "messages": [ToolMessage(
                content=raw,
                tool_call_id=runtime.tool_call_id,
                name="uppercase",
            )],
            "result": parsed,
        })

    return factory.get_tools()
