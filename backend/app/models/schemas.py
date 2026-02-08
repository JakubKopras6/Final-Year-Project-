from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from app.models.database import UserRole


# ============ Auth Schemas ============
class CompanyCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)


class CompanyResponse(BaseModel):
    id: int
    name: str
    created_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2, max_length=255)
    role: UserRole = UserRole.EMPLOYEE


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2, max_length=255)
    company_name: str = Field(..., min_length=2, max_length=255)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: UserRole
    company_id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[int] = None
    email: Optional[str] = None
    company_id: Optional[int] = None
    role: Optional[str] = None


# ============ Document Schemas ============
class DocumentUploadResponse(BaseModel):
    id: int
    filename: str
    original_filename: str
    file_size: int
    uploaded_at: datetime
    processed: bool
    
    class Config:
        from_attributes = True


class DocumentResponse(BaseModel):
    id: int
    filename: str
    original_filename: str
    file_size: int
    page_count: Optional[int]
    uploaded_at: datetime
    processed: bool
    processed_at: Optional[datetime]
    chunk_count: int
    
    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    documents: List[DocumentResponse]
    total: int


# ============ Chat Schemas ============
class ChatQuery(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)


class Source(BaseModel):
    document_id: int
    document_name: str
    page_number: Optional[int]
    chunk_text: str
    relevance_score: float


class ChatResponse(BaseModel):
    query: str
    response: str
    sources: List[Source]
    response_time: int  # milliseconds


class ChatHistoryItem(BaseModel):
    id: int
    query: str
    response: str
    created_at: datetime
    response_time: Optional[int]
    
    class Config:
        from_attributes = True


class ChatHistoryResponse(BaseModel):
    history: List[ChatHistoryItem]
    total: int


# ============ Admin Schemas ============
class UserListResponse(BaseModel):
    users: List[UserResponse]
    total: int


class SystemStats(BaseModel):
    total_documents: int
    total_queries: int
    total_users: int
    avg_response_time: Optional[float]