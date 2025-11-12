from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Q, Avg, Max, Min
from django.db.models.functions import TruncMonth, TruncWeek, TruncDay
from django.http import HttpResponse
from datetime import datetime, timedelta
from django.utils import timezone
import json
import numpy as np

from .models import (
    Disease, Symptom, DiseaseSymptom,
    UserSubmission, SubmissionSymptom, DiseasePrediction
)
from .serializers import (
    DiseaseSerializer, SymptomSerializer,
    UserSubmissionCreateSerializer, UserSubmissionSerializer,
    ReportSerializer
)
from .utils import ReportGenerator
from .ml_predictor import HybridPredictor


class PredictionViewSet(viewsets.ViewSet):
    """
    Handles prediction, training, analytics, and dataset import.
    """
    permission_classes = [permissions.IsAuthenticated]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.predictor = HybridPredictor()

    # ---------------------------------------------------------------------
    def get_client_info(self, request):
        """Extract client info."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        ip = x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')
        if not request.session.session_key:
            request.session.create()
        return {
            'ip_address': ip,
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'session_id': request.session.session_key
        }

    # ---------------------------------------------------------------------
    def calculate_severity(self, symptom_details):
        """Calculate average severity score and category."""
        if not symptom_details:
            return 0, 'NORMAL'
        total_severity = sum(s.get('severity', 5) for s in symptom_details)
        avg_severity = total_severity / len(symptom_details)
        severity_score = (avg_severity / 10) * 100

        if severity_score <= 30:
            category = 'NORMAL'
        elif severity_score <= 70:
            category = 'MODERATE'
        else:
            category = 'RISKY'

        return round(severity_score, 2), category

    # ---------------------------------------------------------------------
    def format_recommendations(self, text_field):
        """Convert multi-line text to a bullet list."""
        if not text_field:
            return []
        lines = text_field.strip().split('\n')
        return [line.strip().lstrip('•- ').strip() for line in lines if line.strip()]

    # ---------------------------------------------------------------------
    @action(detail=False, methods=['post'])
    def predict(self, request):
        """Predict diseases using hybrid (ML + rule-based) approach."""
        serializer = UserSubmissionCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        data = serializer.validated_data

        # Auto-fill missing severities
        for s in data['symptoms']:
            if 'severity' not in s or s['severity'] is None:
                symptom_obj = Symptom.objects.get(id=s['id'])
                ds = DiseaseSymptom.objects.filter(symptom=symptom_obj).order_by('-weight').first()
                s['severity'] = ds.weight if ds else 5

        predictions = self.predictor.predict(
            data['symptoms'],
            request.user if request.user.is_authenticated else None
        )

        if not predictions:
            return Response({'error': 'No matching disease found'}, status=status.HTTP_404_NOT_FOUND)

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

        # Save symptom details (auto-severity supported)
        for s in data['symptoms']:
            symptom = Symptom.objects.get(id=s['id'])
            SubmissionSymptom.objects.create(
                submission=submission,
                symptom=symptom,
                severity=s['severity'],
                duration=s.get('duration', 'Unknown'),
                onset=s.get('onset', 'SUDDEN')
            )

        # Save predictions
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
                } for idx, pred in enumerate(predictions)
            ],
            'recommendations': {
                'lifestyle_tips': self.format_recommendations(primary_disease.lifestyle_tips),
                'diet_advice': self.format_recommendations(primary_disease.diet_advice),
                'medical_advice': self.format_recommendations(primary_disease.medical_advice)
            },
            'additional_info': {
                'severity_interpretation': self.get_severity_interpretation(severity_category),
                'next_steps': self.get_next_steps(severity_category, primary_disease.name),
                'disclaimer': (
                    "This is an AI-assisted prediction using a Hybrid ML model. "
                    "It should not replace professional medical advice."
                )
            }
        }
        return Response(result, status=status.HTTP_201_CREATED)

    # ---------------------------------------------------------------------
    def get_severity_interpretation(self, category):
        return {
            'NORMAL': 'Mild symptoms detected — continue monitoring and maintain good health practices.',
            'MODERATE': 'Moderate symptoms detected — monitor health and seek care if symptoms worsen.',
            'RISKY': 'Severe symptoms detected — consult a healthcare provider immediately.'
        }.get(category, '')

    # ---------------------------------------------------------------------
    def get_next_steps(self, category, disease_name):
        if category == 'RISKY':
            return f"Seek immediate medical attention. Symptoms suggest {disease_name} which needs evaluation."
        elif category == 'MODERATE':
            return "Track symptoms for 3 days. If they worsen, consult a doctor."
        else:
            return "Continue monitoring. Maintain rest and hydration."

    # ---------------------------------------------------------------------
    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def train_model(self, request):
        """Train/retrain Naive Bayes model."""
        try:
            results = self.predictor.nb_predictor.train()
            return Response({'message': 'Model trained successfully', 'details': results})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ---------------------------------------------------------------------
    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def import_dataset(self, request):
        """Import dataset and auto-train model."""
        try:
            from .data_loader import import_disease_data
            from .ml_predictor import NaiveBayesPredictor
            import_disease_data()
            NaiveBayesPredictor().train()
            return Response({'message': 'Dataset imported and model trained successfully'})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ---------------------------------------------------------------------
    @action(detail=False, methods=['get'])
    def analytics(self, request):
        """Return user analytics dashboard."""
        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

        user_submissions = UserSubmission.objects.filter(user=request.user)
        if not user_submissions.exists():
            return Response({
                'message': 'No data available',
                'overview': self._get_empty_overview(),
                'trends': {},
                'insights': {}
            })

        days = int(request.query_params.get('days', 30))
        start_date = datetime.now() - timedelta(days=days)
        filtered = user_submissions.filter(created_at__gte=start_date)
        analytics = {
            'overview': self._get_overview_stats(user_submissions),
            'trends': self._get_trend_analysis(filtered, days),
            'disease_analytics': self._get_disease_analytics(user_submissions),
            'symptom_analytics': self._get_symptom_analytics(user_submissions),
            'health_score': self._calculate_health_score(user_submissions)
        }
        return Response(analytics)

    # ---------------------------------------------------------------------
    def _get_empty_overview(self):
        return {
            'total_predictions': 0,
            'avg_severity': 0,
            'most_common_disease': None,
            'severity_distribution': {'normal': 0, 'moderate': 0, 'risky': 0}
        }

    # ---------------------------------------------------------------------
    def _get_overview_stats(self, submissions):
        stats = submissions.aggregate(
            total=Count('id'),
            avg_severity=Avg('severity_score'),
            max_severity=Max('severity_score'),
            min_severity=Min('severity_score')
        )
        most_common = (
            submissions.values('primary_prediction__name')
            .annotate(count=Count('id')).order_by('-count').first()
        )
        return {
            'total_predictions': stats['total'],
            'avg_severity': round(stats['avg_severity'], 2) if stats['avg_severity'] else 0,
            'max_severity': stats['max_severity'] or 0,
            'min_severity': stats['min_severity'] or 0,
            'most_common_disease': most_common['primary_prediction__name'] if most_common else None,
        }

    # ---------------------------------------------------------------------
    def _get_trend_analysis(self, submissions, days):
        if days <= 7:
            trunc = TruncDay; fmt = '%Y-%m-%d'
        elif days <= 90:
            trunc = TruncWeek; fmt = '%Y-W%W'
        else:
            trunc = TruncMonth; fmt = '%Y-%m'
        trends = (
            submissions.annotate(period=trunc('created_at'))
            .values('period')
            .annotate(count=Count('id'), avg_severity=Avg('severity_score'))
            .order_by('period')
        )
        return [
            {'period': t['period'].strftime(fmt),
             'count': t['count'],
             'avg_severity': round(t['avg_severity'], 2)} for t in trends
        ]

    # ---------------------------------------------------------------------
    def _get_disease_analytics(self, submissions):
        stats = (
            submissions.values('primary_prediction__name')
            .annotate(count=Count('id'), avg_severity=Avg('severity_score'))
            .order_by('-count')
        )
        return [
            {
                'disease': s['primary_prediction__name'],
                'occurrences': s['count'],
                'avg_severity': round(s['avg_severity'], 2)
            } for s in stats
        ]

    # ---------------------------------------------------------------------
    def _get_symptom_analytics(self, submissions):
        stats = (
            SubmissionSymptom.objects.filter(submission__in=submissions)
            .values('symptom__name')
            .annotate(count=Count('id'), avg_severity=Avg('severity'))
            .order_by('-count')[:10]
        )
        return [
            {
                'symptom': s['symptom__name'],
                'frequency': s['count'],
                'avg_severity': round(s['avg_severity'], 2)
            } for s in stats
        ]

    # ---------------------------------------------------------------------
    def _calculate_health_score(self, submissions):
        """Average inverse severity (0–100 health score)."""
        if not submissions.exists():
            return 0
        recent = list(submissions.order_by('-created_at')[:10])
        avg_severity = sum(sub.severity_score for sub in recent) / len(recent)
        risky = sum(1 for sub in recent if sub.severity_category == 'RISKY')
        score = 100 - avg_severity - (risky * 5)
        return max(0, min(100, round(score, 2)))
    # ---------------------------------------------------------------------

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
     # POST /api/predictions/import_dataset/       
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def import_dataset(self, request):
        try:
            from .data_loader import import_disease_data
            import_disease_data()
            return Response({'message': 'Dataset imported successfully'})
        except Exception as e:
            return Response({'error': str(e)}, status=500)

            


class DiseaseViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Disease.objects.all()
    serializer_class = DiseaseSerializer


class SymptomViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Symptom.objects.all()
    serializer_class = SymptomSerializer