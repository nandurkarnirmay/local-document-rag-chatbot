import os
import sys
import shutil
from typing import List
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Ensure server directory is in sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.search import RAGSearch

# Reconfigure standard output to use UTF-8 to prevent UnicodeEncodeError on Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

app = FastAPI(
    title="RAG Chatbot API Server",
    description="A FastAPI backend hosting the FAISS vector store and LangChain RAG pipeline",
    version="1.0.0"
)

# Enable CORS for frontend API calls
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global RAG Search Instance
rag_search = None

def get_rag_search(force_reload: bool = False):
    global rag_search
    if rag_search is None or force_reload:
        print("[INFO] Initializing/Reloading RAG Search Engine...")
        rag_search = RAGSearch()
    return rag_search

# Initialize at startup
@app.on_event("startup")
async def startup_event():
    get_rag_search()

class QueryRequest(BaseModel):
    prompt: str
    top_k: int = 5

@app.get("/")
def read_root():
    return {
        "status": "healthy",
        "service": "RAG Chatbot API Server",
        "version": "1.0.0"
    }

@app.get("/sources")
def get_sources():
    try:
        rag = get_rag_search()
        sources = list(rag.vectorstore.get_indexed_sources())
        return {"sources": sorted(sources)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch indexed sources: {str(e)}")

@app.post("/query")
def query_rag(request: QueryRequest):
    if not request.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty.")
    try:
        rag = get_rag_search()
        answer, sources = rag.search_with_context(request.prompt, top_k=request.top_k)
        return {"answer": answer, "sources": sources}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing RAG query: {str(e)}")

@app.post("/upload")
async def upload_documents(files: List[UploadFile] = File(...)):
    uploaded_count = 0
    saved_paths = []
    
    for file in files:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext == ".pdf":
            target_dir = os.path.join("data", "pdf_files")
        elif ext == ".txt":
            target_dir = os.path.join("data", "text_files")
        elif ext == ".csv":
            target_dir = os.path.join("data", "csv_files")
        elif ext == ".docx":
            target_dir = os.path.join("data", "docx_files")
        elif ext == ".md":
            target_dir = os.path.join("data", "md_files")
        else:
            target_dir = os.path.join("data", "other_files")
            
        os.makedirs(target_dir, exist_ok=True)
        target_path = os.path.join(target_dir, file.filename)
        
        try:
            with open(target_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            uploaded_count += 1
            saved_paths.append(target_path)
        except Exception as e:
            print(f"[ERROR] Failed to save uploaded file {file.filename}: {e}")
            
    if uploaded_count > 0:
        try:
            # Trigger re-indexing
            get_rag_search(force_reload=True)
            return {
                "message": f"Successfully uploaded and indexed {uploaded_count} file(s).",
                "saved_paths": saved_paths
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Files saved but indexing failed: {str(e)}")
            
    raise HTTPException(status_code=400, detail="No files were successfully uploaded.")

@app.post("/sync")
def sync_documents():
    try:
        get_rag_search(force_reload=True)
        rag = get_rag_search()
        sources = list(rag.vectorstore.get_indexed_sources())
        return {
            "message": "Re-scanned and synchronized index successfully.",
            "sources": sorted(sources)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to synchronize documents: {str(e)}")

@app.post("/rebuild")
def rebuild_index():
    try:
        rag = get_rag_search()
        persist_dir = rag.vectorstore.persist_dir
        
        faiss_path = os.path.join(persist_dir, "faiss.index")
        meta_path = os.path.join(persist_dir, "metadata.pkl")
        
        if os.path.exists(faiss_path):
            os.remove(faiss_path)
        if os.path.exists(meta_path):
            os.remove(meta_path)
            
        # Re-initialize
        get_rag_search(force_reload=True)
        
        return {"message": "Index fully rebuilt from scratch successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to rebuild vector store: {str(e)}")
