# chat/dataset_symptom_extractor.py
"""
Dataset-aware symptom extractor with:
- Stopword filtering
- Whole-token matching only (prevents false matches like "and")
- Fuzzy fallback using RapidFuzz
- Severity, onset, duration extraction
- Dataset-driven symptom lookup
"""

import re
from functools import lru_cache
from typing import List, Dict, Any, Optional
from rapidfuzz import fuzz

from predictor.models import Symptom  # adjust if your model path differs


# ============================================================
# CONFIGURATION
# ============================================================

FUZZY_THRESHOLD = 82
DEFAULT_SEVERITY = 5
MAX_SYMPTOMS_RETURN = 10
TOKEN_MIN_LENGTH = 3

STOPWORDS = {
    "and", "or", "the", "is", "am", "are", "to", "in", "on", "of", "for", "a",
    "an", "with", "have", "had", "has", "since", "yesterday", "today", "my",
    "i", "you", "he", "she", "they", "it", "this", "that"
}

SEVERITY_WORD_MAP = {
    10: ["unbearable", "excruciating", "severe", "intense"],
    7: ["strong", "very bad", "bad"],
    5: ["moderate", "some", "noticeable"],
    3: ["mild", "slight", "little"],
}

ONSET_KEYWORDS = {
    "SUDDEN": ["sudden", "instantly", "immediately"],
    "GRADUAL": ["gradually", "slowly", "over time"],
}

DURATION_RE = re.compile(
    r"(\b\d+\s*(?:days?|weeks?|hours?|months?|minutes?)\b|\byesterday\b|\btoday\b|\blast night\b|\bthis morning\b)",
    re.I
)


# ============================================================
# HELPERS
# ============================================================

def tokenize(text: str) -> List[str]:
    """Simple word tokenizer."""
    return re.findall(r"[a-zA-Z0-9]+", text.lower())


def infer_severity(text: str) -> int:
    t = text.lower()
    for sev, words in SEVERITY_WORD_MAP.items():
        for w in words:
            if w in t:
                return sev
    m = re.search(r"\b([1-9]|10)\/?10?\b", t)
    if m:
        return int(m.group(1))
    return DEFAULT_SEVERITY


def detect_onset(text: str) -> str:
    t = text.lower()
    for onset, kws in ONSET_KEYWORDS.items():
        if any(k in t for k in kws):
            return onset
    return "GRADUAL"


def detect_duration(text: str) -> Optional[str]:
    m = DURATION_RE.search(text.lower())
    if m:
        return m.group(1)
    return None


# ============================================================
# LOAD SYMPTOMS (CACHED)
# ============================================================

@lru_cache(maxsize=1)
def load_symptoms() -> List[Dict[str, Any]]:
    rows = []
    for s in Symptom.objects.all():
        name = s.name.lower().strip()
        tokens = tokenize(name)
        rows.append({
            "id": s.id,
            "name": s.name,
            "lower": name,
            "tokens": tokens
        })
    return rows


# ============================================================
# MAIN EXTRACTOR
# ============================================================

def extract_symptoms_from_text_dataset_aware(text: str) -> List[Dict[str, Any]]:
    """
    HIGH-ACCURACY symptom matching based on dataset.
    Avoids false matches like "and" by using:
    - stopword filtering
    - whole-token matching
    - dataset-driven n-gram matching
    - fuzzy fallback
    """
    if not text or not text.strip():
        return []

    text_clean = text.lower()
    tokens = [t for t in tokenize(text_clean) if t not in STOPWORDS]

    symptoms = load_symptoms()

    candidates = {}  # sid → best score

    # ========================================================
    # 1) Exact TOKEN MATCH (safe, no substring)
    # ========================================================
    for s in symptoms:
        sid = s["id"]
        for t in tokens:
            if len(t) < TOKEN_MIN_LENGTH:
                continue

            # match only whole tokens
            if t in s["tokens"]:
                score = 95
                prev = candidates.get(sid, 0)
                if score > prev:
                    candidates[sid] = score

    # ========================================================
    # 2) n-gram matching from user text → symptom multiword names
    # ========================================================
    for s in symptoms:
        sid = s["id"]
        name_tokens = s["tokens"]

        if len(name_tokens) >= 2:
            for i in range(len(tokens) - 1):
                bigram = tokens[i] + " " + tokens[i + 1]
                if bigram in s["lower"]:
                    score = 90
                    if score > candidates.get(sid, 0):
                        candidates[sid] = score

    # ========================================================
    # 3) Fuzzy fallback
    # ========================================================
    if len(candidates) < 3:  # only fuzzy if needed
        for s in symptoms:
            sid = s["id"]
            score = fuzz.partial_ratio(s["lower"], text_clean)
            if score >= FUZZY_THRESHOLD:
                mapped = int(score * 0.9)
                if mapped > candidates.get(sid, 0):
                    candidates[sid] = mapped

    # ========================================================
    # Build output
    # ========================================================
    results = []
    severity = infer_severity(text_clean)
    onset = detect_onset(text_clean)
    duration = detect_duration(text_clean)

    for s in symptoms:
        sid = s["id"]
        if sid in candidates:
            results.append({
                "id": sid,
                "name": s["name"],
                "severity": severity,
                "onset": onset,
                "duration": duration,
                "match_score": candidates[sid]
            })

    # Sort strongest matches first
    results.sort(key=lambda x: -x["match_score"])

    # Cap
    return results[:MAX_SYMPTOMS_RETURN]


# ============================================================
# CONVERT TO PREDICTOR FORMAT
# ============================================================

def to_predictor_symptom_list(extracted: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Convert extractor output into HybridPredictor format.
    """
    out = []
    for s in extracted:
        out.append({
            "id": s["id"],
            "severity": int(s.get("severity", DEFAULT_SEVERITY)),
            "duration": s.get("duration") or "",
            "onset": s.get("onset") or "GRADUAL"
        })
    return out
