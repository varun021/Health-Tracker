from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import permissions
from django.db.models import Count, Q, F, Sum, Avg, Max, Min
from django.db.models.functions import TruncMonth, TruncWeek, TruncDay
from django.http import HttpResponse
from datetime import datetime, timedelta
from .models import Disease, Symptom, DiseaseSymptom, UserSubmission, SubmissionSymptom, DiseasePrediction
from .serializers import (
    DiseaseSerializer, SymptomSerializer, 
    UserSubmissionCreateSerializer, UserSubmissionSerializer,
    PredictionResultSerializer, ReportSerializer
)
from .utils import ReportGenerator
from .ml_predictor import HybridPredictor
import json
from django.utils import timezone
from django.utils.timezone import make_aware


class PredictionViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.predictor = HybridPredictor()
    
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
        """Calculate severity score based on symptom severity and weights"""
        if not symptom_details:
            return 0, 'NORMAL'
        
        total_severity = sum(s['severity'] for s in symptom_details)
        avg_severity = total_severity / len(symptom_details)
        
        severity_score = (avg_severity / 10) * 100
        
        if severity_score <= 30:
            category = 'NORMAL'
        elif severity_score <= 70:
            category = 'MODERATE'
        else:
            category = 'RISKY'
        
        return round(severity_score, 2), category

    def format_recommendations(self, text_field):
        """Convert text field with bullet points to list"""
        if not text_field:
            return []
        
        lines = text_field.strip().split('\n')
        recommendations = []
        
        for line in lines:
            cleaned = line.strip().lstrip('•').lstrip('-').lstrip('*').strip()
            if cleaned:
                recommendations.append(cleaned)
        
        return recommendations

    @action(detail=False, methods=['post'])
    def predict(self, request):
        """Enhanced prediction using Naive Bayes + Rule-based hybrid approach"""
        serializer = UserSubmissionCreateSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        
        # Use hybrid predictor
        predictions = self.predictor.predict(
            data['symptoms'],
            request.user if request.user.is_authenticated else None
        )
        
        if not predictions:
            return Response(
                {'error': 'No matching disease found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        severity_score, severity_category = self.calculate_severity(data['symptoms'])
        client_info = self.get_client_info(request)
        lifestyle_data = data.get('lifestyle', {})
        
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
        
        for symptom_data in data['symptoms']:
            symptom = Symptom.objects.get(id=symptom_data['id'])
            SubmissionSymptom.objects.create(
                submission=submission,
                symptom=symptom,
                severity=symptom_data['severity'],
                duration=symptom_data['duration'],
                onset=symptom_data['onset']
            )
        
        for rank, pred in enumerate(predictions, 1):
            DiseasePrediction.objects.create(
                submission=submission,
                disease=pred['disease'],
                confidence_score=pred['confidence'],
                rank=rank
            )
        
        primary_disease = predictions[0]['disease']
        
        result = {
            'submission': UserSubmissionSerializer(submission).data,
            'predictions': [
                {
                    'disease': pred['disease'].name,
                    'confidence': pred['confidence'],
                    'rank': idx + 1
                }
                for idx, pred in enumerate(predictions)
            ],
            'recommendations': {
                'lifestyle_tips': self.format_recommendations(primary_disease.lifestyle_tips),
                'diet_advice': self.format_recommendations(primary_disease.diet_advice),
                'medical_advice': self.format_recommendations(primary_disease.medical_advice)
            },
            'additional_info': {
                'severity_interpretation': self.get_severity_interpretation(severity_category),
                'next_steps': self.get_next_steps(severity_category, primary_disease.name),
                'disclaimer': "This is an AI-assisted health prediction using Naive Bayes ML algorithm. It should not replace professional medical advice."
            }
        }
        
        return Response(result, status=status.HTTP_201_CREATED)

    def get_severity_interpretation(self, category):
        interpretations = {
            'NORMAL': 'Mild symptoms detected — continue monitoring and maintain good health practices.',
            'MODERATE': 'Moderate symptoms detected — monitor health and seek care if symptoms worsen.',
            'RISKY': 'Severe symptoms detected — consult a healthcare provider immediately.'
        }
        return interpretations.get(category, '')

    def get_next_steps(self, category, disease_name):
        if category == 'RISKY':
            return f"Seek immediate medical attention. Your symptoms suggest {disease_name} which requires professional evaluation."
        elif category == 'MODERATE':
            return f"Track your symptoms for the next 3 days. If symptoms worsen, consult a healthcare provider."
        else:
            return f"Continue monitoring your symptoms. Maintain good hygiene and rest. Consult a doctor if symptoms persist."

    @action(detail=False, methods=['post'])
    def train_model(self, request):
        """Train/retrain the Naive Bayes model"""
        if not request.user.is_staff:
            return Response(
                {'error': 'Admin access required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            results = self.predictor.nb_predictor.train()
            return Response({
                'message': 'Model trained successfully',
                'details': results
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def analytics(self, request):
        """
        Comprehensive analytics dashboard
        """
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        user_submissions = UserSubmission.objects.filter(user=request.user)
        
        if not user_submissions.exists():
            return Response({
                'message': 'No data available',
                'overview': self._get_empty_overview(),
                'trends': {},
                'insights': {}
            })
        
        # Time range filter
        days = int(request.query_params.get('days', 30))
        start_date = datetime.now() - timedelta(days=days)
        filtered_submissions = user_submissions.filter(created_at__gte=start_date)
        
        analytics = {
            'overview': self._get_overview_stats(user_submissions),
            'trends': self._get_trend_analysis(filtered_submissions, days),
            'disease_analytics': self._get_disease_analytics(user_submissions),
            'symptom_analytics': self._get_symptom_analytics(user_submissions),
            'lifestyle_correlation': self._get_lifestyle_correlation(user_submissions),
            'severity_trends': self._get_severity_trends(filtered_submissions),
            'time_patterns': self._get_time_patterns(user_submissions),
            'health_score': self._calculate_health_score(user_submissions)
        }
        
        return Response(analytics)

    def _get_empty_overview(self):
        return {
            'total_predictions': 0,
            'avg_severity': 0,
            'most_common_disease': None,
            'severity_distribution': {'normal': 0, 'moderate': 0, 'risky': 0}
        }

    def _get_overview_stats(self, submissions):
        stats = submissions.aggregate(
            total=Count('id'),
            avg_severity=Avg('severity_score'),
            max_severity=Max('severity_score'),
            min_severity=Min('severity_score')
        )
        
        most_common = (submissions
            .values('primary_prediction__name')
            .annotate(count=Count('id'))
            .order_by('-count')
            .first())
        
        severity_dist = {
            'normal': submissions.filter(severity_category='NORMAL').count(),
            'moderate': submissions.filter(severity_category='MODERATE').count(),
            'risky': submissions.filter(severity_category='RISKY').count()
        }
        
        return {
            'total_predictions': stats['total'],
            'avg_severity': round(stats['avg_severity'], 2) if stats['avg_severity'] else 0,
            'max_severity': stats['max_severity'] or 0,
            'min_severity': stats['min_severity'] or 0,
            'most_common_disease': most_common['primary_prediction__name'] if most_common else None,
            'severity_distribution': severity_dist
        }

    def _get_trend_analysis(self, submissions, days):
        """Analyze trends over time"""
        if days <= 7:
            truncate_func = TruncDay
            date_format = '%Y-%m-%d'
        elif days <= 90:
            truncate_func = TruncWeek
            date_format = '%Y-W%W'
        else:
            truncate_func = TruncMonth
            date_format = '%Y-%m'
        
        trends = (submissions
            .annotate(period=truncate_func('created_at'))
            .values('period')
            .annotate(
                count=Count('id'),
                avg_severity=Avg('severity_score'),
                normal=Count('id', filter=Q(severity_category='NORMAL')),
                moderate=Count('id', filter=Q(severity_category='MODERATE')),
                risky=Count('id', filter=Q(severity_category='RISKY'))
            )
            .order_by('period'))
        
        return [{
            'period': trend['period'].strftime(date_format),
            'count': trend['count'],
            'avg_severity': round(trend['avg_severity'], 2),
            'severity_breakdown': {
                'normal': trend['normal'],
                'moderate': trend['moderate'],
                'risky': trend['risky']
            }
        } for trend in trends]

    def _get_disease_analytics(self, submissions):
        """Detailed disease analytics"""
        disease_stats = (submissions
            .values('primary_prediction__name')
            .annotate(
                count=Count('id'),
                avg_severity=Avg('severity_score'),
                last_occurrence=Max('created_at')
            )
            .order_by('-count'))
        
        return [{
            'disease': stat['primary_prediction__name'],
            'occurrences': stat['count'],
            'avg_severity': round(stat['avg_severity'], 2),
            'last_seen': stat['last_occurrence'].strftime('%Y-%m-%d')
        } for stat in disease_stats]

    def _get_symptom_analytics(self, submissions):
        """Most common symptoms"""
        symptom_stats = (SubmissionSymptom.objects
            .filter(submission__in=submissions)
            .values('symptom__name')
            .annotate(
                count=Count('id'),
                avg_severity=Avg('severity')
            )
            .order_by('-count')[:10])
        
        return [{
            'symptom': stat['symptom__name'],
            'frequency': stat['count'],
            'avg_severity': round(stat['avg_severity'], 2)
        } for stat in symptom_stats]

    def _get_lifestyle_correlation(self, submissions):
        """Correlate lifestyle factors with health outcomes"""
        lifestyle_analysis = {
            'smoking': self._analyze_factor(submissions, 'smoking'),
            'alcohol': self._analyze_factor(submissions, 'alcohol'),
            'sleep': self._analyze_sleep(submissions),
            'stress': self._analyze_stress(submissions)
        }
        
        return lifestyle_analysis

    def _analyze_factor(self, submissions, field):
        with_factor = submissions.filter(**{field: True})
        without_factor = submissions.filter(**{field: False})
        
        return {
            'with_factor': {
                'count': with_factor.count(),
                'avg_severity': round(with_factor.aggregate(avg=Avg('severity_score'))['avg'] or 0, 2)
            },
            'without_factor': {
                'count': without_factor.count(),
                'avg_severity': round(without_factor.aggregate(avg=Avg('severity_score'))['avg'] or 0, 2)
            }
        }

    def _analyze_sleep(self, submissions):
        sleep_data = submissions.filter(sleep_hours__isnull=False)
        
        return {
            'avg_sleep_hours': round(sleep_data.aggregate(avg=Avg('sleep_hours'))['avg'] or 0, 2),
            'correlation_with_severity': self._calculate_correlation(sleep_data, 'sleep_hours', 'severity_score')
        }

    def _analyze_stress(self, submissions):
        stress_data = submissions.filter(stress_level__isnull=False)
        
        return {
            'avg_stress_level': round(stress_data.aggregate(avg=Avg('stress_level'))['avg'] or 0, 2),
            'correlation_with_severity': self._calculate_correlation(stress_data, 'stress_level', 'severity_score')
        }

    def _calculate_correlation(self, queryset, field1, field2):
        """Simple correlation calculation"""
        if not queryset.exists():
            return 0
        
        data = list(queryset.values_list(field1, field2))
        if len(data) < 2:
            return 0
        
        import numpy as np
        arr = np.array(data)
        correlation = np.corrcoef(arr[:, 0], arr[:, 1])[0, 1]
        return round(correlation, 3) if not np.isnan(correlation) else 0

    def _get_severity_trends(self, submissions):
        """Track how severity changes over time"""
        return list(submissions
            .order_by('created_at')
            .values('created_at', 'severity_score', 'severity_category')[:50])

    def _get_time_patterns(self, submissions):
        """Analyze patterns by time of day/week"""
        from django.db.models.functions import ExtractHour, ExtractWeekDay
        
        hour_pattern = (submissions
            .annotate(hour=ExtractHour('created_at'))
            .values('hour')
            .annotate(count=Count('id'))
            .order_by('hour'))
        
        weekday_pattern = (submissions
            .annotate(weekday=ExtractWeekDay('created_at'))
            .values('weekday')
            .annotate(count=Count('id'))
            .order_by('weekday'))
        
        return {
            'by_hour': list(hour_pattern),
            'by_weekday': list(weekday_pattern)
        }

    def _calculate_health_score(self, submissions):
        """Calculate overall health score (0-100)"""
        if not submissions.exists():
            return 0
        
        # Evaluate the queryset immediately to avoid filtering after slicing
        recent = list(submissions.order_by('-created_at')[:10])
        
        # Calculate average severity from the list
        avg_severity = sum(sub.severity_score for sub in recent) / len(recent)
        
        # Count risky cases from the list
        risky_count = sum(1 for sub in recent if sub.severity_category == 'RISKY')
        
        # Invert severity to health score (lower severity = higher health)
        health_score = 100 - avg_severity
        
        # Adjust based on frequency of risky cases
        health_score -= (risky_count * 5)
        
        return max(0, min(100, round(health_score, 2)))

    @action(detail=False, methods=['get'])
    def export_data(self, request):
        """Export user data in various formats"""
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        format_type = request.query_params.get('format', 'json')
        
        submissions = (UserSubmission.objects
            .filter(user=request.user)
            .select_related('primary_prediction')
            .prefetch_related('submission_symptoms__symptom', 'predicted_diseases__disease'))
        
        if format_type == 'csv':
            return self._export_csv(submissions)
        elif format_type == 'json':
            serializer = UserSubmissionSerializer(submissions, many=True)
            return Response(serializer.data)
        else:
            return Response({'error': 'Invalid format'}, status=status.HTTP_400_BAD_REQUEST)

    def _export_csv(self, submissions):
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.writer(output)
        
        writer.writerow(['Date', 'Disease', 'Confidence', 'Severity Score', 'Category', 'Symptoms'])
        
        for sub in submissions:
            symptoms = ', '.join([ss.symptom.name for ss in sub.submission_symptoms.all()])
            pred = sub.predicted_diseases.first()
            
            writer.writerow([
                sub.created_at.strftime('%Y-%m-%d'),
                sub.primary_prediction.name if sub.primary_prediction else '',
                pred.confidence_score if pred else '',
                sub.severity_score,
                sub.severity_category,
                symptoms
            ])
        
        response = HttpResponse(output.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=health_data.csv'
        return response

    @action(detail=False, methods=['get'])
    def history(self, request):
        """Get user submission history with pagination"""
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        
        submissions = (UserSubmission.objects
            .filter(user=request.user)
            .select_related('primary_prediction')
            .prefetch_related('submission_symptoms__symptom', 'predicted_diseases__disease')
            .order_by('-created_at'))
        
        # Pagination
        start = (page - 1) * page_size
        end = start + page_size
        paginated = submissions[start:end]
        
        serializer = UserSubmissionSerializer(paginated, many=True)
        
        return Response({
            'count': submissions.count(),
            'page': page,
            'page_size': page_size,
            'total_pages': (submissions.count() + page_size - 1) // page_size,
            'results': serializer.data
        })

    @action(detail=False, methods=['get'])
    @action(detail=False, methods=['get'])
    def comparison_report(self, request):
        """Compare health metrics across different time periods"""
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Get current period (last 30 days) with timezone awareness
        current_end = timezone.now()
        current_start = current_end - timedelta(days=30)
        
        # Get previous period (30-60 days ago)
        previous_end = current_start
        previous_start = previous_end - timedelta(days=30)
        
        current_data = self._get_period_stats(request.user, current_start, current_end)
        previous_data = self._get_period_stats(request.user, previous_start, previous_end)
        
        # Calculate changes
        comparison = {
            'current_period': {
                'start': current_start.strftime('%Y-%m-%d'),
                'end': current_end.strftime('%Y-%m-%d'),
                'stats': current_data
            },
            'previous_period': {
                'start': previous_start.strftime('%Y-%m-%d'),
                'end': previous_end.strftime('%Y-%m-%d'),
                'stats': previous_data
            },
            'changes': self._calculate_changes(current_data, previous_data)
        }
        
        return Response(comparison)

    def _get_period_stats(self, user, start_date, end_date):
        submissions = UserSubmission.objects.filter(
            user=user,
            created_at__gte=start_date,
            created_at__lte=end_date
        )
        
        if not submissions.exists():
            return {
                'total_predictions': 0,
                'avg_severity': 0,
                'risky_cases': 0,
                'most_common_disease': None
            }
        
        stats = submissions.aggregate(
            total=Count('id'),
            avg_severity=Avg('severity_score'),
            risky=Count('id', filter=Q(severity_category='RISKY'))
        )
        
        most_common = (submissions
            .values('primary_prediction__name')
            .annotate(count=Count('id'))
            .order_by('-count')
            .first())
        
        return {
            'total_predictions': stats['total'],
            'avg_severity': round(stats['avg_severity'], 2) if stats['avg_severity'] else 0,
            'risky_cases': stats['risky'],
            'most_common_disease': most_common['primary_prediction__name'] if most_common else None
        }

    def _calculate_changes(self, current, previous):
        """Calculate percentage changes between periods"""
        changes = {}
        
        for key in ['total_predictions', 'avg_severity', 'risky_cases']:
            current_val = current[key]
            previous_val = previous[key]
            
            if previous_val == 0:
                change = 100 if current_val > 0 else 0
            else:
                change = ((current_val - previous_val) / previous_val) * 100
            
            changes[key] = {
                'value': round(change, 2),
                'direction': 'up' if change > 0 else 'down' if change < 0 else 'stable',
                'is_improvement': self._is_improvement(key, change)
            }
        
        return changes

    def _is_improvement(self, metric, change):
        """Determine if change is positive for health"""
        # For avg_severity and risky_cases, decrease is good
        if metric in ['avg_severity', 'risky_cases']:
            return change < 0
        # For total_predictions, stable or slight decrease might be good
        return abs(change) < 10

    @action(detail=False, methods=['get'])
    def recommendations_based_on_history(self, request):
        """
        Generate personalized recommendations based on user history
        """
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Get all submissions first
        submissions = UserSubmission.objects.filter(user=request.user).order_by('-created_at')
        
        if not submissions.exists():
            return Response({
                'message': 'No history available for recommendations',
                'recommendations': []
            })
        
        # Get the last 20 submissions for analysis - evaluate immediately to avoid multiple slicing
        recent_submissions = list(submissions[:20])
        
        recommendations = []
        
        # Analyze patterns
        avg_severity = sum(s.severity_score for s in recent_submissions) / len(recent_submissions)
        risky_count = sum(1 for s in recent_submissions if s.severity_category == 'RISKY')
        
        # Severity-based recommendations
        if avg_severity > 70:
            recommendations.append({
                'category': 'urgent',
                'title': 'High Average Severity Detected',
                'message': 'Your recent predictions show high severity. Please consult a healthcare provider.',
                'action': 'Schedule a medical checkup'
            })
        elif avg_severity > 50:
            recommendations.append({
                'category': 'warning',
                'title': 'Moderate Health Concerns',
                'message': 'Monitor your symptoms closely and maintain healthy habits.',
                'action': 'Track symptoms daily'
            })
        
        # Risky cases
        if risky_count >= 3:
            recommendations.append({
                'category': 'urgent',
                'title': 'Multiple Risky Cases',
                'message': f'You have {risky_count} risky predictions. Immediate medical attention recommended.',
                'action': 'Consult a doctor immediately'
            })
        
        # Lifestyle recommendations
        smokers = submissions.filter(smoking=True).count()
        if smokers > submissions.count() * 0.7:
            recommendations.append({
                'category': 'lifestyle',
                'title': 'Smoking Cessation',
                'message': 'Smoking is detected in most of your records. Consider quitting for better health.',
                'action': 'Seek smoking cessation support'
            })
        
        # Sleep analysis
        low_sleep = submissions.filter(sleep_hours__lt=6).count()
        if low_sleep > 5:
            recommendations.append({
                'category': 'lifestyle',
                'title': 'Insufficient Sleep',
                'message': 'You frequently report less than 6 hours of sleep. Better sleep can improve health.',
                'action': 'Aim for 7-9 hours of sleep'
            })
        
        # Stress analysis
        high_stress = submissions.filter(stress_level__gte=8).count()
        if high_stress > 5:
            recommendations.append({
                'category': 'lifestyle',
                'title': 'High Stress Levels',
                'message': 'High stress is frequently reported. Consider stress management techniques.',
                'action': 'Practice relaxation techniques'
            })
        
        # Disease pattern
        disease_counts = (submissions
            .values('primary_prediction__name')
            .annotate(count=Count('id'))
            .order_by('-count'))
        
        if disease_counts and disease_counts[0]['count'] >= 5:
            recommendations.append({
                'category': 'medical',
                'title': 'Recurring Condition',
                'message': f'{disease_counts[0]["primary_prediction__name"]} appears frequently in your history.',
                'action': 'Discuss with your doctor about prevention strategies'
            })
        
        # Calculate health score using the already evaluated recent_submissions
        health_score = 100 - avg_severity  # Base score
        health_score -= (risky_count * 5)  # Penalty for risky cases
        health_score = max(0, min(100, round(health_score, 2)))  # Ensure range 0-100
        
        return Response({
            'total_recommendations': len(recommendations),
            'health_score': health_score,
            'recommendations': recommendations
        })

    @action(detail=False, methods=['post', 'get'])
    def generate_report(self, request):
        """Generate comprehensive user report in specified format"""
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if request.method == 'POST':
            data = request.data
        else:
            data = request.query_params.dict()

        serializer = ReportSerializer(data=data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        
        start_date = validated_data.get('start_date')
        end_date = validated_data.get('end_date')
        
        if not start_date:
            start_date = timezone.now() - timedelta(days=30)
        if not end_date:
            end_date = timezone.now()

        submissions = (UserSubmission.objects
            .filter(
                user=request.user, 
                created_at__date__gte=start_date,
                created_at__date__lte=end_date
            )
            .select_related('primary_prediction')
            .prefetch_related('submission_symptoms__symptom', 'predicted_diseases__disease')
            .order_by('-created_at'))

        if not submissions.exists():
            return Response({
                'report_metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'total_predictions': 0,
                    'date_range': {
                        'start': start_date.strftime('%Y-%m-%d'),
                        'end': end_date.strftime('%Y-%m-%d')
                    }
                },
                'predictions': []
            }, status=status.HTTP_200_OK)

        try:
            generator = ReportGenerator(
                submissions,
                include_personal=validated_data.get('include_personal_info', True),
                include_recommendations=validated_data.get('include_recommendations', True)
            )

            format_type = validated_data.get('format', 'pdf')
            
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
            return Response(
                {'error': f'Error generating report: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DiseaseViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Disease.objects.all()
    serializer_class = DiseaseSerializer


class SymptomViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Symptom.objects.all()
    serializer_class = SymptomSerializer