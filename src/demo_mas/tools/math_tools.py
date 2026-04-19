import json
from typing import List
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
from langchain.tools import ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command
from mcp.client.session import ClientSession

from .tool_registry import ToolFactory


def create_math_tools(session: ClientSession) -> List[BaseTool]:
    """Erzeugt session-gebundene Math-Tools. Session wird via Closure erfasst."""
    factory = ToolFactory(session)

    class TwoNumbers(BaseModel):
        a: float = Field(..., description="Erste Zahl")
        b: float = Field(..., description="Zweite Zahl")

    class PowerArgs(BaseModel):
        base: float = Field(..., description="Basis")
        exponent: float = Field(..., description="Exponent")

    @factory.register("add", "Addiert zwei Zahlen.", TwoNumbers)
    async def add(a: float, b: float, runtime: ToolRuntime = None) -> Command:
        result = await session.call_tool("add", {"a": a, "b": b})
        raw = result.content[0].text
        parsed = json.loads(raw) if raw else {}
        return Command(update={
            "messages": [ToolMessage(
                content=raw,
                tool_call_id=runtime.tool_call_id,
                name="add",
            )],
            "result": parsed,
        })

    @factory.register("multiply", "Multipliziert zwei Zahlen.", TwoNumbers)
    async def multiply(a: float, b: float, runtime: ToolRuntime = None) -> Command:
        result = await session.call_tool("multiply", {"a": a, "b": b})
        raw = result.content[0].text
        parsed = json.loads(raw) if raw else {}
        return Command(update={
            "messages": [ToolMessage(
                content=raw,
                tool_call_id=runtime.tool_call_id,
                name="multiply",
            )],
            "result": parsed,
        })

    @factory.register("power", "Berechnet base hoch exponent.", PowerArgs)
    async def power(base: float, exponent: float, runtime: ToolRuntime = None) -> Command:
        result = await session.call_tool("power", {"base": base, "exponent": exponent})
        raw = result.content[0].text
        parsed = json.loads(raw) if raw else {}
        return Command(update={
            "messages": [ToolMessage(
                content=raw,
                tool_call_id=runtime.tool_call_id,
                name="power",
            )],
            "result": parsed,
        })

    return factory.get_tools()
