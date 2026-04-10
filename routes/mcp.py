from fastapi import APIRouter, Request
from tools.mcp_tools import mcp_manager

mcp_router = APIRouter()


#endpoint to connect to the MCP server
#post request to connect to the MCP server
@mcp_router.post("/api/mcp/connect")
async def connect_mcp(request: Request):
    #here frontend will send the url of the MCP server in json format
    data = await request.json()
    #Look for "url" inside data
    #If found → use it
    #If NOT → use default
    url = data.get('url', 'https://render-expense-tracker-mlxb.onrender.com/sse')


    #here we are using connect_and_fetch_tools function from mcp_manager
    #to connect to the MCP server
    #and fetch the tools from the MCP server
    success, message = await mcp_manager.connect_and_fetch_tools(url)

    #returning the success status and message to the frontend
    #also returning tools from mcp server to the frontend 
    return {
        "success": success,
        "message": message,
        "tools": [t.name for t in mcp_manager.tools]
    }



#endpoint to check ststus of mcp server
#get request to check ststus of mcp server
@mcp_router.get("/api/mcp/status")
async def mcp_status():
    return {
        "connected": mcp_manager.is_connected,
        "url": mcp_manager.connected_url,
        "tool_count": len(mcp_manager.tools),
        "tools": [t.name for t in mcp_manager.tools]
    }


#endpoint to disconnect from the MCP server
#post request to disconnect from the MCP server
@mcp_router.post("/api/mcp/disconnect")
async def disconnect_mcp():
    #using disconnect function from mcp_manager
    #to disconnect from the MCP server
    success, message = await mcp_manager.disconnect()
    #returning the success status and message to the frontend
    return {
        "success": success,
        "message": message
    }
