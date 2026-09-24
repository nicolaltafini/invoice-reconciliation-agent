"""Verifica il server MCP collegandosi in-process e stampa la forma dei dati."""

import asyncio
import json

from mcp import Client

from reconciliation.mcp_server import mcp


async def main() -> None:
    async with Client(mcp) as client:
        tools = await client.list_tools()

        print("=== TOOL DISPONIBILI ===")
        for tool in tools.tools:
            print(f"- {tool.name}")

        print("\n=== CAMPI DI UN TOOL ===")
        print(json.dumps(tools.tools[0].model_dump(mode="json"), indent=2, ensure_ascii=False))

        print("\n=== CHIAMATA list_reconciliations(status=DISCREPANCIES) ===")
        result = await client.call_tool("list_reconciliations", {"status": "DISCREPANCIES"})
        print(json.dumps(result.model_dump(mode="json"), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())