from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DiseaseViewSet, SymptomViewSet, PredictionViewSet

# Create a router and register viewsets
router = DefaultRouter()
router.register(r'diseases', DiseaseViewSet, basename='disease')
router.register(r'symptoms', SymptomViewSet, basename='symptom')
router.register(r'predictions', PredictionViewSet, basename='prediction')

# URL patterns
urlpatterns = [
    path('', include(router.urls)),
]