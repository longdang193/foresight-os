from __future__ import annotations

import argparse

from mcp.server.fastmcp import FastMCP


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, required=True)
    args = parser.parse_args()
    server = FastMCP("foresight-optimization", host="127.0.0.1", port=args.port, stateless_http=True)

    @server.tool()
    def read_evidence(query: str) -> str:
        return f"evidence:{query}"

    server.run("streamable-http")


if __name__ == "__main__":
    main()
