# API Reference & Deployment Guide - Health-Tracker

## Table of Contents
1. [API Authentication](#api-authentication)
2. [Core API Endpoints](#core-api-endpoints)
3. [Request/Response Examples](#requestresponse-examples)
4. [Error Handling](#error-handling)
5. [Rate Limiting](#rate-limiting)
6. [Deployment Guide](#deployment-guide)
7. [Environment Configuration](#environment-configuration)
8. [Monitoring & Logging](#monitoring--logging)

---

## API Authentication

### JWT Token Flow

```
1. User Login
   POST /api/users/login/ → Get access_token & refresh_token
   
2. Store Token
   localStorage.setItem('access_token', token)
   
3. Send Requests
   Authorization: Bearer <access_token>
   
4. Token Refresh
   POST /api/users/refresh/ → Get new access_token
   
5. Logout
   POST /api/users/logout/ → Invalidate tokens
```

### Token Configuration

**Access Token Lifetime**: 60 minutes  
**Refresh Token Lifetime**: 1 day  
**Token Storage**: HTTP-only cookies or localStorage

### Login Endpoint

```http
POST /api/users/login/
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}

Response: 200 OK
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "name": "John Doe"
  }
}
```

### Refresh Token Endpoint

```http
POST /api/users/refresh/
Content-Type: application/json

{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}

Response: 200 OK
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

---

## Core API Endpoints

### 1. Disease Endpoints

#### List All Diseases
```http
GET /api/diseases/

Response: 200 OK
[
  {
    "id": 1,
    "name": "Common Cold",
    "description": "Viral infection of upper respiratory tract",
    "lifestyle_tips": "Rest, stay hydrated",
    "diet_advice": "Warm fluids, vitamin C",
    "medical_advice": "Consult if symptoms persist",
    "created_at": "2024-10-01T00:00:00Z"
  },
  ...
]
```

#### Get Disease Details
```http
GET /api/diseases/{id}/

Response: 200 OK
{
  "id": 1,
  "name": "Common Cold",
  "description": "...",
  "symptoms": [
    {
      "symptom": {
        "id": 1,
        "name": "Fever"
      },
      "weight": 7
    },
    ...
  ]
}
```

#### Create Disease (Admin Only)
```http
POST /api/diseases/
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "name": "New Disease",
  "description": "Description here",
  "lifestyle_tips": "Tips",
  "diet_advice": "Advice",
  "medical_advice": "Advice"
}

Response: 201 Created
```

#### Update Disease (Admin Only)
```http
PUT /api/diseases/{id}/
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "name": "Updated Disease",
  "description": "..."
}

Response: 200 OK
```

#### Delete Disease (Admin Only)
```http
DELETE /api/diseases/{id}/
Authorization: Bearer <admin_token>

Response: 204 No Content
```

---

### 2. Symptom Endpoints

#### List All Symptoms
```http
GET /api/symptoms/

Response: 200 OK
[
  {
    "id": 1,
    "name": "Fever",
    "description": "Elevated body temperature above normal",
    "created_at": "2024-10-01T00:00:00Z"
  },
  ...
]
```

#### Get Symptom Details
```http
GET /api/symptoms/{id}/

Response: 200 OK
{
  "id": 1,
  "name": "Fever",
  "description": "..."
}
```

#### Create Symptom (Admin Only)
```http
POST /api/symptoms/
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "name": "Symptom Name",
  "description": "Symptom description"
}

Response: 201 Created
```

---

### 3. Prediction Endpoints

#### Make Prediction
```http
POST /api/predictions/predict/
Authorization: Bearer <user_token>
Content-Type: application/json

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

Response: 201 Created
{
  "submission": {
    "id": 123,
    "name": "John Doe",
    "age": 35,
    "severity_score": 65.5,
    "severity_category": "MODERATE",
    "primary_prediction": "Common Cold"
  },
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
  ],
  "recommendations": {
    "lifestyle_tips": ["Get adequate rest", "Stay hydrated"],
    "diet_advice": ["Warm fluids", "Vitamin C rich foods"],
    "medical_advice": ["Consult doctor if symptoms worsen"]
  },
  "additional_info": {
    "severity_interpretation": "Moderate symptoms detected",
    "next_steps": "Track your symptoms for the next 3 days",
    "disclaimer": "This is an AI-assisted health prediction..."
  }
}
```

#### Get Prediction History
```http
GET /api/predictions/history/?page=1&page_size=20
Authorization: Bearer <user_token>

Response: 200 OK
{
  "count": 45,
  "page": 1,
  "page_size": 20,
  "total_pages": 3,
  "results": [
    {
      "id": 123,
      "name": "John Doe",
      "age": 35,
      "severity_category": "MODERATE",
      "primary_prediction": "Common Cold",
      "created_at": "2024-11-01T12:00:00Z"
    },
    ...
  ]
}
```

#### Get Health Analytics
```http
GET /api/predictions/analytics/?days=30
Authorization: Bearer <user_token>

Response: 200 OK
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
  "health_score": 72.5
}
```

#### Compare Health Periods
```http
GET /api/predictions/comparison_report/
Authorization: Bearer <user_token>

Response: 200 OK
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
    }
  }
}
```

#### Get Personalized Recommendations
```http
GET /api/predictions/recommendations_based_on_history/
Authorization: Bearer <user_token>

Response: 200 OK
{
  "health_score": 68.5,
  "total_recommendations": 3,
  "recommendations": [
    {
      "category": "lifestyle",
      "title": "Insufficient Sleep",
      "message": "You frequently report less than 6 hours of sleep",
      "action": "Aim for 7-9 hours of sleep"
    },
    {
      "category": "lifestyle",
      "title": "High Stress Levels",
      "message": "High stress is frequently reported",
      "action": "Practice relaxation techniques"
    }
  ]
}
```

#### Export User Data
```http
GET /api/predictions/export_data/?format=csv
Authorization: Bearer <user_token>

Response: 200 OK
(CSV file download)

Supported formats: csv, json
```

#### Generate Health Report
```http
POST /api/predictions/generate_report/
Authorization: Bearer <user_token>
Content-Type: application/json

{
  "start_date": "2024-09-01",
  "end_date": "2024-10-21",
  "format": "pdf",
  "include_personal_info": true,
  "include_recommendations": true
}

Response: 200 OK
(PDF/CSV/JSON file download)

Query Parameters (GET):
- start_date (YYYY-MM-DD, optional)
- end_date (YYYY-MM-DD, optional)
- format (pdf, csv, json, default: pdf)
- include_personal_info (boolean, default: true)
- include_recommendations (boolean, default: true)
```

#### Train ML Model (Admin Only)
```http
POST /api/predictions/train_model/
Authorization: Bearer <admin_token>

Response: 200 OK
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

## Request/Response Examples

### Symptom Severity Scale
- **1-3**: Mild (minimal impact on daily activities)
- **4-6**: Moderate (noticeable impact)
- **7-8**: Severe (significant impact)
- **9-10**: Very Severe (cannot perform daily activities)

### Onset Types
```
SUDDEN   - Symptoms appeared suddenly
GRADUAL  - Symptoms developed slowly over time
```

### Diet Types
```
VEG      - Vegetarian
NON_VEG  - Non-Vegetarian
VEGAN    - Vegan
MIXED    - Mixed diet
```

### Gender Options
```
M  - Male
F  - Female
O  - Other
```

### Severity Categories
```
NORMAL   - Severity score < 30
MODERATE - Severity score 30-70
RISKY    - Severity score > 70
```

---

## Error Handling

### Error Response Format
```json
{
  "error": "Error message",
  "code": "ERROR_CODE",
  "details": {...}
}
```

### Common HTTP Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | OK | Successful request |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Invalid input data |
| 401 | Unauthorized | Missing or invalid token |
| 403 | Forbidden | No permission to access |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Duplicate or conflicting data |
| 500 | Server Error | Internal server error |

### Example Error Responses

#### Validation Error
```json
{
  "age": ["Ensure this value is less than or equal to 120."],
  "symptoms": ["At least one symptom is required"]
}
```

#### Authentication Error
```json
{
  "detail": "Authentication credentials were not provided."
}
```

#### Permission Error
```json
{
  "detail": "You do not have permission to perform this action."
}
```

---

## Rate Limiting

### Rate Limit Headers
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1699500000
```

### Rate Limits by Endpoint

| Endpoint | Limit | Window |
|----------|-------|--------|
| /api/predictions/predict/ | 30 | 1 hour |
| /api/predictions/analytics/ | 50 | 1 hour |
| /api/predictions/train_model/ | 5 | 1 day |
| Other endpoints | 100 | 1 hour |

### Rate Limit Exceeded Response
```json
{
  "error": "Rate limit exceeded",
  "retry_after": 300
}
```

---

## Deployment Guide

### Pre-Deployment Checklist

#### Backend
- [ ] Environment variables configured
- [ ] Database migrations applied
- [ ] DEBUG set to False
- [ ] SECRET_KEY generated (strong random string)
- [ ] ALLOWED_HOSTS updated
- [ ] CORS_ALLOWED_ORIGINS set
- [ ] Static files collected
- [ ] ML models trained and saved
- [ ] Tests passing
- [ ] Error logging configured

#### Frontend
- [ ] Environment variables configured
- [ ] API URL updated
- [ ] Build succeeds without errors
- [ ] No console warnings/errors
- [ ] Mobile responsive verified
- [ ] Performance optimized
- [ ] Analytics integrated

### Backend Deployment (Django)

#### Using Gunicorn + Nginx

1. **Install Gunicorn**
   ```bash
   pip install gunicorn
   ```

2. **Create Gunicorn Service** (`/etc/systemd/system/roji-api.service`)
   ```ini
   [Unit]
   Description=Roji API Service
   After=network.target

   [Service]
   Type=notify
   User=www-data
   WorkingDirectory=/var/www/roji/backend
   Environment="PATH=/var/www/roji/backend/venv/bin"
   ExecStart=/var/www/roji/backend/venv/bin/gunicorn \
     --workers 4 \
     --worker-class sync \
     --bind 127.0.0.1:8000 \
     core.wsgi:application

   [Install]
   WantedBy=multi-user.target
   ```

3. **Configure Nginx** (`/etc/nginx/sites-available/roji`)
   ```nginx
   upstream roji_api {
       server 127.0.0.1:8000;
   }

   server {
       listen 80;
       server_name api.example.com;
       
       # Redirect to HTTPS
       return 301 https://$server_name$request_uri;
   }

   server {
       listen 443 ssl http2;
       server_name api.example.com;

       ssl_certificate /etc/letsencrypt/live/api.example.com/fullchain.pem;
       ssl_certificate_key /etc/letsencrypt/live/api.example.com/privkey.pem;

       client_max_body_size 10M;

       location /static/ {
           alias /var/www/roji/backend/static/;
       }

       location /media/ {
           alias /var/www/roji/backend/media/;
       }

       location / {
           proxy_pass http://roji_api;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

4. **Enable and Start Services**
   ```bash
   sudo systemctl enable roji-api
   sudo systemctl start roji-api
   sudo systemctl restart nginx
   ```

#### Using Docker

1. **Create Dockerfile**
   ```dockerfile
   FROM python:3.11-slim

   WORKDIR /app

   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt

   COPY . .

   RUN python manage.py collectstatic --noinput

   EXPOSE 8000

   CMD ["gunicorn", "--bind", "0.0.0.0:8000", "core.wsgi:application"]
   ```

2. **Create docker-compose.yml**
   ```yaml
   version: '3.8'

   services:
     web:
       build: .
       ports:
         - "8000:8000"
       environment:
         - DEBUG=False
         - SECRET_KEY=${SECRET_KEY}
         - DATABASE_URL=postgresql://user:password@db:5432/roji
       depends_on:
         - db
       volumes:
         - ./static:/app/static
         - ./media:/app/media

     db:
       image: postgres:15
       environment:
         - POSTGRES_DB=roji
         - POSTGRES_USER=user
         - POSTGRES_PASSWORD=password
       volumes:
         - postgres_data:/var/lib/postgresql/data

   volumes:
     postgres_data:
   ```

3. **Deploy**
   ```bash
   docker-compose up -d
   ```

### Frontend Deployment (Next.js)

#### Using Vercel (Recommended)

1. **Push to Git**
   ```bash
   git push origin main
   ```

2. **Connect to Vercel**
   - Go to vercel.com
   - Import your Git repository
   - Set environment variables
   - Deploy

3. **Configure Environment Variables**
   ```
   NEXT_PUBLIC_API_URL=https://api.example.com
   ```

#### Using Traditional Hosting

1. **Build**
   ```bash
   npm run build
   ```

2. **Deploy .next folder and public directory**
   ```bash
   npm start
   ```

3. **Configure Reverse Proxy (Nginx)**
   ```nginx
   upstream next_app {
       server 127.0.0.1:3000;
   }

   server {
       listen 443 ssl http2;
       server_name example.com;

       ssl_certificate /etc/letsencrypt/live/example.com/fullchain.pem;
       ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;

       location / {
           proxy_pass http://next_app;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
       }
   }
   ```

---

## Environment Configuration

### Backend (.env)

```bash
# Security
DEBUG=False
SECRET_KEY=your-super-secret-key-change-this
ALLOWED_HOSTS=api.example.com,www.api.example.com

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/roji

# CORS
CORS_ALLOWED_ORIGINS=https://example.com,https://www.example.com

# Email (optional)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# AWS S3 (optional)
USE_S3=True
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_STORAGE_BUCKET_NAME=your-bucket
```

### Frontend (.env.production)

```bash
NEXT_PUBLIC_API_URL=https://api.example.com
NEXT_PUBLIC_APP_NAME=Roji
NEXT_PUBLIC_ANALYTICS_ID=your-analytics-id
```

---

## Monitoring & Logging

### Django Logging Configuration

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': '/var/log/roji/django.log',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'predictor': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
        },
    },
}
```

### Performance Monitoring

```bash
# Check API response times
curl -w "@curl-format.txt" -o /dev/null -s https://api.example.com/api/diseases/

# Monitor database queries
# Enable Django debug toolbar in development
# Use New Relic or DataDog for production
```

### Health Check Endpoint

```http
GET /api/health/

Response: 200 OK
{
  "status": "healthy",
  "database": "connected",
  "cache": "connected",
  "ml_model": "loaded"
}
```

---

**Last Updated**: November 2024  
**Version**: 1.0.0
