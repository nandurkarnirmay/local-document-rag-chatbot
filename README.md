# 🤖 RAG Document Assistant Chatbot

An interactive, high-performance Retrieval-Augmented Generation (RAG) chatbot designed to parse, index, and answer questions from your local PDF and TXT documents. 

Built using a decoupled client-server architecture with a **FastAPI** backend, a **Streamlit** frontend interface, and orchestrated via **LangChain**, **FAISS**, **SentenceTransformers**, and **Groq (Llama 3)**.

---

## ✨ Key Features

- **🔌 Decoupled Client-Server Architecture:** Built with a FastAPI backend API and a Streamlit frontend client. The backend can be run, tested, and integrated with any third-party client.
- **📂 Real-Time Document Center:** Drag-and-drop file uploader to dynamically save, structure, and index your PDF, TXT, CSV, DOCX, or MD files.
- **⚡ Auto-Incremental Indexing:** Automatically scans your data folder on startup and indexes *only* new or updated files in seconds. Launching with an existing index is instant (under 0.5s).
- **💬 Conversational Chat Interface:** A clean, ChatGPT-like chat log that maintains conversation history and checks server health status.
- **🔍 References & Citations:** Each answer features a collapsible panel displaying the exact text passages and source files retrieved from the vector store.
- **🧼 Math Notation Sanitization:** Custom Unicode normalization to cleanly translate complex mathematical symbols and remove PDF font extraction corruption.
- **🔐 Secure Credentials:** Environment variable configuration to keep API keys private.

---

## 🛠️ Tech Stack

- **Frontend:** Streamlit
- **LLM Engine:** Groq API (`llama-3.1-8b-instant`)
- **Orchestration:** LangChain & LangChain Groq
- **Vector Index:** FAISS (Local CPU-based vector store)
- **Embeddings Model:** SentenceTransformers (`all-MiniLM-L6-v2`)
- **Loaders:** PyPDFLoader, TextLoader

---

## 📂 Project Structure

```text
├── client/
│   └── app.py                # Streamlit Frontend UI (Communicates with Backend API)
├── server/
│   ├── main.py               # FastAPI Backend API Server
│   └── modules/
│       ├── data_loader.py    # Document load, extraction & sanitization
│       ├── embedding.py      # Embedding manager class
│       ├── search.py         # RAG pipeline implementation & LLM call
│       ├── text_splitter.py  # Text chunking logic
│       └── vectorstore.py    # FAISS local storage operations
├── data/                     # Source documents directory (PDF/TXT)
├── faiss_store/              # Saved local FAISS index (Created on startup)
├── .env                      # API Configuration file (Ignored by git)
├── pyproject.toml            # Project dependencies & tool configurations
└── requirements.txt          # Python dependencies
```

---

## 🚀 Quick Start

### 1. Prerequisites
Ensure you have Python 3.10+ installed.

### 2. Clone the Repository
```bash
git clone https://github.com/your-username/rag-chatbot-langchain-faiss.git
cd rag-chatbot-langchain-faiss
```

### 3. Setup Virtual Environment & Install Dependencies
We recommend using [uv](https://github.com/astral-sh/uv) or pip:

**Using uv:**
```bash
uv sync
```

**Using standard pip:**
```bash
python -m venv .venv
# On Windows
.venv\Scripts\activate
# On macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the root directory:
```env
GROQ_API_KEY=your_groq_api_key_here
```
*(You can get a free, high-speed API key from the [Groq Console](https://console.groq.com/))*

### 5. Launch the Chatbot

Since the application is split into a backend API server and a frontend client, you need to run both:

**Step A: Run the Backend API Server (FastAPI):**
```bash
.venv\Scripts\uvicorn server.main:app --reload --host 127.0.0.1 --port 8000
```
This runs the FastAPI server at `http://127.0.0.1:8000` and automatically handles loading/scanning documents and processing RAG queries. You can access the API interactive Swagger documentation at `http://127.0.0.1:8000/docs`.

**Step B: Run the Web Interface (Streamlit):**
In a new terminal window:
```bash
.venv\Scripts\streamlit run client/app.py
```
This will open your default browser to `http://localhost:8501`.

---

## 📝 License
This project is open-source and available under the MIT License.
