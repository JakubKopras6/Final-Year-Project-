import os
import shutil
from datetime import datetime
from typing import List
from fastapi import UploadFile
from sqlalchemy.orm import Session
import logging

from app.models.database import Document
from app.config import settings
from app.utils.pdf_parser import PDFParser
from app.utils.text_chunker import TextChunker
from app.services.embedding_service import EmbeddingService
from app.services.vector_store_service import VectorStoreService

logger = logging.getLogger(__name__)


class DocumentService:
    """Handle document upload, processing, and management."""
    
    def __init__(self):
        self.pdf_parser = PDFParser()
        self.text_chunker = TextChunker()
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStoreService()
    
    async def upload_document(
        self,
        file: UploadFile,
        company_id: int,
        user_id: int,
        db: Session
    ) -> Document:
        """
        Upload and process a document.
        
        Args:
            file: Uploaded file
            company_id: Company ID
            user_id: User ID who uploaded
            db: Database session
            
        Returns:
            Document database record
        """
        try:
            # Validate file
            if not file.filename.endswith('.pdf'):
                raise ValueError("Only PDF files are supported")
            
            # Check file size
            file.file.seek(0, 2)  # Seek to end
            file_size = file.file.tell()
            file.file.seek(0)  # Reset to beginning
            
            if file_size > settings.MAX_UPLOAD_SIZE:
                raise ValueError(f"File size exceeds {settings.MAX_UPLOAD_SIZE / (1024*1024)}MB limit")
            
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{company_id}_{timestamp}_{file.filename}"
            file_path = os.path.join(settings.UPLOAD_DIR, filename)
            
            # Save file
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            logger.info(f"File saved: {file_path}")
            
            # Create database record
            document = Document(
                filename=filename,
                original_filename=file.filename,
                file_path=file_path,
                file_size=file_size,
                company_id=company_id,
                uploaded_by=user_id,
                processed=False
            )
            
            db.add(document)
            db.commit()
            db.refresh(document)
            
            # Process document asynchronously (in production, use background task)
            await self._process_document(document.id, file_path, company_id, db)
            
            return document
            
        except Exception as e:
            logger.error(f"Error uploading document: {str(e)}")
            # Cleanup file if it was saved
            if os.path.exists(file_path):
                os.remove(file_path)
            raise
    
    async def _process_document(
        self,
        document_id: int,
        file_path: str,
        company_id: int,
        db: Session
    ):
        """
        Process document: extract text, chunk, generate embeddings, store in vector DB.
        
        Args:
            document_id: Document ID
            file_path: Path to document file
            company_id: Company ID
            db: Database session
        """
        try:
            logger.info(f"Processing document {document_id}")
            
            # Extract text from PDF
            pdf_data = self.pdf_parser.extract_text(file_path)
            
            # Chunk text
            chunks = self.text_chunker.chunk_text(
                text=pdf_data['full_text'],
                document_id=document_id,
                page_info=pdf_data['pages']
            )
            
            logger.info(f"Created {len(chunks)} chunks")
            
            # Generate embeddings
            chunk_texts = [chunk['text'] for chunk in chunks]
            embeddings = self.embedding_service.generate_embeddings(chunk_texts)
            
            # Store in vector database
            self.vector_store.add_documents(
                company_id=company_id,
                document_id=document_id,
                chunks=chunks,
                embeddings=embeddings
            )
            
            # Update document record
            document = db.query(Document).filter(Document.id == document_id).first()
            document.processed = True
            document.processed_at = datetime.utcnow()
            document.page_count = pdf_data['page_count']
            document.chunk_count = len(chunks)
            db.commit()
            
            logger.info(f"Document {document_id} processed successfully")
            
        except Exception as e:
            logger.error(f"Error processing document {document_id}: {str(e)}")
            # Mark as failed
            document = db.query(Document).filter(Document.id == document_id).first()
            if document:
                document.processed = False
                db.commit()
            raise
    
    def get_company_documents(self, company_id: int, db: Session) -> List[Document]:
        """Get all documents for a company."""
        return db.query(Document).filter(
            Document.company_id == company_id
        ).order_by(Document.uploaded_at.desc()).all()
    
    def delete_document(self, document_id: int, company_id: int, db: Session):
        """Delete a document and its embeddings."""
        try:
            document = db.query(Document).filter(
                Document.id == document_id,
                Document.company_id == company_id
            ).first()
            
            if not document:
                raise ValueError("Document not found")
            
            # Delete from vector store
            self.vector_store.delete_document(company_id, document_id)
            
            # Delete file
            if os.path.exists(document.file_path):
                os.remove(document.file_path)
            
            # Delete from database
            db.delete(document)
            db.commit()
            
            logger.info(f"Document {document_id} deleted successfully")
            
        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}")
            raise