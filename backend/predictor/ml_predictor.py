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
    Naive Bayes based disease predictor with training and prediction capabilities.
    Uses weighted disease-symptom relationships and user-submission history.
    """

    def __init__(self):
        self.model = MultinomialNB(alpha=1.0)
        self.label_encoder = LabelEncoder()
        self.symptom_encoder = {}
        self.is_trained = False
        self.model_path = 'ml_models/disease_predictor.pkl'

    # -------------------------------------------------------------------------
    def prepare_training_data(self):
        """
        Prepare weighted training data from DiseaseSymptom and UserSubmission tables.
        """
        diseases = Disease.objects.prefetch_related('disease_symptoms__symptom').all()

        X = []  # feature vectors
        y = []  # labels

        # Encode all symptoms
        all_symptoms = Symptom.objects.all()
        self.symptom_encoder = {symptom.id: idx for idx, symptom in enumerate(all_symptoms)}
        symptom_count = len(all_symptoms)

        # --- From disease-symptom relationships ---
        for disease in diseases:
            disease_symptoms = disease.disease_symptoms.all()
            feature_vector = np.zeros(symptom_count)

            for ds in disease_symptoms:
                symptom_idx = self.symptom_encoder.get(ds.symptom.id)
                if symptom_idx is not None:
                    # normalize weights (1–10 → 0–1)
                    feature_vector[symptom_idx] = ds.weight / 10.0

            X.append(feature_vector)
            y.append(disease.name)

        # --- From historical user submissions ---
        submissions = (
            UserSubmission.objects.prefetch_related('submission_symptoms__symptom', 'primary_prediction')
            .filter(primary_prediction__isnull=False)[:1000]
        )

        for submission in submissions:
            feature_vector = np.zeros(symptom_count)
            for ss in submission.submission_symptoms.all():
                symptom_idx = self.symptom_encoder.get(ss.symptom.id)
                if symptom_idx is not None:
                    feature_vector[symptom_idx] = ss.severity / 10.0  # normalize 0–1
            X.append(feature_vector)
            y.append(submission.primary_prediction.name)

        return np.array(X), np.array(y)

    # -------------------------------------------------------------------------
    def train(self):
        """
        Train or retrain the Naive Bayes model using all data.
        """
        X, y = self.prepare_training_data()
        if len(X) == 0:
            raise ValueError("No training data available")

        y_encoded = self.label_encoder.fit_transform(y)
        self.model.fit(X, y_encoded)
        self.is_trained = True
        self.save_model()

        # Cache for faster predictions
        cache.set('nb_model', self.model, None)
        cache.set('nb_label_encoder', self.label_encoder, None)
        cache.set('nb_symptom_encoder', self.symptom_encoder, None)
        cache.set('nb_trained', True, None)

        return {
            'samples_trained': len(X),
            'diseases': len(self.label_encoder.classes_),
            'symptoms': len(self.symptom_encoder),
        }

    # -------------------------------------------------------------------------
    def predict(self, symptom_data, top_k=3):
        """
        Predict diseases based on symptoms and severity.
        Args:
            symptom_data: [{'id': int, 'severity': float}]
        """
        if not self.is_trained:
            self.load_model()

        symptom_count = len(self.symptom_encoder)
        feature_vector = np.zeros(symptom_count)

        for symptom in symptom_data:
            symptom_idx = self.symptom_encoder.get(symptom['id'])
            if symptom_idx is not None:
                sev = symptom.get('severity', 5) / 10.0  # fallback default
                feature_vector[symptom_idx] = sev

        probabilities = self.model.predict_proba([feature_vector])[0]
        top_indices = np.argsort(probabilities)[-top_k:][::-1]

        predictions = []
        for idx in top_indices:
            disease_name = self.label_encoder.classes_[idx]
            confidence = probabilities[idx] * 100
            try:
                disease = Disease.objects.get(name=disease_name)
                predictions.append({'disease': disease, 'confidence': round(confidence, 2)})
            except Disease.DoesNotExist:
                continue

        return predictions

    # -------------------------------------------------------------------------
    def save_model(self):
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        joblib.dump(
            {
                'model': self.model,
                'label_encoder': self.label_encoder,
                'symptom_encoder': self.symptom_encoder,
                'is_trained': self.is_trained,
            },
            self.model_path,
        )

    # -------------------------------------------------------------------------
    def load_model(self):
        # Try cache first
        cached_model = cache.get('nb_model')
        if cached_model:
            self.model = cached_model
            self.label_encoder = cache.get('nb_label_encoder')
            self.symptom_encoder = cache.get('nb_symptom_encoder')
            self.is_trained = cache.get('nb_trained', False)
            return

        # Fallback to disk
        if os.path.exists(self.model_path):
            data = joblib.load(self.model_path)
            self.model = data['model']
            self.label_encoder = data['label_encoder']
            self.symptom_encoder = data['symptom_encoder']
            self.is_trained = data['is_trained']
        else:
            self.train()


# =============================================================================
#                         HYBRID PREDICTOR
# =============================================================================
class HybridPredictor:
    """
    Combines ML (Naive Bayes) and rule-based predictions with weighting.
    """

    def __init__(self):
        self.nb_predictor = NaiveBayesPredictor()

    # -------------------------------------------------------------------------
    def predict(self, symptom_data, user=None):
        """
        Hybrid prediction: 60% ML + 40% rule-based.
        """
        ml_predictions = self.nb_predictor.predict(symptom_data, top_k=5)
        rule_predictions = self._rule_based_predict(symptom_data, user)
        combined = self._combine_predictions(ml_predictions, rule_predictions)
        return combined[:3]

    # -------------------------------------------------------------------------
    def _rule_based_predict(self, symptom_data, user=None):
        symptom_ids = [s['id'] for s in symptom_data]
        symptom_severities = {s['id']: s.get('severity', 0) for s in symptom_data}

        diseases = Disease.objects.prefetch_related('disease_symptoms')
        disease_scores = []

        # --- User history weighting ---
        user_history = {}
        if user and user.is_authenticated:
            from django.db.models import Count
            from .models import DiseasePrediction

            previous = (
                DiseasePrediction.objects.filter(submission__user=user, confidence_score__gte=70)
                .values('disease_id')
                .annotate(count=Count('id'))
                .order_by('-count')
            )
            user_history = {p['disease_id']: p['count'] for p in previous}

        # --- Rule-based scoring ---
        for disease in diseases:
            disease_symptoms = disease.disease_symptoms.filter(symptom_id__in=symptom_ids)
            if not disease_symptoms.exists():
                continue

            matched_count = disease_symptoms.count()
            total_count = disease.disease_symptoms.count()
            match_percentage = (matched_count / total_count) * 100

            weight_score = 0
            max_possible = 0
            for ds in disease_symptoms:
                user_sev = symptom_severities.get(ds.symptom_id, ds.weight)  # fallback to dataset weight
                weight_score += ds.weight * (user_sev / 10.0)
                max_possible += ds.weight

            weight_percentage = (weight_score / max_possible) * 100 if max_possible > 0 else 0
            confidence = (match_percentage * 0.4) + (weight_percentage * 0.6)

            # History bonus
            if disease.id in user_history:
                bonus = min(user_history[disease.id] * 3, 15)
                confidence = min(confidence + bonus, 100)

            disease_scores.append({'disease': disease, 'confidence': round(confidence, 2)})

        disease_scores.sort(key=lambda x: x['confidence'], reverse=True)
        return disease_scores[:5]

    # -------------------------------------------------------------------------
    def _combine_predictions(self, ml_predictions, rule_predictions):
        """
        Weighted combination of ML (60%) and rule-based (40%) predictions.
        """
        ml_weight = 0.6
        rule_weight = 0.4
        combined = {}

        # Merge ML predictions
        for pred in ml_predictions:
            disease_id = pred['disease'].id
            combined[disease_id] = {
                'disease': pred['disease'],
                'ml_confidence': pred['confidence'],
                'rule_confidence': 0,
            }

        # Merge rule-based predictions
        for pred in rule_predictions:
            disease_id = pred['disease'].id
            if disease_id in combined:
                combined[disease_id]['rule_confidence'] = pred['confidence']
            else:
                combined[disease_id] = {
                    'disease': pred['disease'],
                    'ml_confidence': 0,
                    'rule_confidence': pred['confidence'],
                }

        # Weighted average
        final = []
        for disease_id, data in combined.items():
            weighted = data['ml_confidence'] * ml_weight + data['rule_confidence'] * rule_weight
            final.append({'disease': data['disease'], 'confidence': round(weighted, 2)})

        final.sort(key=lambda x: x['confidence'], reverse=True)
        return final
