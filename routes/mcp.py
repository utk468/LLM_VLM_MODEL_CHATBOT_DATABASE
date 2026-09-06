from fastapi import APIRouter, Request
from tools.mcp_tools import mcp_manager

mcp_router = APIRouter()

@mcp_router.post("/api/mcp/connect")
async def connect_mcp(request: Request):

    data = await request.json()

    url = data.get('url', 'https://render-expense-tracker-mlxb.onrender.com/sse')

    success, message = await mcp_manager.connect_and_fetch_tools(url)

    return {
        "success": success,
        "message": message,
        "tools": [t.name for t in mcp_manager.tools]
    }

@mcp_router.get("/api/mcp/status")
async def mcp_status():
    return {
        "connected": mcp_manager.is_connected,
        "url": mcp_manager.connected_url,
        "tool_count": len(mcp_manager.tools),
        "tools": [t.name for t in mcp_manager.tools]
    }

@mcp_router.post("/api/mcp/disconnect")
async def disconnect_mcp():

    success, message = await mcp_manager.disconnect()

    return {
        "success": success,
        "message": message
    }
