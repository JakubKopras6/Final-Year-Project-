import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Optional
import logging
from app.config import settings

logger = logging.getLogger(__name__)


class VectorStoreService:
    """Manage document embeddings in ChromaDB with multi-tenant isolation."""
    
    def __init__(self):
        """Initialize ChromaDB client."""
        self.client = chromadb.PersistentClient(
            path=settings.CHROMA_DB_DIR,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        logger.info("ChromaDB client initialized")
    
    def _get_collection_name(self, company_id: int) -> str:
        """Generate collection name for a company."""
        return f"company_{company_id}_documents"
    
    def create_collection(self, company_id: int):
        """
        Create a collection for a company.
        
        Args:
            company_id: Company identifier
        """
        try:
            collection_name = self._get_collection_name(company_id)
            self.client.get_or_create_collection(
                name=collection_name,
                metadata={"company_id": company_id}
            )
            logger.info(f"Collection created for company {company_id}")
        except Exception as e:
            logger.error(f"Error creating collection: {str(e)}")
            raise
    
    def add_documents(
        self,
        company_id: int,
        document_id: int,
        chunks: List[Dict],
        embeddings: List[List[float]]
    ):
        """
        Add document chunks and embeddings to vector store.
        
        Args:
            company_id: Company identifier
            document_id: Document identifier
            chunks: List of chunk dictionaries with text and metadata
            embeddings: List of embedding vectors
        """
        try:
            collection_name = self._get_collection_name(company_id)
            collection = self.client.get_or_create_collection(collection_name)
            
            # Prepare data for ChromaDB
            ids = [f"doc_{document_id}_chunk_{chunk['chunk_index']}" for chunk in chunks]
            documents = [chunk['text'] for chunk in chunks]
            metadatas = [
                {
                    "document_id": str(document_id),
                    "chunk_index": chunk['chunk_index'],
                    "page_number": str(chunk.get('page_number', 'unknown')),
                    "char_count": chunk['char_count']
                }
                for chunk in chunks
            ]
            
            # Add to collection
            collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )
            
            logger.info(f"Added {len(chunks)} chunks for document {document_id} to company {company_id}")
            
        except Exception as e:
            logger.error(f"Error adding documents: {str(e)}")
            raise
    
    def search(
        self,
        company_id: int,
        query_embedding: List[float],
        top_k: int = None
    ) -> List[Dict]:
        """
        Search for similar documents.
        
        Args:
            company_id: Company identifier
            query_embedding: Query embedding vector
            top_k: Number of results to return
            
        Returns:
            List of search results with text, metadata, and scores
        """
        try:
            collection_name = self._get_collection_name(company_id)
            collection = self.client.get_collection(collection_name)
            
            k = top_k or settings.TOP_K_RETRIEVAL
            
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=k,
                include=["documents", "metadatas", "distances"]
            )
            
            # Format results
            search_results = []
            if results and results['ids'] and len(results['ids']) > 0:
                for i in range(len(results['ids'][0])):
                    search_results.append({
                        "text": results['documents'][0][i],
                        "metadata": results['metadatas'][0][i],
                        "score": 1 - results['distances'][0][i],  # Convert distance to similarity
                        "document_id": int(results['metadatas'][0][i]['document_id']),
                        "page_number": results['metadatas'][0][i].get('page_number', 'unknown')
                    })
            
            logger.info(f"Retrieved {len(search_results)} results for company {company_id}")
            return search_results
            
        except Exception as e:
            logger.error(f"Error searching documents: {str(e)}")
            raise
    
    def delete_document(self, company_id: int, document_id: int):
        """
        Delete all chunks of a document.
        
        Args:
            company_id: Company identifier
            document_id: Document identifier
        """
        try:
            collection_name = self._get_collection_name(company_id)
            collection = self.client.get_collection(collection_name)
            
            # Query all chunks for this document
            results = collection.get(
                where={"document_id": str(document_id)}
            )
            
            if results and results['ids']:
                collection.delete(ids=results['ids'])
                logger.info(f"Deleted document {document_id} from company {company_id}")
                
        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}")
            raise
    
    def get_collection_count(self, company_id: int) -> int:
        """Get number of documents in company collection."""
        try:
            collection_name = self._get_collection_name(company_id)
            collection = self.client.get_collection(collection_name)
            return collection.count()
        except:
            return 0