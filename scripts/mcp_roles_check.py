"""Verifica che ogni ruolo veda solo i suoi tool e che le regole di approvazione valgano."""

import asyncio

from mcp import Client

from reconciliation.approvals import Role
from reconciliation.mcp_server import create_mcp_server


async def show_tools(role: Role) -> None:
    async with Client(create_mcp_server(role, f"check-{role}")) as client:
        tools = await client.list_tools()
        print(f"{role}: {[tool.name for tool in tools.tools]}")


async def call(role: Role, name: str, arguments: dict) -> None:
    print(f"\n{role} -> {name}({arguments})")
    try:
        async with Client(create_mcp_server(role, f"check-{role}")) as client:
            result = await client.call_tool(name, arguments)
            if result.structured_content is not None:
                output = result.structured_content
            else:
                output = [block.text for block in result.content if getattr(block, "type", None) == "text"]
            print(f"  is_error={result.is_error}")
            print(f"  {output}")
    except Exception as error:
        print(f"  rifiutato dal client: {error}")


async def main() -> None:
    await show_tools(Role.VIEWER)
    await show_tools(Role.OPERATOR)
    await call(Role.VIEWER, "approve_invoice", {"invoice_number": "FA-2026/0145"})
    await call(Role.OPERATOR, "approve_invoice", {"invoice_number": "2026-IV-0311"})
    await call(Role.OPERATOR, "approve_invoice", {"invoice_number": "FA-2026/0145"})


if __name__ == "__main__":
    asyncio.run(main())