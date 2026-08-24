import os
import streamlit as st
import requests

API_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000")

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
if "uploaded_file_cache" not in st.session_state:
    st.session_state.uploaded_file_cache = set()
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

# Verify backend health and fetch sources
try:
    health_check = requests.get(f"{API_URL}/")
    is_backend_online = health_check.status_code == 200
except Exception:
    is_backend_online = False

# Sidebar
with st.sidebar:
    st.title("📂 Document Center")
    st.write("Manage the documents that feed the chatbot's knowledge base.")
    
    if not is_backend_online:
        st.error("⚠️ Backend API Server is offline. Please make sure to run the backend first!")
        st.info("Launch backend with:\n`uvicorn server.main:app --reload`")
        indexed_sources = []
    else:
        # Check indexed files
        try:
            res = requests.get(f"{API_URL}/sources")
            if res.status_code == 200:
                indexed_sources = res.json().get("sources", [])
            else:
                st.error(f"Failed to fetch sources: {res.text}")
                indexed_sources = []
        except Exception as e:
            st.error(f"Error fetching sources: {e}")
            indexed_sources = []
    
    st.subheader("Upload Documents")
    uploaded_files = st.file_uploader(
        "Upload files", 
        type=["pdf", "txt", "csv", "docx", "md"], 
        accept_multiple_files=True,
        disabled=not is_backend_online,
        key=f"uploader_{st.session_state.uploader_key}"
    )

    st.markdown("---")

    st.subheader(f"Indexed Documents ({len(indexed_sources)})")
    if indexed_sources:
        for idx, src in enumerate(indexed_sources):
            filename = os.path.basename(src)
            st.markdown(f"**{idx + 1}.** `{filename}`")
    else:
        if is_backend_online:
            st.info("No documents are currently indexed.")
    
    if uploaded_files and is_backend_online:
        # Prevent upload loop by checking cache of already processed files in current run
        current_names = {f.name for f in uploaded_files}
        st.session_state.uploaded_file_cache = st.session_state.uploaded_file_cache & current_names
        new_files = current_names - st.session_state.uploaded_file_cache
        
        if new_files:
            files_to_upload = []
            for uploaded_file in uploaded_files:
                if uploaded_file.name in new_files:
                    files_to_upload.append(
                        ("files", (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type))
                    )
            
            if files_to_upload:
                with st.spinner("Uploading and indexing files in backend..."):
                    try:
                        res = requests.post(f"{API_URL}/upload", files=files_to_upload)
                        if res.status_code == 200:
                            st.session_state.uploader_key += 1
                            st.session_state.uploaded_file_cache = set()
                            st.success(res.json().get("message", "Files uploaded and indexed successfully!"))
                            st.rerun()
                        else:
                            st.error(f"Upload failed: {res.json().get('detail', res.text)}")
                    except Exception as e:
                        st.error(f"Failed to upload files: {e}")
    else:
        st.session_state.uploaded_file_cache = set()
        
    st.markdown("---")
    
    # Options to sync or force rebuild
    st.subheader("Actions")
    
    # Sync new documents (handled automatically by initialization, but button allows force re-scanning)
    if st.button("🔄 Check & Index New Files", disabled=not is_backend_online):
        with st.spinner("Scanning data/ directory on backend..."):
            try:
                res = requests.post(f"{API_URL}/sync")
                if res.status_code == 200:
                    st.success("Successfully synchronized and updated the index!")
                    st.rerun()
                else:
                    st.error(f"Sync failed: {res.json().get('detail', res.text)}")
            except Exception as e:
                st.error(f"Failed to update index: {e}")
                
    if st.button("🗑️ Force Rebuild Index", disabled=not is_backend_online):
        with st.spinner("Rebuilding index from scratch on backend..."):
            try:
                res = requests.post(f"{API_URL}/rebuild")
                if res.status_code == 200:
                    st.success("Index fully rebuilt successfully!")
                    st.rerun()
                else:
                    st.error(f"Rebuild failed: {res.json().get('detail', res.text)}")
            except Exception as e:
                st.error(f"Failed to rebuild index: {e}")

# Main Chat View
st.title("🤖 RAG Document Assistant")
st.write("Ask questions and get answers directly compiled from your uploaded documents.")

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
if prompt := st.chat_input("Ask a question about your documents...", disabled=not is_backend_online):
    # Display user question
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
        
    # Generate assistant answer
    with st.chat_message("assistant"):
        with st.spinner("Compiling answer from document context..."):
            try:
                res = requests.post(f"{API_URL}/query", json={"prompt": prompt, "top_k": 5})
                if res.status_code == 200:
                    data = res.json()
                    answer = data.get("answer", "")
                    sources = data.get("sources", [])
                else:
                    answer = f"Backend returned error ({res.status_code}): {res.json().get('detail', res.text)}"
                    sources = []
            except Exception as e:
                answer = f"Error querying backend API: {e}"
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
