# app.py - Simple Streamlit PDF Analyzer UI

import streamlit as st
import requests
import json
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="PDF Analyzer",
    page_icon="📄",
    layout="wide"
)

# Title and description
st.title("📄 Persian PDF Analyzer")
st.markdown("Upload a PDF to analyze it using AI")

# Sidebar for app info
with st.sidebar:
    st.header("About")
    st.info(
        "This app analyzes PDFs and extracts structured information "
        "using an LLM API."
    )
    st.markdown("---")
    st.caption(f"Version: 0.1.0")

# Main content area with tabs
tab1, tab2, tab3 = st.tabs(["📤 Upload", "📋 Results", "ℹ️ Help"])

with tab1:
    st.header("Upload PDF")
    
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
            if st.button("🔍 Analyze PDF", type="primary"):
                with st.spinner("Analyzing PDF..."):
                    # Here we'll call the FastAPI backend later
                    # For now, just simulate analysis
                    
                    # Display progress
                    progress_bar = st.progress(0)
                    for i in range(100):
                        progress_bar.progress(i + 1)
                    
                    # Simulated results
                    st.success("✅ Analysis complete!")
                    
                    # Store results in session state
                    st.session_state['results'] = {
                        'filename': uploaded_file.name,
                        'status': 'completed',
                        'data': {
                            'title': 'Sample Document',
                            'author': 'AI Assistant',
                            'pages': 10,
                            'summary': 'This is a sample PDF analysis.'
                        }
                    }
                    
                    # Show results immediately
                    st.balloons()

with tab2:
    st.header("Analysis Results")
    
    # Check if we have results
    if 'results' in st.session_state:
        results = st.session_state['results']
        
        # Display results in a nice format
        st.json(results['data'])
        
        # Or show in a more readable format
        col1, col2 = st.columns(2)
        with col1:
            st.metric("📄 Document", results['filename'])
            st.metric("📊 Pages", results['data']['pages'])
        with col2:
            st.metric("👤 Author", results['data']['author'])
            st.metric("📝 Title", results['data']['title'])
        
        # Show summary
        st.subheader("📝 Summary")
        st.write(results['data']['summary'])
        
        # Export button
        if st.button("📥 Export Results"):
            json_str = json.dumps(results['data'], indent=2)
            st.download_button(
                label="Download as JSON",
                data=json_str,
                file_name=f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    else:
        st.info("No results yet. Upload a PDF and click 'Analyze'.")

with tab3:
    st.header("How to Use This App")
    st.markdown("""
    ### Steps:
    1. **Upload** a PDF file using the Upload tab
    2. **Click** the 'Analyze PDF' button
    3. **View** the extracted results
    4. **Export** the results as JSON
    
    ### Supported Features:
    - 📄 PDF file upload
    - 🤖 AI-powered analysis
    - 📊 Structured data extraction
    - 📥 Export results
    """)
    
    # Show environment info
    with st.expander("🔧 System Info"):
        st.write(f"Python Version: {__import__('sys').version}")
        st.write(f"Streamlit Version: {st.__version__}")

# Footer
st.markdown("---")
st.caption("Made with ❤️ using Streamlit + FastAPI + PostgreSQL")