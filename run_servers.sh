#!/usr/bin/env bash
set -e
trap 'kill 0' EXIT

uv run python -m demo_mas.mcp_servers.math_server &
uv run python -m demo_mas.mcp_servers.text_server &

wait
