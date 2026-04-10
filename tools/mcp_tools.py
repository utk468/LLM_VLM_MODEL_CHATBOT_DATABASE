import asyncio
from typing import Any, List, Optional
from mcp import ClientSession
from mcp.client.sse import sse_client
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, create_model, Field
import json



class MCPToolManager:
    def __init__(self):
        self.tools: List[StructuredTool] = []
        self.connected_url: Optional[str] = None
        self.is_connected = False
        
        self._session: Optional[ClientSession] = None
        self._exit_stack: Optional[asyncio.ExitStack] = None

    async def connect_and_fetch_tools(self, url: str):
        """
        Connects to an MCP server via SSE and fetches available tools.
        In FastAPI, this runs directly in the main event loop.
        """
        if self.is_connected:
            await self.disconnect()

        try:
            from contextlib import AsyncExitStack
            self._exit_stack = AsyncExitStack()
            
            # 1. Connect to SSE
            read_stream, write_stream = await self._exit_stack.enter_async_context(sse_client(url))
            
            # 2. Start Session
            self._session = await self._exit_stack.enter_async_context(ClientSession(read_stream, write_stream))
            
            # 3. Initialize
            await self._session.initialize()
            
            # 4. Fetch Tools
            mcp_tools_response = await self._session.list_tools()
            mcp_tools = mcp_tools_response.tools
            
            new_tools = []
            for tool in mcp_tools:
                def create_tool_fn(tool_name):
                    async def tool_fn(**kwargs):
                        if not self._session:
                            return "Error: MCP Session not initialized."
                        try:
                            result = await self._session.call_tool(tool_name, arguments=kwargs)
                            
                            if hasattr(result, "content"):
                                try:
                                    return result.content[0].text
                                except (IndexError, KeyError, AttributeError):
                                    return str(result.content)
                            return str(result)
                        except Exception as e:
                            return f"Tool Error: {str(e)}"
                    return tool_fn

                name = tool.name
                description = tool.description or f"MCP Tool: {name}"
                
                try:
                    if hasattr(tool, "input_schema"):
                        schema = tool.input_schema
                    elif hasattr(tool, "inputSchema"):
                        schema = tool.inputSchema
                    elif isinstance(tool, dict):
                        schema = tool.get("inputSchema", tool.get("input_schema", {}))
                    else:
                        schema = {}

                    properties = schema.get("properties", {}) if isinstance(schema, dict) else getattr(schema, "properties", {})
                    required = schema.get("required", []) if isinstance(schema, dict) else getattr(schema, "required", [])
                    fields = {}
                    
                    for prop_name, prop_info in properties.items():
                        p_type = Any
                        m_type = prop_info.get("type")
                        if m_type == "string": p_type = str
                        elif m_type == "number": p_type = float
                        elif m_type == "integer": p_type = int
                        elif m_type == "boolean": p_type = bool
                        
                        default_val = ... if prop_name in required else None
                        
                        fields[prop_name] = (
                            p_type, 
                            Field(
                                default=default_val, 
                                description=prop_info.get("description", "")
                            )
                        )
                    
                    args_schema = create_model(f"{name}_schema", **fields)
                except Exception as e:
                    print(f" MCP: Schema generation failed for {name}: {str(e)}")
                    # Use a generic fallback schema to avoid breaking tool-calling logic
                    class FallbackSchema(BaseModel):
                        arguments: dict = Field(default_factory=dict, description="Tool arguments")
                    args_schema = FallbackSchema

                lc_tool = StructuredTool.from_function(
                    coroutine=create_tool_fn(name),
                    name=name,
                    description=description,
                    args_schema=args_schema
                )
                new_tools.append(lc_tool)

            self.tools = new_tools
            self.connected_url = url
            self.is_connected = True
            
            print(f" Fast-MCP: Connected to {url} with {len(self.tools)} tools.")
            return True, "Connected successfully"

        except Exception as e:
            await self.disconnect()
            return False, f"Connection failed: {str(e)}"

    async def disconnect(self):
        """ Cleans up the session and streams. """
        if self._exit_stack:
            try:
                await self._exit_stack.aclose()
            except RuntimeError as e:
                if "generator didn't stop" in str(e):
                    print("ℹ MCP: SSE Generator closed with expected shutdown warning.")
                else:
                    print(f" MCP Disconnect Warning: {str(e)}")
            except Exception as e:
                # Catching any other cleanup errors
                print(f" MCP Disconnect Error: {str(e)}")
        
        self.tools = []
        self.is_connected = False
        self.connected_url = None
        self._session = None
        self._exit_stack = None
        return True, "Disconnected"

mcp_manager = MCPToolManager()