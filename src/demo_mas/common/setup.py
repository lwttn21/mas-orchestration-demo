from pathlib import Path
import os
import yaml
from dotenv import load_dotenv, find_dotenv
from langchain_openai import ChatOpenAI
from functools import lru_cache

load_dotenv(find_dotenv())


@lru_cache(maxsize=1)
def get_config() -> dict:
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
