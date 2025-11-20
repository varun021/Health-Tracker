# chat/assistant_utils.py
import re
from typing import List, Dict, Any

# Critical symptom keywords / regex (expand as needed)
CRITICAL_PATTERNS = [
    r"\b(chest pain|severe chest pain)\b",
    r"\b(difficulty breathing|shortness of breath|trouble breathing)\b",
    r"\b(unconscious|loss of consciousness|fainting)\b",
    r"\b(severe bleeding|bleeding heavily)\b",
    r"\b(confused|confusion|disoriented)\b",
    r"\b(suicidal|suicide|self[-\s]?harm)\b",
    r"\b(severe abdominal pain)\b",
    r"\b(sudden weakness|sudden numbness)\b"
]

# Follow-up question rules: if keywords/symptoms present or absent -> ask these.
FOLLOWUP_RULES = [
    # Each rule: predicate (lambda over context/extracted symptoms/text) -> question
    {
        "id": "chills",
        "predicate": lambda text, extracted: bool(re.search(r"\b(chill|chills|rigor)\b", text, re.I)) == False and any(
            s for s in extracted if "fever" in s["name"].lower()
        ),
        "question": "Do you have chills, shivering, or rigors with the fever?"
    },
    {
        "id": "rash",
        "predicate": lambda text, extracted: True,  # always ask if fever present
        "question": "Do you have any skin rash or red spots anywhere on the body?"
    },
    {
        "id": "travel",
        "predicate": lambda text, extracted: True,
        "question": "Have you travelled recently (especially to rural or tropical areas) or had mosquito bites?"
    },
    {
        "id": "vomiting",
        "predicate": lambda text, extracted: bool(re.search(r"\b(vomit|vomiting|nausea)\b", text, re.I)) == False and True,
        "question": "Are you experiencing nausea, vomiting, or abdominal pain?"
    },
    {
        "id": "breath",
        "predicate": lambda text, extracted: any(s for s in extracted if "cough" in s["name"].lower()),
        "question": "Is the cough severe or do you have difficulty breathing?"
    },
    {
        "id": "vision",
        "predicate": lambda text, extracted: any(s for s in extracted if "headache" in s["name"].lower()),
        "question": "Do you have blurred vision, severe headache, or light sensitivity?"
    }
]

# Basic mapping for summary notes for diseases - can be extended or moved to DB
DISEASE_SUMMARY = {
    "malaria": "Infectious disease often transmitted by mosquitoes — commonly causes fever, chills, headache, body aches.",
    "dengue": "Viral infection transmitted by Aedes mosquitoes; high fever, severe headache, muscle pain, and sometimes rash.",
    "typhoid": "Bacterial infection with high fever and abdominal symptoms; needs medical testing and antibiotics.",
    # Add more short descriptions keyed by lowercase disease name substrings
}

def contains_critical_symptom(text: str, extracted_symptoms: List[Dict[str,Any]]) -> bool:
    """
    Returns True if the message or extracted symptoms indicate a critical/emergency condition.
    """
    # Check text-based patterns first
    t = text.lower() if text else ""
    for pat in CRITICAL_PATTERNS:
        if re.search(pat, t):
            return True

    # Severity-level emergency: any extracted symptom with severity >=9
    for s in extracted_symptoms:
        if s.get("severity", 0) >= 9:
            return True

    return False


def generate_followup_questions(text: str, extracted_symptoms: List[Dict[str,Any]], limit: int = 3) -> List[Dict[str,str]]:
    """
    Generate a short list of follow-up questions to clarify critical details.
    Each question returned as { 'id': 'chills', 'question': '...' }
    """
    questions = []
    # apply rules in order
    for rule in FOLLOWUP_RULES:
        try:
            if rule["predicate"](text, extracted_symptoms):
                questions.append({"id": rule["id"], "question": rule["question"]})
            if len(questions) >= limit:
                break
        except Exception:
            continue

    # deduplicate while preserving order
    seen = set()
    out = []
    for q in questions:
        if q["id"] in seen:
            continue
        seen.add(q["id"])
        out.append(q)
    return out


def explain_predictions(predictions: List[Dict[str,Any]], extracted_symptoms: List[Dict[str,Any]], disease_obj_lookup_fn) -> List[Dict[str,Any]]:
    """
    Build lightweight explainability metadata for UI and logs.
    predictions: [{'disease': DiseaseModelInstance, 'confidence': float}, ...]
    extracted_symptoms: [{'id', 'name', 'severity', ...}, ...]
    disease_obj_lookup_fn: function(disease_id) -> disease object with disease_symptoms relation

    Returns list of explanations per disease:
      {
        'disease': 'Malaria',
        'confidence': 18.7,
        'matched_symptoms': [ {'id':.., 'name':.., 'weight':.., 'user_severity':..} ],
        'contribution_percent': 62.3,
        'summary': '...'
      }
    """
    out = []
    # quick map for user symptoms for lookup
    user_sym_map = {s["id"]: s for s in extracted_symptoms}

    for p in predictions:
        d_obj = p['disease']
        did = getattr(d_obj, 'id', None)
        # fetch disease_symptoms safely via provided function (view will pass a lambda)
        try:
            ds_list = disease_obj_lookup_fn(d_obj)
        except Exception:
            ds_list = []

        matched = []
        matched_weight = 0.0
        total_weight = 0.0
        for ds in ds_list:
            w = getattr(ds, 'weight', 1) or 1
            total_weight += w
            if ds.symptom_id in user_sym_map:
                user_s = user_sym_map[ds.symptom_id]
                matched_weight += w * (min(max(user_s.get('severity',5),1),10) / 10.0)
                matched.append({
                    'id': ds.symptom_id,
                    'name': getattr(ds.symptom, 'name', str(ds.symptom_id)),
                    'weight': w,
                    'user_severity': user_s.get('severity', 5)
                })

        contribution = (matched_weight / total_weight * 100.0) if total_weight > 0 else 0.0
        disease_name = (getattr(d_obj, 'name', '') or '').lower()
        summary = None
        for k, v in DISEASE_SUMMARY.items():
            if k in disease_name:
                summary = v
                break

        out.append({
            'disease': getattr(d_obj, 'name', str(did)),
            'confidence': p.get('confidence', 0.0),
            'matched_symptoms': matched,
            'contribution_percent': round(contribution, 2),
            'summary': summary or ""
        })
    return out
