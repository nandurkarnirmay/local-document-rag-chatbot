import os
import sys
import pickle
from typing import List, Any
import faiss
import numpy as np

from modules.embedding import EmbeddingManager
from modules.text_splitter import split_documents

class FaissVectorStore:
    def __init__(self, persist_dir: str = "faiss_store", embedding_model: str = "all-MiniLM-L6-v2", chunk_size: int = 1000, chunk_overlap: int = 200):
        self.persist_dir = persist_dir
        os.makedirs(self.persist_dir, exist_ok=True)
        self.index = None
        self.metadata = []
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.embedding_model = embedding_model
        self.embedding_manager = EmbeddingManager(model_name=embedding_model)
        

    def build_from_documents(self, documents: List[Any]):
        chunks = split_documents(documents=documents, chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap)
        texts = [chunk.page_content for chunk in chunks]
        embeddings = self.embedding_manager.generate_embeddings(texts)
        metadatas = []
        for chunk in chunks:
            source = chunk.metadata.get("source", "")
            if source:
                try:
                    source = os.path.relpath(source, start=os.getcwd())
                    source = source.replace("\\", "/") # Normalize separators
                except Exception:
                    pass
            metadatas.append({"text": chunk.page_content, "source": source})
        self.add_embeddings(np.array(embeddings).astype('float32'), metadatas)
        self.save()
        print(f"[INFO] Vector Store built and saved to {self.persist_dir}")

    def add_documents(self, documents: List[Any]):
        if not documents:
            print("[INFO] No new documents to add.")
            return
        chunks = split_documents(documents=documents, chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap)
        texts = [chunk.page_content for chunk in chunks]
        embeddings = self.embedding_manager.generate_embeddings(texts)
        metadatas = []
        for chunk in chunks:
            source = chunk.metadata.get("source", "")
            if source:
                try:
                    source = os.path.relpath(source, start=os.getcwd())
                    source = source.replace("\\", "/") # Normalize separators
                except Exception:
                    pass
            metadatas.append({"text": chunk.page_content, "source": source})
        self.add_embeddings(np.array(embeddings).astype('float32'), metadatas)
        self.save()

    def get_indexed_sources(self) -> set:
        if not self.metadata:
            return set()
        sources = set()
        for meta in self.metadata:
            if meta and "source" in meta and meta["source"]:
                sources.add(meta["source"])
        return sources

    def add_embeddings(self, embeddings : np.ndarray, metadatas : List[dict]):
        dim = embeddings.shape[1]
        if self.index is None:
            self.index = faiss.IndexFlatL2(dim)
        self.index.add(embeddings)
        if metadatas:
            self.metadata.extend(metadatas)
        print(f"[INFO] Added {embeddings.shape[0]} vectors to Faiss index.")

    def save(self):
        faiss_path = os.path.join(self.persist_dir, "faiss.index")
        meta_path = os.path.join(self.persist_dir, "metadata.pkl")
        faiss.write_index(self.index, faiss_path)
        with open(meta_path, "wb") as f:
            pickle.dump(self.metadata, f)
        print(f"[INFO] Saved Faiss index and metadata to {self.persist_dir}")
        
    def load(self):
        faiss_path = os.path.join(self.persist_dir, "faiss.index")
        meta_path = os.path.join(self.persist_dir, "metadata.pkl")
        self.index = faiss.read_index(faiss_path)
        with open(meta_path, "rb") as f:
            self.metadata = pickle.load(f)
        print(f"[INFO] Loaded Faiss index and metadata from {self.persist_dir}")
        
    def search(self, query_embedding: np.ndarray, top_k: int = 5):
        D, I = self.index.search(query_embedding, top_k)
        results = []
        for idx, dist in zip(I[0], D[0]):
            meta = self.metadata[idx] if 0 <= idx < len(self.metadata) else None
            results.append({"index": idx, "distance": dist, "metadata": meta})
        return results

    def query(self, query_text: str, top_k: int = 5):
        print(f"[INFO] Querying vector store for: '{query_text}'")
        query_emb = self.embedding_manager.generate_embeddings([query_text]).astype('float32')
        return self.search(query_emb, top_k=top_k)


        