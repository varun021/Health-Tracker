# Create this file at: predictor/management/commands/seed_data.py

from django.core.management.base import BaseCommand
from predictor.models import Disease, Symptom, DiseaseSymptom


class Command(BaseCommand):
    help = 'Seeds the database with diseases, symptoms, and their relationships'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding database...')
        
        # Clear existing data
        DiseaseSymptom.objects.all().delete()
        Disease.objects.all().delete()
        Symptom.objects.all().delete()
        
        # Create Symptoms
        symptoms_data = [
            {'name': 'Fever', 'description': 'Elevated body temperature'},
            {'name': 'Cough', 'description': 'Persistent coughing'},
            {'name': 'Runny Nose', 'description': 'Nasal discharge'},
            {'name': 'Sore Throat', 'description': 'Pain or irritation in throat'},
            {'name': 'Fatigue', 'description': 'Extreme tiredness'},
            {'name': 'Itching', 'description': 'Skin irritation causing scratching'},
            {'name': 'Skin Rash', 'description': 'Red, irritated skin patches'},
            {'name': 'Redness', 'description': 'Skin discoloration'},
            {'name': 'Chills', 'description': 'Feeling cold and shivering'},
            {'name': 'Sweating', 'description': 'Excessive perspiration'},
            {'name': 'Headache', 'description': 'Pain in head region'},
            {'name': 'Nausea', 'description': 'Feeling of sickness'},
            {'name': 'Frequent Urination', 'description': 'Urinating more often'},
            {'name': 'Increased Thirst', 'description': 'Excessive thirst'},
            {'name': 'Blurred Vision', 'description': 'Unclear vision'},
            {'name': 'Slow Healing', 'description': 'Wounds heal slowly'},
            {'name': 'High Blood Pressure', 'description': 'Elevated BP readings'},
            {'name': 'Chest Pain', 'description': 'Pain in chest area'},
            {'name': 'Dizziness', 'description': 'Feeling lightheaded'},
            {'name': 'Shortness of Breath', 'description': 'Difficulty breathing'},
        ]
        
        symptoms = {}
        for symptom_data in symptoms_data:
            symptom = Symptom.objects.create(**symptom_data)
            symptoms[symptom_data['name']] = symptom
        
        # Create Diseases with symptoms
        diseases_data = [
            {
                'name': 'Common Cold',
                'description': 'A viral infection of the upper respiratory tract, usually harmless and self-limiting.',
                'lifestyle_tips': '• Get plenty of rest (7-9 hours sleep)\n• Stay hydrated with warm fluids\n• Avoid crowded places\n• Wash hands frequently\n• Use humidifier for dry air',
                'diet_advice': '• Drink warm water, herbal teas, and soups\n• Consume vitamin C rich foods (citrus fruits)\n• Have honey and ginger tea\n• Eat light, easily digestible foods\n• Avoid dairy if it increases mucus',
                'medical_advice': '• Usually resolves in 7-10 days\n• Use over-the-counter pain relievers if needed\n• Consult doctor if symptoms worsen\n• Seek help if fever exceeds 101°F\n• Get medical attention if breathing difficulty occurs',
                'symptoms': {
                    'Cough': 7,
                    'Runny Nose': 8,
                    'Sore Throat': 6,
                    'Fatigue': 5,
                    'Fever': 4,
                }
            },
            {
                'name': 'Fungal Infection',
                'description': 'A skin infection caused by fungi, resulting in itching, redness, and rash.',
                'lifestyle_tips': '• Keep affected area clean and dry\n• Wear loose, breathable clothing\n• Avoid sharing personal items\n• Change socks and underwear daily\n• Dry thoroughly after bathing',
                'diet_advice': '• Reduce sugar intake (fungi feed on sugar)\n• Increase probiotic foods (yogurt, kefir)\n• Eat garlic (natural antifungal)\n• Include coconut oil in diet\n• Stay well hydrated',
                'medical_advice': '• Apply antifungal cream as prescribed\n• Complete full treatment course\n• See doctor if no improvement in 2 weeks\n• May require oral medication for severe cases\n• Prevent reinfection by following hygiene',
                'symptoms': {
                    'Itching': 9,
                    'Skin Rash': 8,
                    'Redness': 7,
                }
            },
            {
                'name': 'Malaria',
                'description': 'A serious disease transmitted by mosquitoes, causing recurring fever and chills.',
                'lifestyle_tips': '• Use mosquito nets while sleeping\n• Apply insect repellent\n• Wear long sleeves and pants\n• Eliminate standing water around home\n• Install window screens',
                'diet_advice': '• Maintain high fluid intake\n• Eat easily digestible foods\n• Include iron-rich foods (spinach, beans)\n• Have fresh fruits for vitamins\n• Avoid heavy, oily foods',
                'medical_advice': '• SEEK IMMEDIATE MEDICAL ATTENTION\n• Requires antimalarial medication\n• Blood test needed for diagnosis\n• Hospitalization may be required\n• Complete full course of medication',
                'symptoms': {
                    'Fever': 10,
                    'Chills': 9,
                    'Sweating': 8,
                    'Headache': 7,
                    'Nausea': 6,
                }
            },
            {
                'name': 'Diabetes',
                'description': 'A chronic condition affecting blood sugar regulation, requiring ongoing management.',
                'lifestyle_tips': '• Exercise regularly (30 min daily)\n• Monitor blood sugar levels\n• Maintain healthy weight\n• Manage stress through meditation\n• Get adequate sleep\n• Quit smoking',
                'diet_advice': '• Follow low glycemic index diet\n• Eat regular, balanced meals\n• Include whole grains and fiber\n• Limit simple sugars and carbs\n• Choose lean proteins\n• Eat plenty of vegetables',
                'medical_advice': '• Regular doctor checkups essential\n• May require insulin or oral medications\n• Monitor for complications\n• Get eye and foot exams annually\n• Keep emergency glucose tablets\n• Wear medical ID bracelet',
                'symptoms': {
                    'Frequent Urination': 9,
                    'Increased Thirst': 8,
                    'Blurred Vision': 7,
                    'Fatigue': 7,
                    'Slow Healing': 6,
                }
            },
            {
                'name': 'Hypertension',
                'description': 'High blood pressure that can lead to serious complications if left untreated.',
                'lifestyle_tips': '• Reduce sodium intake\n• Exercise regularly (cardio activities)\n• Maintain healthy weight (BMI 18.5-24.9)\n• Limit alcohol consumption\n• Quit smoking\n• Manage stress effectively',
                'diet_advice': '• Follow DASH diet (low sodium)\n• Eat potassium-rich foods (bananas)\n• Include leafy greens and berries\n• Choose whole grains\n• Limit processed foods\n• Reduce caffeine intake',
                'medical_advice': '• Monitor blood pressure regularly at home\n• Take prescribed medications consistently\n• Never skip medications without doctor advice\n• Regular medical checkups required\n• Watch for warning signs (severe headache)\n• Emergency care if BP extremely high',
                'symptoms': {
                    'High Blood Pressure': 10,
                    'Headache': 7,
                    'Dizziness': 6,
                    'Chest Pain': 8,
                    'Shortness of Breath': 7,
                }
            },
        ]
        
        for disease_data in diseases_data:
            disease_symptoms = disease_data.pop('symptoms')
            disease = Disease.objects.create(**disease_data)
            
            # Create DiseaseSymptom relationships
            for symptom_name, weight in disease_symptoms.items():
                DiseaseSymptom.objects.create(
                    disease=disease,
                    symptom=symptoms[symptom_name],
                    weight=weight
                )
        
        self.stdout.write(self.style.SUCCESS('Successfully seeded database!'))
        self.stdout.write(f'Created {Disease.objects.count()} diseases')
        self.stdout.write(f'Created {Symptom.objects.count()} symptoms')
        self.stdout.write(f'Created {DiseaseSymptom.objects.count()} disease-symptom relationships')