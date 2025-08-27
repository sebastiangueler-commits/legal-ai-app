from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# User schemas
class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: str

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = None

class User(UserBase):
    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# Authentication schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

# Case schemas
class CaseBase(BaseModel):
    case_number: str
    title: str
    description: str
    case_type: str
    status: str

class CaseCreate(CaseBase):
    pass

class CaseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    case_type: Optional[str] = None
    status: Optional[str] = None

class Case(CaseBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Document schemas
class DocumentBase(BaseModel):
    title: str
    document_type: str
    content: str

class DocumentCreate(DocumentBase):
    case_id: int

class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    document_type: Optional[str] = None
    content: Optional[str] = None

class Document(DocumentBase):
    id: int
    case_id: int
    user_id: int
    file_path: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# Legal Document schemas
class LegalDocumentBase(BaseModel):
    tribunal: str
    fecha: datetime
    materia: str
    partes: str
    expediente: str
    full_text: str
    url: str

class LegalDocumentCreate(LegalDocumentBase):
    pass

class LegalDocument(LegalDocumentBase):
    id: int
    embedding_vector: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# Prediction schemas
class PredictionBase(BaseModel):
    predicted_outcome: str
    confidence_score: float
    similar_cases: str
    explanation: str

class PredictionCreate(PredictionBase):
    case_id: int

class Prediction(PredictionBase):
    id: int
    case_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Template schemas
class TemplateBase(BaseModel):
    name: str
    document_type: str
    content: str
    structure: str

class TemplateCreate(TemplateBase):
    pass

class Template(TemplateBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Search schemas
class SearchQuery(BaseModel):
    query: str
    tribunal: Optional[str] = None
    materia: Optional[str] = None
    fecha_desde: Optional[datetime] = None
    fecha_hasta: Optional[datetime] = None
    limit: int = 10

class SearchResult(BaseModel):
    legal_document: LegalDocument
    similarity_score: float

# Document generation schemas
class DocumentGenerationRequest(BaseModel):
    case_id: int
    document_type: str
    template_name: str
    case_details: dict

class DocumentGenerationResponse(BaseModel):
    generated_document: str
    template_used: str
    citations: List[str]

# Analysis schemas
class CaseAnalysisRequest(BaseModel):
    case_description: str
    case_type: str
    relevant_facts: List[str]

class CaseAnalysisResponse(BaseModel):
    predicted_outcome: str
    confidence_score: float
    similar_cases: List[LegalDocument]
    explanation: str
    recommendations: List[str]