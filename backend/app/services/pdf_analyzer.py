"""
Analysis Service - Extracts information from PDFs using OpenRouter.

OpenRouter gives access to multiple LLM models through one API.
"""

import os
import json
import re
from typing import Dict, Any, Optional
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
    """
    
    def __init__(self):
        self.client = None
        self.default_model = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the OpenRouter client checking both env var keys."""
        api_key = os.getenv("OPEN_ROUTER_API_KEY") or os.getenv("LLM_API_KEY")
        
        if not api_key:
            logger.warning("OPEN_ROUTER_API_KEY / LLM_API_KEY not set. Using mock mode.")
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
        """Send PDF content to OpenRouter for analysis."""
        model = model or self.default_model
        
        if self.client:
            return self._call_openrouter(text_content, metadata, model, max_tokens)
        else:
            return self._mock_analysis(text_content, metadata)
        
    def _call_openrouter(
            self,
            text_content: str,
            metadata: Dict[str, Any],
            model: str,
            max_tokens: int
        ) -> Dict[str, Any]:
            """Call OpenRouter API with explicit task instructions."""
            
            max_chars = 15000
            if len(text_content) > max_chars:
                text_content = text_content[:max_chars] + "...\n[Truncated]"
                
            system_prompt = (
                "You are a strict data extraction system. Analyze the provided document text and output a JSON object.\n"
                "DO NOT repeat template instructions or placeholders.\n"
                "DO NOT include markdown, commentary, or thinking tags.\n"
                "Output ONLY raw valid JSON."
            )
            
            user_prompt = f"""Read the following PDF text and extract the actual facts into JSON.

    PDF TEXT CONTENT:
    {text_content}

    CRITICAL: Extract actual values from the text above. If a field is missing, use "Unknown" or an empty list [].

    REQUIRED JSON SCHEMA:
    {{
        "title": "Actual title extracted from document",
        "author": "Actual author extracted from document",
        "extracted_date": "Actual date in YYYY-MM-DD or Unknown",
        "summary": "Actual 2-3 sentence summary of the document content",
        "keywords": ["actual_keyword_1", "actual_keyword_2"],
        "type": "invoice, report, article, letter, paper, or document",
        "key_points": ["actual_point_1", "actual_point_2"],
        "entities": {{
            "people": [],
            "organizations": [],
            "locations": []
        }}
    }}
    """
            try:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=max_tokens,
                    temperature=0.1
                )
                content = response.choices[0].message.content
                logger.info(f"OpenRouter response received ({len(content)} chars)")
                return self._parse_response(content)
                
            except Exception as e:
                logger.error(f"OpenRouter API error: {e}")
                return {
                    "title": "Error",
                    "summary": f"Analysis failed: {str(e)}",
                    "keywords": ["error"],
                    "type": "error",
                    "extracted_date": datetime.now().strftime("%Y-%m-%d")
                }
    
    def _parse_response(self, content: str) -> Dict[str, Any]:
        """Parse LLM output, aggressively stripping chain-of-thought blocks."""
        if not content:
            return self._fallback_parse("Empty response received from LLM.")

        # 1. Strip out chain-of-thought / reasoning processes
        content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
        content = re.sub(r"Here's a thinking process:.*?(?=\{)", '', content, flags=re.DOTALL)
        content = re.sub(r"Thinking Process:.*?(?=\{)", '', content, flags=re.DOTALL)

        # 2. Extract JSON from markdown code fences (```json ... ```)
        json_block_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
        if json_block_match:
            try:
                return json.loads(json_block_match.group(1).strip())
            except json.JSONDecodeError:
                pass

        # 3. Direct JSON attempt
        try:
            return json.loads(content.strip())
        except json.JSONDecodeError:
            pass

        # 4. Regex fallback matching outermost brackets
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group().strip())
            except json.JSONDecodeError:
                pass

        return self._fallback_parse(content)

    def _fallback_parse(self, content: str) -> Dict[str, Any]:
        """Graceful degradation structure when JSON parsing completely fails."""
        return {
            "title": "Unknown",
            "author": "Unknown",
            "extracted_date": datetime.now().strftime("%Y-%m-%d"),
            "summary": content[:500] if content else "No structured content extracted.",
            "keywords": [],
            "type": "unknown",
            "key_points": [],
            "entities": {
                "people": [],
                "organizations": [],
                "locations": []
            },
            "raw_response": content[:1000]
        }
    
    def _mock_analysis(self, text_content: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Mock analysis for development (no API key configured)."""
        logger.info("Using mock analysis (OpenRouter API key not configured)")
        lines = [line.strip() for line in text_content.split('\n') if line.strip()]
        first_line = lines[0] if lines else "Untitled Document"
        
        return {
            "title": first_line[:100],
            "author": "Mock Analyzer",
            "extracted_date": datetime.now().strftime("%Y-%m-%d"),
            "summary": f"Mock analysis active (API key missing). First 200 chars: {text_content[:200]}...",
            "keywords": ["mock", "demo", "pdf"],
            "type": "document",
            "key_points": [
                "Mock analysis - No API key configured",
                "Set OPEN_ROUTER_API_KEY in environment variables",
                "Visit https://openrouter.ai to acquire a valid key"
            ],
            "entities": {
                "people": [],
                "organizations": [],
                "locations": []
            },
            "pages": metadata.get('pages', 0) if metadata else 0
        }


# ============================================================
# 3. MAIN ANALYSIS SERVICE
# ============================================================

class AnalysisService:
    """Main service for orchestrating PDF document analysis."""
    
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
        """Analyze a PDF document and update database states."""
        document = crud.get_document(db, document_id)
        if not document:
            raise ValueError(f"Document not found: {document_id}")
        
        self.logger.info(f"Analyzing document: {document.filename} (ID: {document_id})")
        crud.update_document_status(db, document_id, models.DocumentStatus.PROCESSING)
        
        try:
            self.logger.info(f"Extracting text from PDF: {document.file_path}")
            text_content = self.extractor.extract_text(document.file_path)
            
            if not text_content or len(text_content.strip()) < 10:
                raise ValueError("No text extracted from PDF (file may be empty or image-only scanned PDF)")
            
            metadata = self.extractor.get_metadata(document.file_path)
            
            self.logger.info(f"Calling LLM with model: {model or self.llm.default_model}")
            extracted_data = self.llm.analyze_pdf(
                text_content=text_content,
                metadata=metadata,
                model=model
            )
            
            raw_response = json.dumps(extracted_data, indent=2)
            
            self.logger.info("Saving analysis results to database")
            crud.save_analysis_result(
                db=db,
                document_id=document_id,
                extracted_data=extracted_data,
                raw_response=raw_response
            )
            
            crud.update_document_status(db, document_id, models.DocumentStatus.DONE)
            updated_document = crud.get_document(db, document_id)
            
            return {
                "id": updated_document.id,
                "filename": updated_document.filename,
                "status": updated_document.status,
                "extracted_data": updated_document.extracted_data
            }
            
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"Analysis failed: {error_msg}")
            crud.update_document_status(
                db=db,
                document_id=document_id,
                status=models.DocumentStatus.ERROR,
                error_message=error_msg
            )
            raise


# Singleton instance
analysis_service = AnalysisService()