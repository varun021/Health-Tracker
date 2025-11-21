import os
import google.generativeai as genai

# Load API key from environment
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Default model
DEFAULT_MODEL = "models/gemini-2.5-pro"

model = genai.GenerativeModel(model_name=DEFAULT_MODEL)


# --------------------------------------------------------
# HIGH-LEVEL HEALTH ANALYZER
# --------------------------------------------------------
def analyze_symptoms(symptom_text):
    """
    Enhanced medical analysis (non-diagnostic)
    """
    prompt = f"""
    You are an advanced medical AI assistant. A user has described their symptoms. 
    Provide a comprehensive analysis in JSON format with the following keys:

    - possible_diseases
    - diagnosis
    - specialist
    - medicines
    - dietary_recommendations
    - foods_to_avoid
    - suggestions

    User's symptoms: "{symptom_text}"
    """

    response = model.generate_content(prompt)
    return response.text


# --------------------------------------------------------
# GENERAL GEMINI CHAT
# --------------------------------------------------------
def health_chat(message):
    """
    Non-diagnostic general health chat
    """
    prompt = f"""
    You are a helpful AI assistant. Answer safely.
    User: {message}
    """

    response = model.generate_content(prompt)
    return response.text


# --------------------------------------------------------
# MODEL UTILITIES
# --------------------------------------------------------
def list_available_models():
    try:
        models = genai.list_models()
        return [m.name for m in models if m.supports_generate_content]
    except Exception as e:
        return {"error": str(e)}


def get_model_info(model_name):
    try:
        model = genai.get_model(model_name)
        return {
            "name": model.name,
            "description": model.description,
            "supported_methods": model.supported_methods
        }
    except Exception as e:
        return {"error": str(e)}


def generate_content(model_name, prompt):
    try:
        model = genai.GenerativeModel(model_name=model_name)
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return {"error": str(e)}
