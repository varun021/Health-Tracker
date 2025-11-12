from django.core.management.base import BaseCommand
from predictor.data_loader import import_disease_data

class Command(BaseCommand):
    help = "Import diseases and symptoms from dataset CSVs"

    def handle(self, *args, **kwargs):
        import_disease_data()
        self.stdout.write(self.style.SUCCESS("✅ Dataset imported successfully!"))
