from rest_framework import serializers
from .models import Disease, Symptom, DiseaseSymptom, UserSubmission, SubmissionSymptom, DiseasePrediction


class SymptomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Symptom
        fields = ['id', 'name', 'description']


class DiseaseSymptomSerializer(serializers.ModelSerializer):
    symptom = SymptomSerializer(read_only=True)
    
    class Meta:
        model = DiseaseSymptom
        fields = ['symptom', 'weight']


class DiseaseSerializer(serializers.ModelSerializer):
    symptoms = serializers.SerializerMethodField()
    
    class Meta:
        model = Disease
        fields = ['id', 'name', 'description', 'lifestyle_tips', 'diet_advice', 'medical_advice', 'symptoms']
    
    def get_symptoms(self, obj):
        disease_symptoms = DiseaseSymptom.objects.filter(disease=obj)
        return DiseaseSymptomSerializer(disease_symptoms, many=True).data


class SubmissionSymptomInputSerializer(serializers.Serializer):
    """Serializer for symptom input with details"""
    id = serializers.IntegerField()
    severity = serializers.IntegerField(min_value=1, max_value=10, required=False, allow_null=True)
    duration = serializers.CharField(max_length=50)
    onset = serializers.ChoiceField(choices=['SUDDEN', 'GRADUAL'])


class LifestyleSerializer(serializers.Serializer):
    """Serializer for lifestyle information"""
    smoking = serializers.BooleanField(default=False)
    alcohol = serializers.BooleanField(default=False)
    diet = serializers.ChoiceField(choices=['VEG', 'NON_VEG', 'VEGAN', 'MIXED'], required=False)
    sleep_hours = serializers.IntegerField(min_value=0, max_value=24, required=False)
    exercise_frequency = serializers.CharField(max_length=50, required=False)
    stress_level = serializers.IntegerField(min_value=1, max_value=10, required=False)




class UserSubmissionCreateSerializer(serializers.Serializer):
    """Serializer for creating a new submission with all details"""
    # Basic Information
    name = serializers.CharField(max_length=100)
    age = serializers.IntegerField(min_value=0, max_value=120)
    gender = serializers.ChoiceField(choices=['M', 'F', 'O'])
    
    # Physical Metrics
    height = serializers.FloatField(min_value=0, required=False, allow_null=True)
    weight = serializers.FloatField(min_value=0, required=False, allow_null=True)
    
    # Professional Info
    occupation = serializers.CharField(max_length=100, required=False, allow_blank=True)
    
    # Symptoms
    symptoms = SubmissionSymptomInputSerializer(many=True)
    
    # Medical History
    existing_diseases = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    allergies = serializers.CharField(required=False, allow_blank=True)
    medications = serializers.CharField(required=False, allow_blank=True)
    family_history = serializers.CharField(required=False, allow_blank=True)
    
    # Lifestyle
    lifestyle = LifestyleSerializer(required=False)
    
    # Travel
    travel_history = serializers.CharField(required=False, allow_blank=True)

    def validate_symptoms(self, value):
        if not value:
            raise serializers.ValidationError("At least one symptom must be provided.")
        
        # Check if all symptom IDs exist
        symptom_ids = [s['id'] for s in value]
        existing_ids = Symptom.objects.filter(id__in=symptom_ids).values_list('id', flat=True)
        
        if len(existing_ids) != len(symptom_ids):
            raise serializers.ValidationError("One or more invalid symptom IDs provided.")

        # Auto-fill severity from dataset if missing
        from .models import DiseaseSymptom
        for s in value:
            if 'severity' not in s or s['severity'] is None:
                symptom_obj = Symptom.objects.filter(id=s['id']).first()
                if symptom_obj:
                    ds = DiseaseSymptom.objects.filter(symptom=symptom_obj).order_by('-weight').first()
                    s['severity'] = ds.weight if ds else 5
                else:
                    s['severity'] = 5
        return value



class SubmissionSymptomOutputSerializer(serializers.ModelSerializer):
    """Serializer for symptom output in submission"""
    id = serializers.IntegerField(source='symptom.id')
    name = serializers.CharField(source='symptom.name')
    
    class Meta:
        model = SubmissionSymptom
        fields = ['id', 'name', 'severity', 'duration', 'onset']


class DiseasePredictionSerializer(serializers.ModelSerializer):
    """Serializer for predicted diseases"""
    id = serializers.IntegerField(source='disease.id')
    name = serializers.CharField(source='disease.name')
    
    class Meta:
        model = DiseasePrediction
        fields = ['id', 'name', 'confidence_score']


class LifestyleOutputSerializer(serializers.Serializer):
    """Serializer for lifestyle output"""
    smoking = serializers.BooleanField()
    alcohol = serializers.BooleanField()
    diet = serializers.CharField()
    sleep_hours = serializers.IntegerField()
    exercise_frequency = serializers.CharField()
    stress_level = serializers.IntegerField()


class UserSubmissionSerializer(serializers.ModelSerializer):
    """Serializer for submission output"""
    user = serializers.SerializerMethodField()
    symptoms = SubmissionSymptomOutputSerializer(source='submission_symptoms', many=True)
    predicted_diseases = DiseasePredictionSerializer(many=True)
    primary_prediction = serializers.SerializerMethodField()
    lifestyle = serializers.SerializerMethodField()
    
    class Meta:
        model = UserSubmission
        fields = [
            'id', 'user', 'name', 'age', 'gender', 'height', 'weight', 'bmi',
            'occupation', 'symptoms', 'existing_diseases', 'allergies', 'medications',
            'lifestyle', 'travel_history', 'family_history', 'predicted_diseases',
            'primary_prediction', 'severity_score', 'severity_category', 'created_at'
        ]
    
    def get_user(self, obj):
        if obj.user:
            return {
                'id': obj.user.id,
                'username': obj.user.username
            }
        return None
    
    def get_lifestyle(self, obj):
        return {
            'smoking': obj.smoking,
            'alcohol': obj.alcohol,
            'diet': obj.get_diet_display() if obj.diet else '',
            'sleep_hours': obj.sleep_hours,
            'exercise_frequency': obj.exercise_frequency,
            'stress_level': obj.stress_level
        }
    
    def get_primary_prediction(self, obj):
        """Safely get primary prediction name"""
        if obj.primary_prediction:
            return obj.primary_prediction.name
        return None


class PredictionResultSerializer(serializers.Serializer):
    """Complete prediction result with recommendations"""
    submission = UserSubmissionSerializer()
    recommendations = serializers.DictField()
    additional_info = serializers.DictField()


class ReportSerializer(serializers.Serializer):
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    format = serializers.ChoiceField(choices=['pdf', 'csv', 'json'], default='pdf')
    include_personal_info = serializers.BooleanField(default=True)
    include_recommendations = serializers.BooleanField(default=True)