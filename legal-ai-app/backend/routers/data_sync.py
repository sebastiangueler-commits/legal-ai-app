from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import json
from datetime import datetime

from models.database import get_db, User, LegalDocument, Template
from services.auth import get_current_active_user, get_current_superuser
from services.google_drive import google_drive_service
from services.embeddings import embeddings_service
from services.classifier import classifier_service
from config import settings

router = APIRouter(prefix="/data-sync", tags=["data synchronization"])

@router.post("/sync-legal-documents")
async def sync_legal_documents(
    file_id: str,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """Synchronize legal documents from Google Drive JSON file."""
    try:
        print(f"Starting legal documents synchronization from file ID: {file_id}")
        
        # Download and parse legal documents
        documents = google_drive_service.download_legal_documents(file_id)
        
        if not documents:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No documents found in the specified file"
            )
        
        print(f"Downloaded {len(documents)} legal documents")
        
        # Process and store documents
        processed_count = 0
        for doc in documents:
            try:
                # Check if document already exists
                existing_doc = db.query(LegalDocument).filter(
                    LegalDocument.expediente == doc.get('expediente', ''),
                    LegalDocument.tribunal == doc.get('tribunal', '')
                ).first()
                
                if not existing_doc:
                    # Create new legal document
                    legal_doc = LegalDocument(
                        tribunal=doc.get('tribunal', ''),
                        fecha=datetime.fromisoformat(doc.get('fecha', '')) if doc.get('fecha') else datetime.now(),
                        materia=doc.get('materia', ''),
                        partes=doc.get('partes', ''),
                        expediente=doc.get('expediente', ''),
                        full_text=doc.get('full_text', ''),
                        url=doc.get('url', '')
                    )
                    
                    db.add(legal_doc)
                    processed_count += 1
                
            except Exception as e:
                print(f"Error processing document {doc.get('expediente', 'unknown')}: {e}")
                continue
        
        # Commit to database
        db.commit()
        print(f"Successfully processed {processed_count} new legal documents")
        
        # Update embeddings index
        print("Updating embeddings index...")
        embeddings_service.update_index(documents)
        
        return {
            "message": f"Legal documents synchronization completed",
            "total_downloaded": len(documents),
            "new_documents_added": processed_count,
            "embeddings_updated": True
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during legal documents synchronization: {str(e)}"
        )

@router.post("/sync-templates")
async def sync_templates(
    folder_id: str,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """Synchronize document templates from Google Drive folder."""
    try:
        print(f"Starting templates synchronization from folder ID: {folder_id}")
        
        # Download and parse templates
        templates = google_drive_service.download_templates(folder_id)
        
        if not templates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No templates found in the specified folder"
            )
        
        print(f"Downloaded {len(templates)} templates")
        
        # Load templates into document generator
        document_generator.load_templates(templates)
        
        # Store templates in database
        processed_count = 0
        for template in templates:
            try:
                # Check if template already exists
                existing_template = db.query(Template).filter(
                    Template.name == template['name']
                ).first()
                
                if not existing_template:
                    # Create new template
                    db_template = Template(
                        name=template['name'],
                        document_type=template.get('document_type', 'general'),
                        content=template['content'],
                        structure=json.dumps(document_generator.templates[template['name']]['structure'])
                    )
                    
                    db.add(db_template)
                    processed_count += 1
                
            except Exception as e:
                print(f"Error processing template {template['name']}: {e}")
                continue
        
        # Commit to database
        db.commit()
        print(f"Successfully processed {processed_count} new templates")
        
        return {
            "message": f"Templates synchronization completed",
            "total_downloaded": len(templates),
            "new_templates_added": processed_count,
            "templates_loaded": len(document_generator.templates)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during templates synchronization: {str(e)}"
        )

@router.post("/train-models")
async def train_ml_models(
    current_user: User = Depends(get_current_superuser)
):
    """Train the ML models with current data."""
    try:
        if not embeddings_service.documents:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No documents available for training. Please sync data first."
            )
        
        print("Starting ML model training...")
        
        # Train classifier
        training_success = classifier_service.train_classifier(embeddings_service.documents)
        
        if not training_success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to train classifier"
            )
        
        print("ML model training completed successfully")
        
        return {
            "message": "ML models trained successfully",
            "classifier_trained": True,
            "total_training_documents": len(embeddings_service.documents),
            "search_index_available": embeddings_service.faiss_index is not None
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during model training: {str(e)}"
        )

@router.get("/sync-status")
async def get_sync_status(
    current_user: User = Depends(get_current_active_user)
):
    """Get the current synchronization status."""
    try:
        return {
            "legal_documents": {
                "total_indexed": len(embeddings_service.documents) if embeddings_service.documents else 0,
                "search_index_available": embeddings_service.faiss_index is not None,
                "last_sync": "N/A"  # Could be enhanced with timestamp tracking
            },
            "templates": {
                "total_loaded": len(document_generator.templates),
                "types_available": list(set(t['document_type'] for t in document_generator.templates.values()))
            },
            "ml_models": {
                "classifier_trained": classifier_service.is_trained,
                "embeddings_available": embeddings_service.faiss_index is not None,
                "search_capability": embeddings_service.faiss_index is not None
            },
            "google_drive": {
                "service_available": google_drive_service.service is not None,
                "authentication_status": "Authenticated" if google_drive_service.service else "Not authenticated"
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting sync status: {str(e)}"
        )

@router.post("/reindex-documents")
async def reindex_documents(
    current_user: User = Depends(get_current_superuser)
):
    """Rebuild the search index from scratch."""
    try:
        if not embeddings_service.documents:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No documents available for indexing"
            )
        
        print("Starting document reindexing...")
        
        # Create new embeddings
        embeddings = embeddings_service.create_embeddings(embeddings_service.documents)
        
        # Build new FAISS index
        embeddings_service.build_faiss_index(embeddings)
        
        print("Document reindexing completed successfully")
        
        return {
            "message": "Documents reindexed successfully",
            "total_documents_indexed": len(embeddings_service.documents),
            "search_index_rebuilt": True,
            "embeddings_created": embeddings.shape
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during document reindexing: {str(e)}"
        )

@router.get("/document-statistics")
async def get_document_statistics(
    current_user: User = Depends(get_current_active_user)
):
    """Get statistics about the indexed documents."""
    try:
        if not embeddings_service.documents:
            return {
                "message": "No documents indexed",
                "total_documents": 0
            }
        
        # Analyze documents
        tribunals = {}
        materias = {}
        years = {}
        text_lengths = []
        
        for doc in embeddings_service.documents:
            # Tribunal distribution
            tribunal = doc.get('tribunal', 'Unknown')
            tribunals[tribunal] = tribunals.get(tribunal, 0) + 1
            
            # Materia distribution
            materia = doc.get('materia', 'Unknown')
            materias[materia] = materias.get(materia, 0) + 1
            
            # Year distribution
            try:
                year = datetime.fromisoformat(doc.get('fecha', '')).year
                years[year] = years.get(year, 0) + 1
            except:
                pass
            
            # Text length
            text_lengths.append(len(doc.get('full_text', '')))
        
        # Calculate statistics
        avg_text_length = sum(text_lengths) / len(text_lengths) if text_lengths else 0
        
        return {
            "total_documents": len(embeddings_service.documents),
            "tribunal_distribution": dict(sorted(tribunals.items(), key=lambda x: x[1], reverse=True)[:10]),
            "materia_distribution": dict(sorted(materias.items(), key=lambda x: x[1], reverse=True)[:10]),
            "year_distribution": dict(sorted(years.items(), key=lambda x: x[1], reverse=True)[:10]),
            "text_statistics": {
                "average_length": round(avg_text_length, 2),
                "total_text_length": sum(text_lengths),
                "shortest_document": min(text_lengths) if text_lengths else 0,
                "longest_document": max(text_lengths) if text_lengths else 0
            },
            "index_status": {
                "faiss_index_available": embeddings_service.faiss_index is not None,
                "embeddings_created": len(embeddings_service.embeddings) if embeddings_service.embeddings else 0
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting document statistics: {str(e)}"
        )

@router.post("/validate-data")
async def validate_synced_data(
    current_user: User = Depends(get_current_superuser)
):
    """Validate the quality and consistency of synced data."""
    try:
        if not embeddings_service.documents:
            return {
                "message": "No documents to validate",
                "validation_passed": False
            }
        
        print("Starting data validation...")
        
        validation_results = {
            "total_documents": len(embeddings_service.documents),
            "validation_errors": [],
            "warnings": [],
            "passed_validation": True
        }
        
        # Validate document structure
        for i, doc in enumerate(embeddings_service.documents):
            # Check required fields
            required_fields = ['tribunal', 'fecha', 'materia', 'partes', 'expediente', 'full_text']
            missing_fields = [field for field in required_fields if not doc.get(field)]
            
            if missing_fields:
                validation_results["validation_errors"].append({
                    "document_index": i,
                    "expediente": doc.get('expediente', 'Unknown'),
                    "missing_fields": missing_fields
                })
                validation_results["passed_validation"] = False
            
            # Check text length
            text_length = len(doc.get('full_text', ''))
            if text_length < 100:
                validation_results["warnings"].append({
                    "document_index": i,
                    "expediente": doc.get('expediente', 'Unknown'),
                    "warning": f"Very short text ({text_length} characters)"
                })
            
            # Check date format
            try:
                datetime.fromisoformat(doc.get('fecha', ''))
            except:
                validation_results["validation_errors"].append({
                    "document_index": i,
                    "expediente": doc.get('expediente', 'Unknown'),
                    "error": "Invalid date format"
                })
                validation_results["passed_validation"] = False
        
        # Check embeddings consistency
        if embeddings_service.embeddings is not None:
            if len(embeddings_service.embeddings) != len(embeddings_service.documents):
                validation_results["validation_errors"].append({
                    "error": "Mismatch between documents and embeddings count",
                    "documents_count": len(embeddings_service.documents),
                    "embeddings_count": len(embeddings_service.embeddings)
                })
                validation_results["passed_validation"] = False
        
        print(f"Data validation completed. Passed: {validation_results['passed_validation']}")
        
        return validation_results
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during data validation: {str(e)}"
        )