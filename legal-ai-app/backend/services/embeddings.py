import numpy as np
import json
import pickle
import os
from typing import List, Dict, Any, Tuple, Optional
from sentence_transformers import SentenceTransformer
import faiss
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import PCA
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import re

from config import settings

# Download NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

class LegalEmbeddingsService:
    def __init__(self):
        self.model = SentenceTransformer(settings.sentence_transformer_model)
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        self.pca = PCA(n_components=100)
        self.faiss_index = None
        self.documents = []
        self.embeddings = []
        
        # Load existing models if they exist
        self._load_models()
    
    def _load_models(self):
        """Load existing FAISS index and classifier if they exist."""
        try:
            if os.path.exists(settings.faiss_index_path):
                self.faiss_index = faiss.read_index(settings.faiss_index_path)
                print(f"Loaded existing FAISS index from {settings.faiss_index_path}")
            
            if os.path.exists(settings.classifier_model_path):
                with open(settings.classifier_model_path, 'rb') as f:
                    self.classifier = pickle.load(f)
                print(f"Loaded existing classifier from {settings.classifier_model_path}")
                
        except Exception as e:
            print(f"Error loading existing models: {e}")
            print("Will create new models")
    
    def preprocess_text(self, text: str) -> str:
        """Preprocess legal text for better embeddings."""
        # Remove special characters and normalize
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        text = text.lower().strip()
        
        # Remove common legal abbreviations and normalize
        legal_replacements = {
            'dr.': 'doctor',
            'sr.': 'señor',
            'sra.': 'señora',
            'art.': 'artículo',
            'arts.': 'artículos',
            'inc.': 'inciso',
            'incs.': 'incisos',
            'ley': 'ley',
            'código': 'código',
            'tribunal': 'tribunal',
            'juzgado': 'juzgado',
            'cámara': 'cámara',
            'fiscal': 'fiscal',
            'defensor': 'defensor',
            'abogado': 'abogado'
        }
        
        for abbr, full in legal_replacements.items():
            text = text.replace(abbr, full)
        
        return text
    
    def create_embeddings(self, documents: List[Dict[str, Any]]) -> np.ndarray:
        """Create embeddings for a list of legal documents."""
        print(f"Creating embeddings for {len(documents)} documents...")
        
        processed_texts = []
        for doc in documents:
            # Combine relevant fields for embedding
            text_parts = [
                doc.get('tribunal', ''),
                doc.get('materia', ''),
                doc.get('partes', ''),
                doc.get('full_text', '')
            ]
            
            combined_text = ' '.join(filter(None, text_parts))
            processed_text = self.preprocess_text(combined_text)
            processed_texts.append(processed_text)
        
        # Create embeddings
        embeddings = self.model.encode(processed_texts, show_progress_bar=True)
        print(f"Created embeddings with shape: {embeddings.shape}")
        
        return embeddings
    
    def build_faiss_index(self, embeddings: np.ndarray):
        """Build FAISS index for fast similarity search."""
        print("Building FAISS index...")
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)
        
        # Create FAISS index
        dimension = embeddings.shape[1]
        self.faiss_index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
        
        # Add vectors to index
        self.faiss_index.add(embeddings.astype('float32'))
        
        print(f"FAISS index built with {self.faiss_index.ntotal} vectors")
        
        # Save index
        os.makedirs(os.path.dirname(settings.faiss_index_path), exist_ok=True)
        faiss.write_index(self.faiss_index, settings.faiss_index_path)
        print(f"FAISS index saved to {settings.faiss_index_path}")
    
    def search_similar_documents(self, query: str, k: int = 10) -> List[Tuple[int, float]]:
        """Search for similar documents using FAISS."""
        if self.faiss_index is None:
            raise ValueError("FAISS index not built. Please build index first.")
        
        # Create query embedding
        processed_query = self.preprocess_text(query)
        query_embedding = self.model.encode([processed_query])
        
        # Normalize query embedding
        faiss.normalize_L2(query_embedding)
        
        # Search
        scores, indices = self.faiss_index.search(
            query_embedding.astype('float32'), k
        )
        
        # Return results as (index, score) tuples
        results = []
        for i, score in zip(indices[0], scores[0]):
            if i != -1:  # FAISS returns -1 for invalid indices
                results.append((int(i), float(score)))
        
        return results
    
    def extract_features(self, documents: List[Dict[str, Any]]) -> np.ndarray:
        """Extract features for classification using TF-IDF and PCA."""
        print("Extracting features for classification...")
        
        # Prepare text for TF-IDF
        texts = []
        for doc in documents:
            text_parts = [
                doc.get('tribunal', ''),
                doc.get('materia', ''),
                doc.get('full_text', '')[:1000]  # Limit text length
            ]
            combined_text = ' '.join(filter(None, text_parts))
            processed_text = self.preprocess_text(combined_text)
            texts.append(processed_text)
        
        # Create TF-IDF features
        tfidf_features = self.tfidf_vectorizer.fit_transform(texts)
        print(f"TF-IDF features shape: {tfidf_features.shape}")
        
        # Apply PCA for dimensionality reduction
        tfidf_dense = tfidf_features.toarray()
        pca_features = self.pca.fit_transform(tfidf_dense)
        print(f"PCA features shape: {pca_features.shape}")
        
        return pca_features
    
    def extract_outcome_from_text(self, text: str) -> str:
        """Extract legal outcome from text using simple NLP rules."""
        text_lower = text.lower()
        
        # Common outcome indicators
        outcome_indicators = {
            'condena': ['condena', 'condenado', 'condenada', 'condenar'],
            'absolución': ['absuelve', 'absuelto', 'absuelta', 'absolver'],
            'rechazo': ['rechaza', 'rechazado', 'rechazada', 'rechazar'],
            'aceptación': ['acepta', 'aceptado', 'aceptada', 'aceptar'],
            'archivo': ['archiva', 'archivado', 'archivada', 'archivar'],
            'nulidad': ['nulo', 'nula', 'nulidad', 'anular'],
            'recurso': ['recurso', 'recurrido', 'recurrida', 'recurrir']
        }
        
        # Count occurrences of each outcome type
        outcome_counts = {}
        for outcome, keywords in outcome_indicators.items():
            count = sum(text_lower.count(keyword) for keyword in keywords)
            if count > 0:
                outcome_counts[outcome] = count
        
        # Return most common outcome
        if outcome_counts:
            return max(outcome_counts, key=outcome_counts.get)
        else:
            return 'indeterminado'
    
    def get_document_metadata(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata from legal document."""
        return {
            'tribunal': doc.get('tribunal', ''),
            'fecha': doc.get('fecha', ''),
            'materia': doc.get('materia', ''),
            'partes': doc.get('partes', ''),
            'expediente': doc.get('expediente', ''),
            'url': doc.get('url', ''),
            'outcome': self.extract_outcome_from_text(doc.get('full_text', ''))
        }
    
    def update_index(self, new_documents: List[Dict[str, Any]]):
        """Update the FAISS index with new documents."""
        print(f"Updating index with {len(new_documents)} new documents...")
        
        # Create embeddings for new documents
        new_embeddings = self.create_embeddings(new_documents)
        
        # Add to existing index or create new one
        if self.faiss_index is not None:
            # Normalize new embeddings
            faiss.normalize_L2(new_embeddings)
            
            # Add to existing index
            self.faiss_index.add(new_embeddings.astype('float32'))
            
            # Update documents list
            self.documents.extend(new_documents)
            self.embeddings = np.vstack([self.embeddings, new_embeddings]) if len(self.embeddings) > 0 else new_embeddings
            
        else:
            # Create new index
            self.documents = new_documents
            self.embeddings = new_embeddings
            self.build_faiss_index(new_embeddings)
        
        print(f"Index updated. Total documents: {len(self.documents)}")
        
        # Save updated index
        faiss.write_index(self.faiss_index, settings.faiss_index_path)

# Global instance
embeddings_service = LegalEmbeddingsService()