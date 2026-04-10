from fastapi import APIRouter, UploadFile, File, Form
from typing import List
import os
import tempfile
import shutil
from langgraph_backend import ingest_document, tools as static_tools


tools_router = APIRouter()

#file upload endpoint
#here user upload the file and the file is ingested into the database
#post request to upload the file
@tools_router.post("/api/upload")
#here we are using async and await because ingest_document is async
#using UploadFile function from fastapi to upload the file
async def upload(file: UploadFile = File(...)):
    #checking if the file is uploaded
    if not file:
        return {"success": False, "error": "No file"}

    #getting the suffix of the file
    #that is file extension
    suffix = "." + file.filename.split('.')[-1]
    
    #creating a temporary file and copy the uploaded content into temporary file
    #becuase UploadFile is file stream(flow of file data in bytes) not file path
    #and our ingest_document function is taking file path as argument
    #thats why we required file path
    #here we are using tempfile module to create a temporary file
    #and shutil module to copy the uploaded content into temporary file
    #so this is the way to get file path from UploadFile
    #we are finally getting path of the uploaded file and storing it in tmp_path
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        #copying the uploaded content into temporary file using shutil.copyfileobj
        #this is the way to copy the uploaded content into temporary file
        shutil.copyfileobj(file.file, tmp)
        #getting the path of the temporary file using .name attribute
        tmp_path = tmp.name

    #calling the ingest_document function to ingest the file
    try:
        #Read file
        #Split into chunks
        #Create embeddings
        #Store in FAISS vector DB
        success = ingest_document(tmp_path)
 
    #finally block is used to remove the temporary file
    #to prevent storage leaks and also system cleanup
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    #returning the success status to the frontend
    return {"success": success}




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