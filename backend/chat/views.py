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
    text = text.lower()
    return any(re.search(pattern, text) for pattern in EMERGENCY_KEYWORDS)


# ======================================================
# FOLLOW-UP ADJUSTMENT RULES
# ======================================================
FOLLOWUP_BOOSTS = {
    "rash": {"yes": 10.0, "no": -12.0},
    "travel": {"yes": 12.0, "no": -6.0},
    "nausea": {"yes": 6.0, "no": -4.0},
    "chills": {"yes": 8.0, "no": -6.0},
    "vomiting": {"yes": 6.0, "no": -4.0},
}


# ======================================================
# FINAL ChatViewSet (Merged)
# ======================================================
class ChatViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.predictor = HybridPredictor()

    # ---------------------------------------------------------
    # Helper: last meaningful user message
    # ---------------------------------------------------------
    def _last_user_message(self, user):
        return (
            ChatMessage.objects.filter(user=user, role="user")
            .exclude(content__in=["yes", "no"])
            .order_by("-created_at")
            .first()
        )

    # ---------------------------------------------------------
    # Helper: apply followup booster to predictions
    # ---------------------------------------------------------
    def _apply_followup_adjustments(self, preds, followup_id, followup_value):
        base = FOLLOWUP_BOOSTS.get(followup_id, {"yes": 0, "no": 0})
        delta = base.get(followup_value, 0)

        for p in preds:
            p["confidence"] = max(0.0, min(100.0, p["confidence"] + delta))

            try:
                ds_list = p["disease"].disease_symptoms.all()
                for ds in ds_list:
                    if followup_id.lower() in ds.symptom.name.lower():
                        if followup_value == "no":
                            p["confidence"] = max(0, p["confidence"] - 8)
                        else:
                            p["confidence"] = min(100, p["confidence"] + 5)
            except:
                pass

            p["confidence"] = round(p["confidence"], 2)

        preds.sort(key=lambda x: x["confidence"], reverse=True)
        return preds

    # ---------------------------------------------------------
    # NLP Medical Chat
    # ---------------------------------------------------------
    @action(detail=False, methods=["post"])
    def send(self, request):
        user = request.user
        message = (request.data.get("message") or "").strip()
        followup = request.data.get("followup")
        answers = request.data.get("answers", {})

        # ---------------- Follow-up flow ----------------
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

            for fid, val in answers.items():
                normalized = (
                    "yes" if str(val).lower() in ["yes", "y", "true", "1"] else "no"
                )

                ChatMessage.objects.create(
                    user=user,
                    role="user",
                    content=normalized,
                    metadata={
                        "from_followup": True,
                        "followup_id": fid,
                        "followup_value": normalized,
                    },
                )

                preds = self._apply_followup_adjustments(preds, fid, normalized)

            followups = generate_followup_questions(original_text, extracted)
            explanations = explain_predictions(
                preds, extracted, lambda d: d.disease_symptoms.all()
            )

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
                        {"disease": p["disease"].name, "confidence": p["confidence"]}
                        for p in preds
                    ],
                    "followups": followups,
                    "explanations": explanations,
                },
            )

            return Response(
                {
                    "assistant": reply,
                    "symptoms": extracted,
                    "predictions": preds,
                    "followups": followups,
                }
            )

        # ---------------- NEW MESSAGE flow ----------------
        if not message:
            return Response({"error": "Message cannot be empty"}, status=400)

        ChatMessage.objects.create(user=user, role="user", content=message)

        extracted = extract_symptoms_from_text_dataset_aware(message)
        predictor_input = to_predictor_symptom_list(extracted)

        # Emergency detection
        if contains_emergency(message) or contains_critical_symptom(message, extracted):
            msg = "⚠️ Your symptoms may indicate a serious medical issue. Please seek emergency medical care immediately."
            ChatMessage.objects.create(
                user=user, role="assistant", content=msg, metadata={"escalation": True}
            )
            return Response({"assistant": msg, "emergency": True}, status=200)

        # ML prediction
        try:
            preds = self.predictor.predict(predictor_input, user=user)
        except:
            preds = []

        followups = generate_followup_questions(message, extracted)
        explanations = explain_predictions(
            preds, extracted, lambda d: d.disease_symptoms.all()
        )

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
                    {"disease": p["disease"].name, "confidence": p["confidence"]}
                    for p in preds
                ],
                "followups": followups,
                "explanations": explanations,
            },
        )

        return Response(
            {
                "assistant": reply,
                "symptoms": extracted,
                "predictions": preds,
                "followups": followups,
            },
            status=200,
        )

    # ---------------------------------------------------------
    # Chat history
    # ---------------------------------------------------------
    @action(detail=False, methods=["get"])
    def history(self, request):
        user = request.user
        messages = ChatMessage.objects.filter(user=user).order_by("created_at")
        serializer = ChatMessageSerializer(messages, many=True)
        return Response({"results": serializer.data}, status=200)

    # ---------------------------------------------------------
    # Summary
    # ---------------------------------------------------------
    @action(detail=False, methods=["get"])
    def summary(self, request):
        user = request.user
        msgs = (
            ChatMessage.objects.filter(user=user)
            .order_by("-created_at")[:200][::-1]
        )

        unique_symptoms = {}
        top_preds = {}
        followup_answers = {}

        for m in msgs:
            md = m.metadata or {}

            # symptoms
            for s in md.get("symptoms", []):
                unique_symptoms[s["name"]] = s

            # predictions
            for p in md.get("predictions", []):
                name = p["disease"]
                conf = float(p["confidence"])
                top_preds[name] = max(top_preds.get(name, 0), conf)

            # followups
            if m.role == "user" and md.get("from_followup"):
                followup_answers[md["followup_id"]] = md["followup_value"]

        health_score = (
            100 - (sum(top_preds.values()) / len(top_preds))
            if top_preds
            else 75
        )

        return Response(
            {
                "symptoms": list(unique_symptoms.values()),
                "top_predictions": [
                    {"disease": k, "confidence": v}
                    for k, v in sorted(
                        top_preds.items(), key=lambda x: -x[1]
                    )
                ],
                "followup_answers": followup_answers,
                "health_score": round(health_score, 2),
                "last_updated": datetime.datetime.utcnow().isoformat() + "Z",
            },
            status=200,
        )

    # ---------------------------------------------------------
    # Restart chat session
    # ---------------------------------------------------------
    @action(detail=False, methods=["post"])
    def restart(self, request):
        user = request.user
        hard_delete = request.data.get("hard_delete", False)

        if hard_delete:
            ChatMessage.objects.filter(user=user).delete()
            ChatMessage.objects.create(
                user=user,
                role="assistant",
                content="Chat cleared. You can start a new conversation.",
            )
            return Response({"status": "cleared"})

        ChatMessage.objects.create(
            user=user,
            role="assistant",
            content="Conversation restarted. Please describe your symptoms.",
        )
        return Response({"status": "restarted"})

    # ---------------------------------------------------------
    # GEMINI AI Chat
    # ---------------------------------------------------------
    @action(detail=False, methods=["post"])
    def ai(self, request):
        user = request.user
        message = (request.data.get("message") or "").strip()

        if not message:
            return Response({"error": "Message cannot be empty"}, status=400)

        try:
            ai_reply = health_chat(message)
        except Exception as e:
            return Response({"error": f"Gemini Error: {str(e)}"}, status=500)

        ChatMessage.objects.create(
            user=user,
            role="user",
            content=message,
            metadata={"mode": "gemini_chat"},
        )

        ChatMessage.objects.create(
            user=user,
            role="assistant",
            content=ai_reply,
            metadata={"mode": "gemini_chat"},
        )

        return Response({"assistant": ai_reply}, status=200)

    # ---------------------------------------------------------
    # GEMINI Symptom analysis
    # ---------------------------------------------------------
    @action(detail=False, methods=["post"])
    def ai_symptoms(self, request):
        user = request.user
        text = (request.data.get("text") or "").strip()

        if not text:
            return Response({"error": "Symptoms text required"}, status=400)

        try:
            analysis = analyze_symptoms(text)
        except Exception as e:
            return Response({"error": f"Gemini Error: {str(e)}"}, status=500)

        ChatMessage.objects.create(
            user=user,
            role="assistant",
            content=analysis,
            metadata={"mode": "gemini_symptom_analysis"},
        )

        return Response({"analysis": analysis}, status=200)
