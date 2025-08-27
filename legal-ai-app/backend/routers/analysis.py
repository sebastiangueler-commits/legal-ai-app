from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from models.database import get_db, User, Case, Prediction
from models.schemas import (
    CaseAnalysisRequest, CaseAnalysisResponse, PredictionCreate, Prediction as PredictionSchema
)
from services.auth import get_current_active_user
from services.classifier import classifier_service
from services.embeddings import embeddings_service

router = APIRouter(prefix="/analysis", tags=["case analysis"])

@router.post("/predict", response_model=CaseAnalysisResponse)
async def predict_case_outcome(
    request: CaseAnalysisRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Predict the outcome of a legal case."""
    try:
        # Check if classifier is trained
        if not classifier_service.is_trained:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Legal classifier not trained. Please wait for training to complete."
            )
        
        # Get prediction and explanation
        analysis_result = classifier_service.explain_prediction(
            request.case_description,
            request.case_type
        )
        
        # Save prediction to database if case_id is provided
        if hasattr(request, 'case_id') and request.case_id:
            prediction = Prediction(
                case_id=request.case_id,
                predicted_outcome=analysis_result['prediction']['predicted_outcome'],
                confidence_score=analysis_result['prediction']['confidence_score'],
                similar_cases=analysis_result['similar_cases'],
                explanation=analysis_result['explanation']
            )
            db.add(prediction)
            db.commit()
        
        return CaseAnalysisResponse(
            predicted_outcome=analysis_result['prediction']['predicted_outcome'],
            confidence_score=analysis_result['prediction']['confidence_score'],
            similar_cases=analysis_result['similar_cases'],
            explanation=analysis_result['explanation'],
            recommendations=self._generate_recommendations(analysis_result)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during case analysis: {str(e)}"
        )

@router.get("/similar-cases")
async def find_similar_cases(
    query: str,
    limit: int = 10,
    current_user: User = Depends(get_current_active_user)
):
    """Find similar legal cases based on a query."""
    try:
        if not embeddings_service.faiss_index:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Search index not available. Please wait for indexing to complete."
            )
        
        similar_cases = classifier_service.get_similar_cases(query, limit)
        return {
            "query": query,
            "similar_cases": similar_cases,
            "total_found": len(similar_cases)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error finding similar cases: {str(e)}"
        )

@router.get("/predictions", response_model=List[PredictionSchema])
async def get_user_predictions(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get predictions made by the current user."""
    predictions = db.query(Prediction).join(Case).filter(Case.user_id == current_user.id).offset(skip).limit(limit).all()
    return predictions

@router.get("/predictions/{prediction_id}", response_model=PredictionSchema)
async def get_prediction(
    prediction_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific prediction by ID."""
    prediction = db.query(Prediction).join(Case).filter(
        Prediction.id == prediction_id,
        Case.user_id == current_user.id
    ).first()
    
    if not prediction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prediction not found"
        )
    
    return prediction

@router.delete("/predictions/{prediction_id}")
async def delete_prediction(
    prediction_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a prediction."""
    prediction = db.query(Prediction).join(Case).filter(
        Prediction.id == prediction_id,
        Case.user_id == current_user.id
    ).first()
    
    if not prediction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prediction not found"
        )
    
    db.delete(prediction)
    db.commit()
    
    return {"message": "Prediction deleted successfully"}

@router.get("/model-status")
async def get_model_status(current_user: User = Depends(get_current_active_user)):
    """Get the status of the ML models."""
    return {
        "classifier_trained": classifier_service.is_trained,
        "search_index_available": embeddings_service.faiss_index is not None,
        "total_documents_indexed": len(embeddings_service.documents) if embeddings_service.documents else 0,
        "available_outcome_classes": list(classifier_service.label_encoder.classes_) if classifier_service.is_trained else []
    }

@router.post("/train-model")
async def train_legal_classifier(
    current_user: User = Depends(get_current_active_user)
):
    """Trigger training of the legal classifier (admin only)."""
    # Check if user is admin
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can trigger model training"
        )
    
    try:
        # Check if we have documents to train on
        if not embeddings_service.documents:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No documents available for training. Please index documents first."
            )
        
        # Train the classifier
        success = classifier_service.train_classifier(embeddings_service.documents)
        
        if success:
            return {"message": "Legal classifier trained successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to train classifier"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error training classifier: {str(e)}"
        )

@router.get("/model-performance")
async def get_model_performance(
    current_user: User = Depends(get_current_active_user)
):
    """Get model performance metrics (admin only)."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can view model performance"
        )
    
    try:
        if not classifier_service.is_trained:
            return {"message": "Model not trained yet"}
        
        # Use a subset of documents for evaluation
        test_docs = embeddings_service.documents[-100:] if len(embeddings_service.documents) > 100 else embeddings_service.documents
        
        performance = classifier_service.evaluate_model(test_docs)
        return performance
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting model performance: {str(e)}"
        )

def _generate_recommendations(analysis_result: dict) -> List[str]:
    """Generate recommendations based on analysis results."""
    recommendations = []
    
    confidence = analysis_result['prediction']['confidence_score']
    outcome = analysis_result['prediction']['predicted_outcome']
    
    if confidence < 0.6:
        recommendations.append("Considera consultar con un abogado especializado debido a la baja confianza en la predicción.")
    
    if outcome == "condena":
        recommendations.append("El caso muestra tendencias hacia una condena. Revisa cuidadosamente la evidencia y argumentos de defensa.")
    elif outcome == "absolución":
        recommendations.append("El caso muestra tendencias hacia una absolución. Mantén la estrategia de defensa actual.")
    elif outcome == "rechazo":
        recommendations.append("El caso muestra tendencias hacia un rechazo. Considera revisar la fundamentación legal.")
    
    if analysis_result['similar_cases']:
        recommendations.append(f"Revisa los {len(analysis_result['similar_cases'])} casos similares encontrados para entender mejor el precedente.")
    
    return recommendations