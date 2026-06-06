from langchain_community.document_loaders import PyPDFLoader, TextLoader, CSVLoader
from pathlib import Path
from typing import List, Any
import unicodedata

def clean_text(text: str) -> str:
    text = unicodedata.normalize('NFKD', text)
    cleaned = []
    for c in text:
        cp = ord(c)
        # Keep standard ASCII, Greek letters, math operators, and degree symbol
        if cp < 128 or (0x0370 <= cp <= 0x03FF) or (0x2200 <= cp <= 0x22FF) or cp == 0x00B0:
            cleaned.append(c)
    return "".join(cleaned)

def load_all_documents(data_dir : str) -> List[Any]:
    data_path = Path(data_dir).resolve()
    print(f"[DEBUG] Loading documents from {data_path}")
    documents = []

    if not data_path.exists():
        print("[ERROR] Data directory not found.")
        return []

    #PDF Files
    pdf_files = list(data_path.glob("**/*.pdf"))
    print(f"[DEBUG] Found {len(pdf_files)} PDF files")
    for pdf_file in pdf_files:
        print(f"[DEBUG] Loading PDF file : {pdf_file}")
        try:
            loader = PyPDFLoader(str(pdf_file))
            loaded = loader.load()
            for doc in loaded:
                doc.page_content = clean_text(doc.page_content)
            documents.extend(loaded)
        except Exception as e:
            print(f"[ERROR] Error loading PDF {pdf_file}: {e}")

    #TXT Files
    txt_files = list(data_path.glob("**/*.txt"))
    print(f"[DEBUG] Found {len(txt_files)} TXT files.")
    for txt_file in txt_files:
        print(f"[DEBUG] Loading TXT file : {txt_file}")
        try:
            loader = TextLoader(str(txt_file), encoding='utf-8')
            loaded = loader.load()
            for doc in loaded:
                doc.page_content = clean_text(doc.page_content)
            documents.extend(loaded)
        except Exception as e:
            print(f"[ERROR] Error loading TXT file {txt_file}: {e}")

    #CSV Files
    csv_files = list(data_path.glob("**/*.csv"))
    print(f"[DEBUG] Found {len(csv_files)} CSV files.")
    for csv_file in csv_files:
        print(f"[DEBUG] Loading CSV file : {csv_file}")
        try:
            loader = CSVLoader(str(csv_file))
            loaded = loader.load()
            for doc in loaded:
                doc.page_content = clean_text(doc.page_content)
            documents.extend(loaded)
        except Exception as e:
            print(f"[ERROR] Error loading CSV file {csv_file}: {e}")

    return documents


def load_document(file_path: Path) -> List[Any]:
    file_path = Path(file_path).resolve()
    if not file_path.exists():
        print(f"[ERROR] File not found: {file_path}")
        return []

    ext = file_path.suffix.lower()
    try:
        loaded = []
        if ext == ".pdf":
            loader = PyPDFLoader(str(file_path))
            loaded = loader.load()
        elif ext == ".txt":
            loader = TextLoader(str(file_path), encoding='utf-8')
            loaded = loader.load()
        elif ext == ".csv":
            loader = CSVLoader(str(file_path))
            loaded = loader.load()
        else:
            print(f"[WARNING] Unsupported file type: {ext}")
            return []

        for doc in loaded:
            doc.page_content = clean_text(doc.page_content)
        return loaded
    except Exception as e:
        print(f"[ERROR] Error loading file {file_path}: {e}")
    return []


    