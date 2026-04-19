from typing import Callable, List, Optional, Type
from pydantic import BaseModel
from langchain_core.tools import StructuredTool, BaseTool
from mcp.client.session import ClientSession


class ToolFactory:
    """Factory für session-gebundene Tools via Closure-Pattern."""

    def __init__(self, session: ClientSession):
        self.session = session
        self.tools: List[BaseTool] = []

    def register(
        self,
        name: str,
        description: str,
        args_schema: Optional[Type[BaseModel]] = None,
    ) -> Callable:
        if args_schema is None:
            class EmptySchema(BaseModel):
                pass
            args_schema = EmptySchema

        def decorator(func: Callable) -> Callable:
            self.tools.append(StructuredTool.from_function(
                coroutine=func,
                name=name,
                description=description,
                args_schema=args_schema,
            ))
            return func
        return decorator

    def get_tools(self) -> List[BaseTool]:
        return self.tools.copy()
