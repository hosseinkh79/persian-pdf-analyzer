"""
PDF Analyzer - Streamlit Frontend

A modern UI for uploading and analyzing PDFs using AI.
Connects to FastAPI backend with proper error handling and state management.
"""

import os
import json
import time
from datetime import datetime
from typing import Optional, Dict, Any, List

import streamlit as st
import requests
import pandas as pd

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
# CUSTOM CSS FOR CLEANER BADGES & TAGS
# ============================================================

st.markdown("""
<style>
    /* Global Container Padding */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Entity Tag Styling */
    .entity-tag {
        display: inline-block;
        background-color: #f3f4f6;
        color: #1f2937;
        border: 1px solid #e5e7eb;
        padding: 0.25rem 0.65rem;
        border-radius: 6px;
        font-size: 0.85rem;
        margin: 0.2rem;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# CONFIGURATION & STATE INITIALIZATION
# ============================================================

BACKEND_URL = os.getenv("BACKEND_API_URL", "http://localhost:8003")
API_BASE = BACKEND_URL

if 'documents' not in st.session_state:
    st.session_state.documents = []
if 'selected_doc' not in st.session_state:
    st.session_state.selected_doc = None
if 'processing' not in st.session_state:
    st.session_state.processing = False
if 'refresh' not in st.session_state:
    st.session_state.refresh = False

# ============================================================
# API HELPER FUNCTIONS
# ============================================================

def check_backend_health() -> bool:
    try:
        response = requests.get(f"{API_BASE}/health_ui", timeout=3)
        return response.status_code == 200
    except Exception:
        return False

def upload_pdf(file) -> Optional[Dict[str, Any]]:
    try:
        files = {"file": (file.name, file, "application/pdf")}
        response = requests.post(f"{API_BASE}/documents/upload", files=files, timeout=30)
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        st.error(f"Upload error: {str(e)}")
        return None

def analyze_document(document_id: str) -> Optional[Dict[str, Any]]:
    try:
        response = requests.post(f"{API_BASE}/documents/{document_id}/analyze", timeout=90)
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        st.error(f"Analysis error: {str(e)}")
        return None

def get_documents() -> Optional[List[Dict[str, Any]]]:
    try:
        response = requests.get(f"{API_BASE}/documents/", timeout=10)
        return response.json() if response.status_code == 200 else None
    except Exception:
        return None

def get_document_detail(doc_id: str) -> Optional[Dict[str, Any]]:
    try:
        response = requests.get(f"{API_BASE}/documents/{doc_id}", timeout=10)
        return response.json() if response.status_code == 200 else None
    except Exception:
        return None

def delete_document(doc_id: str) -> bool:
    try:
        response = requests.delete(f"{API_BASE}/documents/{doc_id}", timeout=10)
        return response.status_code == 200
    except Exception:
        return False

def format_file_size(size_bytes: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} GB"

# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.title("📄 PDF Analyzer")
    st.caption("AI-Powered Document Intelligence")
    st.divider()
    
    is_online = check_backend_health()
    if is_online:
        st.success("✅ Backend Online", icon="🟢")
    else:
        st.warning("⚠️ Backend Unreachable", icon="🟠")
        st.caption(f"Target: `{API_BASE}`")
    
    st.divider()
    
    if st.session_state.documents:
        total = len(st.session_state.documents)
        done = sum(1 for d in st.session_state.documents if str(d.get('status')).lower() in ['done', 'completed'])
        
        col_a, col_b = st.columns(2)
        col_a.metric("Total Docs", total)
        col_b.metric("Processed", done)

# ============================================================
# MAIN CONTENT
# ============================================================

st.title("📄 Document Extraction Dashboard")
st.markdown("Upload complex PDF documents to automatically extract structured intelligence, keywords, summaries, and key points.")

if st.session_state.refresh or not st.session_state.documents:
    docs = get_documents()
    if docs is not None:
        st.session_state.documents = docs
        st.session_state.refresh = False

tab1, tab2, tab3 = st.tabs([
    "📤 Upload & Analyze",
    "📋 Documents Library",
    "📊 Usage Analytics"
])

# ============================================================
# TAB 1: UPLOAD & ANALYZE
# ============================================================

with tab1:
    col1, col2 = st.columns([3, 2], gap="medium")
    
    with col1:
        st.subheader("Upload Document")
        uploaded_file = st.file_uploader(
            "Select PDF File",
            type=['pdf'],
            help="Maximum supported file size: 100MB",
            label_visibility="collapsed"
        )
        
        if uploaded_file:
            size_fmt = format_file_size(uploaded_file.size)
            st.info(f"📁 **{uploaded_file.name}** ({size_fmt})")
            
            if st.button("🚀 Analyze PDF Document", type="primary", use_container_width=True, disabled=st.session_state.processing):
                st.session_state.processing = True
                
                # Visual Progress Indicators
                progress_bar = st.progress(0, text="Initializing processing pipeline...")
                status_box = st.empty()
                
                # Step 1: Uploading
                status_box.info("📤 Uploading document to server...")
                progress_bar.progress(25, text="Uploading document...")
                upload_res = upload_pdf(uploaded_file)
                
                if upload_res and 'id' in upload_res:
                    doc_id = upload_res['id']
                    
                    # Step 2: Extraction & Processing
                    status_box.info(f"⚙️ Document uploaded (`{doc_id[:8]}`). Extracting text & running AI analysis...")
                    progress_bar.progress(65, text="Analyzing PDF content with LLM...")
                    
                    analysis_res = analyze_document(doc_id)
                    
                    if analysis_res:
                        # Step 3: Complete
                        progress_bar.progress(100, text="Analysis complete!")
                        status_box.success("🎉 Analysis completed successfully!")
                        st.session_state.selected_doc = analysis_res
                        st.session_state.refresh = True
                        st.toast("Document analysis complete!", icon="✅")
                    else:
                        progress_bar.progress(100, text="Analysis failed.")
                        status_box.error("❌ Failed to analyze document content.")
                else:
                    progress_bar.progress(100, text="Upload failed.")
                    status_box.error("❌ Failed to upload document.")
                        
                st.session_state.processing = False
                time.sleep(1)
                st.rerun()

    with col2:
        st.subheader("System Overview")
        if st.session_state.documents:
            total = len(st.session_state.documents)
            done = sum(1 for d in st.session_state.documents if str(d.get('status')).lower() in ['done', 'completed'])
            err = sum(1 for d in st.session_state.documents if str(d.get('status')).lower() == 'error')
            
            st.metric("Total Uploads", total)
            c1, c2 = st.columns(2)
            c1.metric("Successfully Analyzed", done)
            c2.metric("Failed Operations", err)
        else:
            st.caption("No documents registered in the system yet.")

    # Display Analysis Results
    if st.session_state.selected_doc:
        st.divider()
        result = st.session_state.selected_doc
        extracted = result.get('extracted_data', {})
        
        if extracted:
            st.subheader("📊 Document Analysis Results")
            
            # Metadata Section (Using Streamlit Container instead of raw HTML background)
            with st.container(border=True):
                st.markdown(f"### 📄 {result.get('filename', 'Document')}")
                
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Document Title", str(extracted.get('title', 'N/A'))[:25] + "..." if len(str(extracted.get('title', ''))) > 25 else str(extracted.get('title', 'N/A')))
                m2.metric("Author", extracted.get('author', 'N/A'))
                m3.metric("Type", str(extracted.get('type', 'Document')).capitalize())
                m4.metric("Extracted Date", extracted.get('extracted_date', 'N/A'))
                
                st.divider()
                
                # Summary
                st.markdown("#### 📝 Executive Summary")
                st.write(extracted.get('summary', 'No summary generated.'))
                
                # Fixed Streamlit Pills (omitted invalid selection_mode=None)
                keywords = extracted.get('keywords', [])
                if keywords:
                    st.markdown("#### 🏷️ Keywords & Concepts")
                    st.pills(
                        label="Keywords",
                        options=keywords[:12],
                        disabled=True,
                        label_visibility="collapsed"
                    )
            
            st.write("") # Spacing
            
            # Detailed Breakdown Tabs
            st_tab1, st_tab2, st_tab3 = st.tabs(["📌 Key Points", "👥 Named Entities", "🔍 Raw JSON"])
            
            with st_tab1:
                key_points = extracted.get('key_points', [])
                if key_points:
                    for pt in key_points:
                        st.markdown(f"- {pt}")
                else:
                    st.caption("No key points available.")
            
            with st_tab2:
                entities = extracted.get('entities', {})
                if isinstance(entities, dict) and any(entities.values()):
                    col_p, col_o, col_l = st.columns(3)
                    
                    with col_p:
                        st.markdown("**People**")
                        for p in entities.get('people', []):
                            st.markdown(f'<span class="entity-tag">👤 {p}</span>', unsafe_allow_html=True)
                            
                    with col_o:
                        st.markdown("**Organizations**")
                        for o in entities.get('organizations', []):
                            st.markdown(f'<span class="entity-tag">🏢 {o}</span>', unsafe_allow_html=True)
                            
                    with col_l:
                        st.markdown("**Locations**")
                        for l in entities.get('locations', []):
                            st.markdown(f'<span class="entity-tag">📍 {l}</span>', unsafe_allow_html=True)
                else:
                    st.caption("No entities detected.")
            
            with st_tab3:
                st.json(extracted)

            # Export Actions
            st.divider()
            ex_col1, ex_col2, ex_col3 = st.columns([2, 2, 1])
            
            with ex_col1:
                json_data = json.dumps(extracted, indent=2, ensure_ascii=False)
                st.download_button(
                    "📥 Download JSON",
                    data=json_data,
                    file_name=f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    use_container_width=True
                )
                
            with ex_col2:
                try:
                    df = pd.DataFrame([extracted])
                    csv_data = df.to_csv(index=False)
                    st.download_button(
                        "📊 Download CSV",
                        data=csv_data,
                        file_name=f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                except Exception:
                    pass
                    
            with ex_col3:
                if st.button("Clear Results", use_container_width=True):
                    st.session_state.selected_doc = None
                    st.rerun()

# ============================================================
# TAB 2: DOCUMENTS LIBRARY
# ============================================================

with tab2:
    st.subheader("📋 Document Library")
    
    if not st.session_state.documents:
        st.info("No documents found in database.")
    else:
        top_c1, top_c2 = st.columns([5, 1])
        search_query = top_c1.text_input("Search Filename", placeholder="Filter documents...", label_visibility="collapsed")
        
        if top_c2.button("🔄 Refresh", use_container_width=True):
            st.session_state.refresh = True
            st.rerun()
            
        docs = st.session_state.documents
        if search_query:
            docs = [d for d in docs if search_query.lower() in str(d.get('filename', '')).lower()]
            
        st.divider()
        
        for doc in docs:
            doc_status = str(doc.get('status', 'unknown')).lower()
            
            with st.container(border=True):
                c1, c2, c3, c4, c5 = st.columns([3, 1.5, 2, 1.5, 1])
                
                c1.markdown(f"**📄 {doc.get('filename', 'Unknown')}**")
                c1.caption(f"ID: `{doc['id'][:8]}...`")
                
                c2.caption(f"Status: **{doc_status.upper()}**")
                
                created_at = doc.get('created_at', '')
                c3.caption(created_at[:10] if created_at else "—")
                
                if doc_status in ['done', 'completed']:
                    if c4.button("Inspect", key=f"view_{doc['id']}", use_container_width=True):
                        detail = get_document_detail(doc['id'])
                        if detail:
                            st.session_state.selected_doc = detail
                            st.rerun()
                else:
                    c4.caption("Processing...")
                    
                if c5.button("🗑️", key=f"del_{doc['id']}", use_container_width=True):
                    if delete_document(doc['id']):
                        st.toast("Document deleted successfully")
                        st.session_state.refresh = True
                        time.sleep(0.3)
                        st.rerun()

# ============================================================
# TAB 3: ANALYTICS
# ============================================================

with tab3:
    st.subheader("📊 Document Processing Analytics")
    
    if st.session_state.documents:
        docs = st.session_state.documents
        total = len(docs)
        done = sum(1 for d in docs if str(d.get('status')).lower() in ['done', 'completed'])
        processing = sum(1 for d in docs if str(d.get('status')).lower() == 'processing')
        failed = sum(1 for d in docs if str(d.get('status')).lower() == 'error')
        
        a1, a2, a3, a4 = st.columns(4)
        a1.metric("Total Documents", total)
        a2.metric("Completion Rate", f"{(done/total*100):.1f}%" if total > 0 else "0%")
        a3.metric("Processing Queue", processing)
        a4.metric("Errors", failed)
        
        st.divider()
        st.markdown("#### Status Breakdown")
        
        status_counts = {"Completed": done, "Processing": processing, "Failed": failed}
        for label, count in status_counts.items():
            pct = (count / total) if total > 0 else 0
            st.write(f"**{label}** ({count})")
            st.progress(pct)
    else:
        st.caption("No analytics available.")