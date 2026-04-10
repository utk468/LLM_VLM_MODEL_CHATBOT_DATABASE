from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import InMemoryVectorStore
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.tools import tool

embedding = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vector_store = InMemoryVectorStore(embedding=embedding)

def clear_document():
    """
    Clears the current vector database.
    Useful when uploading a new document.
    """
    global vector_store
    vector_store = InMemoryVectorStore(embedding=embedding)

def is_document_ingested() -> bool:
    """
    Checks if any document is currently stored.
    """
    global vector_store
    if hasattr(vector_store, 'store'):
        return len(vector_store.store) > 0
    return False

def ingest_document(file_path: str) -> bool:
    """
    Loads a PDF or text file and stores it in vector DB.
    """
    global vector_store

    if file_path.lower().endswith(".pdf"):
        loader = PyPDFLoader(file_path)
    else:
        loader = TextLoader(file_path, encoding="utf-8")

    docs = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )

    splits = splitter.split_documents(docs)

    if not splits:
        print(" No text extracted from document!")
        return False

    # Reset vector store on new ingestion
    vector_store = InMemoryVectorStore(embedding=embedding)
    vector_store.add_documents(splits)

    print(" Document ingested successfully!")
    return True

@tool
def query_uploaded_document(query: str) -> str:
    """Search and query the content of the currently uploaded/ingested documents."""
    global vector_store
    
    try:
        results = vector_store.similarity_search(query, k=3)
        if not results:
            return "No document found or no relevant info."
        
        context = "\n\n".join([doc.page_content for doc in results])
        return f"From document:\n{context}"
    except Exception:
        # Handling for cases where the vector store is not initialized or search fails
        return "No document uploaded yet."
