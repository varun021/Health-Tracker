from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import permissions
from django.db.models import Count, Q, F, Sum, Avg
from django.db.models.functions import TruncMonth, ExtractHour, ExtractWeekDay
from django.http import HttpResponse
from datetime import datetime, timedelta
from .models import Disease, Symptom, DiseaseSymptom, UserSubmission, SubmissionSymptom, DiseasePrediction
from .serializers import (
    DiseaseSerializer, SymptomSerializer, 
    UserSubmissionCreateSerializer, UserSubmissionSerializer,
    PredictionResultSerializer, ReportSerializer
)
from .utils import ReportGenerator
import json


class DiseaseViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Disease.objects.all()
    serializer_class = DiseaseSerializer


class SymptomViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Symptom.objects.all()
    serializer_class = SymptomSerializer


class PredictionViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]
    
    def get_client_info(self, request):
        """Extract client information from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        
        if not request.session.session_key:
            request.session.create()
            
        return {
            'ip_address': ip,
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'session_id': request.session.session_key
        }

    def calculate_severity(self, symptom_details):
        """
        Calculate severity score based on symptom severity and weights
        """
        if not symptom_details:
            return 0, 'NORMAL'
        
        total_severity = sum(s['severity'] for s in symptom_details)
        avg_severity = total_severity / len(symptom_details)
        
        # Normalize to 0-100 scale
        severity_score = (avg_severity / 10) * 100
        
        # Categorize
        if severity_score <= 30:
            category = 'NORMAL'
        elif severity_score <= 70:
            category = 'MODERATE'
        else:
            category = 'RISKY'
        
        return round(severity_score, 2), category
    
    def predict_multiple_diseases(self, symptom_data, user=None):
        """
        Predict top 3 diseases based on symptoms with confidence scores
        """
        symptom_ids = [s['id'] for s in symptom_data]
        symptom_severities = {s['id']: s['severity'] for s in symptom_data}
        
        # Get all diseases with their symptoms
        diseases = Disease.objects.prefetch_related('disease_symptoms')
        disease_scores = []
        
        # Get user history for personalization
        user_history = {}
        if user and user.is_authenticated:
            previous_predictions = (DiseasePrediction.objects
                .filter(submission__user=user, confidence_score__gte=70)
                .values('disease_id')
                .annotate(count=Count('id'))
                .order_by('-count'))
            user_history = {p['disease_id']: p['count'] for p in previous_predictions}

        for disease in diseases:
            disease_symptoms = disease.disease_symptoms.filter(symptom_id__in=symptom_ids)
            
            if disease_symptoms.exists():
                # Calculate matching score
                matched_count = disease_symptoms.count()
                total_disease_symptoms = disease.disease_symptoms.count()
                
                # Base matching percentage
                match_percentage = (matched_count / total_disease_symptoms) * 100
                
                # Weight-based score considering symptom severity
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
                
                # Combined score
                confidence = (match_percentage * 0.4) + (weight_percentage * 0.6)
                
                # Add user history bonus
                if disease.id in user_history:
                    history_bonus = min(user_history[disease.id] * 3, 15)
                    confidence = min(confidence + history_bonus, 100)
                
                disease_scores.append({
                    'disease': disease,
                    'confidence': round(confidence, 2)
                })
        
        # Sort by confidence and get top 3
        disease_scores.sort(key=lambda x: x['confidence'], reverse=True)
        top_predictions = disease_scores[:3]
        
        return top_predictions

    def format_recommendations(self, text_field):
        """Convert text field with bullet points to list"""
        if not text_field:
            return []
        
        lines = text_field.strip().split('\n')
        recommendations = []
        
        for line in lines:
            # Remove bullet points and clean up
            cleaned = line.strip().lstrip('•').lstrip('-').lstrip('*').strip()
            if cleaned:
                recommendations.append(cleaned)
        
        return recommendations

    @action(detail=False, methods=['post'])
    def predict(self, request):
        """
        Enhanced prediction endpoint with comprehensive response
        """
        serializer = UserSubmissionCreateSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        
        # Get disease predictions
        predictions = self.predict_multiple_diseases(
            data['symptoms'],
            request.user if request.user.is_authenticated else None
        )
        
        if not predictions:
            return Response(
                {'error': 'No matching disease found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Calculate severity
        severity_score, severity_category = self.calculate_severity(data['symptoms'])
        
        # Get client info
        client_info = self.get_client_info(request)
        
        # Extract lifestyle data
        lifestyle_data = data.get('lifestyle', {})
        
        # Create submission
        submission = UserSubmission.objects.create(
            user=request.user if request.user.is_authenticated else None,
            name=data['name'],
            age=data['age'],
            gender=data['gender'],
            height=data.get('height'),
            weight=data.get('weight'),
            occupation=data.get('occupation', ''),
            existing_diseases=data.get('existing_diseases', []),
            allergies=data.get('allergies', ''),
            medications=data.get('medications', ''),
            family_history=data.get('family_history', ''),
            smoking=lifestyle_data.get('smoking', False),
            alcohol=lifestyle_data.get('alcohol', False),
            diet=lifestyle_data.get('diet', ''),
            sleep_hours=lifestyle_data.get('sleep_hours'),
            exercise_frequency=lifestyle_data.get('exercise_frequency', ''),
            stress_level=lifestyle_data.get('stress_level'),
            travel_history=data.get('travel_history', ''),
            primary_prediction=predictions[0]['disease'],
            severity_score=severity_score,
            severity_category=severity_category,
            **client_info
        )
        
        # Add symptoms with details
        for symptom_data in data['symptoms']:
            symptom = Symptom.objects.get(id=symptom_data['id'])
            SubmissionSymptom.objects.create(
                submission=submission,
                symptom=symptom,
                severity=symptom_data['severity'],
                duration=symptom_data['duration'],
                onset=symptom_data['onset']
            )
        
        # Add disease predictions
        for rank, pred in enumerate(predictions, 1):
            DiseasePrediction.objects.create(
                submission=submission,
                disease=pred['disease'],
                confidence_score=pred['confidence'],
                rank=rank
            )
        
        # Get primary disease for recommendations
        primary_disease = predictions[0]['disease']
        
        # Prepare response
        result = {
            'submission': UserSubmissionSerializer(submission).data,
            'recommendations': {
                'lifestyle_tips': self.format_recommendations(primary_disease.lifestyle_tips),
                'diet_advice': self.format_recommendations(primary_disease.diet_advice),
                'medical_advice': self.format_recommendations(primary_disease.medical_advice)
            },
            'additional_info': {
                'severity_interpretation': self.get_severity_interpretation(severity_category),
                'next_steps': self.get_next_steps(severity_category, primary_disease.name),
                'disclaimer': "This is an AI-assisted health prediction. It should not replace professional medical advice."
            }
        }
        
        return Response(result, status=status.HTTP_201_CREATED)

    def get_severity_interpretation(self, category):
        """Get interpretation based on severity category"""
        interpretations = {
            'NORMAL': 'Mild symptoms detected — continue monitoring and maintain good health practices.',
            'MODERATE': 'Moderate symptoms detected — monitor health and seek care if symptoms worsen.',
            'RISKY': 'Severe symptoms detected — consult a healthcare provider immediately.'
        }
        return interpretations.get(category, '')

    def get_next_steps(self, category, disease_name):
        """Get next steps based on severity"""
        if category == 'RISKY':
            return f"Seek immediate medical attention. Your symptoms suggest {disease_name} which requires professional evaluation."
        elif category == 'MODERATE':
            return f"Track your symptoms for the next 3 days. If symptoms worsen, consult a healthcare provider."
        else:
            return f"Continue monitoring your symptoms. Maintain good hygiene and rest. Consult a doctor if symptoms persist."

    @action(detail=False, methods=['get'])
    def history(self, request):
        """Get user submission history"""
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )
            
        submissions = (UserSubmission.objects
            .filter(user=request.user)
            .select_related('primary_prediction')
            .prefetch_related('submission_symptoms__symptom', 'predicted_diseases__disease')
            .order_by('-created_at')[:20])
            
        serializer = UserSubmissionSerializer(submissions, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def reports(self, request):
        """
        NEW: GET endpoint to fetch all user reports with optional filtering
        Query params:
        - limit: number of reports (default: 10)
        - start_date: filter from date (YYYY-MM-DD)
        - end_date: filter to date (YYYY-MM-DD)
        - severity: filter by severity (NORMAL, MODERATE, RISKY)
        """
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Base queryset
        queryset = (UserSubmission.objects
            .filter(user=request.user)
            .select_related('primary_prediction')
            .prefetch_related('submission_symptoms__symptom', 'predicted_diseases__disease'))
        
        # Apply filters
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        severity = request.query_params.get('severity')
        limit = request.query_params.get('limit', 10)
        
        try:
            limit = int(limit)
        except ValueError:
            limit = 10
        
        if start_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                queryset = queryset.filter(created_at__date__gte=start_date)
            except ValueError:
                return Response(
                    {'error': 'Invalid start_date format. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        if end_date:
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                queryset = queryset.filter(created_at__date__lte=end_date)
            except ValueError:
                return Response(
                    {'error': 'Invalid end_date format. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        if severity and severity in ['NORMAL', 'MODERATE', 'RISKY']:
            queryset = queryset.filter(severity_category=severity)
        
        # Order and limit
        submissions = queryset.order_by('-created_at')[:limit]
        
        # Serialize
        serializer = UserSubmissionSerializer(submissions, many=True)
        
        # Add metadata
        response_data = {
            'count': submissions.count(),
            'total_count': UserSubmission.objects.filter(user=request.user).count(),
            'filters_applied': {
                'start_date': start_date.strftime('%Y-%m-%d') if start_date else None,
                'end_date': end_date.strftime('%Y-%m-%d') if end_date else None,
                'severity': severity,
                'limit': limit
            },
            'reports': serializer.data
        }
        
        return Response(response_data)

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get comprehensive user statistics with proper formatting"""
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        print(f"User ID: {request.user.id}")  # Debug print
        
        user_submissions = UserSubmission.objects.filter(user=request.user)
        print(f"Total submissions found: {user_submissions.count()}")  # Debug print
        
        if not user_submissions.exists():
            print("No submissions found for user")  # Debug print
            return Response({
                'message': 'No submissions found',
                'overall': {
                    'total_predictions': 0,
                    'avg_severity': 0,
                    'normal_cases': 0,
                    'moderate_cases': 0,
                    'risky_cases': 0
                },
                'diseases': [],
                'monthly_trends': [],
                'severity_distribution': {
                    'normal': 0,
                    'moderate': 0,
                    'risky': 0
                },
                'recent_activity': []
            })
        
        # Overall statistics
        overall_stats = user_submissions.aggregate(
            total_predictions=Count('id'),
            avg_severity=Avg('severity_score'),
            normal_cases=Count('id', filter=Q(severity_category='NORMAL')),
            moderate_cases=Count('id', filter=Q(severity_category='MODERATE')),
            risky_cases=Count('id', filter=Q(severity_category='RISKY'))
        )
        
        # Format average severity
        if overall_stats['avg_severity']:
            overall_stats['avg_severity'] = round(overall_stats['avg_severity'], 2)
        else:
            overall_stats['avg_severity'] = 0
        
        # Disease statistics
        disease_stats = (user_submissions
            .values('primary_prediction__name')
            .annotate(
                count=Count('id'), 
                avg_severity=Avg('severity_score')
            )
            .order_by('-count')[:5])
        
        # Format disease stats
        formatted_disease_stats = []
        for stat in disease_stats:
            formatted_disease_stats.append({
                'disease_name': stat['primary_prediction__name'],
                'count': stat['count'],
                'avg_severity': round(stat['avg_severity'], 2) if stat['avg_severity'] else 0,
                'percentage': round((stat['count'] / overall_stats['total_predictions']) * 100, 1)
            })
        
        # Monthly trends (last 6 months)
        six_months_ago = datetime.now() - timedelta(days=180)
        monthly_stats = (user_submissions
            .filter(created_at__gte=six_months_ago)
            .annotate(month=TruncMonth('created_at'))
            .values('month')
            .annotate(
                count=Count('id'), 
                avg_severity=Avg('severity_score')
            )
            .order_by('month'))
        
        # Format monthly stats
        formatted_monthly_stats = []
        for stat in monthly_stats:
            formatted_monthly_stats.append({
                'month': stat['month'].strftime('%Y-%m'),
                'month_name': stat['month'].strftime('%B %Y'),
                'count': stat['count'],
                'avg_severity': round(stat['avg_severity'], 2) if stat['avg_severity'] else 0
            })
        
        # Recent activity (last 5 submissions)
        recent_submissions = (user_submissions
            .select_related('primary_prediction')
            .order_by('-created_at')[:5])
        
        recent_activity = []
        for sub in recent_submissions:
            recent_activity.append({
                'id': sub.id,
                'date': sub.created_at.strftime('%Y-%m-%d'),
                'time': sub.created_at.strftime('%H:%M'),
                'disease': sub.primary_prediction.name if sub.primary_prediction else 'Unknown',
                'severity_category': sub.severity_category,
                'severity_score': sub.severity_score
            })
        
        # Compile response
        statistics = {
            'overall': overall_stats,
            'diseases': formatted_disease_stats,
            'monthly_trends': formatted_monthly_stats,
            'severity_distribution': {
                'normal': {
                    'count': overall_stats['normal_cases'],
                    'percentage': round((overall_stats['normal_cases'] / overall_stats['total_predictions']) * 100, 1)
                },
                'moderate': {
                    'count': overall_stats['moderate_cases'],
                    'percentage': round((overall_stats['moderate_cases'] / overall_stats['total_predictions']) * 100, 1)
                },
                'risky': {
                    'count': overall_stats['risky_cases'],
                    'percentage': round((overall_stats['risky_cases'] / overall_stats['total_predictions']) * 100, 1)
                }
            },
            'recent_activity': recent_activity
        }
        
        return Response(statistics)

    @action(detail=False, methods=['post', 'get'])
    def generate_report(self, request):
        """Generate user report in specified format"""
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        print(f"User ID: {request.user.id}")  # Debug print
        
        # Handle both POST and GET requests
        if request.method == 'POST':
            data = request.data
        else:
            data = request.query_params.dict()

        print(f"Request data: {data}")  # Debug print

        serializer = ReportSerializer(data=data)
        if not serializer.is_valid():
            print(f"Serializer errors: {serializer.errors}")  # Debug print
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        
        # Set date range with defaults
        start_date = validated_data.get('start_date')
        end_date = validated_data.get('end_date')
        
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).date()
        if not end_date:
            end_date = datetime.now().date()

        print(f"Date range: {start_date} to {end_date}")  # Debug print

        # Fetch submissions
        submissions = (UserSubmission.objects
            .filter(
                user=request.user, 
                created_at__date__gte=start_date,
                created_at__date__lte=end_date
            )
            .select_related('primary_prediction')
            .prefetch_related('submission_symptoms__symptom', 'predicted_diseases__disease')
            .order_by('-created_at'))

        print(f"Found {submissions.count()} submissions")  # Debug print

        if not submissions.exists():
            # Return an empty report payload (200) so clients can handle "no data" gracefully
            return Response({
                'report_metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'total_predictions': 0,
                    'date_range': {
                        'start': start_date.strftime('%Y-%m-%d'),
                        'end': end_date.strftime('%Y-%m-%d')
                    },
                    'include_personal_info': validated_data.get('include_personal_info', True),
                    'include_recommendations': validated_data.get('include_recommendations', True)
                },
                'predictions': []
            }, status=status.HTTP_200_OK)

        try:
            # Generate report
            generator = ReportGenerator(
                submissions,
                include_personal=validated_data.get('include_personal_info', True),
                include_recommendations=validated_data.get('include_recommendations', True)
            )

            format_type = validated_data.get('format', 'pdf')
            print(f"Generating report in {format_type} format")  # Debug print
            
            if format_type == 'pdf':
                pdf = generator.generate_pdf()
                response = HttpResponse(pdf, content_type='application/pdf')
                filename = f'medical_report_{start_date}_{end_date}.pdf'
                response['Content-Disposition'] = f'attachment; filename={filename}'
                return response
                
            elif format_type == 'csv':
                csv_data = generator.generate_csv()
                response = HttpResponse(csv_data, content_type='text/csv')
                filename = f'medical_report_{start_date}_{end_date}.csv'
                response['Content-Disposition'] = f'attachment; filename={filename}'
                return response
                
            else:  # json
                json_str = generator.generate_json()
                json_data = json.loads(json_str)
                return Response(json_data, status=status.HTTP_200_OK)
                
        except Exception as e:
            print(f"Error generating report: {str(e)}")  # Debug print
            return Response(
                {'error': f'Error generating report: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )