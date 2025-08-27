from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from models.database import get_db, User, Case, Document
from models.schemas import CaseCreate, CaseUpdate, Case as CaseSchema
from services.auth import get_current_active_user

router = APIRouter(prefix="/cases", tags=["case management"])

@router.post("/", response_model=CaseSchema)
async def create_case(
    case: CaseCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new legal case."""
    try:
        # Check if case number already exists for this user
        existing_case = db.query(Case).filter(
            Case.case_number == case.case_number,
            Case.user_id == current_user.id
        ).first()
        
        if existing_case:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Case number already exists for this user"
            )
        
        # Create new case
        db_case = Case(
            case_number=case.case_number,
            title=case.title,
            description=case.description,
            case_type=case.case_type,
            status=case.status,
            user_id=current_user.id
        )
        
        db.add(db_case)
        db.commit()
        db.refresh(db_case)
        
        return db_case
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating case: {str(e)}"
        )

@router.get("/", response_model=List[CaseSchema])
async def get_user_cases(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = None,
    case_type_filter: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all cases for the current user with optional filtering."""
    try:
        query = db.query(Case).filter(Case.user_id == current_user.id)
        
        # Apply filters
        if status_filter:
            query = query.filter(Case.status == status_filter)
        
        if case_type_filter:
            query = query.filter(Case.case_type == case_type_filter)
        
        # Order by creation date (newest first)
        cases = query.order_by(Case.created_at.desc()).offset(skip).limit(limit).all()
        
        return cases
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting cases: {str(e)}"
        )

@router.get("/{case_id}", response_model=CaseSchema)
async def get_case(
    case_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific case by ID."""
    try:
        case = db.query(Case).filter(
            Case.id == case_id,
            Case.user_id == current_user.id
        ).first()
        
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Case not found or access denied"
            )
        
        return case
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting case: {str(e)}"
        )

@router.put("/{case_id}", response_model=CaseSchema)
async def update_case(
    case_id: int,
    case_update: CaseUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a case."""
    try:
        case = db.query(Case).filter(
            Case.id == case_id,
            Case.user_id == current_user.id
        ).first()
        
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Case not found or access denied"
            )
        
        # Update fields
        if case_update.title is not None:
            case.title = case_update.title
        if case_update.description is not None:
            case.description = case_update.description
        if case_update.case_type is not None:
            case.case_type = case_update.case_type
        if case_update.status is not None:
            case.status = case_update.status
        
        db.commit()
        db.refresh(case)
        
        return case
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating case: {str(e)}"
        )

@router.delete("/{case_id}")
async def delete_case(
    case_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a case and all associated documents."""
    try:
        case = db.query(Case).filter(
            Case.id == case_id,
            Case.user_id == current_user.id
        ).first()
        
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Case not found or access denied"
            )
        
        # Delete associated documents first
        documents = db.query(Document).filter(Document.case_id == case_id).all()
        for doc in documents:
            db.delete(doc)
        
        # Delete the case
        db.delete(case)
        db.commit()
        
        return {"message": f"Case '{case.title}' and {len(documents)} documents deleted successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting case: {str(e)}"
        )

@router.get("/{case_id}/documents")
async def get_case_documents(
    case_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all documents associated with a specific case."""
    try:
        # Verify case ownership
        case = db.query(Case).filter(
            Case.id == case_id,
            Case.user_id == current_user.id
        ).first()
        
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Case not found or access denied"
            )
        
        # Get documents
        documents = db.query(Document).filter(Document.case_id == case_id).order_by(Document.created_at.desc()).all()
        
        return {
            "case": {
                "id": case.id,
                "title": case.title,
                "case_number": case.case_number
            },
            "documents": [
                {
                    "id": doc.id,
                    "title": doc.title,
                    "document_type": doc.document_type,
                    "created_at": doc.created_at,
                    "content_length": len(doc.content)
                }
                for doc in documents
            ],
            "total_documents": len(documents)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting case documents: {str(e)}"
        )

@router.get("/{case_id}/summary")
async def get_case_summary(
    case_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a summary of a case including key information."""
    try:
        # Get case with documents
        case = db.query(Case).filter(
            Case.id == case_id,
            Case.user_id == current_user.id
        ).first()
        
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Case not found or access denied"
            )
        
        # Get document count and types
        documents = db.query(Document).filter(Document.case_id == case_id).all()
        
        document_types = {}
        for doc in documents:
            doc_type = doc.document_type
            document_types[doc_type] = document_types.get(doc_type, 0) + 1
        
        # Calculate case age
        from datetime import datetime
        case_age = (datetime.utcnow() - case.created_at).days
        
        return {
            "case_info": {
                "id": case.id,
                "case_number": case.case_number,
                "title": case.title,
                "case_type": case.case_type,
                "status": case.status,
                "created_at": case.created_at,
                "updated_at": case.updated_at,
                "age_days": case_age
            },
            "documents": {
                "total_count": len(documents),
                "by_type": document_types,
                "recent_documents": [
                    {
                        "id": doc.id,
                        "title": doc.title,
                        "type": doc.document_type,
                        "created_at": doc.created_at
                    }
                    for doc in sorted(documents, key=lambda x: x.created_at, reverse=True)[:5]
                ]
            },
            "case_status": {
                "is_active": case.status == "active",
                "has_documents": len(documents) > 0,
                "last_activity": case.updated_at
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting case summary: {str(e)}"
        )

@router.post("/{case_id}/change-status")
async def change_case_status(
    case_id: int,
    new_status: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Change the status of a case."""
    try:
        # Validate status
        valid_statuses = ["active", "pending", "closed", "archived"]
        if new_status not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )
        
        # Get case
        case = db.query(Case).filter(
            Case.id == case_id,
            Case.user_id == current_user.id
        ).first()
        
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Case not found or access denied"
            )
        
        # Update status
        old_status = case.status
        case.status = new_status
        db.commit()
        
        return {
            "message": f"Case status changed from '{old_status}' to '{new_status}'",
            "case_id": case_id,
            "old_status": old_status,
            "new_status": new_status
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error changing case status: {str(e)}"
        )

@router.get("/statistics/summary")
async def get_cases_statistics(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get summary statistics for user's cases."""
    try:
        # Get all user cases
        cases = db.query(Case).filter(Case.user_id == current_user.id).all()
        
        if not cases:
            return {
                "total_cases": 0,
                "message": "No cases found"
            }
        
        # Calculate statistics
        total_cases = len(cases)
        status_counts = {}
        type_counts = {}
        
        for case in cases:
            # Status counts
            status_counts[case.status] = status_counts.get(case.status, 0) + 1
            
            # Type counts
            type_counts[case.case_type] = type_counts.get(case.case_type, 0) + 1
        
        # Get recent activity
        from datetime import datetime, timedelta
        recent_cases = [case for case in cases if case.updated_at > datetime.utcnow() - timedelta(days=30)]
        
        return {
            "total_cases": total_cases,
            "status_distribution": status_counts,
            "type_distribution": type_counts,
            "recent_activity": {
                "cases_updated_last_30_days": len(recent_cases),
                "active_cases": status_counts.get("active", 0),
                "pending_cases": status_counts.get("pending", 0)
            },
            "case_types": list(type_counts.keys())
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting case statistics: {str(e)}"
        )