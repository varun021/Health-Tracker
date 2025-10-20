from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from .models import Disease, Symptom, DiseaseSymptom

class DiseaseAPITests(APITestCase):
    def setUp(self):
        # Create test data
        self.disease = Disease.objects.create(
            name="Common Cold",
            description="A viral infection of the upper respiratory tract",
            lifestyle_tips="Rest and stay hydrated",
            diet_advice="Consume vitamin C rich foods",
            medical_advice="Over-the-counter medications may help"
        )
        
        self.symptom = Symptom.objects.create(
            name="Fever",
            description="Elevated body temperature"
        )
        
        DiseaseSymptom.objects.create(
            disease=self.disease,
            symptom=self.symptom,
            weight=7  # Added weight value
        )

    def test_list_diseases(self):
        """Test retrieving list of diseases"""
        url = reverse('disease-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Common Cold')

    def test_get_disease_detail(self):
        """Test retrieving a single disease"""
        url = reverse('disease-detail', args=[self.disease.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Common Cold')

class SymptomAPITests(APITestCase):
    def setUp(self):
        self.symptom = Symptom.objects.create(
            name="Headache",
            description="Pain in the head or upper neck"
        )

    def test_list_symptoms(self):
        """Test retrieving list of symptoms"""
        url = reverse('symptom-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Headache')

class PredictionAPITests(APITestCase):
    def setUp(self):
        # Create test data
        self.disease = Disease.objects.create(
            name="Flu",
            description="Influenza viral infection",
            lifestyle_tips="Rest",
            diet_advice="Hydrate well",
            medical_advice="Consult doctor if severe"
        )
        
        self.symptom1 = Symptom.objects.create(name="Fever")
        self.symptom2 = Symptom.objects.create(name="Cough")
        
        # Added weight values for disease symptoms
        DiseaseSymptom.objects.create(
            disease=self.disease, 
            symptom=self.symptom1,
            weight=8
        )
        DiseaseSymptom.objects.create(
            disease=self.disease, 
            symptom=self.symptom2,
            weight=6
        )

    def test_predict_disease(self):
        """Test disease prediction endpoint"""
        url = reverse('prediction-predict')
        data = {
            'name': 'John Doe',
            'age': 30,
            'gender': 'M',
            'symptoms': [self.symptom1.id, self.symptom2.id]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('submission', response.data)
        self.assertIn('recommendations', response.data)

    def test_prediction_history(self):
        """Test prediction history endpoint"""
        url = reverse('prediction-history')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
