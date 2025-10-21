"""
Django management command to train the Naive Bayes model
Usage: python manage.py train_model
"""
from django.core.management.base import BaseCommand
from predictor.ml_predictor import NaiveBayesPredictor  # Updated import path


class Command(BaseCommand):
    help = 'Train the Naive Bayes disease prediction model'

    def add_arguments(self, parser):
        parser.add_argument(
            '--retrain',
            action='store_true',
            help='Force retrain even if model exists',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Starting model training...'))
        
        try:
            predictor = NaiveBayesPredictor()
            
            if options['retrain']:
                self.stdout.write('Forcing retrain...')
            
            results = predictor.train()
            
            self.stdout.write(self.style.SUCCESS('Model trained successfully!'))
            self.stdout.write(f"Samples trained: {results['samples_trained']}")
            self.stdout.write(f"Diseases: {results['diseases']}")
            self.stdout.write(f"Symptoms: {results['symptoms']}")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error training model: {str(e)}'))
            raise