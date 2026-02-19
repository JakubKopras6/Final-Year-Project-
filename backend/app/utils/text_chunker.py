from typing import List, Dict
import re
from app.config import settings


class TextChunker:
    """Intelligently chunk text for better retrieval."""
    
    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        """
        Initialize text chunker.
        
        Args:
            chunk_size: Maximum characters per chunk
            chunk_overlap: Number of overlapping characters between chunks
        """
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP
    
    def chunk_text(self, text: str, document_id: int = None, page_info: List[Dict] = None) -> List[Dict]:
        """
        Split text into chunks with metadata.
        
        Args:
            text: Full document text
            document_id: ID of source document
            page_info: List of page information
            
        Returns:
            List of chunk dictionaries with text and metadata
        """
        # Clean text
        text = self._clean_text(text)
        
        # Split into sentences for better chunking
        sentences = self._split_sentences(text)
        
        chunks = []
        current_chunk = []
        current_length = 0
        chunk_index = 0
        
        for sentence in sentences:
            sentence_length = len(sentence)
            
            # If adding this sentence exceeds chunk size, save current chunk
            if current_length + sentence_length > self.chunk_size and current_chunk:
                chunk_text = " ".join(current_chunk)
                chunks.append({
                    "text": chunk_text,
                    "chunk_index": chunk_index,
                    "document_id": document_id,
                    "page_number": self._estimate_page(chunk_text, page_info) if page_info else None,
                    "char_count": len(chunk_text)
                })
                
                # Keep overlap sentences for context
                overlap_text = chunk_text[-self.chunk_overlap:] if len(chunk_text) > self.chunk_overlap else chunk_text
                current_chunk = [overlap_text, sentence]
                current_length = len(overlap_text) + sentence_length
                chunk_index += 1
            else:
                current_chunk.append(sentence)
                current_length += sentence_length
        
        # Add remaining chunk
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            chunks.append({
                "text": chunk_text,
                "chunk_index": chunk_index,
                "document_id": document_id,
                "page_number": self._estimate_page(chunk_text, page_info) if page_info else None,
                "char_count": len(chunk_text)
            })
        
        return chunks
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)
        # Remove multiple newlines
        text = re.sub(r'\n+', '\n', text)
        return text.strip()
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Simple sentence splitting
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _estimate_page(self, chunk_text: str, page_info: List[Dict]) -> int:
        """
        Estimate which page a chunk belongs to.
        
        Args:
            chunk_text: The chunk text
            page_info: List of page information
            
        Returns:
            Estimated page number
        """
        if not page_info:
            return None
        
        # Find which page contains most of this chunk
        for page in page_info:
            if chunk_text[:100] in page["text"]:
                return page["page_number"]
        
        return 1  # Default to first page if not found