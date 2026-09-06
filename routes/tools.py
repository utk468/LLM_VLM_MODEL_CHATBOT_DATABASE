from fastapi import APIRouter, UploadFile, File, Form
from typing import List
import os
import tempfile
import shutil
from langgraph_backend import tools as static_tools

tools_router = APIRouter()

@tools_router.get("/api/tools/static")

async def get_static_tools():
    return {
        "tools": [t.name for t in static_tools]
    }

