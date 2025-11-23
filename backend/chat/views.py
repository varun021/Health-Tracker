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
from chat.gemini_client import health_chat, analyze_symptoms

import datetime
import re

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
    return any(re.search(p, text.lower()) for p in EMERGENCY_KEYWORDS)


# ======================================================
# FOLLOWUP BOOST RULES
# ======================================================
FOLLOWUP_BOOSTS = {
    "rash": {"yes": 10.0, "no": -12.0},
    "travel": {"yes": 12.0, "no": -6.0},
    "nausea": {"yes": 6.0, "no": -4.0},
    "chills": {"yes": 8.0, "no": -6.0},
    "vomiting": {"yes": 6.0, "no": -4.0},
}


# ======================================================
# MAIN ChatViewSet
# ======================================================
class ChatViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.predictor = HybridPredictor()

    # ---------------------------------------------------------
    # Helper: Get last meaningful message (not yes/no)
    # ---------------------------------------------------------
    def _last_user_message(self, user):
        return (
            ChatMessage.objects.filter(user=user, role="user")
            .exclude(content__in=["yes", "no"])
            .order_by("-created_at")
            .first()
        )

    # ---------------------------------------------------------
    # Helper: Apply followup scoring adjustments
    # ---------------------------------------------------------
    def _apply_followup_adjustments(self, preds, fid, val):
        base = FOLLOWUP_BOOSTS.get(fid, {"yes": 0, "no": 0})
        delta = base.get(val, 0)

        for p in preds:
            p["confidence"] = max(0, min(100, p["confidence"] + delta))

            # Disease-aware adjustment
            try:
                for ds in p["disease"].disease_symptoms.all():
                    if fid.lower() in ds.symptom.name.lower():
                        if val == "no":
                            p["confidence"] -= 8
                        else:
                            p["confidence"] += 5
            except:
                pass

            p["confidence"] = round(max(0, min(100, p["confidence"])), 2)

        preds.sort(key=lambda x: x["confidence"], reverse=True)
        return preds

    # ---------------------------------------------------------
    # MAIN SEND ENDPOINT (Chat flow + Followups)
    # ---------------------------------------------------------
    @action(detail=False, methods=["post"])
    def send(self, request):
        user = request.user
        message = (request.data.get("message") or "").strip()
        followup = request.data.get("followup")
        answers = request.data.get("answers", {})

        # ===========================
        # FOLLOW-UP FLOW
        # ===========================
        if followup or answers:
            if followup:
                fid = list(followup.keys())[0]
                answers = {fid: followup[fid]}

            last_msg = self._last_user_message(user)
            if not last_msg:
                return Response({"error": "No prior message found"}, status=400)

            original_text = last_msg.content
            extracted = extract_symptoms_from_text_dataset_aware(original_text)
            predictor_input = to_predictor_symptom_list(extracted)

            try:
                preds = self.predictor.predict(predictor_input, user=user)
            except:
                preds = []

            # Apply each followup answer
            for fid, val in answers.items():
                val_norm = "yes" if str(val).lower() in ["yes", "y", "true", "1"] else "no"

                ChatMessage.objects.create(
                    user=user,
                    role="user",
                    content=val_norm,
                    metadata={"from_followup": True, "followup_id": fid, "followup_value": val_norm},
                )

                preds = self._apply_followup_adjustments(preds, fid, val_norm)

            followups = generate_followup_questions(original_text, extracted)
            explanations = explain_predictions(preds, extracted, lambda d: d.disease_symptoms.all())

            reply = "Updated possible conditions:\n"
            for p in preds:
                reply += f"• {p['disease'].name} ({p['confidence']}%)\n"

            ChatMessage.objects.create(
                user=user,
                role="assistant",
                content=reply,
                metadata={
                    "symptoms": extracted,
                    "predictions": [
                        {"disease": p["disease"].name, "confidence": p["confidence"]} for p in preds
                    ],
                    "followups": followups,
                    "explanations": explanations,
                },
            )

            return Response(
                {
                    "assistant": reply,
                    "symptoms": extracted,
                    "predictions": [
                        {"disease": p["disease"].name, "confidence": p["confidence"]} for p in preds
                    ],
                    "followups": followups,
                }
            )

        # ===========================
        # NEW MESSAGE FLOW
        # ===========================
        if not message:
            return Response({"error": "Message cannot be empty"}, status=400)

        ChatMessage.objects.create(user=user, role="user", content=message)

        extracted = extract_symptoms_from_text_dataset_aware(message)
        predictor_input = to_predictor_symptom_list(extracted)

        # Emergency detection
        if contains_emergency(message) or contains_critical_symptom(message, extracted):
            msg = (
                "⚠️ Your symptoms may indicate a serious medical issue.\n"
                "Please seek emergency medical care immediately."
            )
            ChatMessage.objects.create(user=user, role="assistant", content=msg, metadata={"escalation": True})
            return Response({"assistant": msg, "emergency": True})

        # ML predictions
        try:
            preds = self.predictor.predict(predictor_input, user=user)
        except:
            preds = []

        followups = generate_followup_questions(message, extracted)
        explanations = explain_predictions(preds, extracted, lambda d: d.disease_symptoms.all())

        reply = "I detected these symptoms:\n"
        for s in extracted:
            reply += f"• {s['name']} (severity {s['severity']}/10)\n"

        reply += "\nPossible conditions:\n"
        for p in preds:
            reply += f"• {p['disease'].name} ({p['confidence']}%)\n"

        ChatMessage.objects.create(
            user=user,
            role="assistant",
            content=reply,
            metadata={
                "symptoms": extracted,
                "predictions": [
                    {"disease": p["disease"].name, "confidence": p["confidence"]} for p in preds
                ],
                "followups": followups,
                "explanations": explanations,
            },
        )

        return Response(
            {
                "assistant": reply,
                "symptoms": extracted,
                "predictions": [
                    {"disease": p["disease"].name, "confidence": p["confidence"]} for p in preds
                ],
                "followups": followups,
            }
        )

    # ---------------------------------------------------------
    # HISTORY
    # ---------------------------------------------------------
    @action(detail=False, methods=["get"])
    def history(self, request):
        msgs = ChatMessage.objects.filter(user=request.user).order_by("created_at")
        return Response({"results": ChatMessageSerializer(msgs, many=True).data})

    # ---------------------------------------------------------
    # SUMMARY
    # ---------------------------------------------------------
    @action(detail=False, methods=["get"])
    def summary(self, request):
        user = request.user
        msgs = ChatMessage.objects.filter(user=user).order_by("-created_at")[:200][::-1]

        sym_map = {}
        top_preds = {}
        followup_answers = {}

        for m in msgs:
            md = m.metadata or {}

            for s in md.get("symptoms", []):
                sym_map[s["name"]] = s

            for p in md.get("predictions", []):
                d = p["disease"]
                conf = float(p["confidence"])
                top_preds[d] = max(top_preds.get(d, 0), conf)

            if m.role == "user" and md.get("from_followup"):
                followup_answers[md["followup_id"]] = md["followup_value"]

        health_score = 100 - (sum(top_preds.values()) / len(top_preds)) if top_preds else 75

        return Response(
            {
                "symptoms": list(sym_map.values()),
                "top_predictions": sorted(
                    [{"disease": k, "confidence": v} for k, v in top_preds.items()],
                    key=lambda x: -x["confidence"],
                ),
                "followup_answers": followup_answers,
                "health_score": round(health_score, 2),
                "last_updated": datetime.datetime.utcnow().isoformat() + "Z",
            }
        )

    # ---------------------------------------------------------
    # RESTART
    # ---------------------------------------------------------
    @action(detail=False, methods=["post"])
    def restart(self, request):
        user = request.user
        hard_delete = request.data.get("hard_delete", False)

        if hard_delete:
            ChatMessage.objects.filter(user=user).delete()
            ChatMessage.objects.create(user=user, role="assistant", content="Chat cleared. Start again.")
            return Response({"status": "cleared"})

        ChatMessage.objects.create(
            user=user, role="assistant", content="Conversation restarted. Please describe your symptoms."
        )
        return Response({"status": "restarted"})

    # ---------------------------------------------------------
    # GEMINI Chat
    # ---------------------------------------------------------
    @action(detail=False, methods=["post"])
    def ai(self, request):
        message = (request.data.get("message") or "").strip()
        if not message:
            return Response({"error": "Message cannot be empty"}, status=400)

        try:
            ai_reply = health_chat(message)
        except Exception as e:
            return Response({"error": f"Gemini Error: {str(e)}"}, status=500)

        user = request.user

        ChatMessage.objects.create(user=user, role="user", content=message, metadata={"mode": "gemini_chat"})
        ChatMessage.objects.create(user=user, role="assistant", content=ai_reply, metadata={"mode": "gemini_chat"})

        return Response({"assistant": ai_reply})

    # ---------------------------------------------------------
    # GEMINI Symptom Analysis
    # ---------------------------------------------------------
    @action(detail=False, methods=["post"])
    def ai_symptoms(self, request):
        text = (request.data.get("text") or "").strip()
        if not text:
            return Response({"error": "Symptoms text required"}, status=400)

        try:
            analysis = analyze_symptoms(text)
        except Exception as e:
            return Response({"error": f"Gemini Error: {str(e)}"}, status=500)

        ChatMessage.objects.create(
            user=request.user,
            role="assistant",
            content=analysis,
            metadata={"mode": "gemini_symptom_analysis"},
        )

        return Response({"analysis": analysis})
