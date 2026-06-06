from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List, Any

def split_documents(documents : List[Any], chunk_size : int = 1000, chunk_overlap : int = 200) -> List[Any]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size = chunk_size,
        chunk_overlap = chunk_overlap,
        length_function = len,
        separators = ["\n\n", "\n", ".", ""]
    )

    chunks = splitter.split_documents(documents)
    print(f"[INFO] Split {len(chunks)} chunks from {len(documents)} documents.")

    return chunks