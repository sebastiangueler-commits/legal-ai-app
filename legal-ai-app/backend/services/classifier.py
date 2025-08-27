import pickle
import os
import numpy as np
from typing import List, Dict, Any, Tuple
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
from sklearn.preprocessing import LabelEncoder
import joblib

from config import settings
from services.embeddings import embeddings_service

class LegalDocumentClassifier:
    def __init__(self):
        self.classifier = None
        self.label_encoder = LabelEncoder()
        self.feature_names = []
        self.is_trained = False
        
        # Load existing classifier if it exists
        self._load_classifier()
    
    def _load_classifier(self):
        """Load existing trained classifier if it exists."""
        try:
            if os.path.exists(settings.classifier_model_path):
                model_data = joblib.load(settings.classifier_model_path)
                self.classifier = model_data['classifier']
                self.label_encoder = model_data['label_encoder']
                self.feature_names = model_data['feature_names']
                self.is_trained = True
                print(f"Loaded existing classifier from {settings.classifier_model_path}")
                
        except Exception as e:
            print(f"Error loading existing classifier: {e}")
            print("Will train new classifier")
    
    def prepare_training_data(self, documents: List[Dict[str, Any]]) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare training data for the classifier."""
        print("Preparing training data...")
        
        # Extract features using embeddings service
        features = embeddings_service.extract_features(documents)
        
        # Extract outcomes
        outcomes = []
        for doc in documents:
            outcome = embeddings_service.extract_outcome_from_text(doc.get('full_text', ''))
            outcomes.append(outcome)
        
        # Encode outcomes
        encoded_outcomes = self.label_encoder.fit_transform(outcomes)
        
        print(f"Training data prepared: {features.shape[0]} samples, {features.shape[1]} features")
        print(f"Outcome classes: {self.label_encoder.classes_}")
        
        return features, encoded_outcomes
    
    def train_classifier(self, documents: List[Dict[str, Any]], test_size: float = 0.2):
        """Train the legal document classifier."""
        if len(documents) < 10:
            print("Not enough documents for training. Need at least 10 documents.")
            return False
        
        print("Training legal document classifier...")
        
        # Prepare training data
        features, outcomes = self.prepare_training_data(documents)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            features, outcomes, test_size=test_size, random_state=42, stratify=outcomes
        )
        
        # Initialize classifier
        self.classifier = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        
        # Train classifier
        self.classifier.fit(X_train, y_train)
        
        # Evaluate
        y_pred = self.classifier.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        print(f"Classifier training completed!")
        print(f"Accuracy: {accuracy:.4f}")
        print("\nClassification Report:")
        print(classification_report(y_test, y_pred, target_names=self.label_encoder.classes_))
        
        # Save classifier
        self._save_classifier()
        self.is_trained = True
        
        return True
    
    def _save_classifier(self):
        """Save the trained classifier to disk."""
        try:
            os.makedirs(os.path.dirname(settings.classifier_model_path), exist_ok=True)
            
            model_data = {
                'classifier': self.classifier,
                'label_encoder': self.label_encoder,
                'feature_names': self.feature_names
            }
            
            joblib.dump(model_data, settings.classifier_model_path)
            print(f"Classifier saved to {settings.classifier_model_path}")
            
        except Exception as e:
            print(f"Error saving classifier: {e}")
    
    def predict_outcome(self, case_description: str, case_type: str = None) -> Dict[str, Any]:
        """Predict the outcome of a legal case."""
        if not self.is_trained:
            raise ValueError("Classifier not trained. Please train the classifier first.")
        
        # Create feature vector for the case
        case_doc = {
            'tribunal': '',
            'materia': case_type or 'general',
            'full_text': case_description
        }
        
        features = embeddings_service.extract_features([case_doc])
        
        # Make prediction
        prediction_proba = self.classifier.predict_proba(features)[0]
        predicted_class_idx = self.classifier.predict(features)[0]
        
        # Get predicted outcome and confidence
        predicted_outcome = self.label_encoder.classes_[predicted_class_idx]
        confidence_score = prediction_proba[predicted_class_idx]
        
        # Get feature importance for explanation
        feature_importance = self._get_feature_importance(features[0])
        
        return {
            'predicted_outcome': predicted_outcome,
            'confidence_score': float(confidence_score),
            'all_probabilities': {
                outcome: float(prob) 
                for outcome, prob in zip(self.label_encoder.classes_, prediction_proba)
            },
            'feature_importance': feature_importance
        }
    
    def _get_feature_importance(self, features: np.ndarray) -> Dict[str, float]:
        """Get feature importance for explanation."""
        if hasattr(self.classifier, 'feature_importances_'):
            importance_dict = {}
            for i, importance in enumerate(self.classifier.feature_importances_):
                feature_name = f"feature_{i}"
                importance_dict[feature_name] = float(importance)
            
            # Sort by importance
            sorted_importance = dict(
                sorted(importance_dict.items(), key=lambda x: x[1], reverse=True)[:10]
            )
            return sorted_importance
        
        return {}
    
    def get_similar_cases(self, case_description: str, k: int = 5) -> List[Dict[str, Any]]:
        """Get similar cases using embeddings."""
        try:
            # Search for similar documents
            similar_indices = embeddings_service.search_similar_documents(case_description, k)
            
            similar_cases = []
            for idx, score in similar_indices:
                if idx < len(embeddings_service.documents):
                    doc = embeddings_service.documents[idx]
                    similar_cases.append({
                        'tribunal': doc.get('tribunal', ''),
                        'fecha': doc.get('fecha', ''),
                        'materia': doc.get('materia', ''),
                        'partes': doc.get('partes', ''),
                        'expediente': doc.get('expediente', ''),
                        'url': doc.get('url', ''),
                        'similarity_score': float(score),
                        'outcome': embeddings_service.extract_outcome_from_text(doc.get('full_text', ''))
                    })
            
            return similar_cases
            
        except Exception as e:
            print(f"Error getting similar cases: {e}")
            return []
    
    def explain_prediction(self, case_description: str, case_type: str = None) -> Dict[str, Any]:
        """Provide explanation for a prediction."""
        # Get prediction
        prediction = self.predict_outcome(case_description, case_type)
        
        # Get similar cases
        similar_cases = self.get_similar_cases(case_description, k=3)
        
        # Create explanation
        explanation = self._create_explanation(prediction, similar_cases, case_description)
        
        return {
            'prediction': prediction,
            'similar_cases': similar_cases,
            'explanation': explanation
        }
    
    def _create_explanation(self, prediction: Dict[str, Any], similar_cases: List[Dict[str, Any]], case_description: str) -> str:
        """Create human-readable explanation for the prediction."""
        outcome = prediction['predicted_outcome']
        confidence = prediction['confidence_score']
        
        explanation_parts = [
            f"Basado en el análisis del caso, se predice un resultado de **{outcome}** con una confianza del {confidence:.1%}."
        ]
        
        if similar_cases:
            explanation_parts.append("\n**Casos similares encontrados:**")
            for i, case in enumerate(similar_cases[:3], 1):
                explanation_parts.append(
                    f"{i}. {case['materia']} - {case['tribunal']} ({case['fecha']}) - Resultado: {case['outcome']}"
                )
        
        if confidence > 0.8:
            explanation_parts.append("\n**Alta confianza:** El modelo está muy seguro de esta predicción basándose en casos muy similares.")
        elif confidence > 0.6:
            explanation_parts.append("\n**Confianza moderada:** El modelo encuentra algunos casos similares pero la predicción tiene cierta incertidumbre.")
        else:
            explanation_parts.append("\n**Baja confianza:** El modelo no encuentra casos muy similares, por lo que la predicción es menos confiable.")
        
        return "\n".join(explanation_parts)
    
    def evaluate_model(self, test_documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Evaluate the model performance on test data."""
        if not self.is_trained:
            raise ValueError("Classifier not trained. Please train the classifier first.")
        
        print("Evaluating model performance...")
        
        # Prepare test data
        features, outcomes = self.prepare_training_data(test_documents)
        
        # Make predictions
        predictions = self.classifier.predict(features)
        prediction_probas = self.classifier.predict_proba(features)
        
        # Calculate metrics
        accuracy = accuracy_score(outcomes, predictions)
        
        # Calculate confidence scores
        confidence_scores = []
        for i, pred in enumerate(predictions):
            confidence_scores.append(prediction_probas[i][pred])
        
        avg_confidence = np.mean(confidence_scores)
        
        return {
            'accuracy': float(accuracy),
            'average_confidence': float(avg_confidence),
            'total_samples': len(test_documents),
            'class_distribution': dict(zip(self.label_encoder.classes_, np.bincount(outcomes)))
        }

# Global instance
classifier_service = LegalDocumentClassifier()