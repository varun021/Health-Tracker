# chat/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Count

from .models import ChatMessage
from .serializers import ChatMessageSerializer

from chat.assistant_utils import (
    generate_followup_questions,
    explain_predictions,
    contains_critical_symptom,
)
from chat.dataset_symptom_extractor import (
    extract_symptoms_from_text_dataset_aware,
    to_predictor_symptom_list,
)
from predictor.ml_predictor import HybridPredictor

import re
import datetime

# ======================================================
# Emergency keyword detection
# ======================================================
EMERGENCY_KEYWORDS = [
    r"chest pain",
    r"shortness of breath",
    r"difficulty breathing",
    r"unconscious",
    r"severe bleeding",
    r"suicidal",
    r"self[-\s]?harm",
    r"stroke",
    r"heart attack",
]


def contains_emergency(text: str) -> bool:
    text = text.lower()
    return any(re.search(p, text) for p in EMERGENCY_KEYWORDS)


# ======================================================
# Follow-up scoring maps (tunable)
# ======================================================
# For positive answers (yes) we apply a small boost to diseases that strongly
# require that feature; for negatives (no) we penalize.
# These are baseline heuristics — you can move to DB if you want more control.
FOLLOWUP_BOOSTS = {
    "rash": {"yes": 10.0, "no": -12.0},
    "travel": {"yes": 12.0, "no": -6.0},
    "nausea": {"yes": 6.0, "no": -4.0},
    "chills": {"yes": 8.0, "no": -6.0},
    "vomiting": {"yes": 6.0, "no": -4.0},
    # add more followups here
}


# ======================================================
# Chat ViewSet
# ======================================================
class ChatViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.predictor = HybridPredictor()

    # ---------------------------
    # Helpers
    # ---------------------------
    def _last_user_message(self, user):
        return (
            ChatMessage.objects.filter(user=user, role="user")
            .exclude(content__in=["yes", "no"])
            .order_by("-created_at")
            .first()
        )

    def _apply_followup_adjustments(self, preds, followup_id, followup_value):
        """
        Adjust prediction confidences using:
        - static boost/penalty (FOLLOWUP_BOOSTS)
        - disease_symptoms presence (if disease contains symptom names matching followup)
        """
        # static boost
        base = FOLLOWUP_BOOSTS.get(followup_id, {"yes": 0, "no": 0})
        delta = base.get(followup_value, 0)

        # Apply adjustments: if followup is about 'rash' and user says 'no', penalize diseases that have rash symptom.
        for p in preds:
            # Apply the static delta first
            p["confidence"] = max(0.0, min(100.0, p["confidence"] + delta))

            # Disease-aware adjustments: try to penalize/boost based on disease_symptoms matching followup token
            try:
                ds_qs = p["disease"].disease_symptoms.all()
                # check if any symptom name contains the followup_id (simple heuristic)
                has_feature = False
                for ds in ds_qs:
                    sname = getattr(ds.symptom, "name", "") or ""
                    if followup_id.lower() in sname.lower():
                        has_feature = True
                        break

                if followup_value == "no" and has_feature:
                    # stronger penalty for diseases that *expect* the feature
                    p["confidence"] = max(0.0, p["confidence"] - 8.0)
                elif followup_value == "yes" and has_feature:
                    # small extra boost
                    p["confidence"] = min(100.0, p["confidence"] + 5.0)
            except Exception:
                # if anything fails, skip disease-aware adjustment for that disease
                continue

        # Re-normalize / round
        for p in preds:
            p["confidence"] = round(max(0.0, min(100.0, p.get("confidence", 0.0))), 2)

        # Sort
        preds.sort(key=lambda x: x["confidence"], reverse=True)
        return preds

    # ---------------------------
    # SEND (handles both normal messages and followup answers)
    # ---------------------------
    @action(detail=False, methods=["post"])
    def send(self, request):
        user = request.user
        message = (request.data.get("message") or "").strip()
        followup = request.data.get("followup", None)  # expected { id: value } where value is 'yes'/'no'
        answers = request.data.get("answers", {})  # optional: multiple followup answers in one request

        # ----------------------
        # FOLLOW-UP (single) flow
        # ----------------------
        if followup or answers:
            # Accept either single followup or a dict of answers
            if followup:
                # single
                k = list(followup.keys())[0]
                v = followup[k]
                answers = {k: v}

            # get last user message (context); must exist
            last_user = self._last_user_message(user)
            if not last_user:
                return Response(
                    {"error": "No prior conversation found to attach follow-up answers."},
                    status=400,
                )

            original_text = last_user.content
            # parse previously extracted symptoms from last assistant metadata if available
            # fallback to re-extraction from original_text
            extracted = extract_symptoms_from_text_dataset_aware(original_text)
            predictor_input = to_predictor_symptom_list(extracted)

            # run base predictions
            try:
                preds = self.predictor.predict(predictor_input, user=user)
            except Exception:
                preds = []

            # apply all answers iteratively (support multi answers)
            for fid, val in (answers or {}).items():
                val_norm = str(val).strip().lower()
                val_norm = "yes" if val_norm in ["yes", "y", "true", "1"] else "no" if val_norm in ["no", "n", "false", "0"] else val_norm

                # persist the user's answer as a ChatMessage (so conversation history includes it)
                ChatMessage.objects.create(
                    user=user,
                    role="user",
                    content=val_norm,
                    metadata={"followup_id": fid, "followup_value": val_norm, "from_followup": True},
                )

                # apply adjustments on preds
                preds = self._apply_followup_adjustments(preds, fid, val_norm)

            # compute followups and explanations using updated preds
            followups = generate_followup_questions(original_text, extracted, limit=3)
            explanations = explain_predictions(preds, extracted, lambda d: d.disease_symptoms.all())

            # assistant reply text summarizing update
            reply_lines = ["Thanks — I've updated the possible conditions based on your answers.", ""]
            reply_lines.append("Updated possible conditions:")
            for p in preds[:6]:
                reply_lines.append(f"• {p['disease'].name} ({p['confidence']}% confidence)")
            reply_lines.append("")

            if followups:
                reply_lines.append("Further questions to refine the result:")
                for f in followups:
                    reply_lines.append(f"- {f['question']}")
                reply_lines.append("")

            reply_lines.append(
                "Continue monitoring symptoms. This service is informational and not a substitute for a medical professional."
            )
            assistant_text = "\n".join(reply_lines)

            # save assistant message with metadata
            ChatMessage.objects.create(
                user=user,
                role="assistant",
                content=assistant_text,
                metadata={
                    "symptoms": extracted,
                    "predictions": [{"disease": p["disease"].name, "confidence": p["confidence"]} for p in preds],
                    "followups": followups,
                    "explanations": explanations,
                    "followup_answers": answers,
                },
            )

            return Response(
                {
                    "assistant": assistant_text,
                    "symptoms": extracted,
                    "predictions": [{"disease": p["disease"].name, "confidence": p["confidence"]} for p in preds],
                    "followups": followups,
                    "explanations": explanations,
                }
            )

        # ----------------------
        # NORMAL MESSAGE flow
        # ----------------------
        if not message:
            return Response({"error": "Message cannot be empty."}, status=400)

        # record the user's natural language message
        ChatMessage.objects.create(user=user, role="user", content=message)

        # emergency / critical detection
        extracted_symptoms = extract_symptoms_from_text_dataset_aware(message)
        predictor_input = to_predictor_symptom_list(extracted_symptoms)

        if contains_emergency(message) or contains_critical_symptom(message, extracted_symptoms):
            assistant_text = (
                "Your message suggests a potentially serious condition. Please seek immediate medical care or contact emergency services."
            )
            ChatMessage.objects.create(user=user, role="assistant", content=assistant_text, metadata={"escalation": True})
            return Response({"assistant": assistant_text, "emergency": True}, status=200)

        # run predictor
        try:
            preds = self.predictor.predict(predictor_input, user=user)
        except Exception:
            preds = []

        # generate followups and explanations
        followups = generate_followup_questions(message, extracted_symptoms, limit=3)
        explanations = explain_predictions(preds, extracted_symptoms, lambda d: d.disease_symptoms.all())

        # build assistant message
        reply_lines = []
        if extracted_symptoms:
            reply_lines.append("I detected these symptoms:")
            for s in extracted_symptoms:
                reply_lines.append(f"• {s['name']} (severity {s.get('severity',5)}/10)")
            reply_lines.append("")

        if preds:
            reply_lines.append("Possible related conditions:")
            for p in preds[:6]:
                reply_lines.append(f"• {p['disease'].name} ({p['confidence']}% confidence)")
            reply_lines.append("")

        if followups:
            reply_lines.append("To help narrow things down, please answer these short questions:")
            for f in followups:
                reply_lines.append(f"- {f['question']}")
            reply_lines.append("")

        reply_lines.append(
            "Next steps:\n• Monitor your symptoms.\n• Rest and stay hydrated.\n• If symptoms worsen, consult a healthcare professional.\nThis is a computer-assisted prediction and should not replace professional medical advice."
        )

        assistant_text = "\n".join(reply_lines)

        # save assistant message
        ChatMessage.objects.create(
            user=user,
            role="assistant",
            content=assistant_text,
            metadata={
                "symptoms": extracted_symptoms,
                "predictions": [{"disease": p["disease"].name, "confidence": p["confidence"]} for p in preds],
                "followups": followups,
                "explanations": explanations,
            },
        )

        return Response(
            {
                "assistant": assistant_text,
                "symptoms": extracted_symptoms,
                "predictions": [{"disease": p["disease"].name, "confidence": p["confidence"]} for p in preds],
                "followups": followups,
                "explanations": explanations,
            },
            status=200,
        )

    # --------------------------------------------------
    # CHAT HISTORY
    # --------------------------------------------------
    @action(detail=False, methods=["get"])
    def history(self, request):
        user = request.user
        messages = ChatMessage.objects.filter(user=user).order_by("created_at")
        serializer = ChatMessageSerializer(messages, many=True)
        return Response({"results": serializer.data}, status=200)

    # --------------------------------------------------
    # CONVERSATION SUMMARY (new)
    # --------------------------------------------------
    @action(detail=False, methods=["get"])
    def summary(self, request):
        """
        Returns a short summary of recent conversation (last 20 messages):
          - detected symptoms (unique)
          - top predictions aggregated
          - follow-up answers collected
          - a simple health_score heuristic (0-100)
        """
        user = request.user
        msgs = ChatMessage.objects.filter(user=user).order_by("-created_at")[:200]  # recent
        msgs_list = list(msgs[::-1])  # chronological

        # collect symptoms & predictions from assistant metadata
        unique_symptoms = {}
        top_preds = {}
        followup_answers = {}

        for m in msgs_list:
            md = getattr(m, "metadata", {}) or {}
            for s in md.get("symptoms", []) or []:
                unique_symptoms[s["name"]] = s
            for p in md.get("predictions", []) or []:
                name = p.get("disease")
                if not name:
                    continue
                top_preds[name] = max(top_preds.get(name, 0), float(p.get("confidence", 0)))
            for fa in md.get("followup_answers", []) if isinstance(md.get("followup_answers", []), list) else []:
                # if stored as list
                followup_answers.update(fa if isinstance(fa, dict) else {})
            # also check user ChatMessage entries that stored followup metadata
            if m.role == "user" and md.get("from_followup"):
                fid = md.get("followup_id")
                fval = md.get("followup_value")
                if fid:
                    followup_answers[fid] = fval

        # simple health score: inverse of top prediction confidence average (toy heuristic)
        if top_preds:
            avg_conf = sum(top_preds.values()) / len(top_preds)
            health_score = max(0, 100 - avg_conf)
        else:
            health_score = 75.0

        summary = {
            "symptoms": list(unique_symptoms.values()),
            "top_predictions": [{"disease": k, "confidence": v} for k, v in sorted(top_preds.items(), key=lambda x: -x[1])],
            "followup_answers": followup_answers,
            "health_score": round(health_score, 2),
            "last_updated": datetime.datetime.utcnow().isoformat() + "Z",
        }

        return Response(summary, status=200)

    # --------------------------------------------------
    # RESTART CONSULTATION (new)
    # --------------------------------------------------
    @action(detail=False, methods=["post"])
    def restart(self, request):
        """
        Restart current consultation: marks conversation restart by inserting a system message
        and optionally clears stored followup answers. We avoid hard-deleting messages by default.
        """
        user = request.user
        # optional: delete messages for a clean slate (disabled by default)
        hard_delete = bool(request.data.get("hard_delete", False))

        if hard_delete:
            ChatMessage.objects.filter(user=user).delete()
            ChatMessage.objects.create(user=user, role="assistant", content="Consultation restarted. You can start a new conversation.")
            return Response({"status": "cleared"}, status=200)

        # Insert a system assistant message to mark restart and save
        ChatMessage.objects.create(user=user, role="assistant", content="Consultation restarted. Please describe your symptoms.")
        return Response({"status": "restarted"}, status=200)
