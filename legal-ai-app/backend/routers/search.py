from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from models.database import get_db, User, LegalDocument
from models.schemas import SearchQuery, SearchResult
from services.auth import get_current_active_user
from services.embeddings import embeddings_service

router = APIRouter(prefix="/search", tags=["legal search"])

@router.post("/query", response_model=List[SearchResult])
async def search_legal_documents(
    search_query: SearchQuery,
    current_user: User = Depends(get_current_active_user)
):
    """Search for legal documents using vector similarity and filters."""
    try:
        if not embeddings_service.faiss_index:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Search index not available. Please wait for indexing to complete."
            )
        
        # Perform vector search
        similar_indices = embeddings_service.search_similar_documents(
            search_query.query, 
            search_query.limit
        )
        
        # Filter results based on criteria
        filtered_results = []
        for idx, score in similar_indices:
            if idx < len(embeddings_service.documents):
                doc = embeddings_service.documents[idx]
                
                # Apply filters
                if search_query.tribunal and search_query.tribunal.lower() not in doc.get('tribunal', '').lower():
                    continue
                    
                if search_query.materia and search_query.materia.lower() not in doc.get('materia', '').lower():
                    continue
                
                if search_query.fecha_desde:
                    try:
                        doc_date = datetime.fromisoformat(doc.get('fecha', ''))
                        if doc_date < search_query.fecha_desde:
                            continue
                    except:
                        pass
                
                if search_query.fecha_hasta:
                    try:
                        doc_date = datetime.fromisoformat(doc.get('fecha', ''))
                        if doc_date > search_query.fecha_hasta:
                            continue
                    except:
                        pass
                
                # Create search result
                legal_doc = LegalDocument(
                    id=idx,
                    tribunal=doc.get('tribunal', ''),
                    fecha=datetime.fromisoformat(doc.get('fecha', '')) if doc.get('fecha') else datetime.now(),
                    materia=doc.get('materia', ''),
                    partes=doc.get('partes', ''),
                    expediente=doc.get('expediente', ''),
                    full_text=doc.get('full_text', ''),
                    url=doc.get('url', '')
                )
                
                result = SearchResult(
                    legal_document=legal_doc,
                    similarity_score=score
                )
                
                filtered_results.append(result)
        
        # Sort by similarity score
        filtered_results.sort(key=lambda x: x.similarity_score, reverse=True)
        
        return filtered_results[:search_query.limit]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during search: {str(e)}"
        )

@router.get("/semantic")
async def semantic_search(
    query: str = Query(..., description="Search query in natural language"),
    limit: int = Query(10, description="Maximum number of results"),
    current_user: User = Depends(get_current_active_user)
):
    """Semantic search for legal documents using natural language queries."""
    try:
        if not embeddings_service.faiss_index:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Search index not available. Please wait for indexing to complete."
            )
        
        # Perform semantic search
        similar_indices = embeddings_service.search_similar_documents(query, limit)
        
        results = []
        for idx, score in similar_indices:
            if idx < len(embeddings_service.documents):
                doc = embeddings_service.documents[idx]
                results.append({
                    'tribunal': doc.get('tribunal', ''),
                    'fecha': doc.get('fecha', ''),
                    'materia': doc.get('materia', ''),
                    'partes': doc.get('partes', ''),
                    'expediente': doc.get('expediente', ''),
                    'url': doc.get('url', ''),
                    'similarity_score': float(score),
                    'excerpt': doc.get('full_text', '')[:200] + '...' if len(doc.get('full_text', '')) > 200 else doc.get('full_text', '')
                })
        
        return {
            'query': query,
            'results': results,
            'total_found': len(results)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during semantic search: {str(e)}"
        )

@router.get("/by-tribunal")
async def search_by_tribunal(
    tribunal: str = Query(..., description="Tribunal name to search for"),
    limit: int = Query(20, description="Maximum number of results"),
    current_user: User = Depends(get_current_active_user)
):
    """Search for legal documents by specific tribunal."""
    try:
        if not embeddings_service.documents:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="No documents available for search."
            )
        
        results = []
        for doc in embeddings_service.documents:
            if tribunal.lower() in doc.get('tribunal', '').lower():
                results.append({
                    'tribunal': doc.get('tribunal', ''),
                    'fecha': doc.get('fecha', ''),
                    'materia': doc.get('materia', ''),
                    'partes': doc.get('partes', ''),
                    'expediente': doc.get('expediente', ''),
                    'url': doc.get('url', ''),
                    'excerpt': doc.get('full_text', '')[:200] + '...' if len(doc.get('full_text', '')) > 200 else doc.get('full_text', '')
                })
                
                if len(results) >= limit:
                    break
        
        return {
            'tribunal': tribunal,
            'results': results,
            'total_found': len(results)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching by tribunal: {str(e)}"
        )

@router.get("/by-materia")
async def search_by_materia(
    materia: str = Query(..., description="Legal matter to search for"),
    limit: int = Query(20, description="Maximum number of results"),
    current_user: User = Depends(get_current_active_user)
):
    """Search for legal documents by specific legal matter."""
    try:
        if not embeddings_service.documents:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="No documents available for search."
            )
        
        results = []
        for doc in embeddings_service.documents:
            if materia.lower() in doc.get('materia', '').lower():
                results.append({
                    'tribunal': doc.get('tribunal', ''),
                    'fecha': doc.get('fecha', ''),
                    'materia': doc.get('materia', ''),
                    'partes': doc.get('partes', ''),
                    'expediente': doc.get('expediente', ''),
                    'url': doc.get('url', ''),
                    'excerpt': doc.get('full_text', '')[:200] + '...' if len(doc.get('full_text', '')) > 200 else doc.get('full_text', '')
                })
                
                if len(results) >= limit:
                    break
        
        return {
            'materia': materia,
            'results': results,
            'total_found': len(results)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching by materia: {str(e)}"
        )

@router.get("/by-date-range")
async def search_by_date_range(
    fecha_desde: str = Query(..., description="Start date (YYYY-MM-DD)"),
    fecha_hasta: str = Query(..., description="End date (YYYY-MM-DD)"),
    limit: int = Query(20, description="Maximum number of results"),
    current_user: User = Depends(get_current_active_user)
):
    """Search for legal documents within a date range."""
    try:
        if not embeddings_service.documents:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="No documents available for search."
            )
        
        # Parse dates
        try:
            start_date = datetime.fromisoformat(fecha_desde)
            end_date = datetime.fromisoformat(fecha_hasta)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use YYYY-MM-DD"
            )
        
        results = []
        for doc in embeddings_service.documents:
            try:
                doc_date = datetime.fromisoformat(doc.get('fecha', ''))
                if start_date <= doc_date <= end_date:
                    results.append({
                        'tribunal': doc.get('tribunal', ''),
                        'fecha': doc.get('fecha', ''),
                        'materia': doc.get('materia', ''),
                        'partes': doc.get('partes', ''),
                        'expediente': doc.get('expediente', ''),
                        'url': doc.get('url', ''),
                        'excerpt': doc.get('full_text', '')[:200] + '...' if len(doc.get('full_text', '')) > 200 else doc.get('full_text', '')
                    })
                    
                    if len(results) >= limit:
                        break
            except:
                continue
        
        return {
            'fecha_desde': fecha_desde,
            'fecha_hasta': fecha_hasta,
            'results': results,
            'total_found': len(results)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching by date range: {str(e)}"
        )

@router.get("/advanced")
async def advanced_search(
    query: str = Query(..., description="Search query"),
    tribunal: Optional[str] = Query(None, description="Filter by tribunal"),
    materia: Optional[str] = Query(None, description="Filter by legal matter"),
    fecha_desde: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    fecha_hasta: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    min_similarity: float = Query(0.5, description="Minimum similarity score"),
    limit: int = Query(20, description="Maximum number of results"),
    current_user: User = Depends(get_current_active_user)
):
    """Advanced search with multiple filters and similarity threshold."""
    try:
        if not embeddings_service.faiss_index:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Search index not available. Please wait for indexing to complete."
            )
        
        # Perform vector search with higher limit for filtering
        search_limit = min(limit * 3, 100)  # Get more results for filtering
        similar_indices = embeddings_service.search_similar_documents(query, search_limit)
        
        # Apply filters
        filtered_results = []
        for idx, score in similar_indices:
            if idx < len(embeddings_service.documents) and score >= min_similarity:
                doc = embeddings_service.documents[idx]
                
                # Apply filters
                if tribunal and tribunal.lower() not in doc.get('tribunal', '').lower():
                    continue
                    
                if materia and materia.lower() not in doc.get('materia', '').lower():
                    continue
                
                if fecha_desde:
                    try:
                        doc_date = datetime.fromisoformat(doc.get('fecha', ''))
                        start_date = datetime.fromisoformat(fecha_desde)
                        if doc_date < start_date:
                            continue
                    except:
                        continue
                
                if fecha_hasta:
                    try:
                        doc_date = datetime.fromisoformat(doc.get('fecha', ''))
                        end_date = datetime.fromisoformat(fecha_hasta)
                        if doc_date > end_date:
                            continue
                    except:
                        continue
                
                # Add to results
                filtered_results.append({
                    'tribunal': doc.get('tribunal', ''),
                    'fecha': doc.get('fecha', ''),
                    'materia': doc.get('materia', ''),
                    'partes': doc.get('partes', ''),
                    'expediente': doc.get('expediente', ''),
                    'url': doc.get('url', ''),
                    'similarity_score': float(score),
                    'excerpt': doc.get('full_text', '')[:200] + '...' if len(doc.get('full_text', '')) > 200 else doc.get('full_text', '')
                })
                
                if len(filtered_results) >= limit:
                    break
        
        return {
            'query': query,
            'filters': {
                'tribunal': tribunal,
                'materia': materia,
                'fecha_desde': fecha_desde,
                'fecha_hasta': fecha_hasta,
                'min_similarity': min_similarity
            },
            'results': filtered_results,
            'total_found': len(filtered_results)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during advanced search: {str(e)}"
        )

@router.get("/statistics")
async def get_search_statistics(current_user: User = Depends(get_current_active_user)):
    """Get statistics about the searchable documents."""
    try:
        if not embeddings_service.documents:
            return {
                "total_documents": 0,
                "index_status": "Not available"
            }
        
        # Count documents by tribunal
        tribunals = {}
        materias = {}
        years = {}
        
        for doc in embeddings_service.documents:
            tribunal = doc.get('tribunal', 'Unknown')
            tribunals[tribunal] = tribunals.get(tribunal, 0) + 1
            
            materia = doc.get('materia', 'Unknown')
            materias[materia] = materias.get(materia, 0) + 1
            
            try:
                year = datetime.fromisoformat(doc.get('fecha', '')).year
                years[year] = years.get(year, 0) + 1
            except:
                pass
        
        return {
            "total_documents": len(embeddings_service.documents),
            "index_status": "Available" if embeddings_service.faiss_index else "Not available",
            "tribunals": dict(sorted(tribunals.items(), key=lambda x: x[1], reverse=True)[:10]),
            "materias": dict(sorted(materias.items(), key=lambda x: x[1], reverse=True)[:10]),
            "years": dict(sorted(years.items(), key=lambda x: x[1], reverse=True)[:10])
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting search statistics: {str(e)}"
        )