import sys
from modules.data_loader import load_all_documents
from modules.vectorstore import FaissVectorStore
from modules.search import RAGSearch

# Reconfigure standard output to use UTF-8 to prevent UnicodeEncodeError on Windows
#for non UTF-8 outputs like ∅, ɑ, etc
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def main():
    print("Hello from rag-chatbot!")


if __name__ == "__main__":
    main()
    load_all_documents("data")
    faiss_vector_store = FaissVectorStore("faiss_store")
    rag_search = RAGSearch()
    query = rag_search.search_and_summarize("What are the advantages of a Electron microscope over a optical microscope?")
    print(query)
    

