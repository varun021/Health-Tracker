"""
Machine Learning predictor using Naive Bayes for disease prediction
"""
import numpy as np
from sklearn.naive_bayes import MultinomialNB
from sklearn.preprocessing import LabelEncoder
from django.core.cache import cache
import joblib
import os
from .models import Disease, Symptom, DiseaseSymptom, UserSubmission, SubmissionSymptom


class NaiveBayesPredictor:
    """
    Naive Bayes based disease predictor with training and prediction capabilities
    """
    
    def __init__(self):
        self.model = MultinomialNB(alpha=1.0)
        self.label_encoder = LabelEncoder()
        self.symptom_encoder = {}
        self.is_trained = False
        self.model_path = 'ml_models/disease_predictor.pkl'
        self.encoder_path = 'ml_models/encoders.pkl'
        
    def prepare_training_data(self):
        """
        Prepare training data from existing disease-symptom relationships
        """
        diseases = Disease.objects.prefetch_related('disease_symptoms__symptom').all()
        
        X = []  # Feature vectors (symptoms)
        y = []  # Labels (diseases)
        
        # Get all symptoms for encoding
        all_symptoms = Symptom.objects.all()
        self.symptom_encoder = {symptom.id: idx for idx, symptom in enumerate(all_symptoms)}
        symptom_count = len(all_symptoms)
        
        # Create training samples
        for disease in diseases:
            disease_symptoms = disease.disease_symptoms.all()
            
            # Create feature vector
            feature_vector = np.zeros(symptom_count)
            
            for ds in disease_symptoms:
                symptom_idx = self.symptom_encoder.get(ds.symptom.id)
                if symptom_idx is not None:
                    # Use weight as feature value (1-10)
                    feature_vector[symptom_idx] = ds.weight
            
            X.append(feature_vector)
            y.append(disease.name)
        
        # Also train on historical user submissions for better accuracy
        submissions = UserSubmission.objects.prefetch_related(
            'submission_symptoms__symptom',
            'primary_prediction'
        ).filter(primary_prediction__isnull=False)[:1000]  # Last 1000 submissions
        
        for submission in submissions:
            feature_vector = np.zeros(symptom_count)
            
            for ss in submission.submission_symptoms.all():
                symptom_idx = self.symptom_encoder.get(ss.symptom.id)
                if symptom_idx is not None:
                    # Use user's severity rating
                    feature_vector[symptom_idx] = ss.severity
            
            X.append(feature_vector)
            y.append(submission.primary_prediction.name)
        
        return np.array(X), np.array(y)
    
    def train(self):
        """
        Train the Naive Bayes model
        """
        X, y = self.prepare_training_data()
        
        if len(X) == 0:
            raise ValueError("No training data available")
        
        # Encode labels
        y_encoded = self.label_encoder.fit_transform(y)
        
        # Train model
        self.model.fit(X, y_encoded)
        self.is_trained = True
        
        # Save model
        self.save_model()
        
        return {
            'samples_trained': len(X),
            'diseases': len(self.label_encoder.classes_),
            'symptoms': len(self.symptom_encoder)
        }
    
    def predict(self, symptom_data, top_k=3):
        """
        Predict diseases based on symptoms
        
        Args:
            symptom_data: List of dicts with 'id' and 'severity'
            top_k: Number of top predictions to return
            
        Returns:
            List of predictions with confidence scores
        """
        if not self.is_trained:
            self.load_model()
        
        # Prepare feature vector
        symptom_count = len(self.symptom_encoder)
        feature_vector = np.zeros(symptom_count)
        
        for symptom in symptom_data:
            symptom_idx = self.symptom_encoder.get(symptom['id'])
            if symptom_idx is not None:
                feature_vector[symptom_idx] = symptom['severity']
        
        # Get probabilities for all classes
        probabilities = self.model.predict_proba([feature_vector])[0]
        
        # Get top k predictions
        top_indices = np.argsort(probabilities)[-top_k:][::-1]
        
        predictions = []
        for idx in top_indices:
            disease_name = self.label_encoder.classes_[idx]
            confidence = probabilities[idx] * 100
            
            # Get disease object
            try:
                disease = Disease.objects.get(name=disease_name)
                predictions.append({
                    'disease': disease,
                    'confidence': round(confidence, 2)
                })
            except Disease.DoesNotExist:
                continue
        
        return predictions
    
    def save_model(self):
        """Save trained model and encoders"""
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        
        joblib.dump({
            'model': self.model,
            'label_encoder': self.label_encoder,
            'symptom_encoder': self.symptom_encoder,
            'is_trained': self.is_trained
        }, self.model_path)
    
    def load_model(self):
        """Load trained model and encoders"""
        if os.path.exists(self.model_path):
            data = joblib.load(self.model_path)
            self.model = data['model']
            self.label_encoder = data['label_encoder']
            self.symptom_encoder = data['symptom_encoder']
            self.is_trained = data['is_trained']
        else:
            # Train if model doesn't exist
            self.train()


class HybridPredictor:
    """
    Hybrid predictor combining rule-based and ML approaches
    """
    
    def __init__(self):
        self.nb_predictor = NaiveBayesPredictor()
    
    def predict(self, symptom_data, user=None):
        """
        Hybrid prediction combining Naive Bayes and rule-based approach
        """
        # Get ML predictions
        ml_predictions = self.nb_predictor.predict(symptom_data, top_k=5)
        
        # Get rule-based predictions (existing logic)
        rule_predictions = self._rule_based_predict(symptom_data, user)
        
        # Combine predictions
        combined = self._combine_predictions(ml_predictions, rule_predictions)
        
        return combined[:3]  # Return top 3
    
    def _rule_based_predict(self, symptom_data, user=None):
        """Original rule-based prediction logic"""
        symptom_ids = [s['id'] for s in symptom_data]
        symptom_severities = {s['id']: s['severity'] for s in symptom_data}
        
        diseases = Disease.objects.prefetch_related('disease_symptoms')
        disease_scores = []
        
        # User history
        user_history = {}
        if user and user.is_authenticated:
            from django.db.models import Count
            from .models import DiseasePrediction
            previous_predictions = (DiseasePrediction.objects
                .filter(submission__user=user, confidence_score__gte=70)
                .values('disease_id')
                .annotate(count=Count('id'))
                .order_by('-count'))
            user_history = {p['disease_id']: p['count'] for p in previous_predictions}

        for disease in diseases:
            disease_symptoms = disease.disease_symptoms.filter(symptom_id__in=symptom_ids)
            
            if disease_symptoms.exists():
                matched_count = disease_symptoms.count()
                total_disease_symptoms = disease.disease_symptoms.count()
                
                match_percentage = (matched_count / total_disease_symptoms) * 100
                
                weight_score = 0
                max_possible_weight = 0
                
                for ds in disease_symptoms:
                    symptom_severity = symptom_severities.get(ds.symptom_id, 5)
                    weight_score += ds.weight * (symptom_severity / 10)
                    max_possible_weight += ds.weight
                
                if max_possible_weight > 0:
                    weight_percentage = (weight_score / max_possible_weight) * 100
                else:
                    weight_percentage = 0
                
                confidence = (match_percentage * 0.4) + (weight_percentage * 0.6)
                
                if disease.id in user_history:
                    history_bonus = min(user_history[disease.id] * 3, 15)
                    confidence = min(confidence + history_bonus, 100)
                
                disease_scores.append({
                    'disease': disease,
                    'confidence': round(confidence, 2)
                })
        
        disease_scores.sort(key=lambda x: x['confidence'], reverse=True)
        return disease_scores[:5]
    
    def _combine_predictions(self, ml_predictions, rule_predictions):
        """
        Combine ML and rule-based predictions with weighted averaging
        """
        # ML weight: 60%, Rule-based weight: 40%
        ml_weight = 0.6
        rule_weight = 0.4
        
        combined = {}
        
        # Add ML predictions
        for pred in ml_predictions:
            disease_id = pred['disease'].id
            combined[disease_id] = {
                'disease': pred['disease'],
                'ml_confidence': pred['confidence'],
                'rule_confidence': 0
            }
        
        # Add rule-based predictions
        for pred in rule_predictions:
            disease_id = pred['disease'].id
            if disease_id in combined:
                combined[disease_id]['rule_confidence'] = pred['confidence']
            else:
                combined[disease_id] = {
                    'disease': pred['disease'],
                    'ml_confidence': 0,
                    'rule_confidence': pred['confidence']
                }
        
        # Calculate weighted scores
        final_predictions = []
        for disease_id, data in combined.items():
            weighted_confidence = (
                data['ml_confidence'] * ml_weight +
                data['rule_confidence'] * rule_weight
            )
            final_predictions.append({
                'disease': data['disease'],
                'confidence': round(weighted_confidence, 2)
            })
        
        final_predictions.sort(key=lambda x: x['confidence'], reverse=True)
        return final_predictions