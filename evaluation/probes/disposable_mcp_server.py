from mcp.server.fastmcp import FastMCP


mcp = FastMCP("foresight-disposable")


@mcp.tool()
def read_evidence(query: str) -> dict[str, str]:
    return {
        "source": "disposable-mcp",
        "query": query,
        "excerpt": "Capacity remains uncertain.",
        "source_version": "fixture-v1",
        "date": "2030-01-01",
    }


@mcp.tool()
async def delayed_evidence(seconds: float = 0.05) -> str:
    import asyncio

    await asyncio.sleep(seconds)
    return "delayed"


@mcp.tool()
def malformed_evidence() -> list[str]:
    return ["malformed", "fixture"]


@mcp.tool()
def mutate_fixture() -> str:
    return "mutation-not-allowed"


if __name__ == "__main__":
    mcp.run()
