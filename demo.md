# Demo-MAS-Projekt — Implementierungsplan

> **Zweck:** Ein vereinfachtes Multi-Agent-System (MAS) als Lern- und Demo-Projekt für die Bachelorarbeit zum Thema **Orchestrierung von LLM-Agenten**. Die Architektur spiegelt das Hauptprojekt (MAS in Production) wider, ist aber stark abgespeckt: kein Frontend, keine Datenbanken, triviale Domäne.
>
> **Dieses File ist self-contained** — eine neue Claude-Code-Session in einem frischen Repo kann damit von Null starten.

---

## 1. Projektziele

### Lernziele
- **MCP-Server** eigenständig implementieren (FastMCP, HTTP-Transport)
- **Tool-Wrapper** mit Registry und Closure-basierter Session-Bindung bauen
- **Agent-Layer** mit LangGraph aufbauen
- **Query Processor** als Async-Context-Manager, der MCP-Sessions verwaltet
- **Orchestrierungsmuster** vergleichen (linear, Supervisor, Swarm) — thesisrelevant

### Nicht-Ziele (bewusst weggelassen)
- Kein Frontend (reiner CLI)
- Keine Datenbank (MongoDB/Qdrant kommt ggf. später)
- Kein HITL, kein Tracing-Dashboard, kein Streaming-UI
- Keine Voice-Services, kein ACE, keine Evaluation-Pipeline
- Keine komplexe Fachdomäne — triviale Tools (Math, Text)

### Fachdomäne der Demo
Triviale Platzhalter-Domäne: **Rechner- und Text-Utilities**. Zwei MCP-Server liefern je 2–3 Tools:
- `math_server`: `add`, `multiply`, `power`
- `text_server`: `word_count`, `reverse`, `uppercase`

Das lässt die Orchestrierung im Vordergrund — die eigentliche Thesis-Frage.

---

## 2. Architektur (abstrakt)

```
┌────────────────────────────────────────────────────┐
│  CLI Entry (main.py)                               │
│  - Parst Query                                     │
│  - Instanziiert QueryProcessor                     │
│  - Gibt Ergebnis auf Konsole aus                   │
└────────────────────┬───────────────────────────────┘
                     │
┌────────────────────▼───────────────────────────────┐
│  Query Processor Layer                             │
│  - QueryProcessor (abstract base, async context)   │
│  - LinearProcessor / SupervisorProcessor / Swarm   │
│  - Managed: MCP-Sessions, Tool-Binding, Graph      │
└────────────────────┬───────────────────────────────┘
                     │
┌────────────────────▼───────────────────────────────┐
│  Agent Layer (LangGraph)                           │
│  - create_react_agent pro Agent                    │
│  - Shared AppState (TypedDict)                     │
└────────────────────┬───────────────────────────────┘
                     │
┌────────────────────▼───────────────────────────────┐
│  Tool Wrapper Layer                                │
│  - ToolFactory mit Closure-Pattern                 │
│  - LangChain StructuredTools                       │
│  - Übersetzt MCP-Protokoll ↔ LangGraph Command API │
└────────────────────┬───────────────────────────────┘
                     │ MCP Protocol (HTTP/SSE)
┌────────────────────▼───────────────────────────────┐
│  MCP Server Layer (FastMCP)                        │
│  - math_server   (Port 3001)                       │
│  - text_server   (Port 3002)                       │
│  - Jeder Server ist ein eigener Prozess            │
└────────────────────────────────────────────────────┘
```

### Kernpatterns (aus dem Hauptprojekt übernommen)

1. **Async Context Manager** für QueryProcessor (`__aenter__`/`__aexit__`) — sauberes Session-Lifecycle-Management
2. **Closure-basiertes Session-Binding** — Tools erfassen MCP-Sessions via Closure, kein globaler State
3. **Command API** — Tools geben `Command(update=...)` zurück, statt direkt State zu mutieren
4. **ClientSessionGroup** — Sammelt alle MCP-Sessions in einem verwalteten Gruppenobjekt

---

## 3. Tech Stack

| Kategorie | Library | Zweck |
|---|---|---|
| LLM-Provider | **OpenRouter** (via `langchain-openai`) | Zugriff auf Gemini/Claude/GPT |
| Agent-Orchestrierung | `langgraph` ≥ 1.0 | State-Machine-Workflows |
| LLM-Abstraktion | `langchain` ≥ 1.0 | Modelle und Tools |
| Tool-Protokoll | `fastmcp` ≥ 2.13 | MCP-Server und -Client |
| MCP-Client | `mcp` (Python SDK) | `ClientSessionGroup`, Tool-Calls |
| Logging | `loguru` | Einfaches strukturiertes Logging |
| Config | `python-dotenv`, `pyyaml` | `.env` + `config.yaml` |
| Validation | `pydantic` ≥ 2.0 | Schemas |
| Async HTTP | `httpx` | Health-Checks |

**Python:** 3.11 oder 3.12

**Dependency-Manager-Empfehlung:** `uv` (schnell, modern) oder `pip` mit `pyproject.toml`.

---

## 4. Projektstruktur

```
demo_mas/
├── .env.example                    # Template für API-Keys
├── .gitignore
├── config.yaml                     # LLM- & Server-Konfiguration
├── pyproject.toml                  # Dependencies + Package-Metadata
├── README.md
├── demo.md                         # Dieses File (dient als Context für Claude)
│
├── run_servers.sh                  # Startskript: alle MCP-Server parallel (Phase 1+)
│
└── src/demo_mas/
    ├── __init__.py
    ├── main.py                     # CLI-Entry-Point
    │
    ├── common/
    │   ├── __init__.py
    │   ├── schema.py               # AppState (TypedDict für LangGraph)
    │   ├── prompts.py              # System-Prompts pro Agent
    │   ├── setup.py                # LLM-Init (OpenRouter), Config-Loader
    │   └── utils.py                # ServerConfig, MCP-URLs, Health-Checks
    │
    ├── mcp_servers/
    │   ├── __init__.py
    │   ├── math_server.py          # FastMCP-Server, Port 3001
    │   └── text_server.py          # FastMCP-Server, Port 3002
    │
    ├── tools/
    │   ├── __init__.py
    │   ├── tool_registry.py        # ToolFactory (Closure-Pattern)
    │   ├── math_tools.py           # create_math_tools(session)
    │   └── text_tools.py           # create_text_tools(session)
    │
    ├── agents/
    │   ├── __init__.py
    │   └── agent_builder.py        # Helper um create_react_agent
    │
    └── processors/
        ├── __init__.py
        ├── base.py                 # QueryProcessor (abstract, async context)
        ├── linear_processor.py     # Linear pipeline (Phase 3)
        ├── supervisor_processor.py # Supervisor-Muster (Phase 5)
        └── swarm_processor.py      # Swarm-Muster (Phase 5)
```

---

## 5. Prerequisites

### Vor Phase 0 besorgen
1. **OpenRouter Account** → https://openrouter.ai/ → API-Key erstellen
2. **Python 3.11 oder 3.12** installiert (`python --version`)
3. Optional: `uv` installieren (`pip install uv`)

### `.env.example` Inhalt (Phase 0 erstellen)
```bash
# OpenRouter (primary LLM provider)
OPENROUTER_API_KEY=sk-or-v1-...

# Optional: für Tracing später
# LANGSMITH_API_KEY=...
```

**WICHTIG:** Keine Anführungszeichen um Werte in `.env` — Docker/python-dotenv interpretieren diese sonst als Teil des Values.

### `config.yaml` Inhalt (Phase 0 erstellen)
```yaml
# LLM Configuration
provider: "openrouter"

openrouter:
  model_name: "google/gemini-2.5-flash"  # günstig + schnell für Demo
  base_url: "https://openrouter.ai/api/v1"

model_parameters:
  temperature: 0.2
  max_tokens: 4096

# MCP Server URLs (lokal, nicht Docker)
mcp_servers:
  math_server:
    url: "http://127.0.0.1:3001/mcp"
  text_server:
    url: "http://127.0.0.1:3002/mcp"
```

---

## 6. Build-Phasen (in dieser Reihenfolge mit Claude Code umsetzen)

Jede Phase ist ein in sich geschlossener, **testbarer** Meilenstein. Erst weitergehen, wenn die Phase funktioniert.

### Phase 0 — Projekt-Skeleton & LLM-Verbindung ✅ Start hier

**Ziel:** Leeres Projekt, Dependencies installiert, LLM antwortet auf einen Test-Prompt.

**Dateien anlegen:**
- `pyproject.toml`
- `.env.example` + `.env` (Kopie mit echtem Key)
- `.gitignore` (mindestens: `.env`, `__pycache__`, `*.egg-info`, `.venv`)
- `config.yaml`
- `src/demo_mas/__init__.py` (leer)
- `src/demo_mas/common/__init__.py`
- `src/demo_mas/common/setup.py`
- `src/demo_mas/common/utils.py`

**`pyproject.toml` Minimal-Skelett:**
```toml
[project]
name = "demo-mas"
version = "0.1.0"
requires-python = ">=3.11,<3.13"
dependencies = [
    "langchain>=1.0",
    "langgraph>=1.0",
    "langchain-openai>=0.2",
    "fastmcp>=2.13",
    "mcp>=1.0",
    "pydantic>=2.0",
    "python-dotenv",
    "pyyaml",
    "loguru",
    "httpx",
    "uvicorn",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/demo_mas"]
```

**`common/setup.py` — LLM-Init mit OpenRouter:**
```python
from pathlib import Path
import os
import yaml
from dotenv import load_dotenv, find_dotenv
from langchain_openai import ChatOpenAI
from functools import lru_cache

load_dotenv(find_dotenv())

@lru_cache(maxsize=1)
def get_config() -> dict:
    # Auto-Discovery: suche config.yaml im Projekt-Root
    here = Path(__file__).resolve()
    for parent in here.parents:
        cfg = parent / "config.yaml"
        if cfg.exists():
            with open(cfg) as f:
                return yaml.safe_load(f)
    raise FileNotFoundError("config.yaml nicht gefunden")

def get_llm():
    cfg = get_config()
    provider = cfg["provider"]
    params = cfg.get("model_parameters", {})

    if provider == "openrouter":
        or_cfg = cfg["openrouter"]
        return ChatOpenAI(
            model=or_cfg["model_name"],
            base_url=or_cfg["base_url"],
            api_key=os.getenv("OPENROUTER_API_KEY"),
            temperature=params.get("temperature", 0.2),
            max_tokens=params.get("max_tokens", 4096),
        )
    raise ValueError(f"Unbekannter Provider: {provider}")
```

**Test (Phase 0 abgeschlossen wenn):**
```bash
uv sync  # oder: pip install -e .
python -c "from demo_mas.common.setup import get_llm; print(get_llm().invoke('Sag Hallo').content)"
```
→ Muss eine sinnvolle LLM-Antwort liefern.

---

### Phase 1 — Erster MCP-Server

**Ziel:** `math_server.py` läuft als eigener Prozess, hat 2–3 Tools, Health-Endpoint antwortet.

**Dateien anlegen:**
- `src/demo_mas/mcp_servers/__init__.py`
- `src/demo_mas/mcp_servers/math_server.py`

**`mcp_servers/math_server.py` Skelett:**
```python
from mcp.server.fastmcp import FastMCP
from starlette.responses import JSONResponse
from loguru import logger
import sys

logger.remove()
logger.add(sys.stderr, level="INFO")

mcp = FastMCP(
    name="math_server",
    host="127.0.0.1",
    port=3001,
    streamable_http_path="/mcp",
)

@mcp.tool()
async def add(a: float, b: float) -> dict:
    """Addiert zwei Zahlen und gibt das Ergebnis zurück."""
    result = a + b
    logger.info(f"add({a}, {b}) = {result}")
    return {"result": result, "operation": "add"}

@mcp.tool()
async def multiply(a: float, b: float) -> dict:
    """Multipliziert zwei Zahlen."""
    result = a * b
    logger.info(f"multiply({a}, {b}) = {result}")
    return {"result": result, "operation": "multiply"}

@mcp.tool()
async def power(base: float, exponent: float) -> dict:
    """Berechnet base hoch exponent."""
    result = base ** exponent
    return {"result": result, "operation": "power"}

# Health-Endpoint für spätere Health-Checks
@mcp.custom_route("/health", methods=["GET"])
async def health(_):
    return JSONResponse({"status": "ok", "server": "math_server"})

if __name__ == "__main__":
    logger.info("Starting math_server on http://127.0.0.1:3001/mcp")
    mcp.run(transport="streamable-http")
```

**Test (Phase 1 abgeschlossen wenn):**
```bash
# Terminal 1:
python -m demo_mas.mcp_servers.math_server

# Terminal 2:
curl http://127.0.0.1:3001/health
# → {"status":"ok","server":"math_server"}
```

---

### Phase 2 — Tool-Wrapper mit Registry & Closures

**Ziel:** Python-Skript, das via `ClientSessionGroup` mit dem MCP-Server spricht und ein Tool aufruft — über den `ToolFactory`-Wrapper.

**Dateien anlegen:**
- `src/demo_mas/common/schema.py`
- `src/demo_mas/common/utils.py`
- `src/demo_mas/tools/__init__.py`
- `src/demo_mas/tools/tool_registry.py`
- `src/demo_mas/tools/math_tools.py`

**`common/schema.py`:**
```python
from typing import TypedDict, Annotated, Any
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AppState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    result: Any  # Tool-Ergebnisse
    query: str
```

**`common/utils.py`:**
```python
from datetime import timedelta
from pydantic import BaseModel
from mcp.client.session_group import StreamableHttpParameters, ServerParameters
from .setup import get_config

class ServerConfig(BaseModel):
    name: str
    params: ServerParameters

def get_server_params() -> list[ServerConfig]:
    cfg = get_config()
    configs = []
    for name, server_cfg in cfg["mcp_servers"].items():
        params = StreamableHttpParameters(
            url=server_cfg["url"],
            timeout=timedelta(seconds=60),
            sse_read_timeout=300.0,
        )
        configs.append(ServerConfig(name=name, params=params))
    return configs
```

**`tools/tool_registry.py` — Der Kern des Closure-Patterns:**
```python
from typing import Callable, List, Optional, Type
from pydantic import BaseModel
from langchain_core.tools import StructuredTool, BaseTool
from langchain.tools import ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command
from mcp.client.session import ClientSession
from loguru import logger
import json

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
```

**`tools/math_tools.py` — Beispiel für Closure-Binding:**
```python
from typing import List
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
from langchain.tools import ToolRuntime
from langchain_core.messages import ToolMessage
from langgraph.types import Command
from mcp.client.session import ClientSession
from loguru import logger
import json

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
            "messages": [ToolMessage(content=raw, tool_call_id=runtime.tool_call_id, name="multiply")],
            "result": parsed,
        })

    @factory.register("power", "Berechnet base hoch exponent.", PowerArgs)
    async def power(base: float, exponent: float, runtime: ToolRuntime = None) -> Command:
        result = await session.call_tool("power", {"base": base, "exponent": exponent})
        raw = result.content[0].text
        parsed = json.loads(raw) if raw else {}
        return Command(update={
            "messages": [ToolMessage(content=raw, tool_call_id=runtime.tool_call_id, name="power")],
            "result": parsed,
        })

    return factory.get_tools()
```

**Test (Phase 2 abgeschlossen wenn):**
Ad-hoc Skript, das einen MCP-Client öffnet, ein Tool aufruft und das Ergebnis loggt. (Wird ausgeführt, während `math_server` läuft.)

---

### Phase 3 — Erster Agent + Query Processor (Linear)

**Ziel:** Eine natürlich-sprachliche Query (`"Was ist 7 + 5?"`) wird von einem Agenten korrekt beantwortet, indem er das `add`-Tool aufruft.

**Dateien anlegen:**
- `src/demo_mas/common/prompts.py`
- `src/demo_mas/agents/__init__.py`
- `src/demo_mas/agents/agent_builder.py`
- `src/demo_mas/processors/__init__.py`
- `src/demo_mas/processors/base.py`
- `src/demo_mas/processors/linear_processor.py`
- `src/demo_mas/main.py`

**`common/prompts.py`:**
```python
MATH_AGENT_PROMPT = """Du bist ein Rechen-Agent. Nutze die verfügbaren Math-Tools,
um Berechnungen durchzuführen. Gib das Ergebnis in einem klaren Satz zurück."""

SUPERVISOR_PROMPT = """Du koordinierst mehrere Fach-Agenten. Entscheide,
welcher Agent die Anfrage am besten beantworten kann."""
```

**`processors/base.py` — Abstract Base mit Async Context Manager:**
```python
from abc import ABC, abstractmethod
from contextlib import AsyncExitStack
from typing import Optional, List
from loguru import logger

from mcp.client.session_group import ClientSessionGroup
from langgraph.graph.state import CompiledStateGraph
from langchain_core.messages import HumanMessage, SystemMessage

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
            await self._stack.aexit(exc_type, exc_val, tb) if False else await self._stack.__aexit__(exc_type, exc_val, tb)
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

        final_state = None
        async for event in self.app.astream(initial_state, config, stream_mode="updates"):
            for node_name, node_state in event.items():
                logger.info(f"Node '{node_name}' done")
                final_state = node_state
                yield node_state
        return final_state

    @abstractmethod
    def _initialize_agent_tools(self): ...

    @abstractmethod
    def _compile_graph(self): ...
```

**`agents/agent_builder.py`:**
```python
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
```

**`processors/linear_processor.py`:**
```python
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
```

**`main.py` — CLI-Entry:**
```python
import asyncio
import sys
from loguru import logger

from demo_mas.common.utils import get_server_params
from demo_mas.processors.linear_processor import LinearProcessor

async def main(query: str):
    configs = get_server_params()
    async with LinearProcessor(configs) as processor:
        async for state in processor.aprocess_query(query):
            pass

        final = state
        last_msg = final["messages"][-1]
        print("\n=== ANTWORT ===")
        print(last_msg.content)

if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else "Was ist 12 * 7?"
    asyncio.run(main(query))
```

**Test (Phase 3 abgeschlossen wenn):**
```bash
# Terminal 1: math_server läuft
python -m demo_mas.mcp_servers.math_server

# Terminal 2:
python -m demo_mas.main "Was ist 12 mal 7?"
# → Antwort sollte "84" enthalten
```

---

### Phase 4 — Zweiter MCP-Server + Zweiter Agent

**Ziel:** Zwei Agenten, jeder mit eigenem Toolset, in linearer Pipeline.

**Dateien anlegen/ändern:**
- `src/demo_mas/mcp_servers/text_server.py` (neu, Port 3002)
- `src/demo_mas/tools/text_tools.py` (neu)
- `src/demo_mas/common/prompts.py` (erweitern: `TEXT_AGENT_PROMPT`)
- `config.yaml` (erweitern: `text_server` URL)
- `src/demo_mas/processors/linear_processor.py` (erweitern: 2 Agenten)
- `run_servers.sh` (neu, startet beide Server parallel)

**`text_server.py` baugleich zu `math_server.py`** mit Port 3002 und Tools:
- `word_count(text: str)` → `{"count": int}`
- `reverse(text: str)` → `{"reversed": str}`
- `uppercase(text: str)` → `{"uppercase": str}`

**`run_servers.sh`:**
```bash
#!/usr/bin/env bash
set -e
trap 'kill 0' EXIT

python -m demo_mas.mcp_servers.math_server &
python -m demo_mas.mcp_servers.text_server &

wait
```
→ `chmod +x run_servers.sh`

**Erweitere `LinearProcessor._compile_graph`** um ein zweites Knoten:
```python
text_agent = build_agent("text_agent", self.text_tools, TEXT_AGENT_PROMPT)
builder.add_node("text_agent", text_agent)
builder.add_edge("math_agent", "text_agent")
builder.add_edge("text_agent", END)
```

**Test (Phase 4 abgeschlossen wenn):**
Eine Query wie `"Rechne 5+3 aus und gib mir das Ergebnis in Großbuchstaben"` durchläuft beide Agenten korrekt.

---

### Phase 5 — Alternative Orchestrierungsmuster (**thesisrelevant**)

**Ziel:** Gleiche Agenten/Tools, unterschiedliche Orchestrierung. Direkt vergleichbar für die Thesis-Evaluation.

**Dateien anlegen:**
- `src/demo_mas/processors/supervisor_processor.py`
- `src/demo_mas/processors/swarm_processor.py`

**Supervisor-Muster:**
Ein dedizierter Supervisor-Agent entscheidet dynamisch, welcher Fach-Agent als Nächstes läuft. Nutze `langgraph-supervisor` oder baue manuell mit conditional edges.

**Swarm-Muster:**
Agenten rufen sich gegenseitig via `Command(goto=...)` auf — kein zentraler Koordinator. Nutze `langgraph-swarm` oder baue manuell.

**CLI erweitern:**
`main.py` mit `--processor linear|supervisor|swarm` Argument.

**Bei der Implementierung:** Das Command-API in Tools bleibt identisch — nur die Graph-Struktur in `_compile_graph()` ändert sich. Das ist genau der Punkt, den die Thesis zeigen will: **gleiche Tools, gleiche Agenten, verschiedene Orchestrierung**.

**Evaluations-Metriken** (simpel, aber thesisrelevant):
- Token-Verbrauch pro Query (`response.usage_metadata` sammeln)
- Wall-Clock-Zeit pro Query
- Anzahl Tool-Calls

Diese in einem simplen `results/comparison.csv` festhalten — kein Dashboard nötig.

**Test (Phase 5 abgeschlossen wenn):**
Gleiche Query durch alle drei Processor — nachweislich unterschiedliche Call-Sequenzen, messbare Token/Zeit-Unterschiede.

---

### Phase 6 — Docker (optional, erst wenn stabil)

**Wann sinnvoll?**
- Wenn du das Projekt in der Thesis-Verteidigung vorzeigen willst
- Wenn du später Datenbanken (MongoDB/Qdrant) hinzufügst
- Wenn du ≥3 MCP-Server hast

**Nicht sinnvoll**, solange du aktiv entwickelst — lokaler Start mit `run_servers.sh` ist schneller zu debuggen.

**Dateien, wenn du Docker machst:**
- `Dockerfile.mcp` — Basis-Image für alle MCP-Server
- `docker-compose.yml` — Ein Service pro MCP-Server + ein App-Service
- `.dockerignore`

**Server-URLs in `config.yaml` anpassen** (Container-Namen statt `127.0.0.1`):
```yaml
mcp_servers:
  math_server:
    url: "http://math_server:3001/mcp"
```

**Netzwerk:** Alle Services in ein `app-network` Bridge-Netzwerk.

---

## 7. Wichtige Stolperfallen

### 7.1 MCP-Transport
- **Nutze HTTP-Transport** (`streamable-http`), nicht `stdio`. Bleibt vergleichbar mit dem Hauptprojekt und erlaubt echte Microservice-Architektur.
- In FastMCP: `mcp.run(transport="streamable-http")` + `streamable_http_path="/mcp"`.

### 7.2 Session-Lifecycle
- MCP-Sessions **müssen geöffnet sein, bevor** Tools erzeugt werden (Closure erfasst die Session).
- MCP-Sessions **müssen sauber geschlossen werden** — deshalb `AsyncExitStack` in `__aenter__`/`__aexit__`.
- **Nie** eine Session nach dem Exit des Context Managers aufrufen → kryptische `anyio`-Fehler.

### 7.3 ToolRuntime ist injected, nicht übergeben
LangGraph injiziert `runtime: ToolRuntime` automatisch in den Tool-Call. Signatur muss `runtime: ToolRuntime = None` (oder ohne Default — LangGraph injiziert trotzdem) enthalten. Der Agent sendet dieses Argument **nicht** mit.

### 7.4 `.env` ohne Anführungszeichen
```bash
# ✅ CORRECT
OPENROUTER_API_KEY=sk-or-v1-abc...
# ❌ WRONG (Quotes werden Teil des Werts)
OPENROUTER_API_KEY="sk-or-v1-abc..."
```

### 7.5 OpenRouter-Spezifika
- `base_url` ist `https://openrouter.ai/api/v1` — OpenAI-kompatibel
- Modellnamen mit Provider-Prefix: `google/gemini-2.5-flash`, `anthropic/claude-3-5-sonnet`, `openai/gpt-4o-mini`
- Für die Demo: **Gemini Flash** ist günstig, schnell und reicht vollkommen
- Prüfe Credits auf https://openrouter.ai/activity

### 7.6 Keine verfrühte Abstraktion
- Abstrakte Basisklasse `QueryProcessor` **erst in Phase 3** einführen (beim ersten echten Processor — YAGNI).
- Drei Orchestrierungsmuster **erst in Phase 5**, nicht früher.
- Kein Tracing, kein Checkpointing-Backend-Wechsel, kein Streaming, bis Phase 5 abgeschlossen ist.

### 7.7 `create_react_agent`-Input-Format
Beim Einhängen als LangGraph-Knoten erwartet der ReAct-Agent einen State, der mindestens `messages` enthält. Dein `AppState` erfüllt das via `add_messages`-Reducer.

---

## 8. Thesis-Anknüpfungspunkte

Das Demo-Projekt ist explizit so designed, dass es **die Forschungsfrage der Thesis** (Orchestrierung) direkt demonstriert:

| Thesis-Aspekt | Wo im Demo-Projekt sichtbar |
|---|---|
| **Vergleich Orchestrierungsmuster** | Phase 5 — drei Processors mit identischem Tool-/Agent-Stack |
| **Token-/Zeit-Evaluation** | Phase 5 — `usage_metadata` per Processor sammeln |
| **Skalierbarkeit** | Architektur: mehr MCP-Server hinzufügen = ein weiterer Eintrag in `config.yaml` |
| **Tool-Abstraktion über MCP** | Phase 1–2 — Tools laufen in eigenen Prozessen, sprachneutral |
| **Closure-basiertes Binding** | `tool_registry.py` — zeigt sauberes Scope-Management ohne globalen State |

---

## 9. Reihenfolge der Prompts für Claude Code (neue Session)

Wenn du im neuen Repo startest, gib Claude Code in dieser Reihenfolge die Prompts:

1. **Phase 0:** *"Lies `demo.md` komplett. Setze Phase 0 um: lege `pyproject.toml`, `.env.example`, `.gitignore`, `config.yaml`, und `src/demo_mas/common/setup.py` an. Teste abschließend, dass `get_llm().invoke('hi')` funktioniert."*

2. **Phase 1:** *"Umsetze Phase 1 aus `demo.md`: `math_server.py` als FastMCP-Server. Teste den Health-Endpoint."*

3. **Phase 2:** *"Phase 2: Tool-Registry mit Closure-Pattern und `math_tools.py`. Schreibe ein kleines Testskript, das via `ClientSessionGroup` das `add`-Tool aufruft."*

4. **Phase 3:** *"Phase 3: `QueryProcessor` (abstract), `LinearProcessor`, `agent_builder.py`, `main.py`. End-to-end-Test mit `python -m demo_mas.main 'Was ist 12 mal 7?'`."*

5. **Phase 4:** *"Phase 4: `text_server.py` + `text_tools.py` + zweiter Agent in `LinearProcessor`. `run_servers.sh` für Parallelstart."*

6. **Phase 5:** *"Phase 5: `supervisor_processor.py` und `swarm_processor.py`. CLI um `--processor` erweitern. Einfache Evaluations-CSV pro Query (Tokens, Zeit, Tool-Calls)."*

7. **Phase 6 (optional):** *"Phase 6: Docker-Compose-Setup für alle MCP-Server."*

**Wichtig:** Zwischen den Phasen immer erst testen, bevor die nächste beginnt. Ein kaputter Processor in Phase 3 blockiert Phase 5 komplett.

---

## 10. Zusammenfassung / Kern-Takeaways

- **Klein starten:** 1 Server, 1 Tool, 1 Agent. End-to-End funktionsfähig, dann erweitern.
- **Closure-Pattern** ist das Herzstück — macht Session-Management sauber und testbar.
- **Async Context Manager** im Processor erzwingt sauberes Resource-Lifecycle.
- **Kein Docker** bis Phase 6 — lokale Entwicklung ist schneller.
- **OpenRouter + Gemini Flash** ist für die Demo optimal (günstig, schnell, ausreichend).
- **Orchestrierungs-Vergleich** ist der Thesis-Kern — Phase 5 ist das eigentliche Ziel, alles davor ist Infrastruktur.
