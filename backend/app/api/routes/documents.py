from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.schemas import DocumentUploadResponse, DocumentResponse, DocumentListResponse
from app.services.document_service import DocumentService
from app.api.dependencies import get_current_user, get_current_admin_user
from app.models.database import User

router = APIRouter(prefix="/documents", tags=["Documents"])
document_service = DocumentService()


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Upload a document (admin only).
    
    Uploads and processes a PDF document, extracting text and generating embeddings.
    """
    try:
        document = await document_service.upload_document(
            file=file,
            company_id=current_user.company_id,
            user_id=current_user.id,
            db=db
        )
        return DocumentUploadResponse.from_orm(document)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document upload failed: {str(e)}"
        )


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all documents for the user's company.
    
    Returns all documents uploaded by the company.
    """
    try:
        documents = document_service.get_company_documents(
            company_id=current_user.company_id,
            db=db
        )
        return DocumentListResponse(
            documents=[DocumentResponse.from_orm(doc) for doc in documents],
            total=len(documents)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve documents"
        )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Delete a document (admin only).
    
    Removes document from database and vector store.
    """
    try:
        document_service.delete_document(
            document_id=document_id,
            company_id=current_user.company_id,
            db=db
        )
        return {"message": "Document deleted successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document"
        )