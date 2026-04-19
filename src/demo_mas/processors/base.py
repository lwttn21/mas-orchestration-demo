from abc import ABC, abstractmethod
from contextlib import AsyncExitStack
from typing import Optional, List

from loguru import logger
from mcp.client.session_group import ClientSessionGroup
from langgraph.graph.state import CompiledStateGraph
from langchain_core.messages import HumanMessage

from demo_mas.common.utils import ServerConfig


class QueryProcessor(ABC):
    def __init__(self, server_configs: List[ServerConfig]):
        self.server_configs = server_configs
        self.session_map = {}
        self.group: Optional[ClientSessionGroup] = None
        self._stack: Optional[AsyncExitStack] = None
        self.app: Optional[CompiledStateGraph] = None

    async def __aenter__(self):
        logger.info("Processor: Setting up MCP session group...")
        self._stack = AsyncExitStack()
        self.group = ClientSessionGroup()
        await self._stack.enter_async_context(self.group)

        for config in self.server_configs:
            try:
                session = await self.group.connect_to_server(config.params)
                self.session_map[config.name] = session
                logger.info(f"Connected: {config.name}")
            except Exception as e:
                logger.error(f"Failed to connect to {config.name}: {e}")
                await self._stack.aclose()
                raise

        self._initialize_agent_tools()
        self._compile_graph()
        return self

    async def __aexit__(self, exc_type, exc_val, tb):
        logger.info("Processor: Shutting down...")
        if self._stack:
            await self._stack.__aexit__(exc_type, exc_val, tb)
        self.session_map = {}
        self._stack = None
        self.group = None

    async def aprocess_query(self, query: str, thread_id: int = 1):
        if not self.app:
            raise RuntimeError("Graph nicht kompiliert.")

        initial_state = {
            "messages": [HumanMessage(content=query)],
            "result": None,
            "query": query,
        }
        config = {"configurable": {"thread_id": thread_id}}

        async for event in self.app.astream(initial_state, config, stream_mode="updates"):
            for node_name, node_state in event.items():
                logger.info(f"Node '{node_name}' done")
                yield node_state

    @abstractmethod
    def _initialize_agent_tools(self): ...

    @abstractmethod
    def _compile_graph(self): ...
