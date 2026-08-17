# app.py - Streamlit PDF Analyzer UI with FastAPI Integration

import streamlit as st
import requests
import json
import os
from datetime import datetime
from typing import Optional, Dict, Any

# ============================================================
# 1. CONFIGURATION
# ============================================================

# Get backend URL from environment variable (for Docker) or use default
BACKEND_URL = os.getenv("BACKEND_API_URL")
API_BASE = BACKEND_URL

# Page configuration
st.set_page_config(
    page_title="PDF Analyzer",
    page_icon="📄",
    layout="wide"
)

# ============================================================
# 2. SESSION STATE INITIALIZATION
# ============================================================

if 'results' not in st.session_state:
    st.session_state['results'] = None
if 'uploaded_file' not in st.session_state:
    st.session_state['uploaded_file'] = None
if 'document_id' not in st.session_state:
    st.session_state['document_id'] = None
if 'processing' not in st.session_state:
    st.session_state['processing'] = False

# ============================================================
# 3. HELPER FUNCTIONS
# ============================================================

def check_backend_health() -> bool:
    """Check if FastAPI backend is available"""
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def upload_document(file) -> Optional[Dict[str, Any]]:
    """Upload PDF to FastAPI backend"""
    try:
        files = {
            "file": (file.name, file, "application/pdf")
        }
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
        st.error("Cannot connect to backend. Is the API running?")
        return None
    except Exception as e:
        st.error(f"Upload error: {str(e)}")
        return None

def analyze_document(document_id: str) -> Optional[Dict[str, Any]]:
    """Trigger analysis on the backend"""
    try:
        response = requests.post(
            f"{API_BASE}/analysis/analyze/{document_id}",
            timeout=60  # LLM might take time
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

def get_document_status(document_id: str) -> Optional[Dict[str, Any]]:
    """Get document status and results from backend"""
    try:
        response = requests.get(
            f"{API_BASE}/documents/{document_id}",
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except:
        return None

def poll_analysis_status(document_id: str, max_wait: int = 60) -> Optional[Dict[str, Any]]:
    """Poll backend until analysis is complete or fails"""
    import time
    
    start_time = time.time()
    last_status = None
    
    # Create progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    while time.time() - start_time < max_wait:
        # Check status
        result = get_document_status(document_id)
        
        if not result:
            status_text.error("Lost connection to backend")
            return None
        
        current_status = result.get('status', 'unknown')
        
        # Update progress based on status
        if current_status == 'uploaded':
            progress = 0.2
            status_text.info("📤 File uploaded, queued for analysis...")
        elif current_status == 'processing':
            progress = 0.5
            status_text.info("🤖 AI is analyzing your document...")
        elif current_status == 'completed':
            progress = 1.0
            status_text.success("✅ Analysis complete!")
            progress_bar.progress(progress)
            return result
        elif current_status == 'failed':
            status_text.error("❌ Analysis failed")
            return result
        
        # Update progress bar
        progress_bar.progress(progress)
        
        # Wait before polling again
        time.sleep(2)
    
    status_text.warning("⏰ Analysis is taking longer than expected. Check back later.")
    return None

# ============================================================
# 4. UI - SIDEBAR
# ============================================================

with st.sidebar:
    st.header("About")
    st.info(
        "This app analyzes PDFs and extracts structured information "
        "using an LLM API."
    )
    
    # Backend connection status
    st.markdown("---")
    st.subheader("🔌 Connection Status")
    
    if check_backend_health():
        st.success("✅ Connected to FastAPI backend")
        st.caption(f"API: {API_BASE}")
    else:
        st.error("❌ Cannot connect to backend")
        st.caption("Make sure FastAPI is running")
    
    st.markdown("---")
    st.caption(f"Version: 0.1.0")

# ============================================================
# 5. UI - MAIN TABS
# ============================================================

tab1, tab2, tab3 = st.tabs(["📤 Upload", "📋 Results", "ℹ️ Help"])

# ============================================================
# TAB 1: UPLOAD
# ============================================================

with tab1:
    st.header("Upload PDF")
    
    # Check backend connection first
    if not check_backend_health():
        st.warning("⚠️ Backend API is not available. Please start the FastAPI server.")
        st.stop()
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type=['pdf'],
        help="Upload a PDF file to analyze"
    )
    
    if uploaded_file is not None:
        # Show file details
        col1, col2 = st.columns(2)
        
        with col1:
            st.success(f"✅ File uploaded: {uploaded_file.name}")
            st.write(f"📏 Size: {uploaded_file.size} bytes")
            st.write(f"📅 Uploaded: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        with col2:
            # Analyze button
            if st.button("🔍 Analyze PDF", type="primary", disabled=st.session_state['processing']):
                st.session_state['processing'] = True
                
                try:
                    # Step 1: Upload to backend
                    with st.spinner("Uploading document..."):
                        upload_result = upload_document(uploaded_file)
                    
                    if upload_result and 'id' in upload_result:
                        document_id = upload_result['id']
                        st.session_state['document_id'] = document_id
                        st.success(f"✅ Document uploaded with ID: {document_id}")
                        
                        # Step 2: Trigger analysis
                        with st.spinner("Starting analysis..."):
                            analysis_result = analyze_document(document_id)
                        
                        if analysis_result:
                            # Step 3: Poll for completion
                            st.info("⏳ Waiting for analysis to complete...")
                            final_result = poll_analysis_status(document_id)
                            
                            if final_result:
                                # Store results in session state
                                st.session_state['results'] = {
                                    'filename': uploaded_file.name,
                                    'document_id': document_id,
                                    'status': final_result.get('status'),
                                    'data': final_result.get('analysis', {}).get('structured_data', {}),
                                    'raw_response': final_result.get('analysis', {}).get('raw_llm_response'),
                                    'timestamp': datetime.now().isoformat()
                                }
                                
                                # Show success
                                st.balloons()
                                st.success("🎉 Analysis complete! Check the Results tab.")
                            else:
                                st.error("Failed to get analysis results")
                    else:
                        st.error("Upload failed. Please try again.")
                
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
                
                finally:
                    st.session_state['processing'] = False
                    st.rerun()

# ============================================================
# TAB 2: RESULTS
# ============================================================

with tab2:
    st.header("Analysis Results")
    
    # Check if we have results
    if st.session_state['results']:
        results = st.session_state['results']
        data = results.get('data', {})
        
        # Display document info
        st.subheader("📄 Document Information")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("📄 Filename", results.get('filename', 'Unknown'))
        with col2:
            st.metric("🆔 Document ID", results.get('document_id', 'Unknown')[:8] + '...')
        with col3:
            st.metric("📊 Status", results.get('status', 'unknown').upper())
        
        st.markdown("---")
        
        # Display structured data if available
        if data:
            st.subheader("📊 Extracted Data")
            
            # Show in a nice format
            col1, col2 = st.columns(2)
            
            with col1:
                # Display key metrics
                if 'title' in data:
                    st.metric("📝 Title", data['title'])
                if 'author' in data:
                    st.metric("👤 Author", data['author'])
                if 'pages' in data:
                    st.metric("📄 Pages", data['pages'])
            
            with col2:
                # Display more metrics
                if 'topics' in data and data['topics']:
                    st.write("**🏷️ Topics:**")
                    for topic in data['topics'][:5]:
                        st.markdown(f"- {topic}")
            
            # Show summary
            if 'summary' in data:
                st.subheader("📝 Summary")
                st.write(data['summary'])
            
            # Show full JSON
            with st.expander("🔍 View Full JSON Data"):
                st.json(data)
            
            # Show raw LLM response
            if results.get('raw_response'):
                with st.expander("📜 Raw LLM Response"):
                    st.text(results['raw_response'])
            
            # Export buttons
            st.markdown("---")
            col1, col2 = st.columns(2)
            
            with col1:
                # Export as JSON
                json_str = json.dumps(data, indent=2, ensure_ascii=False)
                st.download_button(
                    label="📥 Download JSON",
                    data=json_str,
                    file_name=f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    use_container_width=True
                )
            
            with col2:
                # Export as text
                text_output = f"""
PDF Analysis Report
===================
Filename: {results.get('filename')}
Document ID: {results.get('document_id')}
Analyzed: {results.get('timestamp')}

Title: {data.get('title', 'N/A')}
Author: {data.get('author', 'N/A')}
Pages: {data.get('pages', 'N/A')}

Summary:
{data.get('summary', 'N/A')}

Topics:
{', '.join(data.get('topics', ['N/A']))}
"""
                st.download_button(
                    label="📥 Download TXT",
                    data=text_output,
                    file_name=f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
        else:
            st.warning("No structured data found in analysis results")
        
        # Clear results button
        if st.button("🗑️ Clear Results", type="secondary"):
            st.session_state['results'] = None
            st.session_state['document_id'] = None
            st.rerun()
            
    else:
        st.info("No results yet. Upload a PDF and click 'Analyze PDF'.")
        
        # Show example of what results will look like
        with st.expander("📖 What to expect"):
            st.markdown("""
            Once analysis is complete, you'll see:
            
            - **Document Information**: Filename, ID, status
            - **Extracted Data**: Title, author, pages, summary
            - **Topics**: Key topics identified
            - **Full JSON**: Complete structured data
            - **Export Options**: Download as JSON or TXT
            """)

# ============================================================
# TAB 3: HELP
# ============================================================

with tab3:
    st.header("How to Use This App")
    
    st.markdown("""
    ### 📋 Steps:
    1. **Upload** a PDF file using the Upload tab
    2. **Click** the 'Analyze PDF' button
    3. **Wait** for the AI to process your document
    4. **View** the extracted results in the Results tab
    5. **Export** the results as JSON or TXT
    
    ### 🤖 How It Works:
    1. Your PDF is uploaded to the FastAPI backend
    2. The backend sends the document to an LLM API
    3. The LLM extracts structured information
    4. Results are stored in PostgreSQL
    5. You can view and export the results
    
    ### 🛠️ Supported Features:
    - 📄 PDF file upload
    - 🤖 AI-powered analysis using LLM
    - 📊 Structured data extraction
    - 💾 Results stored in database
    - 📥 Export results as JSON or TXT
    - 🔄 Real-time progress updates
    
    ### 🏗️ Architecture:
    - **Frontend**: Streamlit (this UI)
    - **Backend**: FastAPI
    - **Database**: PostgreSQL
    - **AI**: LLM API (OpenAI/Anthropic/etc.)
    - **Containerization**: Docker & Docker Compose
    """)
    
    # Show environment info
    with st.expander("🔧 System Info"):
        st.write(f"**Python Version:** {__import__('sys').version}")
        st.write(f"**Streamlit Version:** {st.__version__}")
        st.write(f"**Backend API URL:** {API_BASE}")
        st.write(f"**Backend Status:** {'✅ Connected' if check_backend_health() else '❌ Disconnected'}")
    
    # Show troubleshooting
    with st.expander("⚠️ Troubleshooting"):
        st.markdown("""
        ### Common Issues:
        
        **"Cannot connect to backend"**
        - Make sure FastAPI is running: `docker-compose up backend`
        - Check if port 8003 is exposed correctly
        - Verify environment variable `BACKEND_API_URL`
        
        **"Analysis timed out"**
        - LLM API might be slow
        - Check your internet connection
        - Verify API key is valid
        
        **"Upload failed"**
        - File must be a valid PDF
        - File size might be too large
        - Check disk space in uploads folder
        
        **"No results found"**
        - Wait for analysis to complete
        - Check status in backend logs: `docker-compose logs backend`
        """)

# ============================================================
# 6. FOOTER
# ============================================================

st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.caption("Made with ❤️ using Streamlit")
with col2:
    st.caption("Powered by FastAPI + PostgreSQL")
with col3:
    st.caption(f"v0.1.0")

# Auto-refresh results if processing
if st.session_state.get('processing', False):
    st.rerun()