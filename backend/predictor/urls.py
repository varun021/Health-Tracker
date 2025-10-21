from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DiseaseViewSet, SymptomViewSet, PredictionViewSet

router = DefaultRouter()
router.register(r'diseases', DiseaseViewSet, basename='disease')
router.register(r'symptoms', SymptomViewSet, basename='symptom')
router.register(r'predictions', PredictionViewSet, basename='prediction')

urlpatterns = [
    path('', include(router.urls)),
]

# API Endpoints:
#
# GET /api/diseases/ - List all diseases
# GET /api/diseases/{id}/ - Get disease details
#
# GET /api/symptoms/ - List all symptoms
# GET /api/symptoms/{id}/ - Get symptom details
#
# POST /api/predictions/predict/ - Make a disease prediction
# POST /api/predictions/train_model/ - Train Naive Bayes model (admin only)
# GET /api/predictions/history/ - Get prediction history (paginated)
# GET /api/predictions/analytics/ - Comprehensive analytics dashboard
# GET /api/predictions/comparison_report/ - Compare health metrics
# GET /api/predictions/recommendations_based_on_history/ - Personalized recommendations
# GET /api/predictions/export_data/?format=csv|json - Export user data
# GET|POST /api/predictions/generate_report/ - Generate PDF/CSV/JSON report