import pdfplumber
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


class PDFParser:
    """Parse PDF documents and extract text content."""
    
    @staticmethod
    def extract_text(file_path: str) -> Dict[str, any]:
        """
        Extract text from PDF file.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Dictionary containing:
                - full_text: Complete document text
                - pages: List of page texts
                - page_count: Number of pages
                - metadata: Document metadata
        """
        try:
            pages_text = []
            full_text = ""
            
            with pdfplumber.open(file_path) as pdf:
                page_count = len(pdf.pages)
                
                for page_num, page in enumerate(pdf.pages, 1):
                    text = page.extract_text()
                    if text:
                        pages_text.append({
                            "page_number": page_num,
                            "text": text.strip()
                        })
                        full_text += f"\n\n--- Page {page_num} ---\n\n{text.strip()}"
                
                metadata = pdf.metadata if hasattr(pdf, 'metadata') else {}
            
            logger.info(f"Successfully extracted text from {page_count} pages")
            
            return {
                "full_text": full_text.strip(),
                "pages": pages_text,
                "page_count": page_count,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"Error parsing PDF {file_path}: {str(e)}")
            raise Exception(f"Failed to parse PDF: {str(e)}")
    
    @staticmethod
    def validate_pdf(file_path: str) -> bool:
        """
        Validate if file is a proper PDF.
        
        Args:
            file_path: Path to file
            
        Returns:
            True if valid PDF, False otherwise
        """
        try:
            with pdfplumber.open(file_path) as pdf:
                # Try to access first page
                if len(pdf.pages) > 0:
                    return True
            return False
        except Exception as e:
            logger.error(f"PDF validation failed: {str(e)}")
            return False