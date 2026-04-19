from datetime import timedelta
from pydantic import BaseModel
from mcp.client.session_group import StreamableHttpParameters, ServerParameters

from .setup import get_config


class ServerConfig(BaseModel):
    name: str
    params: ServerParameters

    model_config = {"arbitrary_types_allowed": True}


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
