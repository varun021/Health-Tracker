from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings

class Disease(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    lifestyle_tips = models.TextField()
    diet_advice = models.TextField()
    medical_advice = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']


class Symptom(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']


class DiseaseSymptom(models.Model):
    disease = models.ForeignKey(Disease, on_delete=models.CASCADE, related_name='disease_symptoms')
    symptom = models.ForeignKey(Symptom, on_delete=models.CASCADE, related_name='symptom_diseases')
    weight = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Weight of symptom (1-10, where 10 is most severe)"
    )
    
    class Meta:
        unique_together = ['disease', 'symptom']
        ordering = ['-weight']
    
    def __str__(self):
        return f"{self.disease.name} - {self.symptom.name} (Weight: {self.weight})"


class UserSubmission(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    SEVERITY_CHOICES = [
        ('NORMAL', 'Normal'),
        ('MODERATE', 'Moderate'),
        ('RISKY', 'Risky'),
    ]
    
    DIET_CHOICES = [
        ('VEG', 'Vegetarian'),
        ('NON_VEG', 'Non-Vegetarian'),
        ('VEGAN', 'Vegan'),
        ('MIXED', 'Mixed'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=100)
    age = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(120)])
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    
    # Physical Metrics
    height = models.FloatField(validators=[MinValueValidator(0)], help_text="Height in cm", null=True, blank=True)
    weight = models.FloatField(validators=[MinValueValidator(0)], help_text="Weight in kg", null=True, blank=True)
    bmi = models.FloatField(null=True, blank=True)
    
    # Professional Info
    occupation = models.CharField(max_length=100, blank=True)
    
    # Medical History
    existing_diseases = models.JSONField(default=list, blank=True)
    allergies = models.TextField(blank=True)
    medications = models.TextField(blank=True)
    family_history = models.TextField(blank=True)
    
    # Lifestyle Information
    smoking = models.BooleanField(default=False)
    alcohol = models.BooleanField(default=False)
    diet = models.CharField(max_length=20, choices=DIET_CHOICES, blank=True)
    sleep_hours = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(24)], null=True, blank=True)
    exercise_frequency = models.CharField(max_length=50, blank=True)
    stress_level = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)], null=True, blank=True)
    
    # Travel
    travel_history = models.TextField(blank=True)
    
    # Prediction Results
    primary_prediction = models.ForeignKey(Disease, on_delete=models.SET_NULL, null=True, related_name='primary_submissions')
    severity_score = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    severity_category = models.CharField(max_length=10, choices=SEVERITY_CHOICES)
    
    # System Information
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='submissions', null=True)
    ip_address = models.GenericIPAddressField(null=True)
    user_agent = models.CharField(max_length=255, blank=True)
    session_id = models.CharField(max_length=100, null=True, blank=True)
    
    def save(self, *args, **kwargs):
        # Calculate BMI if height and weight are provided
        if self.height and self.weight:
            height_m = self.height / 100  # Convert cm to meters
            self.bmi = round(self.weight / (height_m ** 2), 1)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.name} - {self.primary_prediction} ({self.created_at.strftime('%Y-%m-%d')})"
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['user', '-created_at']),
        ]


class SubmissionSymptom(models.Model):
    """Junction table to store symptom details for each submission"""
    ONSET_CHOICES = [
        ('SUDDEN', 'Sudden'),
        ('GRADUAL', 'Gradual'),
    ]
    
    submission = models.ForeignKey(UserSubmission, on_delete=models.CASCADE, related_name='submission_symptoms')
    symptom = models.ForeignKey(Symptom, on_delete=models.CASCADE)
    severity = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    duration = models.CharField(max_length=50, help_text="e.g., '3 days', '1 week'")
    onset = models.CharField(max_length=10, choices=ONSET_CHOICES)
    
    class Meta:
        unique_together = ['submission', 'symptom']
    
    def __str__(self):
        return f"{self.submission.name} - {self.symptom.name}"


class DiseasePrediction(models.Model):
    """Store multiple disease predictions for each submission"""
    submission = models.ForeignKey(UserSubmission, on_delete=models.CASCADE, related_name='predicted_diseases')
    disease = models.ForeignKey(Disease, on_delete=models.CASCADE)
    confidence_score = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    rank = models.IntegerField(default=1)
    
    class Meta:
        ordering = ['-confidence_score']
        unique_together = ['submission', 'disease']
    
    def __str__(self):
        return f"{self.submission.name} - {self.disease.name} ({self.confidence_score}%)"