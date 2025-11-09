# Backend Implementation Guide - Roji Disease Predictor

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Project Setup](#project-setup)
3. [Database Models](#database-models)
4. [Machine Learning Engine](#machine-learning-engine)
5. [API Endpoints](#api-endpoints)
6. [Authentication](#authentication)
7. [Views & Serializers](#views--serializers)
8. [Utilities & Helpers](#utilities--helpers)
9. [Admin Configuration](#admin-configuration)
10. [Testing](#testing)

---

## Architecture Overview

### Project Structure
```
backend/
├── core/                          # Django project settings
│   ├── settings.py               # Main configuration
│   ├── urls.py                   # Root URL routing
│   ├── asgi.py                   # ASGI server entry
│   ├── wsgi.py                   # WSGI server entry
│   └── __init__.py
├── predictor/                    # Main prediction app
│   ├── models.py                 # Database models
│   ├── views.py                  # API viewsets
│   ├── serializers.py            # DRF serializers
│   ├── ml_predictor.py           # ML engine
│   ├── utils.py                  # Helper functions
│   ├── urls.py                   # App URL routing
│   ├── admin.py                  # Django admin config
│   ├── tests.py                  # Unit tests
│   └── __init__.py
├── users/                        # User management app
│   ├── models.py
│   ├── views.py
│   ├── serializers.py
│   ├── authentication.py         # JWT authentication
│   └── ...
├── ml_models/                    # Trained ML models
│   ├── disease_predictor.pkl     # Trained Naive Bayes model
│   └── encoders.pkl              # Label & feature encoders
├── manage.py                     # Django CLI
└── requirements.txt              # Python dependencies
```

### Key Technologies
- **Web Framework**: Django + Django REST Framework
- **Database**: SQLite (dev) / PostgreSQL (production)
- **Machine Learning**: scikit-learn, NumPy
- **API Documentation**: drf-spectacular
- **Authentication**: djangorestframework-simplejwt
- **Admin UI**: Jazzmin

---

## Project Setup

### 1. Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Database Setup
```bash
# Create migrations for model changes
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser for admin access
python manage.py createsuperuser
```

### 4. Load Initial Data
```bash
# Seed diseases, symptoms, and relationships
python manage.py seed_data
```

### 5. Train ML Model
```bash
# Train the Naive Bayes model
python manage.py train_model
```

### 6. Run Development Server
```bash
python manage.py runserver
```

Server runs on: `http://localhost:8000`

---

## Database Models

### 1. Disease Model
```python
class Disease(models.Model):
    name = CharField(max_length=100, unique=True)
    description = TextField()
    lifestyle_tips = TextField()
    diet_advice = TextField()
    medical_advice = TextField()
    created_at = DateTimeField(auto_now_add=True)
```

**Purpose**: Store disease definitions with associated advice  
**Relationships**: Connected to Symptoms via DiseaseSymptom junction table

### 2. Symptom Model
```python
class Symptom(models.Model):
    name = CharField(max_length=100, unique=True)
    description = TextField(blank=True)
    created_at = DateTimeField(auto_now_add=True)
```

**Purpose**: Define available symptoms in the system  
**Relationships**: Connected to Diseases via DiseaseSymptom junction table

### 3. DiseaseSymptom Model (Junction Table)
```python
class DiseaseSymptom(models.Model):
    disease = ForeignKey(Disease, on_delete=CASCADE)
    symptom = ForeignKey(Symptom, on_delete=CASCADE)
    weight = IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    
    class Meta:
        unique_together = ['disease', 'symptom']
```

**Purpose**: Define many-to-many relationship with symptom weights (1-10)  
**Weight Meaning**: 10 = highly indicative of disease, 1 = less indicative

### 4. UserSubmission Model
```python
class UserSubmission(models.Model):
    # Personal Information
    name = CharField(max_length=100)
    age = IntegerField(validators=[MinValueValidator(0), MaxValueValidator(120)])
    gender = CharField(max_length=1, choices=GENDER_CHOICES)
    
    # Physical Metrics
    height = FloatField(help_text="Height in cm")  # Optional
    weight = FloatField(help_text="Weight in kg")  # Optional
    bmi = FloatField()  # Calculated automatically
    
    # Professional & Medical
    occupation = CharField(max_length=100, blank=True)
    existing_diseases = JSONField(default=list)
    allergies = TextField(blank=True)
    medications = TextField(blank=True)
    family_history = TextField(blank=True)
    
    # Lifestyle
    smoking = BooleanField(default=False)
    alcohol = BooleanField(default=False)
    diet = CharField(choices=DIET_CHOICES)
    sleep_hours = IntegerField(validators=[0, 24])
    exercise_frequency = CharField(max_length=50)
    stress_level = IntegerField(validators=[1, 10])
    
    # Travel
    travel_history = TextField(blank=True)
    
    # Prediction Results
    primary_prediction = ForeignKey(Disease, on_delete=SET_NULL)
    severity_score = FloatField(validators=[0, 100])
    severity_category = CharField(choices=SEVERITY_CHOICES)
    
    # Metadata
    user = ForeignKey(User, on_delete=CASCADE, null=True)
    created_at = DateTimeField(auto_now_add=True)
    ip_address = GenericIPAddressField(null=True)
    session_id = CharField(max_length=100, null=True)
```

**Purpose**: Store complete user health submissions and prediction results  
**Automatic**: BMI calculation in save() method

### 5. SubmissionSymptom Model (Junction Table)
```python
class SubmissionSymptom(models.Model):
    submission = ForeignKey(UserSubmission, on_delete=CASCADE)
    symptom = ForeignKey(Symptom, on_delete=CASCADE)
    severity = IntegerField(validators=[1, 10])
    duration = CharField(max_length=50)  # e.g., "3 days", "1 week"
    onset = CharField(choices=[('SUDDEN', 'Sudden'), ('GRADUAL', 'Gradual')])
    
    class Meta:
        unique_together = ['submission', 'symptom']
```

**Purpose**: Store detailed symptom information for each submission

### 6. DiseasePrediction Model
```python
class DiseasePrediction(models.Model):
    submission = ForeignKey(UserSubmission, on_delete=CASCADE)
    disease = ForeignKey(Disease, on_delete=CASCADE)
    confidence_score = FloatField(validators=[0, 100])
    rank = IntegerField(default=1)  # 1st, 2nd, 3rd prediction
    
    class Meta:
        unique_together = ['submission', 'disease']
        ordering = ['-confidence_score']
```

**Purpose**: Store multiple disease predictions for each submission

---

## Machine Learning Engine

### Overview
Located in `predictor/ml_predictor.py`, uses hybrid approach:
- **60% Naive Bayes** (ML-based)
- **40% Rule-Based** (Domain knowledge)

### NaiveBayesPredictor Class

#### Training
```python
class NaiveBayesPredictor:
    def train(self):
        """Train the Naive Bayes model"""
        X, y = self.prepare_training_data()
        y_encoded = self.label_encoder.fit_transform(y)
        self.model.fit(X, y_encoded)
        self.save_model()
```

**Training Data Sources:**
1. Disease-symptom definitions (weighted 1-10)
2. Last 1000 user submissions with verified predictions
3. Feature vectors: symptom severity scores

#### Prediction
```python
def predict(self, symptom_data, top_k=3):
    """Predict diseases from symptom input"""
    feature_vector = self._prepare_features(symptom_data)
    probabilities = self.model.predict_proba([feature_vector])[0]
    return self._get_top_predictions(probabilities, top_k)
```

### HybridPredictor Class

#### Combined Prediction
```python
class HybridPredictor:
    def predict(self, symptom_data, user=None):
        # Get ML predictions
        ml_predictions = self.nb_predictor.predict(symptom_data, top_k=5)
        
        # Get rule-based predictions
        rule_predictions = self._rule_based_predict(symptom_data, user)
        
        # Combine with weights
        return self._combine_predictions(ml_predictions, rule_predictions)
```

#### Combination Formula
```
Final Score = (ML_Score × 0.6) + (Rule_Score × 0.4)
```

#### Rule-Based Scoring
```python
def _rule_based_predict(self, symptom_data, user=None):
    """Calculate confidence based on domain rules"""
    for disease in Disease.objects.all():
        # Match percentage (40% weight)
        match_pct = (matched_symptoms / total_disease_symptoms) * 100
        
        # Weight-based score (60% weight)
        weight_score = sum(ds.weight * (symptom_severity / 10))
        weight_pct = (weight_score / max_weight) * 100
        
        # Combined confidence
        confidence = (match_pct * 0.4) + (weight_pct * 0.6)
        
        # User history bonus (optional)
        if user in history:
            confidence = min(confidence + history_bonus, 100)
```

---

## API Endpoints

### Disease Endpoints
```
GET    /api/diseases/              List all diseases
GET    /api/diseases/{id}/         Get disease details
POST   /api/diseases/              Create disease (admin)
PUT    /api/diseases/{id}/         Update disease (admin)
DELETE /api/diseases/{id}/         Delete disease (admin)
```

### Symptom Endpoints
```
GET    /api/symptoms/              List all symptoms
GET    /api/symptoms/{id}/         Get symptom details
POST   /api/symptoms/              Create symptom (admin)
PUT    /api/symptoms/{id}/         Update symptom (admin)
DELETE /api/symptoms/{id}/         Delete symptom (admin)
```

### Prediction Endpoints
```
POST   /api/predictions/predict/                        Make prediction
GET    /api/predictions/history/                        Prediction history (paginated)
GET    /api/predictions/analytics/?days=30              Get analytics
GET    /api/predictions/comparison_report/              Compare periods
GET    /api/predictions/recommendations_based_on_history/  Get recommendations
POST   /api/predictions/train_model/                    Train model (admin)
GET    /api/predictions/export_data/?format=csv|json    Export data
GET|POST /api/predictions/generate_report/              Generate report
```

### User Authentication Endpoints
```
POST   /api/users/register/        Register new user
POST   /api/users/login/           User login
POST   /api/users/logout/          User logout
POST   /api/users/refresh/         Refresh JWT token
GET    /api/users/profile/         Get user profile
PUT    /api/users/profile/         Update user profile
```

---

## Authentication

### JWT Implementation
Uses `djangorestframework-simplejwt` with cookie support.

#### Token Configuration (settings.py)
```python
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_COOKIE': 'access_token',
    'AUTH_COOKIE_SECURE': False,  # True in production
    'AUTH_COOKIE_HTTP_ONLY': True,
}
```

#### Custom Authentication Class
Located in `users/authentication.py`:
```python
class CookieJWTAuthentication(JWTAuthentication):
    """Extract JWT from HTTP cookies instead of Authorization header"""
    
    def get_validated_token(self, raw_token):
        # Read from cookies if not in header
        if raw_token is None:
            return None
        return super().get_validated_token(raw_token)
```

#### Usage
```python
# In views - automatic authentication
class MyViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Model.objects.filter(user=self.request.user)
```

---

## Views & Serializers

### DiseaseViewSet
```python
class DiseaseViewSet(viewsets.ModelViewSet):
    queryset = Disease.objects.all()
    serializer_class = DiseaseSerializer
    permission_classes = [AllowAny]  # Public read
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'destroy']:
            return [IsAdminUser()]
        return [AllowAny()]
```

### SymptomViewSet
```python
class SymptomViewSet(viewsets.ModelViewSet):
    queryset = Symptom.objects.all()
    serializer_class = SymptomSerializer
    permission_classes = [AllowAny]  # Public read
```

### PredictionViewSet
```python
class PredictionViewSet(viewsets.ModelViewSet):
    queryset = UserSubmission.objects.all()
    serializer_class = UserSubmissionSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def predict(self, request):
        """Main prediction endpoint"""
        serializer = PredictionRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        submission = self._create_submission(serializer.validated_data)
        predictions = self._get_predictions(submission)
        
        return Response(self._format_response(submission, predictions))
    
    @action(detail=False, methods=['get'])
    def analytics(self, request):
        """Return comprehensive health analytics"""
        days = request.query_params.get('days', 30)
        return Response(self._calculate_analytics(days))
    
    @action(detail=False, methods=['post'], permission_classes=[IsAdminUser])
    def train_model(self, request):
        """Retrain the ML model"""
        predictor = HybridPredictor()
        result = predictor.nb_predictor.train()
        return Response({'message': 'Model trained', 'details': result})
```

### Serializers

#### UserSubmissionSerializer
```python
class UserSubmissionSerializer(serializers.ModelSerializer):
    submission_symptoms = SubmissionSymptomSerializer(many=True)
    
    class Meta:
        model = UserSubmission
        fields = ['id', 'name', 'age', 'gender', 'height', 'weight', 
                  'bmi', 'submission_symptoms', 'severity_score', 
                  'severity_category', 'primary_prediction', 'created_at']
```

---

## Utilities & Helpers

### utils.py Functions

#### 1. Severity Scoring
```python
def calculate_severity_score(symptom_data, predicted_diseases):
    """Calculate overall severity score (0-100)"""
    total_severity = sum(s['severity'] for s in symptom_data)
    avg_severity = total_severity / len(symptom_data)
    
    disease_severity = max(d['confidence'] for d in predicted_diseases)
    
    return (avg_severity * 0.3) + (disease_severity * 0.7)
```

#### 2. Severity Category
```python
def get_severity_category(score):
    """Categorize severity"""
    if score < 30:
        return 'NORMAL'
    elif score < 70:
        return 'MODERATE'
    else:
        return 'RISKY'
```

#### 3. Recommendation Generation
```python
def generate_recommendations(disease, lifestyle):
    """Create personalized recommendations"""
    lifestyle_tips = []
    
    if lifestyle['sleep_hours'] < 6:
        lifestyle_tips.append("Increase sleep to 7-9 hours")
    
    if lifestyle['stress_level'] > 7:
        lifestyle_tips.append("Practice stress management techniques")
    
    return {
        'lifestyle_tips': lifestyle_tips,
        'diet_advice': disease.diet_advice.split('\n'),
        'medical_advice': disease.medical_advice.split('\n')
    }
```

#### 4. Report Generation
```python
def generate_pdf_report(submission, format='pdf'):
    """Generate health report in various formats"""
    if format == 'pdf':
        return self._generate_pdf(submission)
    elif format == 'csv':
        return self._generate_csv(submission)
    elif format == 'json':
        return self._generate_json(submission)
```

#### 5. Analytics Calculation
```python
def calculate_analytics(user, days=30):
    """Calculate comprehensive health analytics"""
    start_date = timezone.now() - timedelta(days=days)
    submissions = UserSubmission.objects.filter(
        user=user,
        created_at__gte=start_date
    )
    
    return {
        'total_predictions': submissions.count(),
        'avg_severity': submissions.aggregate(Avg('severity_score')),
        'most_common_disease': submissions.values('primary_prediction').annotate(count=Count('id')),
        'trends': self._calculate_trends(submissions)
    }
```

---

## Admin Configuration

### admin.py Setup
```python
from django.contrib import admin
from .models import Disease, Symptom, DiseaseSymptom, UserSubmission, SubmissionSymptom, DiseasePrediction

@admin.register(Disease)
class DiseaseAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at']

@admin.register(Symptom)
class SymptomAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']
    readonly_fields = ['created_at']

@admin.register(DiseaseSymptom)
class DiseaseSymptomAdmin(admin.ModelAdmin):
    list_display = ['disease', 'symptom', 'weight']
    list_filter = ['disease']
    search_fields = ['disease__name', 'symptom__name']

@admin.register(UserSubmission)
class UserSubmissionAdmin(admin.ModelAdmin):
    list_display = ['name', 'age', 'severity_category', 'primary_prediction', 'created_at']
    list_filter = ['severity_category', 'created_at']
    search_fields = ['name', 'user__email']
    readonly_fields = ['created_at', 'bmi', 'severity_score']
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('name', 'age', 'gender', 'user')
        }),
        ('Physical Metrics', {
            'fields': ('height', 'weight', 'bmi')
        }),
        ('Medical History', {
            'fields': ('existing_diseases', 'allergies', 'medications', 'family_history')
        }),
        ('Lifestyle', {
            'fields': ('smoking', 'alcohol', 'diet', 'sleep_hours', 'exercise_frequency', 'stress_level')
        }),
        ('Prediction Results', {
            'fields': ('primary_prediction', 'severity_score', 'severity_category')
        }),
        ('Metadata', {
            'fields': ('created_at', 'ip_address', 'session_id'),
            'classes': ('collapse',)
        }),
    )
```

---

## Testing

### Running Tests
```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test predictor

# Run with verbosity
python manage.py test -v 2

# Run specific test class
python manage.py test predictor.tests.PredictionTestCase

# Run specific test method
python manage.py test predictor.tests.PredictionTestCase.test_prediction
```

### Sample Tests (tests.py)
```python
from django.test import TestCase
from .models import Disease, Symptom, DiseaseSymptom

class DiseaseModelTest(TestCase):
    def setUp(self):
        self.disease = Disease.objects.create(
            name="Common Cold",
            description="A viral infection",
            lifestyle_tips="Rest",
            diet_advice="Warm fluids",
            medical_advice="See doctor if persistent"
        )
    
    def test_disease_creation(self):
        self.assertEqual(self.disease.name, "Common Cold")
        self.assertTrue(self.disease.created_at)

class PredictionTestCase(TestCase):
    def test_prediction_endpoint(self):
        # Test /api/predictions/predict/
        response = self.client.post('/api/predictions/predict/', {
            'name': 'John',
            'age': 30,
            'gender': 'M',
            'symptoms': [{'id': 1, 'severity': 8}]
        }, format='json')
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('predicted_diseases', response.json())
```

---

## Deployment Checklist

- [ ] Update `DEBUG = False` in settings.py
- [ ] Set `ALLOWED_HOSTS` to your domain
- [ ] Use PostgreSQL instead of SQLite
- [ ] Generate strong `SECRET_KEY`
- [ ] Set `SECURE_SSL_REDIRECT = True`
- [ ] Configure CORS_ALLOWED_ORIGINS
- [ ] Use environment variables for secrets
- [ ] Set up Gunicorn/uWSGI server
- [ ] Configure Nginx reverse proxy
- [ ] Set up database backups
- [ ] Configure logging and monitoring
- [ ] Run `python manage.py collectstatic`
- [ ] Run all tests before deployment

---

**Last Updated**: November 2024  
**Version**: 1.0.0
