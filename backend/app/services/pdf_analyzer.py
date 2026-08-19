"""
Analysis Service - Extracts information from PDFs using OpenRouter.

OpenRouter gives access to multiple LLM models through one API.
"""

import os
import json
import re
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from sqlalchemy.orm import Session

# PDF processing libraries
try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

# OpenRouter uses the OpenAI client
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from app import crud, models
from app.config import settings

# Configure logging
logger = logging.getLogger(__name__)


# ============================================================
# 1. PDF EXTRACTION
# ============================================================

class PDFExtractor:
    """Extract text from PDF files."""
    
    @staticmethod
    def extract_text(file_path: str) -> str:
        """Extract text from PDF file."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found: {file_path}")
        
        # Try pdfplumber first (more accurate)
        if pdfplumber:
            try:
                return PDFExtractor._extract_with_pdfplumber(file_path)
            except Exception as e:
                logger.warning(f"pdfplumber extraction failed: {e}, falling back to PyPDF2")
        
        # Fallback to PyPDF2
        if PyPDF2:
            return PDFExtractor._extract_with_pypdf2(file_path)
        
        raise ImportError("No PDF library available. Install pdfplumber or PyPDF2")
    
    @staticmethod
    def _extract_with_pdfplumber(file_path: str) -> str:
        """Extract text using pdfplumber."""
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text.strip()
    
    @staticmethod
    def _extract_with_pypdf2(file_path: str) -> str:
        """Extract text using PyPDF2."""
        text = ""
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text.strip()
    
    @staticmethod
    def get_metadata(file_path: str) -> Dict[str, Any]:
        """Extract PDF metadata."""
        metadata = {'pages': 0}
        
        if PyPDF2:
            try:
                with open(file_path, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    metadata['pages'] = len(reader.pages)
                    if reader.metadata:
                        for key, value in reader.metadata.items():
                            clean_key = key.replace('/', '').lower()
                            metadata[clean_key] = value
            except Exception as e:
                logger.warning(f"Failed to extract metadata: {e}")
        
        return metadata


# ============================================================
# 2. OPENROUTER LLM SERVICE
# ============================================================

class OpenRouterService:
    """
    Service for calling LLM APIs via OpenRouter.
    
    OpenRouter provides access to many models:
    - nvidia/nemotron-3.5-lightning:free
    - openai/gpt-4
    - anthropic/claude-3
    - meta-llama/llama-3
    - google/gemini-pro
    - mistralai/mistral-7b
    and many more!
    """
    
    def __init__(self):
        self.client = None
        self.default_model = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the OpenRouter client."""
        api_key = os.getenv("LLM_API_KEY")
        
        if not api_key:
            logger.warning("OPEN_ROUTER_API_KEY not set. Using mock mode.")
            self.client = None
            return
        
        if not OpenAI:
            logger.error("OpenAI package not installed. Install with: pip install openai")
            self.client = None
            return
        
        try:
            self.client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=api_key,
                default_headers={
                    "X-Title": os.getenv("OPENROUTER_TITLE", "PDF Analyzer")
                }
            )
            self.default_model = os.getenv("LLM_MODEL_NAME", "nvidia/nemotron-3.5-lightning:free")
            logger.info(f"✅ OpenRouter client initialized with model: {self.default_model}")
        except Exception as e:
            logger.error(f"Failed to initialize OpenRouter client: {e}")
            self.client = None
    
    def analyze_pdf(
        self,
        text_content: str,
        metadata: Dict[str, Any] = None,
        model: str = None,
        max_tokens: int = 1000
    ) -> Dict[str, Any]:
        """
        Send PDF content to OpenRouter for analysis.
        
        Args:
            text_content: Extracted text from PDF
            metadata: PDF metadata
            model: Specific model to use (e.g., "openai/gpt-4")
            max_tokens: Maximum tokens in response
            
        Returns:
            Structured data extracted from PDF
        """
        # Use default model if none specified
        model = model or self.default_model
        
        # Prepare the prompt
        prompt = self._prepare_prompt(text_content, metadata)
        
        # Call OpenRouter
        if self.client:
            return self._call_openrouter(prompt, model, max_tokens)
        else:
            # Mock mode for development
            return self._mock_analysis(text_content, metadata)
    
    def _prepare_prompt(self, text_content: str, metadata: Dict[str, Any] = None) -> str:
        """Prepare the prompt for the LLM."""
        
        # Truncate text if too long
        max_chars = 15000  # ~5000 tokens
        if len(text_content) > max_chars:
            text_content = text_content[:max_chars] + "...\n[Content truncated due to length]"
        
        # System prompt
        system_prompt = """You are an expert document analyzer. Extract structured information from the provided PDF content.

Extract the following information:
1. Title - The main title of the document
2. Author - The author(s) of the document
3. Date - The date mentioned in the document (format: YYYY-MM-DD)
4. Summary - A concise summary of the document (2-3 sentences)
5. Keywords - 5-10 key topics or concepts from the document
6. Type - Document type (invoice, report, article, letter, contract, etc.)
7. Key Points - 3-5 main points from the document
8. Entities - Any important entities mentioned (names, organizations, locations)

Return ONLY valid JSON in this exact format (no other text):
{
    "title": "Document title or 'Unknown'",
    "author": "Author name or 'Unknown'",
    "date": "YYYY-MM-DD or 'Unknown'",
    "summary": "Brief summary of the document",
    "keywords": ["keyword1", "keyword2", "keyword3"],
    "type": "document type",
    "key_points": ["point1", "point2", "point3"],
    "entities": {
        "people": ["name1", "name2"],
        "organizations": ["org1", "org2"],
        "locations": ["location1", "location2"]
    }
}

Be thorough but concise. If information is not available, use "Unknown" or empty lists."""
        
        # User prompt with actual content
        user_prompt = f"""
PDF Information:
- Pages: {metadata.get('pages', 'Unknown') if metadata else 'Unknown'}

PDF Content:
{text_content}

Extract the structured information from this PDF and return ONLY valid JSON.
"""
        
        return system_prompt + "\n\n" + user_prompt
    
    def _call_openrouter(self, prompt: str, model: str, max_tokens: int) -> Dict[str, Any]:
        """Call OpenRouter API."""
        
        try:
            # Extract just the JSON part from the prompt
            # The prompt already has the system and user messages combined
            # We need to split them for the API call
            
            # Find where the user content starts
            parts = prompt.split("PDF Content:")
            if len(parts) > 1:
                system_part = parts[0]
                user_content = parts[1]
            else:
                system_part = "You are a helpful document analyst. Extract structured information from PDFs."
                user_content = prompt
            
            # Prepare messages for OpenRouter
            messages = [
                {
                    "role": "system",
                    "content": system_part.strip()
                },
                {
                    "role": "user",
                    "content": f"""Extract structured information from this PDF:

{user_content.strip()}

Return ONLY valid JSON with the following structure:
{{
    "title": "...",
    "author": "...",
    "date": "...",
    "summary": "...",
    "keywords": [...],
    "type": "...",
    "key_points": [...],
    "entities": {{
        "people": [...],
        "organizations": [...],
        "locations": [...]
    }}
}}"""
                }
            ]
            
            # Make the API call
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.3,  # Lower for consistent results
                top_p=0.9,
                extra_headers={
                    "X-Title": os.getenv("OPENROUTER_TITLE", "PDF Analyzer")
                }
            )
            
            # Extract and parse the response
            content = response.choices[0].message.content
            logger.info(f"OpenRouter response received ({len(content)} chars)")
            
            return self._parse_response(content)
            
        except Exception as e:
            logger.error(f"OpenRouter API error: {e}")
            return {
                "error": str(e),
                "title": "Error",
                "summary": f"Analysis failed: {str(e)}",
                "keywords": ["error"],
                "type": "error"
            }
    
    def _parse_response(self, content: str) -> Dict[str, Any]:
        """Parse and validate the LLM response."""
        try:
            # Try to parse as JSON directly
            data = json.loads(content)
            return data
        except json.JSONDecodeError:
            # Try to extract JSON from text
            try:
                # Find JSON-like content between curly braces
                json_match = re.search(r'\{[^{}]*\}', content, re.DOTALL)
                if json_match:
                    # Try to find complete JSON with nested objects
                    # Use a more robust regex for nested JSON
                    json_match = re.search(r'\{.*\}', content, re.DOTALL)
                    if json_match:
                        data = json.loads(json_match.group())
                        return data
            except:
                pass
            
            # If all fails, try to extract information manually
            return {
                "title": "Unknown",
                "author": "Unknown",
                "date": "Unknown",
                "summary": content[:500] if content else "No content extracted",
                "keywords": [],
                "type": "unknown",
                "key_points": [],
                "entities": {
                    "people": [],
                    "organizations": [],
                    "locations": []
                },
                "raw_response": content[:1000]  # Truncate
            }
    
    def _mock_analysis(self, text_content: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Mock analysis for development (no API key)."""
        logger.info("Using mock analysis (OpenRouter API key not configured)")
        
        lines = text_content.split('\n')
        first_line = lines[0] if lines else ""
        
        return {
            "title": first_line[:100] or "Untitled Document",
            "author": "Mock Analyzer",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "summary": f"Mock analysis (OpenRouter not configured). First 200 chars: {text_content[:200]}...",
            "keywords": ["mock", "openrouter", "demo", "pdf"],
            "type": "document",
            "key_points": [
                "Mock analysis - No API key configured",
                "Set OPEN_ROUTER_API_KEY in .env",
                "Visit https://openrouter.ai to get a key"
            ],
            "entities": {
                "people": [],
                "organizations": [],
                "locations": []
            },
            "pages": metadata.get('pages', 'Unknown') if metadata else 'Unknown'
        }


# ============================================================
# 3. MAIN ANALYSIS SERVICE
# ============================================================

class AnalysisService:
    """
    Main service for analyzing PDF documents.
    
    Orchestrates:
    1. PDF extraction
    2. LLM analysis via OpenRouter
    3. Result storage
    """
    
    def __init__(self):
        self.extractor = PDFExtractor()
        self.llm = OpenRouterService()
        self.logger = logging.getLogger(__name__)
    
    def analyze_document(
        self,
        db: Session,
        document_id: str,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze a PDF document.
        
        Args:
            db: Database session
            document_id: ID of the document to analyze
            model: Specific LLM model to use (e.g., "openai/gpt-4")
            
        Returns:
            Analysis results
        """
        # Get document from database
        document = crud.get_document(db, document_id)
        if not document:
            raise ValueError(f"Document not found: {document_id}")
        
        self.logger.info(f"Analyzing document: {document.filename} (ID: {document_id})")
        
        # Update status to processing
        crud.update_document_status(db, document_id, models.DocumentStatus.PROCESSING)
        
        try:
            # Extract PDF text
            self.logger.info(f"Extracting text from PDF: {document.file_path}")
            text_content = self.extractor.extract_text(document.file_path)
            
            if not text_content or len(text_content.strip()) < 10:
                raise ValueError("No text could be extracted from PDF (file might be scanned or empty)")
            
            # Get PDF metadata
            metadata = self.extractor.get_metadata(document.file_path)
            
            self.logger.info(f"Extracted {len(text_content)} characters, {metadata.get('pages', 0)} pages")
            
            # Analyze with LLM
            self.logger.info(f"Calling OpenRouter with model: {model or self.llm.default_model}")
            extracted_data = self.llm.analyze_pdf(
                text_content=text_content,
                metadata=metadata,
                model=model
            )
            
            # Store raw response for debugging
            raw_response = json.dumps(extracted_data, indent=2)
            
            # Save results to database
            self.logger.info("Saving analysis results to database")
            crud.save_analysis_result(
                db=db,
                document_id=document_id,
                extracted_data=extracted_data,
                raw_response=raw_response
            )
            
            # Get updated document
            document = crud.get_document(db, document_id)
            
            self.logger.info(f"Analysis complete for document: {document.filename}")
            
            return {
                "id": document.id,
                "filename": document.filename,
                "status": document.status,
                "extracted_data": document.extracted_data
            }
            
        except Exception as e:
            # Update status to error
            error_msg = str(e)
            self.logger.error(f"Analysis failed: {error_msg}")
            crud.update_document_status(
                db=db,
                document_id=document_id,
                status=models.DocumentStatus.ERROR,
                error_message=error_msg
            )
            raise


# ============================================================
# 4. SINGLETON INSTANCE
# ============================================================

# Create a single instance of the analysis service
analysis_service = AnalysisService()