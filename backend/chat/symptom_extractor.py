# chat/symptom_extractor.py
import re
from rapidfuzz import fuzz
from predictor.models import Symptom

SEVERITY_KEYWORDS = {
    3: ["mild", "slight", "little"],
    5: ["some", "moderate"],
    7: ["bad", "heavy", "strong"],
    9: ["severe", "terrible", "intense"],
}

def estimate_severity(text):
    text = text.lower()
    for severity, words in SEVERITY_KEYWORDS.items():
        if any(w in text for w in words):
            return severity
    return 5

def extract_symptoms_from_text(text):
    """Extract symptom matches & severity from free text."""
    text_clean = text.lower()
    symptoms = Symptom.objects.all()

    detected = []

    for symptom in symptoms:
        name = symptom.name.lower()

        if name in text_clean:
            detected.append({
                "id": symptom.id,
                "name": symptom.name,
                "severity": estimate_severity(text_clean),
            })
            continue

        score = fuzz.partial_ratio(name, text_clean)
        if score >= 80:
            detected.append({
                "id": symptom.id,
                "name": symptom.name,
                "severity": estimate_severity(text_clean),
            })

    return detected
