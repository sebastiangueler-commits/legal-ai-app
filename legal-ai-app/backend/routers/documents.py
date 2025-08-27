from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
import json

from models.database import get_db, User, Case, Document, Template
from models.schemas import (
    DocumentGenerationRequest, DocumentGenerationResponse, DocumentCreate, 
    Document as DocumentSchema, TemplateCreate, Template as TemplateSchema
)
from services.auth import get_current_active_user
from services.document_generator import document_generator

router = APIRouter(prefix="/documents", tags=["document generation"])

@router.post("/generate", response_model=DocumentGenerationResponse)
async def generate_legal_document(
    request: DocumentGenerationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Generate a legal document using templates and AI."""
    try:
        # Verify case exists and belongs to user
        case = db.query(Case).filter(
            Case.id == request.case_id,
            Case.user_id == current_user.id
        ).first()
        
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Case not found or access denied"
            )
        
        # Generate document
        generated_doc = document_generator.generate_document(
            request.template_name,
            request.case_details,
            request.case_id
        )
        
        # Save generated document to database
        db_document = Document(
            title=f"{request.document_type} - {case.title}",
            document_type=request.document_type,
            content=generated_doc['generated_document'],
            case_id=request.case_id,
            user_id=current_user.id
        )
        
        db.add(db_document)
        db.commit()
        db.refresh(db_document)
        
        return DocumentGenerationResponse(
            generated_document=generated_doc['generated_document'],
            template_used=generated_doc['template_used'],
            citations=generated_doc['citations']
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating document: {str(e)}"
        )

@router.get("/templates", response_model=List[TemplateSchema])
async def get_available_templates(
    current_user: User = Depends(get_current_active_user)
):
    """Get list of available document templates."""
    try:
        templates = document_generator.get_available_templates()
        return templates
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting templates: {str(e)}"
        )

@router.post("/templates", response_model=TemplateSchema)
async def create_custom_template(
    template: TemplateCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a custom document template."""
    try:
        # Check if template name already exists
        existing_template = db.query(Template).filter(Template.name == template.name).first()
        if existing_template:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Template name already exists"
            )
        
        # Create template in document generator
        success = document_generator.create_custom_template(
            template.name,
            template.content,
            template.document_type
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create template"
            )
        
        # Save to database
        db_template = Template(
            name=template.name,
            document_type=template.document_type,
            content=template.content,
            structure=json.dumps(document_generator.templates[template.name]['structure'])
        )
        
        db.add(db_template)
        db.commit()
        db.refresh(db_template)
        
        return db_template
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating template: {str(e)}"
        )

@router.get("/templates/{template_name}")
async def get_template_details(
    template_name: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get detailed information about a specific template."""
    try:
        if template_name not in document_generator.templates:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )
        
        template = document_generator.templates[template_name]
        return {
            'name': template_name,
            'document_type': template['document_type'],
            'structure': template['structure'],
            'placeholders': template['structure']['placeholders'],
            'sections': template['structure']['sections']
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting template details: {str(e)}"
        )

@router.post("/upload-template")
async def upload_template_file(
    file: UploadFile = File(...),
    template_name: str = None,
    document_type: str = None,
    current_user: User = Depends(get_current_active_user)
):
    """Upload a template file (PDF, DOC, TXT)."""
    try:
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No file provided"
            )
        
        # Read file content
        content = await file.read()
        
        # Extract text based on file type
        if file.filename.endswith('.txt'):
            text_content = content.decode('utf-8')
        elif file.filename.endswith('.pdf'):
            # Use PyMuPDF to extract text
            import fitz
            doc = fitz.open(stream=content, filetype="pdf")
            text_content = ""
            for page in doc:
                text_content += page.get_text()
            doc.close()
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported file type. Use PDF or TXT files."
            )
        
        # Use filename as template name if not provided
        if not template_name:
            template_name = file.filename.rsplit('.', 1)[0]
        
        if not document_type:
            document_type = "general"
        
        # Create template
        success = document_generator.create_custom_template(
            template_name,
            text_content,
            document_type
        )
        
        if success:
            return {
                "message": f"Template '{template_name}' created successfully",
                "template_name": template_name,
                "document_type": document_type,
                "content_length": len(text_content)
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create template"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading template: {str(e)}"
        )

@router.post("/summarize")
async def summarize_document(
    document_content: str,
    summary_type: str = "technical",  # "technical" or "citizen"
    current_user: User = Depends(get_current_active_user)
):
    """Generate a summary of a legal document."""
    try:
        if summary_type not in ["technical", "citizen"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Summary type must be 'technical' or 'citizen'"
            )
        
        summary = document_generator.generate_summary(document_content, summary_type)
        
        return {
            "summary": summary,
            "summary_type": summary_type,
            "original_length": len(document_content),
            "summary_length": len(summary)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating summary: {str(e)}"
        )

@router.get("/user-documents", response_model=List[DocumentSchema])
async def get_user_documents(
    skip: int = 0,
    limit: int = 100,
    case_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get documents created by the current user."""
    try:
        query = db.query(Document).filter(Document.user_id == current_user.id)
        
        if case_id:
            query = query.filter(Document.case_id == case_id)
        
        documents = query.offset(skip).limit(limit).all()
        return documents
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting user documents: {str(e)}"
        )

@router.get("/user-documents/{document_id}", response_model=DocumentSchema)
async def get_user_document(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific document by ID."""
    try:
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.user_id == current_user.id
        ).first()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found or access denied"
            )
        
        return document
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting document: {str(e)}"
        )

@router.put("/user-documents/{document_id}", response_model=DocumentSchema)
async def update_user_document(
    document_id: int,
    document_update: DocumentCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a user's document."""
    try:
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.user_id == current_user.id
        ).first()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found or access denied"
            )
        
        # Update fields
        document.title = document_update.title
        document.document_type = document_update.document_type
        document.content = document_update.content
        
        db.commit()
        db.refresh(document)
        
        return document
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating document: {str(e)}"
        )

@router.delete("/user-documents/{document_id}")
async def delete_user_document(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a user's document."""
    try:
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.user_id == current_user.id
        ).first()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found or access denied"
            )
        
        db.delete(document)
        db.commit()
        
        return {"message": "Document deleted successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting document: {str(e)}"
        )

@router.post("/analyze-structure")
async def analyze_document_structure(
    document_content: str,
    current_user: User = Depends(get_current_active_user)
):
    """Analyze the structure of a legal document."""
    try:
        structure = document_generator._analyze_template_structure(document_content)
        
        return {
            "document_length": len(document_content),
            "structure": structure,
            "sections_found": len(structure['sections']),
            "placeholders_found": len(structure['placeholders'])
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing document structure: {str(e)}"
        )

@router.get("/generation-status")
async def get_generation_status(current_user: User = Depends(get_current_active_user)):
    """Get the status of document generation services."""
    try:
        return {
            "ai_services_available": {
                "openai": document_generator.openai_client is not None,
                "anthropic": document_generator.anthropic_client is not None
            },
            "templates_loaded": len(document_generator.templates),
            "template_types": list(set(t['document_type'] for t in document_generator.templates.values())),
            "generation_capabilities": {
                "ai_enhancement": document_generator.openai_client is not None or document_generator.anthropic_client is not None,
                "template_filling": True,
                "citation_integration": True
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting generation status: {str(e)}"
        )