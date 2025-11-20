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


# # =============================================================================
# #                         HYBRID PREDICTOR
# # =============================================================================
# class HybridPredictor:
#     """
#     Combines ML (Naive Bayes) and rule-based predictions with weighting.
#     """

#     def __init__(self):
#         self.nb_predictor = NaiveBayesPredictor()

#     # -------------------------------------------------------------------------
#     def predict(self, symptom_data, user=None):
#         """
#         Hybrid prediction: 60% ML + 40% rule-based.
#         """
#         ml_predictions = self.nb_predictor.predict(symptom_data, top_k=5)
#         rule_predictions = self._rule_based_predict(symptom_data, user)
#         combined = self._combine_predictions(ml_predictions, rule_predictions)
#         return combined[:3]

#     # -------------------------------------------------------------------------
#     def _rule_based_predict(self, symptom_data, user=None):
#         symptom_ids = [s['id'] for s in symptom_data]
#         symptom_severities = {s['id']: s.get('severity', 0) for s in symptom_data}

#         diseases = Disease.objects.prefetch_related('disease_symptoms')
#         disease_scores = []

#         # --- User history weighting ---
#         user_history = {}
#         if user and user.is_authenticated:
#             from django.db.models import Count
#             from .models import DiseasePrediction

#             previous = (
#                 DiseasePrediction.objects.filter(submission__user=user, confidence_score__gte=70)
#                 .values('disease_id')
#                 .annotate(count=Count('id'))
#                 .order_by('-count')
#             )
#             user_history = {p['disease_id']: p['count'] for p in previous}

#         # --- Rule-based scoring ---
#         for disease in diseases:
#             disease_symptoms = disease.disease_symptoms.filter(symptom_id__in=symptom_ids)
#             if not disease_symptoms.exists():
#                 continue

#             matched_count = disease_symptoms.count()
#             total_count = disease.disease_symptoms.count()
#             match_percentage = (matched_count / total_count) * 100

#             weight_score = 0
#             max_possible = 0
#             for ds in disease_symptoms:
#                 user_sev = symptom_severities.get(ds.symptom_id, ds.weight)  # fallback to dataset weight
#                 weight_score += ds.weight * (user_sev / 10.0)
#                 max_possible += ds.weight

#             weight_percentage = (weight_score / max_possible) * 100 if max_possible > 0 else 0
#             confidence = (match_percentage * 0.4) + (weight_percentage * 0.6)

#             # History bonus
#             if disease.id in user_history:
#                 bonus = min(user_history[disease.id] * 3, 15)
#                 confidence = min(confidence + bonus, 100)

#             disease_scores.append({'disease': disease, 'confidence': round(confidence, 2)})

#         disease_scores.sort(key=lambda x: x['confidence'], reverse=True)
#         return disease_scores[:5]

#     # -------------------------------------------------------------------------
#     def _combine_predictions(self, ml_predictions, rule_predictions):
#         """
#         Weighted combination of ML (60%) and rule-based (40%) predictions.
#         """
#         ml_weight = 0.6
#         rule_weight = 0.4
#         combined = {}

#         # Merge ML predictions
#         for pred in ml_predictions:
#             disease_id = pred['disease'].id
#             combined[disease_id] = {
#                 'disease': pred['disease'],
#                 'ml_confidence': pred['confidence'],
#                 'rule_confidence': 0,
#             }

#         # Merge rule-based predictions
#         for pred in rule_predictions:
#             disease_id = pred['disease'].id
#             if disease_id in combined:
#                 combined[disease_id]['rule_confidence'] = pred['confidence']
#             else:
#                 combined[disease_id] = {
#                     'disease': pred['disease'],
#                     'ml_confidence': 0,
#                     'rule_confidence': pred['confidence'],
#                 }

#         # Weighted average
#         final = []
#         for disease_id, data in combined.items():
#             weighted = data['ml_confidence'] * ml_weight + data['rule_confidence'] * rule_weight
#             final.append({'disease': data['disease'], 'confidence': round(weighted, 2)})

#         final.sort(key=lambda x: x['confidence'], reverse=True)
#         return final


# =============================================================================
#                    CONSERVATIVE UPGRADED HYBRID PREDICTOR
# =============================================================================

class HybridPredictor:
    """
    Conservative hybrid predictor:
    - Combines ML (Naive Bayes) + Rule-based predictions
    - Applies prevalence priors (user history)
    - Boosts common infectious diseases
    - Penalizes rare or unlikely diseases
    - Applies co-occurrence weighting with disease symptom weights
    - Filters very low-confidence results
    """

    COMMON_DISEASE_KEYWORDS = [
        "viral", "flu", "influenza", "fever", "dengue", "malaria",
        "typhoid", "covid", "respiratory", "cold", "infection"
    ]

    RARE_DISEASE_KEYWORDS = [
        "aids", "cancer", "leukemia", "brain hemorrhage",
        "stroke", "amyotrophic"
    ]

    COMMON_BOOST = 8.0        # +8% for common infectious diseases
    RARE_PENALTY = 15.0       # -15% for rare improbable diseases
    MIN_CONFIDENCE = 12.0     # hide noise predictions below 12%

    ML_WEIGHT = 0.55
    RULE_WEIGHT = 0.35
    COOCCURRENCE_WEIGHT = 0.10   # stronger than ML/rule but capped

    def __init__(self):
        self.nb_predictor = NaiveBayesPredictor()

    # -------------------------------------------------------------------------
    def predict(self, symptom_data, user=None):
        """
        Conservative hybrid prediction:
        Boosts common infections and penalizes rare diseases.
        """
        ml_predictions = self.nb_predictor.predict(symptom_data, top_k=10)
        rule_predictions = self._rule_based_predict(symptom_data, user)

        # Merge ML + rule into candidate map
        candidates = {}
        for pred in ml_predictions:
            did = pred['disease'].id
            candidates[did] = {
                'disease': pred['disease'],
                'ml_conf': pred['confidence'],
                'rule_conf': 0.0,
            }

        for pred in rule_predictions:
            did = pred['disease'].id
            if did in candidates:
                candidates[did]['rule_conf'] = pred['confidence']
            else:
                candidates[did] = {
                    'disease': pred['disease'],
                    'ml_conf': 0.0,
                    'rule_conf': pred['confidence'],
                }

        if not candidates:
            return []

        # Compute co-occurrence boost
        cooccur_map = self._cooccurrence_boost(symptom_data, candidates)

        # Apply prevalence priors (if any)
        prevalence_map = self._prevalence_priors(candidates.keys(), user)

        # FINAL scoring
        final = []
        for did, entry in candidates.items():
            disease_name = entry['disease'].name.lower()

            # Base score
            ml = entry.get('ml_conf', 0.0)
            rule = entry.get('rule_conf', 0.0)
            score = ml * self.ML_WEIGHT + rule * self.RULE_WEIGHT

            # Co-occurrence with symptom weights
            score += cooccur_map.get(did, 0.0) * self.COOCCURRENCE_WEIGHT

            # Prevalence prior influence
            score += prevalence_map.get(did, 0.0) * 4  # small prior boost

            # Common disease boost
            if any(k in disease_name for k in self.COMMON_DISEASE_KEYWORDS):
                score += self.COMMON_BOOST

            # Rare disease penalty
            if any(k in disease_name for k in self.RARE_DISEASE_KEYWORDS):
                score -= self.RARE_PENALTY

            # Normalize
            score = max(0.0, min(100.0, score))

            final.append({
                'disease': entry['disease'],
                'confidence': round(score, 2)
            })

        # Sort and filter
        final.sort(key=lambda x: x['confidence'], reverse=True)

        # Filter low confidence
        final = [f for f in final if f['confidence'] >= self.MIN_CONFIDENCE]

        # Return top 3
        return final[:3]

    # -------------------------------------------------------------------------
    def _rule_based_predict(self, symptom_data, user=None):
        symptom_ids = [s['id'] for s in symptom_data]
        symptom_sev = {s['id']: s.get('severity', 5) for s in symptom_data}

        diseases = Disease.objects.prefetch_related('disease_symptoms')
        scores = []

        # User prevalence history
        user_history = {}
        if user and user.is_authenticated:
            from django.db.models import Count
            from .models import DiseasePrediction
            previous = (
                DiseasePrediction.objects.filter(submission__user=user, confidence_score__gte=70)
                .values('disease_id')
                .annotate(count=Count('id'))
            )
            user_history = {p['disease_id']: p['count'] for p in previous}

        # Rule-based scoring
        for d in diseases:
            ds_qs = d.disease_symptoms.all()

            total_count = ds_qs.count()
            if total_count == 0:
                continue

            matched = []
            weight_sum = 0.0
            total_weight = 0.0

            for ds in ds_qs:
                total_weight += (ds.weight or 1.0)
                if ds.symptom_id in symptom_ids:
                    matched.append(ds)
                    sev = symptom_sev.get(ds.symptom_id, ds.weight or 5)
                    weight_sum += (ds.weight or 1.0) * (sev / 10.0)

            if not matched:
                continue

            match_ratio = len(matched) / total_count
            weight_ratio = weight_sum / total_weight if total_weight else 0

            conf = match_ratio * 40 + weight_ratio * 60

            # User history bonus
            if d.id in user_history:
                conf += min(user_history[d.id] * 2, 10)

            scores.append({'disease': d, 'confidence': round(conf, 2)})

        scores.sort(key=lambda x: x['confidence'], reverse=True)
        return scores[:10]

    # -------------------------------------------------------------------------
    def _cooccurrence_boost(self, symptom_data, candidates):
        """Boost diseases whose TOP-weighted symptoms match user symptoms."""
        user_sym_ids = {s['id'] for s in symptom_data}
        boost = {}

        for did, entry in candidates.items():
            disease = entry['disease']
            ds_qs = disease.disease_symptoms.all().order_by('-weight')[:6]

            top_weight = sum(ds.weight or 1 for ds in ds_qs)
            if top_weight == 0:
                boost[did] = 0
                continue

            matched = sum(ds.weight or 1 for ds in ds_qs if ds.symptom_id in user_sym_ids)
            ratio = matched / top_weight
            boost[did] = round(ratio * 100, 2)

        return boost

    # -------------------------------------------------------------------------
    def _prevalence_priors(self, disease_ids, user=None):
        """Estimate prior probability from user's history, else uniform small prior."""
        priors = {did: 0.02 for did in disease_ids}  # tiny prior

        if not user or not user.is_authenticated:
            return priors

        try:
            from .models import DiseasePrediction
            from django.db.models import Count

            counts = (
                DiseasePrediction.objects.filter(disease_id__in=disease_ids)
                .values('disease_id')
                .annotate(count=Count('id'))
            )

            total = sum(c['count'] for c in counts) or 0
            if total == 0:
                return priors

            for c in counts:
                priors[c['disease_id']] = c['count'] / total

        except:
            pass

        return priors
