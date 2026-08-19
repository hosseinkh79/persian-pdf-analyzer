
"""
PDF Analyzer - Streamlit Frontend

A beautiful UI for uploading and analyzing PDFs using AI.
Connects to FastAPI backend with proper error handling and state management.
"""

import streamlit as st
import requests
import json
import os
import time
from datetime import datetime
from typing import Optional, Dict, Any
import pandas as pd
from typing import List

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="PDF Analyzer Pro",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# CUSTOM CSS FOR BEAUTIFUL UI
# ============================================================

st.markdown("""
<style>
    /* Main container styling */
    .main {
        padding: 0rem 1rem;
    }
    
    /* Card styling */
    .card {
        background: white;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
    }
    
    /* Status badges */
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .status-uploaded {
        background: #E3F2FD;
        color: #1565C0;
    }
    
    .status-processing {
        background: #FFF3E0;
        color: #E65100;
    }
    
    .status-done {
        background: #E8F5E9;
        color: #2E7D32;
    }
    
    .status-error {
        background: #FFEBEE;
        color: #C62828;
    }
    
    /* Metric cards */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        border-left: 4px solid #4CAF50;
        text-align: center;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #1a1a1a;
    }
    
    .metric-label {
        font-size: 0.85rem;
        color: #666;
        margin-top: 0.25rem;
    }
    
    /* Document cards */
    .doc-card {
        background: white;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
        margin-bottom: 0.5rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        transition: all 0.2s ease;
    }
    
    .doc-card:hover {
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.12);
        transform: translateY(-2px);
    }
    
    /* Upload area */
    .upload-area {
        border: 2px dashed #ccc;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        background: #fafafa;
        transition: all 0.3s ease;
    }
    
    .upload-area:hover {
        border-color: #4CAF50;
        background: #f1f8e9;
    }
    
    /* Progress bar styling */
    .stProgress > div > div {
        background-color: #4CAF50;
    }
    
    /* Button styling */
    .stButton > button {
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        font-weight: 500;
        color: #1a1a1a;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# CONFIGURATION
# ============================================================

# Get backend URL from environment
BACKEND_URL = os.getenv("BACKEND_API_URL", "http://localhost:8003")
API_BASE = BACKEND_URL

# Session state initialization
if 'documents' not in st.session_state:
    st.session_state.documents = []
if 'selected_doc' not in st.session_state:
    st.session_state.selected_doc = None
if 'processing' not in st.session_state:
    st.session_state.processing = False
if 'refresh' not in st.session_state:
    st.session_state.refresh = False

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def check_backend_health() -> bool:
    """Check if backend API is available."""
    try:
        response = requests.get(f"{API_BASE}/health_ui", timeout=3)
        return response.status_code == 200
    except:
        return False

def upload_pdf(file) -> Optional[Dict[str, Any]]:
    """Upload a PDF to the backend."""
    try:
        files = {"file": (file.name, file, "application/pdf")}
        response = requests.post(
            f"{API_BASE}/documents/upload",
            files=files,
            timeout=30
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Upload failed: {response.status_code} - {response.text}")
            return None
    except requests.exceptions.Timeout:
        st.error("Upload timed out. Please try again.")
        return None
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to backend. Please check if the API is running.")
        return None
    except Exception as e:
        st.error(f"Upload error: {str(e)}")
        return None

def analyze_document(document_id: str) -> Optional[Dict[str, Any]]:
    """Trigger analysis on a document."""
    try:
        response = requests.post(
            f"{API_BASE}/documents/{document_id}/analyze",
            timeout=60
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Analysis failed: {response.status_code} - {response.text}")
            return None
    except requests.exceptions.Timeout:
        st.error("Analysis timed out. The LLM might be taking too long.")
        return None
    except Exception as e:
        st.error(f"Analysis error: {str(e)}")
        return None

def get_documents() -> Optional[List[Dict[str, Any]]]:
    """Get all documents from the backend."""
    try:
        response = requests.get(f"{API_BASE}/documents/", timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Failed to fetch documents: {str(e)}")
        return None

def get_document_detail(doc_id: str) -> Optional[Dict[str, Any]]:
    """Get detailed information about a specific document."""
    try:
        response = requests.get(f"{API_BASE}/documents/{doc_id}", timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Failed to fetch document details: {str(e)}")
        return None

def delete_document(doc_id: str) -> bool:
    """Delete a document."""
    try:
        response = requests.delete(f"{API_BASE}/documents/{doc_id}", timeout=10)
        return response.status_code == 200
    except Exception as e:
        st.error(f"Failed to delete document: {str(e)}")
        return False

def get_status_color(status: str) -> str:
    """Get color for status badge."""
    colors = {
        "uploaded": "status-uploaded",
        "processing": "status-processing",
        "done": "status-done",
        "error": "status-error"
    }
    return colors.get(status, "status-uploaded")

def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} GB"

# ============================================================
# SIDEBAR - Navigation & Status
# ============================================================

with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/000000/pdf.png", width=80)
    st.title("📄 PDF Analyzer")
    st.caption("v1.0.0")
    
    st.markdown("---")
    
    # Backend connection status
    st.subheader("🔌 Status")
    if check_backend_health():
        st.success("✅ Backend Connected")
        st.caption(f"API: {API_BASE}")
    else:
        st.error("❌ Backend Offline")
        st.caption("Please start the FastAPI server")
    
    st.markdown("---")
    
    # Quick stats
    st.subheader("📊 Quick Stats")
    if st.session_state.documents:
        total = len(st.session_state.documents)
        done = sum(1 for d in st.session_state.documents if d.get('status') == 'done')
        processing = sum(1 for d in st.session_state.documents if d.get('status') == 'processing')
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total", total)
        with col2:
            st.metric("✅ Done", done)
        
        if processing > 0:
            st.warning(f"⏳ {processing} processing...")
    
    st.markdown("---")
    
    # About
    with st.expander("ℹ️ About"):
        st.markdown("""
        **PDF Analyzer Pro** uses AI to extract structured information from PDF documents.
        
        **Features:**
        - 📤 Upload PDFs
        - 🤖 AI-powered extraction
        - 📊 View results
        - 📥 Export data
        - 🗑️ Manage documents
        
        **Tech Stack:**
        - Frontend: Streamlit
        - Backend: FastAPI
        - Database: PostgreSQL
        - AI: LLM API
        """)

# ============================================================
# MAIN CONTENT AREA
# ============================================================

st.title("📄 PDF Analyzer Pro")
st.markdown("Upload PDF documents and extract structured information using AI")

# Check backend connection
if not check_backend_health():
    st.error("⚠️ Cannot connect to the backend API. Please ensure the FastAPI server is running.")
    st.stop()

# ============================================================
# REFRESH DOCUMENTS
# ============================================================

# Auto-refresh documents
if st.session_state.refresh or not st.session_state.documents:
    docs = get_documents()
    if docs is not None:
        st.session_state.documents = docs
        st.session_state.refresh = False

# ============================================================
# TAB 1: UPLOAD & ANALYZE
# ============================================================

tab1, tab2, tab3 = st.tabs([
    "📤 Upload & Analyze",
    "📋 Documents",
    "📊 Analytics"
])

with tab1:
    st.markdown("### Upload a PDF for Analysis")
    
    col1, col2 = st.columns([3, 2])
    
    with col1:
        # Upload area
        uploaded_file = st.file_uploader(
            "Choose a PDF file",
            type=['pdf'],
            help="Upload a PDF file to analyze (max 100MB)",
            key="file_uploader"
        )
        
        if uploaded_file:
            file_size = format_file_size(uploaded_file.size)
            st.success(f"✅ **{uploaded_file.name}** ({file_size})")
            
            # File details
            with st.expander("📄 File Details"):
                st.markdown(f"""
                - **Filename:** {uploaded_file.name}
                - **Size:** {file_size}
                - **Type:** application/pdf
                - **Uploaded:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                """)
            
            # Analyze button
            if st.button("🔍 Analyze PDF", type="primary", use_container_width=True, disabled=st.session_state.processing):
                st.session_state.processing = True
                
                # Step 1: Upload
                with st.status("📤 Uploading PDF...", expanded=True) as status:
                    upload_result = upload_pdf(uploaded_file)
                    
                    if upload_result:
                        doc_id = upload_result['id']
                        status.write(f"✅ Uploaded successfully! Document ID: `{doc_id[:8]}...`")
                        
                        # Step 2: Analyze
                        status.write("🤖 Starting AI analysis...")
                        analysis_result = analyze_document(doc_id)
                        
                        if analysis_result:
                            status.write("✅ Analysis complete!")
                            status.update(label="✅ Analysis Complete!", state="complete")
                            
                            # Show results
                            st.balloons()
                            st.success("🎉 Analysis complete! View the results below.")
                            
                            # Store result
                            st.session_state.selected_doc = analysis_result
                            
                            # Refresh document list
                            st.session_state.refresh = True
                        else:
                            status.update(label="❌ Analysis Failed", state="error")
                    else:
                        status.update(label="❌ Upload Failed", state="error")
                
                st.session_state.processing = False
                st.rerun()
    
    with col2:
        # Quick stats card
        st.markdown("### 📊 Quick Stats")
        
        if st.session_state.documents:
            total = len(st.session_state.documents)
            done = sum(1 for d in st.session_state.documents if d.get('status') == 'done')
            processing = sum(1 for d in st.session_state.documents if d.get('status') == 'processing')
            error = sum(1 for d in st.session_state.documents if d.get('status') == 'error')
            
            st.metric("📄 Total Documents", total)
            
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric("✅ Analyzed", done, delta=None)
            with col_b:
                st.metric("⏳ Processing", processing)
            with col_c:
                st.metric("❌ Failed", error)
        else:
            st.info("No documents uploaded yet.")
    
    # ============================================================
    # DISPLAY RESULTS (if available)
    # ============================================================
    
    if st.session_state.selected_doc:
        st.markdown("---")
        st.markdown("### 📊 Analysis Results")
        
        result = st.session_state.selected_doc
        extracted = result.get('extracted_data', {})
        
        if extracted:
            # Display in a nice card
            st.markdown('<div class="card">', unsafe_allow_html=True)
            
            # Header with status
            status_color = get_status_color(result.get('status', 'uploaded'))
            st.markdown(f"""
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                <h3 style="margin: 0;">📄 {result.get('filename', 'Document')}</h3>
                <span class="status-badge {status_color}">{result.get('status', 'unknown')}</span>
            </div>
            """, unsafe_allow_html=True)
            
            # Key metrics in columns
            cols = st.columns(4)
            metrics = [
                ("📝 Title", extracted.get('title', 'N/A')),
                ("📄 Pages", extracted.get('pages', 'N/A')),
                ("🏷️ Keywords", len(extracted.get('keywords', []))),
                ("📅 Date", extracted.get('extracted_date', 'N/A'))
            ]
            
            for col, (label, value) in zip(cols, metrics):
                with col:
                    st.metric(label, value)
            
            # Summary
            st.markdown("---")
            st.markdown("#### 📝 Summary")
            st.write(extracted.get('summary', 'No summary available.'))
            
            # Keywords as tags
            keywords = extracted.get('keywords', [])
            if keywords:
                st.markdown("#### 🏷️ Keywords")
                keyword_html = " ".join([
                    f'<span style="'
                    f'background-color: #eef2ff; '
                    f'color: #3730a3; '
                    f'border: 1px solid #c7d2fe; '
                    f'padding: 0.35rem 0.85rem; '
                    f'border-radius: 20px; '
                    f'margin: 0.25rem; '
                    f'display: inline-block; '
                    f'font-size: 0.85rem; '
                    f'font-weight: 500;'
                    f'">{kw}</span>'
                    for kw in keywords[:10]
                ])
                st.markdown(keyword_html, unsafe_allow_html=True)
            
            # Full JSON expander
            with st.expander("🔍 View Full JSON Data"):
                st.json(extracted)
            
            # Export options
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Export as JSON
                json_str = json.dumps(extracted, indent=2, ensure_ascii=False)
                st.download_button(
                    label="📥 Download JSON",
                    data=json_str,
                    file_name=f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    use_container_width=True
                )
            
            with col2:
                # Export as CSV (if data is tabular)
                try:
                    df = pd.DataFrame([extracted])
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="📊 Download CSV",
                        data=csv,
                        file_name=f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                except:
                    pass
            
            with col3:
                # Clear results
                if st.button("🗑️ Clear Results", use_container_width=True):
                    st.session_state.selected_doc = None
                    st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("No data extracted from this document yet.")

# ============================================================
# TAB 2: DOCUMENTS LIST
# ============================================================

with tab2:
    st.markdown("### 📋 All Documents")
    
    if not st.session_state.documents:
        st.info("No documents uploaded yet. Go to the 'Upload & Analyze' tab to get started.")
    else:
        # Refresh button
        col1, col2 = st.columns([6, 1])
        with col2:
            if st.button("🔄 Refresh"):
                st.session_state.refresh = True
                st.rerun()
        
        # Search and filter
        search = st.text_input("🔍 Search documents", placeholder="Filter by filename...")
        
        # Filter documents
        docs = st.session_state.documents
        if search:
            docs = [d for d in docs if search.lower() in d.get('filename', '').lower()]
        
        # Display documents
        for doc in docs:
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([3, 1.5, 1.5, 1.5, 1])
                
                with col1:
                    st.markdown(f"**📄 {doc.get('filename', 'Unknown')}**")
                    st.caption(f"ID: `{doc['id'][:8]}...`")
                
                with col2:
                    status = doc.get('status', 'unknown')
                    status_color = get_status_color(status)
                    st.markdown(f'<span class="status-badge {status_color}">{status}</span>', unsafe_allow_html=True)
                
                with col3:
                    created = doc.get('created_at', '')
                    if created:
                        try:
                            dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
                            st.caption(dt.strftime('%Y-%m-%d %H:%M'))
                        except:
                            st.caption(created[:10])
                
                with col4:
                    if status == 'done':
                        if st.button("📊 View", key=f"view_{doc['id']}", use_container_width=True):
                            detail = get_document_detail(doc['id'])
                            if detail:
                                st.session_state.selected_doc = detail
                                st.rerun()
                    elif status == 'processing':
                        st.caption("⏳ Processing...")
                
                with col5:
                    if st.button("🗑️", key=f"delete_{doc['id']}", use_container_width=True):
                        if delete_document(doc['id']):
                            st.success(f"Deleted {doc['filename']}")
                            st.session_state.refresh = True
                            time.sleep(0.5)
                            st.rerun()
        
        # Pagination info
        st.caption(f"Showing {len(docs)} of {len(st.session_state.documents)} documents")

# ============================================================
# TAB 3: ANALYTICS
# ============================================================

with tab3:
    st.markdown("### 📊 Analytics Dashboard")
    
    if st.session_state.documents:
        docs = st.session_state.documents
        
        # Stats row
        col1, col2, col3, col4 = st.columns(4)
        
        total = len(docs)
        done = sum(1 for d in docs if d.get('status') == 'done')
        processing = sum(1 for d in docs if d.get('status') == 'processing')
        error = sum(1 for d in docs if d.get('status') == 'error')
        
        with col1:
            st.metric("📄 Total Documents", total)
        with col2:
            st.metric("✅ Completed", done, delta=f"{done/total*100:.0f}%" if total > 0 else "0%")
        with col3:
            st.metric("⏳ Processing", processing)
        with col4:
            st.metric("❌ Failed", error)
        
        st.markdown("---")
        
        # Status distribution
        st.markdown("#### 📊 Document Status Distribution")
        
        status_data = {
            "Uploaded": sum(1 for d in docs if d.get('status') == 'uploaded'),
            "Processing": processing,
            "Completed": done,
            "Failed": error
        }
        
        # Display as bars
        max_val = max(status_data.values()) if status_data.values() else 1
        for label, count in status_data.items():
            pct = (count / max_val * 100) if max_val > 0 else 0
            col1, col2 = st.columns([1, 4])
            with col1:
                st.write(f"**{label}**")
            with col2:
                st.progress(pct / 100)
                st.caption(f"{count} documents ({pct:.0f}%)")
        
        st.markdown("---")
        
        # Recent activity
        st.markdown("#### 🕐 Recent Activity")
        
        # Sort by created_at
        sorted_docs = sorted(docs, key=lambda x: x.get('created_at', ''), reverse=True)[:10]
        
        for doc in sorted_docs:
            created = doc.get('created_at', '')
            if created:
                try:
                    dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
                    time_ago = datetime.now() - dt
                    if time_ago.days > 0:
                        time_str = f"{time_ago.days}d ago"
                    elif time_ago.seconds > 3600:
                        time_str = f"{time_ago.seconds // 3600}h ago"
                    elif time_ago.seconds > 60:
                        time_str = f"{time_ago.seconds // 60}m ago"
                    else:
                        time_str = "Just now"
                except:
                    time_str = "Unknown"
                
                status = doc.get('status', 'unknown')
                status_emoji = {
                    'done': '✅',
                    'processing': '⏳',
                    'uploaded': '📤',
                    'error': '❌'
                }.get(status, '📄')
                
                st.markdown(f"{status_emoji} **{doc.get('filename', 'Unknown')}** - {status} ({time_str})")
    else:
        st.info("No data available yet. Upload some documents to see analytics.")

# ============================================================
# FOOTER
# ============================================================

st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.caption("Made with ❤️ using Streamlit")
with col2:
    st.caption("Powered by FastAPI + PostgreSQL")
with col3:
    st.caption(f"v1.0.0 | {datetime.now().strftime('%Y')}")

# ============================================================
# AUTO-REFRESH FOR PROCESSING DOCUMENTS
# ============================================================

# Check if any documents are processing and auto-refresh
if st.session_state.documents:
    processing_docs = [d for d in st.session_state.documents if d.get('status') == 'processing']
    if processing_docs:
        # Auto-refresh every 5 seconds if documents are processing
        st.toast(f"⏳ {len(processing_docs)} document(s) processing...", icon="⏳")
        time.sleep(2)  # Small delay to prevent rapid refresh
        st.session_state.refresh = True
        st.rerun()

# ============================================================
# REQUIRED PACKAGES
# ============================================================

# frontend/requirements.txt:
# streamlit>=1.28.0
# requests>=2.31.0
# pandas>=2.0.0
# python-dotenv>=1.0.0





















# # app.py - Streamlit PDF Analyzer UI with FastAPI Integration

# import streamlit as st
# import requests
# import json
# import os
# from datetime import datetime
# from typing import Optional, Dict, Any

# # ============================================================
# # 1. CONFIGURATION
# # ============================================================

# # Get backend URL from environment variable (for Docker) or use default
# BACKEND_URL = os.getenv("BACKEND_API_URL")
# API_BASE = BACKEND_URL

# # Page configuration
# st.set_page_config(
#     page_title="PDF Analyzer",
#     page_icon="📄",
#     layout="wide"
# )

# # ============================================================
# # 2. SESSION STATE INITIALIZATION
# # ============================================================

# if 'results' not in st.session_state:
#     st.session_state['results'] = None
# if 'uploaded_file' not in st.session_state:
#     st.session_state['uploaded_file'] = None
# if 'document_id' not in st.session_state:
#     st.session_state['document_id'] = None
# if 'processing' not in st.session_state:
#     st.session_state['processing'] = False

# # ============================================================
# # 3. HELPER FUNCTIONS
# # ============================================================

# def check_backend_health() -> bool:
#     """Check if FastAPI backend is available"""
#     try:
#         print(f"APIBASE_URL is  {API_BASE}")
#         response = requests.get(f"{API_BASE}/health_ui", timeout=5)
#         return response.status_code == 200
#     except:
#         return False

# def upload_document(file) -> Optional[Dict[str, Any]]:
#     """Upload PDF to FastAPI backend"""
#     try:
#         files = {
#             "file": (file.name, file, "application/pdf")
#         }
#         response = requests.post(
#             f"{API_BASE}/documents/upload",
#             files=files,
#             timeout=30
#         )
        
#         if response.status_code == 200:
#             return response.json()
#         else:
#             st.error(f"Upload failed: {response.status_code} - {response.text}")
#             return None
#     except requests.exceptions.Timeout:
#         st.error("Upload timed out. Please try again.")
#         return None
#     except requests.exceptions.ConnectionError:
#         st.error("Cannot connect to backend. Is the API running?")
#         return None
#     except Exception as e:
#         st.error(f"Upload error: {str(e)}")
#         return None

# def analyze_document(document_id: str) -> Optional[Dict[str, Any]]:
#     """Trigger analysis on the backend"""
#     try:
#         response = requests.post(
#             f"{API_BASE}/analysis/analyze/{document_id}",
#             timeout=60  # LLM might take time
#         )
        
#         if response.status_code == 200:
#             return response.json()
#         else:
#             st.error(f"Analysis failed: {response.status_code} - {response.text}")
#             return None
#     except requests.exceptions.Timeout:
#         st.error("Analysis timed out. The LLM might be taking too long.")
#         return None
#     except Exception as e:
#         st.error(f"Analysis error: {str(e)}")
#         return None

# def get_document_status(document_id: str) -> Optional[Dict[str, Any]]:
#     """Get document status and results from backend"""
#     try:
#         response = requests.get(
#             f"{API_BASE}/documents/{document_id}",
#             timeout=10
#         )
        
#         if response.status_code == 200:
#             return response.json()
#         else:
#             return None
#     except:
#         return None

# def poll_analysis_status(document_id: str, max_wait: int = 60) -> Optional[Dict[str, Any]]:
#     """Poll backend until analysis is complete or fails"""
#     import time
    
#     start_time = time.time()
#     last_status = None
    
#     # Create progress bar
#     progress_bar = st.progress(0)
#     status_text = st.empty()
    
#     while time.time() - start_time < max_wait:
#         # Check status
#         result = get_document_status(document_id)
        
#         if not result:
#             status_text.error("Lost connection to backend")
#             return None
        
#         current_status = result.get('status', 'unknown')
        
#         # Update progress based on status
#         if current_status == 'uploaded':
#             progress = 0.2
#             status_text.info("📤 File uploaded, queued for analysis...")
#         elif current_status == 'processing':
#             progress = 0.5
#             status_text.info("🤖 AI is analyzing your document...")
#         elif current_status == 'completed':
#             progress = 1.0
#             status_text.success("✅ Analysis complete!")
#             progress_bar.progress(progress)
#             return result
#         elif current_status == 'failed':
#             status_text.error("❌ Analysis failed")
#             return result
        
#         # Update progress bar
#         progress_bar.progress(progress)
        
#         # Wait before polling again
#         time.sleep(2)
    
#     status_text.warning("⏰ Analysis is taking longer than expected. Check back later.")
#     return None

# # ============================================================
# # 4. UI - SIDEBAR
# # ============================================================

# with st.sidebar:
#     st.header("About")
#     st.info(
#         "This app analyzes PDFs and extracts structured information "
#         "using an LLM API."
#     )
    
#     # Backend connection status
#     st.markdown("---")
#     st.subheader("🔌 Connection Status")
    
#     if check_backend_health():
#         st.success("✅ Connected to FastAPI backend")
#         st.caption(f"API: {API_BASE}")
#     else:
#         st.error("❌ Cannot connect to backend")
#         st.caption("Make sure FastAPI is running")
    
#     st.markdown("---")
#     st.caption(f"Version: 0.1.0")

# # ============================================================
# # 5. UI - MAIN TABS
# # ============================================================

# tab1, tab2, tab3 = st.tabs(["📤 Upload", "📋 Results", "ℹ️ Help"])

# # ============================================================
# # TAB 1: UPLOAD
# # ============================================================

# with tab1:
#     st.header("Upload PDF")
    
#     # Check backend connection first
#     if not check_backend_health():
#         st.warning("⚠️ Backend API is not available. Please start the FastAPI server.")
#         st.stop()
    
#     # File uploader
#     uploaded_file = st.file_uploader(
#         "Choose a PDF file",
#         type=['pdf'],
#         help="Upload a PDF file to analyze"
#     )
    
#     if uploaded_file is not None:
#         # Show file details
#         col1, col2 = st.columns(2)
        
#         with col1:
#             st.success(f"✅ File uploaded: {uploaded_file.name}")
#             st.write(f"📏 Size: {uploaded_file.size} bytes")
#             st.write(f"📅 Uploaded: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
#         with col2:
#             # Analyze button
#             if st.button("🔍 Analyze PDF", type="primary", disabled=st.session_state['processing']):
#                 st.session_state['processing'] = True
                
#                 try:
#                     # Step 1: Upload to backend
#                     with st.spinner("Uploading document..."):
#                         upload_result = upload_document(uploaded_file)
                    
#                     if upload_result and 'id' in upload_result:
#                         document_id = upload_result['id']
#                         st.session_state['document_id'] = document_id
#                         st.success(f"✅ Document uploaded with ID: {document_id}")
                        
#                         # Step 2: Trigger analysis
#                         with st.spinner("Starting analysis..."):
#                             analysis_result = analyze_document(document_id)
                        
#                         if analysis_result:
#                             # Step 3: Poll for completion
#                             st.info("⏳ Waiting for analysis to complete...")
#                             final_result = poll_analysis_status(document_id)
                            
#                             if final_result:
#                                 # Store results in session state
#                                 st.session_state['results'] = {
#                                     'filename': uploaded_file.name,
#                                     'document_id': document_id,
#                                     'status': final_result.get('status'),
#                                     'data': final_result.get('analysis', {}).get('structured_data', {}),
#                                     'raw_response': final_result.get('analysis', {}).get('raw_llm_response'),
#                                     'timestamp': datetime.now().isoformat()
#                                 }
                                
#                                 # Show success
#                                 st.balloons()
#                                 st.success("🎉 Analysis complete! Check the Results tab.")
#                             else:
#                                 st.error("Failed to get analysis results")
#                     else:
#                         st.error("Upload failed. Please try again.")
                
#                 except Exception as e:
#                     st.error(f"An error occurred: {str(e)}")
                
#                 finally:
#                     st.session_state['processing'] = False
#                     st.rerun()

# # ============================================================
# # TAB 2: RESULTS
# # ============================================================

# with tab2:
#     st.header("Analysis Results")
    
#     # Check if we have results
#     if st.session_state['results']:
#         results = st.session_state['results']
#         data = results.get('data', {})
        
#         # Display document info
#         st.subheader("📄 Document Information")
#         col1, col2, col3 = st.columns(3)
        
#         with col1:
#             st.metric("📄 Filename", results.get('filename', 'Unknown'))
#         with col2:
#             st.metric("🆔 Document ID", results.get('document_id', 'Unknown')[:8] + '...')
#         with col3:
#             st.metric("📊 Status", results.get('status', 'unknown').upper())
        
#         st.markdown("---")
        
#         # Display structured data if available
#         if data:
#             st.subheader("📊 Extracted Data")
            
#             # Show in a nice format
#             col1, col2 = st.columns(2)
            
#             with col1:
#                 # Display key metrics
#                 if 'title' in data:
#                     st.metric("📝 Title", data['title'])
#                 if 'author' in data:
#                     st.metric("👤 Author", data['author'])
#                 if 'pages' in data:
#                     st.metric("📄 Pages", data['pages'])
            
#             with col2:
#                 # Display more metrics
#                 if 'topics' in data and data['topics']:
#                     st.write("**🏷️ Topics:**")
#                     for topic in data['topics'][:5]:
#                         st.markdown(f"- {topic}")
            
#             # Show summary
#             if 'summary' in data:
#                 st.subheader("📝 Summary")
#                 st.write(data['summary'])
            
#             # Show full JSON
#             with st.expander("🔍 View Full JSON Data"):
#                 st.json(data)
            
#             # Show raw LLM response
#             if results.get('raw_response'):
#                 with st.expander("📜 Raw LLM Response"):
#                     st.text(results['raw_response'])
            
#             # Export buttons
#             st.markdown("---")
#             col1, col2 = st.columns(2)
            
#             with col1:
#                 # Export as JSON
#                 json_str = json.dumps(data, indent=2, ensure_ascii=False)
#                 st.download_button(
#                     label="📥 Download JSON",
#                     data=json_str,
#                     file_name=f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
#                     mime="application/json",
#                     use_container_width=True
#                 )
            
#             with col2:
#                 # Export as text
#                 text_output = f"""
# PDF Analysis Report
# ===================
# Filename: {results.get('filename')}
# Document ID: {results.get('document_id')}
# Analyzed: {results.get('timestamp')}

# Title: {data.get('title', 'N/A')}
# Author: {data.get('author', 'N/A')}
# Pages: {data.get('pages', 'N/A')}

# Summary:
# {data.get('summary', 'N/A')}

# Topics:
# {', '.join(data.get('topics', ['N/A']))}
# """
#                 st.download_button(
#                     label="📥 Download TXT",
#                     data=text_output,
#                     file_name=f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
#                     mime="text/plain",
#                     use_container_width=True
#                 )
#         else:
#             st.warning("No structured data found in analysis results")
        
#         # Clear results button
#         if st.button("🗑️ Clear Results", type="secondary"):
#             st.session_state['results'] = None
#             st.session_state['document_id'] = None
#             st.rerun()
            
#     else:
#         st.info("No results yet. Upload a PDF and click 'Analyze PDF'.")
        
#         # Show example of what results will look like
#         with st.expander("📖 What to expect"):
#             st.markdown("""
#             Once analysis is complete, you'll see:
            
#             - **Document Information**: Filename, ID, status
#             - **Extracted Data**: Title, author, pages, summary
#             - **Topics**: Key topics identified
#             - **Full JSON**: Complete structured data
#             - **Export Options**: Download as JSON or TXT
#             """)

# # ============================================================
# # TAB 3: HELP
# # ============================================================

# with tab3:
#     st.header("How to Use This App")
    
#     st.markdown("""
#     ### 📋 Steps:
#     1. **Upload** a PDF file using the Upload tab
#     2. **Click** the 'Analyze PDF' button
#     3. **Wait** for the AI to process your document
#     4. **View** the extracted results in the Results tab
#     5. **Export** the results as JSON or TXT
    
#     ### 🤖 How It Works:
#     1. Your PDF is uploaded to the FastAPI backend
#     2. The backend sends the document to an LLM API
#     3. The LLM extracts structured information
#     4. Results are stored in PostgreSQL
#     5. You can view and export the results
    
#     ### 🛠️ Supported Features:
#     - 📄 PDF file upload
#     - 🤖 AI-powered analysis using LLM
#     - 📊 Structured data extraction
#     - 💾 Results stored in database
#     - 📥 Export results as JSON or TXT
#     - 🔄 Real-time progress updates
    
#     ### 🏗️ Architecture:
#     - **Frontend**: Streamlit (this UI)
#     - **Backend**: FastAPI
#     - **Database**: PostgreSQL
#     - **AI**: LLM API (OpenAI/Anthropic/etc.)
#     - **Containerization**: Docker & Docker Compose
#     """)
    
#     # Show environment info
#     with st.expander("🔧 System Info"):
#         st.write(f"**Python Version:** {__import__('sys').version}")
#         st.write(f"**Streamlit Version:** {st.__version__}")
#         st.write(f"**Backend API URL:** {API_BASE}")
#         st.write(f"**Backend Status:** {'✅ Connected' if check_backend_health() else '❌ Disconnected'}")
    
#     # Show troubleshooting
#     with st.expander("⚠️ Troubleshooting"):
#         st.markdown("""
#         ### Common Issues:
        
#         **"Cannot connect to backend"**
#         - Make sure FastAPI is running: `docker-compose up backend`
#         - Check if port 8003 is exposed correctly
#         - Verify environment variable `BACKEND_API_URL`
        
#         **"Analysis timed out"**
#         - LLM API might be slow
#         - Check your internet connection
#         - Verify API key is valid
        
#         **"Upload failed"**
#         - File must be a valid PDF
#         - File size might be too large
#         - Check disk space in uploads folder
        
#         **"No results found"**
#         - Wait for analysis to complete
#         - Check status in backend logs: `docker-compose logs backend`
#         """)

# # ============================================================
# # 6. FOOTER
# # ============================================================

# st.markdown("---")
# col1, col2, col3 = st.columns(3)
# with col1:
#     st.caption("Made with ❤️ using Streamlit")
# with col2:
#     st.caption("Powered by FastAPI + PostgreSQL")
# with col3:
#     st.caption(f"v0.1.0")

# # Auto-refresh results if processing
# if st.session_state.get('processing', False):
#     st.rerun()