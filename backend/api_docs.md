# Disease Prediction API Documentation

## Overview
This API uses a **Hybrid Prediction System** combining:
- **Naive Bayes Machine Learning Algorithm** (60% weight)
- **Rule-based Symptom Matching** (40% weight)

## Authentication
All endpoints except disease/symptom listings require authentication using JWT tokens or session authentication.

---

## Endpoints

### 1. Disease Management

#### `GET /api/diseases/`
List all diseases with their symptoms and recommendations.

**Response:**
```json
[
  {
    "id": 1,
    "name": "Common Cold",
    "description": "Viral infection of upper respiratory tract",
    "lifestyle_tips": "Rest, stay hydrated...",
    "diet_advice": "Warm fluids, vitamin C...",
    "medical_advice": "Consult if symptoms persist...",
    "symptoms": [
      {
        "symptom": {
          "id": 1,
          "name": "Fever",
          "description": "Elevated body temperature"
        },
        "weight": 7
      }
    ]
  }
]
```

#### `GET /api/diseases/{id}/`
Get detailed information about a specific disease.

---

### 2. Symptom Management

#### `GET /api/symptoms/`
List all available symptoms.

**Response:**
```json
[
  {
    "id": 1,
    "name": "Fever",
    "description": "Elevated body temperature above normal"
  }
]
```

---

### 3. Prediction System

#### `POST /api/predictions/predict/`
Make a disease prediction using Naive Bayes + Rule-based hybrid approach.

**Request Body:**
```json
{
  "name": "John Doe",
  "age": 35,
  "gender": "M",
  "height": 175.5,
  "weight": 70.2,
  "occupation": "Software Engineer",
  "symptoms": [
    {
      "id": 1,
      "severity": 8,
      "duration": "3 days",
      "onset": "SUDDEN"
    },
    {
      "id": 2,
      "severity": 6,
      "duration": "2 days",
      "onset": "GRADUAL"
    }
  ],
  "existing_diseases": ["Hypertension"],
  "allergies": "Penicillin",
  "medications": "Aspirin",
  "family_history": "Diabetes in family",
  "lifestyle": {
    "smoking": false,
    "alcohol": true,
    "diet": "MIXED",
    "sleep_hours": 7,
    "exercise_frequency": "3 times per week",
    "stress_level": 6
  },
  "travel_history": "None recent"
}
```

**Response:**
```json
{
  "submission": {
    "id": 123,
    "name": "John Doe",
    "age": 35,
    "severity_score": 65.5,
    "severity_category": "MODERATE",
    "primary_prediction": "Common Cold",
    "predicted_diseases": [
      {
        "id": 1,
        "name": "Common Cold",
        "confidence_score": 85.5
      },
      {
        "id": 2,
        "name": "Flu",
        "confidence_score": 72.3
      },
      {
        "id": 3,
        "name": "Sinusitis",
        "confidence_score": 45.8
      }
    ]
  },
  "predictions": [
    {
      "disease": "Common Cold",
      "confidence": 85.5,
      "rank": 1
    }
  ],
  "recommendations": {
    "lifestyle_tips": [
      "Get adequate rest",
      "Stay hydrated"
    ],
    "diet_advice": [
      "Warm fluids",
      "Vitamin C rich foods"
    ],
    "medical_advice": [
      "Consult doctor if symptoms worsen"
    ]
  },
  "additional_info": {
    "severity_interpretation": "Moderate symptoms detected — monitor health and seek care if symptoms worsen.",
    "next_steps": "Track your symptoms for the next 3 days. If symptoms worsen, consult a healthcare provider.",
    "disclaimer": "This is an AI-assisted health prediction using Naive Bayes ML algorithm. It should not replace professional medical advice."
  }
}
```

---

### 4. Analytics & Reports

#### `GET /api/predictions/analytics/?days=30`
Get comprehensive health analytics.

**Query Parameters:**
- `days` (optional): Number of days to analyze (default: 30)

**Response:**
```json
{
  "overview": {
    "total_predictions": 15,
    "avg_severity": 45.5,
    "max_severity": 85.0,
    "min_severity": 20.0,
    "most_common_disease": "Common Cold",
    "severity_distribution": {
      "normal": 5,
      "moderate": 8,
      "risky": 2
    }
  },
  "trends": [
    {
      "period": "2024-10-01",
      "count": 3,
      "avg_severity": 42.5,
      "severity_breakdown": {
        "normal": 1,
        "moderate": 2,
        "risky": 0
      }
    }
  ],
  "disease_analytics": [
    {
      "disease": "Common Cold",
      "occurrences": 5,
      "avg_severity": 40.5,
      "last_seen": "2024-10-20"
    }
  ],
  "symptom_analytics": [
    {
      "symptom": "Fever",
      "frequency": 12,
      "avg_severity": 7.5
    }
  ],
  "lifestyle_correlation": {
    "smoking": {
      "with_factor": {
        "count": 3,
        "avg_severity": 65.0
      },
      "without_factor": {
        "count": 12,
        "avg_severity": 40.0
      }
    },
    "sleep": {
      "avg_sleep_hours": 6.8,
      "correlation_with_severity": -0.45
    },
    "stress": {
      "avg_stress_level": 6.2,
      "correlation_with_severity": 0.62
    }
  },
  "severity_trends": [...],
  "time_patterns": {
    "by_hour": [...],
    "by_weekday": [...]
  },
  "health_score": 72.5
}
```

---

#### `GET /api/predictions/comparison_report/`
Compare health metrics between current and previous 30-day periods.

**Response:**
```json
{
  "current_period": {
    "start": "2024-09-21",
    "end": "2024-10-21",
    "stats": {
      "total_predictions": 10,
      "avg_severity": 45.5,
      "risky_cases": 2,
      "most_common_disease": "Common Cold"
    }
  },
  "previous_period": {
    "start": "2024-08-22",
    "end": "2024-09-21",
    "stats": {
      "total_predictions": 8,
      "avg_severity": 52.0,
      "risky_cases": 3,
      "most_common_disease": "Flu"
    }
  },
  "changes": {
    "total_predictions": {
      "value": 25.0,
      "direction": "up",
      "is_improvement": false
    },
    "avg_severity": {
      "value": -12.5,
      "direction": "down",
      "is_improvement": true
    },
    "risky_cases": {
      "value": -33.33,
      "direction": "down",
      "is_improvement": true
    }
  }
}
```

---

#### `GET /api/predictions/recommendations_based_on_history/`
Get personalized health recommendations based on user history.

**Response:**
```json
{
  "total_recommendations": 3,
  "health_score": 68.5,
  "recommendations": [
    {
      "category": "lifestyle",
      "title": "Insufficient Sleep",
      "message": "You frequently report less than 6 hours of sleep. Better sleep can improve health.",
      "action": "Aim for 7-9 hours of sleep"
    },
    {
      "category": "lifestyle",
      "title": "High Stress Levels",
      "message": "High stress is frequently reported. Consider stress management techniques.",
      "action": "Practice relaxation techniques"
    }
  ]
}
```

---

#### `GET /api/predictions/history/?page=1&page_size=20`
Get paginated prediction history.

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Items per page (default: 20)

**Response:**
```json
{
  "count": 45,
  "page": 1,
  "page_size": 20,
  "total_pages": 3,
  "results": [...]
}
```

---

#### `GET /api/predictions/export_data/?format=csv|json`
Export all user data.

**Query Parameters:**
- `format`: Export format (csv or json)

**Response:**
- CSV file download or JSON data

---

#### `POST /api/predictions/generate_report/`
#### `GET /api/predictions/generate_report/`
Generate comprehensive health report in PDF, CSV, or JSON format.

**Request Body (POST) or Query Parameters (GET):**
```json
{
  "start_date": "2024-09-01",
  "end_date": "2024-10-21",
  "format": "pdf",
  "include_personal_info": true,
  "include_recommendations": true
}
```

**Query Parameters (GET):**
- `start_date` (optional): Start date (YYYY-MM-DD)
- `end_date` (optional): End date (YYYY-MM-DD)
- `format` (optional): pdf, csv, or json (default: pdf)
- `include_personal_info` (optional): Include personal details (default: true)
- `include_recommendations` (optional): Include recommendations (default: true)

**Response:**
- PDF/CSV file download or JSON data

---

### 5. Model Training (Admin Only)

#### `POST /api/predictions/train_model/`
Train or retrain the Naive Bayes model.

**Requires:** Staff/Admin access

**Response:**
```json
{
  "message": "Model trained successfully",
  "details": {
    "samples_trained": 1500,
    "diseases": 25,
    "symptoms": 80
  }
}
```

---

## Data Models

### Symptom Input
```json
{
  "id": 1,
  "severity": 8,
  "duration": "3 days",
  "onset": "SUDDEN" | "GRADUAL"
}
```

### Lifestyle Data
```json
{
  "smoking": false,
  "alcohol": true,
  "diet": "VEG" | "NON_VEG" | "VEGAN" | "MIXED",
  "sleep_hours": 7,
  "exercise_frequency": "3 times per week",
  "stress_level": 6
}
```

---

## Error Responses

```json
{
  "error": "Error message describing what went wrong"
}
```

**Common Status Codes:**
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `500` - Internal Server Error

---

## Setup Instructions

### 1. Install Dependencies
```bash
pip install django djangorestframework scikit-learn numpy joblib
```

### 2. Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 3. Create ML Models Directory
```bash
mkdir ml_models
```

### 4. Train the Model
```bash
python manage.py train_model
```

### 5. Populate Database
Add diseases, symptoms, and their relationships through Django admin or fixtures.

---

## How the Hybrid Prediction Works

1. **Naive Bayes Component (60% weight)**:
   - Trains on disease-symptom relationships from database
   - Learns from historical user submissions
   - Uses symptom severity as feature values
   - Provides probability-based predictions

2. **Rule-Based Component (40% weight)**:
   - Matches symptoms using weighted scoring
   - Considers symptom severity
   - Includes user history bonus
   - Uses domain knowledge from disease-symptom weights

3. **Final Prediction**:
   - Combines both approaches with weighted averaging
   - Returns top 3 diseases with confidence scores
   - Provides comprehensive recommendations

---

## Best Practices

1. **Train the model regularly** with new user data
2. **Set appropriate symptom weights** in disease-symptom relationships
3. **Monitor prediction accuracy** through user feedback
4. **Update recommendations** based on medical knowledge
5. **Ensure data privacy** - all user data is protected

---

## Notes

- All severity scores are on a scale of 0-100
- Confidence scores represent prediction certainty (0-100%)
- Health score is calculated from recent predictions (0-100, higher is better)
- Recommendations are personalized based on user history and patterns

python manage.py train_model
python manage.py seed_data