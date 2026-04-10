from fastapi import APIRouter, UploadFile, File, Form
from typing import List
import os
import tempfile
import shutil
from langgraph_backend import tools as static_tools


tools_router = APIRouter()




#endpoint to get the static tools
#get request to get the static tools
@tools_router.get("/api/tools/static")
#from langgraph_backend we are importing static tools
#static tools are the tools that are not from the MCP server
async def get_static_tools():
    return {
        "tools": [t.name for t in static_tools]
    }
#here we are extracting tools name from the static tools