import asyncio
import sys
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    root=Path(__file__).resolve().parents[1]
    params=StdioServerParameters(command=sys.executable,args=[str(root/'run_mcp.py')],cwd=str(root))
    async with stdio_client(params) as (read,write):
        async with ClientSession(read,write) as session:
            await session.initialize()
            result=await session.list_tools()
            assert len(result.tools)==8
            response=await session.call_tool('expiring_memberships',{'days':-1})
            assert response.isError
            print('MCP startup, eight tools and validation call passed')
asyncio.run(main())
