import sys
import os
import streamlit as st

# Ensure server path is available
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'server')))

from modules.search import RAGSearch

st.set_page_config(
    page_title="RAG Document Chatbot",
    page_icon="🤖",
    layout="wide"
)

# Custom premium styling via CSS markdown
st.markdown("""
<style>
    .reportview-container {
        background: #0f1116;
    }
    h1 {
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
        background: linear-gradient(45deg, #FF4B4B, #FF8F8F);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .source-card {
        border-left: 3px solid #FF4B4B;
        padding-left: 10px;
        margin-bottom: 10px;
        background-color: #1a1c24;
        border-radius: 4px;
        padding: 8px;
    }
    .source-title {
        font-weight: bold;
        color: #FF8F8F;
        font-size: 0.9em;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = []

# Instantiate search engine (cached in session state so it doesn't reload on every interaction)
if "rag" not in st.session_state:
    with st.spinner("Initializing RAG Search Engine (loading PyTorch, sentence-transformers, and FAISS)..."):
        try:
            st.session_state.rag = RAGSearch()
        except Exception as e:
            st.error(f"Error initializing RAG search engine: {e}")
            st.stop()

rag = st.session_state.rag

# Sidebar
with st.sidebar:
    st.title("📂 Document Center")
    st.write("Manage the documents that feed the chatbot's knowledge base.")
    
    # Check indexed files
    indexed_sources = sorted(list(rag.vectorstore.get_indexed_sources()))
    
    st.subheader(f"Indexed Documents ({len(indexed_sources)})")
    if indexed_sources:
        for idx, src in enumerate(indexed_sources):
            # Show filename
            filename = os.path.basename(src)
            st.markdown(f"**{idx + 1}.** `{filename}`")
    else:
        st.info("No documents are currently indexed.")
        
    st.markdown("---")
    
    st.subheader("Upload Documents")
    uploaded_files = st.file_uploader(
        "Upload PDF or TXT files", 
        type=["pdf", "txt"], 
        accept_multiple_files=True
    )
    
    if uploaded_files:
        uploaded_count = 0
        for uploaded_file in uploaded_files:
            ext = os.path.splitext(uploaded_file.name)[1].lower()
            if ext == ".pdf":
                target_dir = os.path.join("data", "pdf_files")
            else:
                target_dir = os.path.join("data", "text_files")
                
            os.makedirs(target_dir, exist_ok=True)
            target_path = os.path.join(target_dir, uploaded_file.name)
            
            if not os.path.exists(target_path):
                try:
                    with open(target_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    uploaded_count += 1
                except Exception as e:
                    st.error(f"Error saving {uploaded_file.name}: {e}")
                    
        if uploaded_count > 0:
            with st.spinner("Indexing newly uploaded files..."):
                try:
                    st.session_state.rag = RAGSearch()
                    st.success(f"Successfully uploaded and indexed {uploaded_count} new file(s)!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to update database index: {e}")
        
    st.markdown("---")
    
    # Options to sync or force rebuild
    st.subheader("Actions")
    
    # Sync new documents (handled automatically by initialization, but button allows force re-scanning)
    if st.button("🔄 Check & Index New Files"):
        with st.spinner("Scanning data/ directory for updates..."):
            try:
                st.session_state.rag = RAGSearch()
                st.success("Successfully checked and updated the index!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to update index: {e}")
                
    if st.button("🗑️ Force Rebuild Index"):
        with st.spinner("Rebuilding index from scratch..."):
            try:
                # Remove index files on disk
                persist_dir = rag.vectorstore.persist_dir
                faiss_path = os.path.join(persist_dir, "faiss.index")
                meta_path = os.path.join(persist_dir, "metadata.pkl")
                if os.path.exists(faiss_path):
                    os.remove(faiss_path)
                if os.path.exists(meta_path):
                    os.remove(meta_path)
                    
                # Re-initialize search engine (which triggers full scan and rebuild)
                st.session_state.rag = RAGSearch()
                st.success("Index fully rebuilt successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to rebuild index: {e}")

# Main Chat View
st.title("🤖 RAG Document Assistant")
st.write("Ask questions and get answers directly compiled from your uploaded documents (PDFs & TXTs).")

# Display message history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        # If assistant message has source references, display them
        if msg["role"] == "assistant" and "sources" in msg and msg["sources"]:
            with st.expander("🔍 View References & Citations"):
                for src in msg["sources"]:
                    filename = os.path.basename(src['source'])
                    st.markdown(
                        f"<div class='source-card'>"
                        f"<div class='source-title'>📄 {filename}</div>"
                        f"<div style='font-size:0.85em; color:#d1d5db;'>{src['text']}</div>"
                        f"</div>", 
                        unsafe_allow_html=True
                    )

# Get new user input
if prompt := st.chat_input("Ask a question about your documents..."):
    # Display user question
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
        
    # Generate assistant answer
    with st.chat_message("assistant"):
        with st.spinner("Compiling answer from document context..."):
            try:
                answer, sources = rag.search_with_context(prompt)
            except Exception as e:
                answer = f"Error querying search engine: {e}"
                sources = []
                
            st.markdown(answer)
            
            # Show sources if any
            if sources:
                with st.expander("🔍 View References & Citations"):
                    for src in sources:
                        filename = os.path.basename(src['source'])
                        st.markdown(
                            f"<div class='source-card'>"
                            f"<div class='source-title'>📄 {filename}</div>"
                            f"<div style='font-size:0.85em; color:#d1d5db;'>{src['text']}</div>"
                            f"</div>", 
                            unsafe_allow_html=True
                        )
                        
            # Save message history
            st.session_state.messages.append({
                "role": "assistant",
                "content": answer,
                "sources": sources
            })
