import os
from dotenv import load_dotenv
from modules.vectorstore import FaissVectorStore
from langchain_groq import ChatGroq

load_dotenv()

class RAGSearch:
    def __init__(self, persist_dir: str = "faiss_store", embedding_model: str = "all-MiniLM-L6-v2", llm_model: str = "llama-3.1-8b-instant"):
        self.vectorstore = FaissVectorStore(persist_dir, embedding_model)
        # Load or build vectorstore
        faiss_path = os.path.join(persist_dir, "faiss.index")
        meta_path = os.path.join(persist_dir, "metadata.pkl")
        
        # Load existing index if it exists
        if os.path.exists(faiss_path) and os.path.exists(meta_path):
            self.vectorstore.load()
            
        # Scan data directory for documents (skipping CSV files)
        from modules.data_loader import load_document
        from pathlib import Path
        
        data_path = Path("data").resolve()
        disk_files = list(data_path.glob("**/*.pdf")) + list(data_path.glob("**/*.txt"))
        indexed_sources = self.vectorstore.get_indexed_sources()
        
        new_files = []
        for f in disk_files:
            rel = os.path.relpath(f, start=os.getcwd()).replace("\\", "/")
            if rel not in indexed_sources:
                new_files.append((f, rel))
                
        # Auto-index new files incrementally
        if new_files:
            print(f"[INFO] Found {len(new_files)} new/unindexed file(s). Indexing incrementally...")
            docs = []
            for abs_path, rel_path in new_files:
                print(f"  -> Loading: {rel_path}")
                docs.extend(load_document(abs_path))
            
            if docs:
                if self.vectorstore.index is None:
                    self.vectorstore.build_from_documents(docs)
                else:
                    self.vectorstore.add_documents(docs)
            print("[INFO] Vector store is up to date.")
        else:
            if self.vectorstore.index is None:
                print("[WARNING] Vector store index is empty and no documents found on disk.")
            else:
                print("[INFO] Vector store is already up to date with disk files.")
                
        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            raise ValueError("GROQ_API_KEY environment variable is not set. Please define it in your .env file.")
        self.llm = ChatGroq(groq_api_key=groq_api_key, model_name=llm_model)
        print(f"[INFO] Groq LLM initialized: {llm_model}")

    def search_and_summarize(self, query: str, top_k: int = 5) -> str:
        results = self.vectorstore.query(query, top_k=top_k)
        texts = [r["metadata"].get("text", "") for r in results if r["metadata"]]
        context = "\n\n".join(texts)
        if not context:
            return "No relevant documents found."
        prompt = f"""Summarize the following context for the query: '{query}'\n\nContext:\n{context}\n\nSummary:"""
        response = self.llm.invoke([prompt])
        return response.content

    def search_with_context(self, query: str, top_k: int = 5) -> tuple:
        results = self.vectorstore.query(query, top_k=top_k)
        texts = []
        sources = []
        for r in results:
            if r["metadata"]:
                text = r["metadata"].get("text", "")
                src = r["metadata"].get("source", "Unknown source")
                texts.append(text)
                sources.append({"text": text, "source": src})
        
        context = "\n\n".join(texts)
        if not context:
            return "No relevant documents found.", []
            
        prompt = f"""Summarize the following context for the query: '{query}'\n\nContext:\n{context}\n\nSummary:"""
        response = self.llm.invoke([prompt])
        return response.content, sources

