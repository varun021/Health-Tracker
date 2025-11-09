# Roji - AI-Powered Disease Prediction System

> An intelligent health prediction platform combining Machine Learning (Naive Bayes) with rule-based symptom matching to provide accurate disease predictions and personalized health recommendations.

## 📋 Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Architecture](#architecture)
- [API Documentation](#api-documentation)
- [Contributing](#contributing)
- [License](#license)

## 🎯 Overview

Roji is a full-stack health prediction application that helps users understand potential health conditions based on their symptoms. It uses a **hybrid prediction system** combining:

- **Naive Bayes Machine Learning (60% weight)**: Data-driven probability-based predictions
- **Rule-based Matching (40% weight)**: Domain knowledge and symptom weighted scoring

The system analyzes comprehensive health data including:
- Physical symptoms with severity and duration
- Demographic information (age, gender, height, weight)
- Medical history (existing diseases, allergies, medications)
- Lifestyle factors (sleep, exercise, stress, diet, smoking, alcohol)
- Travel history and occupation

## ✨ Key Features

### For Users
- 🏥 **Symptom Assessment**: Input symptoms with severity levels and duration
- 🤖 **AI-Powered Predictions**: Get disease predictions with confidence scores
- 📊 **Health Analytics**: Track health trends over time
- 💊 **Personalized Recommendations**: Lifestyle, diet, and medical advice
- 📈 **Health Tracking**: Monitor predictions history and patterns
- 📄 **Report Generation**: Export health data in PDF, CSV, or JSON formats
- 🔐 **Secure Authentication**: JWT-based user authentication

### For Admins
- 🎓 **Model Training**: Train/retrain ML model with new data
- 🗂️ **Disease Management**: Add/edit/delete diseases and symptoms
- ⚖️ **Symptom Weighting**: Set disease-symptom relationship weights
- 📊 **Data Analytics**: View comprehensive health statistics
- 👥 **User Management**: Monitor user submissions and data

## 🛠 Tech Stack

### Backend
- **Framework**: Django 4.x with Django REST Framework
- **ML/AI**: scikit-learn (Naive Bayes), NumPy
- **Database**: SQLite (development), PostgreSQL (production-ready)
- **Authentication**: JWT (Simple JWT) with cookie support
- **API Documentation**: drf-spectacular (Swagger/ReDoc)
- **Admin UI**: Jazzmin (enhanced Django admin)

### Frontend
- **Framework**: Next.js 15.5.6 with React 19.1.0
- **Build Tool**: Turbopack (fast rebuilds)
- **Styling**: Tailwind CSS v4
- **Components**: Radix UI + shadcn/ui
- **State Management**: Zustand
- **HTTP Client**: Axios
- **Icons**: Lucide React, Tabler Icons
- **UI Enhancements**: Sonner (toast notifications), Embla Carousel
- **Validation**: Zod
- **Animations**: TW Animate CSS

## 📁 Project Structure

```
roji-project/
├── backend/                    # Django backend
│   ├── core/                   # Project settings & configuration
│   │   ├── settings.py         # Django settings
│   │   ├── urls.py             # URL routing
│   │   ├── wsgi.py             # WSGI configuration
│   │   └── asgi.py             # ASGI configuration
│   ├── predictor/              # Disease prediction app
│   │   ├── models.py           # Database models
│   │   ├── views.py            # API viewsets
│   │   ├── serializers.py      # DRF serializers
│   │   ├── ml_predictor.py     # ML engine (Naive Bayes + hybrid)
│   │   ├── utils.py            # Utility functions
│   │   ├── urls.py             # App URLs
│   │   └── admin.py            # Django admin configuration
│   ├── users/                  # User management app
│   ├── ml_models/              # Trained ML models & encoders
│   ├── manage.py               # Django management script
│   ├── requirements.txt        # Python dependencies
│   ├── db.sqlite3              # Development database
│   └── api_docs.md             # API documentation
│
└── frontend/                   # Next.js frontend
    ├── app/                    # Next.js app directory
    │   ├── (auth)/             # Auth related pages
    │   │   ├── login/
    │   │   ├── signup/
    │   │   └── auth/
    │   ├── dashboard/          # Main dashboard
    │   └── layout.jsx          # Root layout
    ├── components/             # React components
    │   ├── ui/                 # Reusable UI components
    │   ├── auth/               # Authentication components
    │   ├── symptom/            # Symptom-related components
    │   ├── app-sidebar.jsx     # Sidebar navigation
    │   └── ...
    ├── lib/                    # Utility functions
    │   └── stores/             # Zustand stores
    ├── styles/                 # Global styles
    ├── package.json            # Dependencies
    ├── next.config.mjs         # Next.js configuration
    ├── tailwind.config.js      # Tailwind configuration
    └── README.md               # Frontend README
```

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- Node.js 18+
- npm or yarn
- Git

### Backend Setup

1. **Clone and navigate to backend**
   ```bash
   cd backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

6. **Seed initial data** (optional)
   ```bash
   python manage.py seed_data
   ```

7. **Start development server**
   ```bash
   python manage.py runserver
   ```
   Backend runs on: `http://localhost:8000`
   Admin panel: `http://localhost:8000/admin`
   API docs: `http://localhost:8000/api/schema/swagger-ui/`

### Frontend Setup

1. **Navigate to frontend**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Create .env.local**
   ```bash
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

4. **Start development server**
   ```bash
   npm run dev
   ```
   Frontend runs on: `http://localhost:3000`

## 🏗 Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React/Next.js)                 │
│  - User Interface                                           │
│  - Authentication (JWT)                                    │
│  - State Management (Zustand)                              │
│  - Real-time notifications (Sonner)                        │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP/REST API
┌────────────────────▼────────────────────────────────────────┐
│              Backend (Django + DRF)                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ API Layer (ViewSets)                                 │  │
│  │ - DiseaseViewSet                                     │  │
│  │ - SymptomViewSet                                     │  │
│  │ - PredictionViewSet                                  │  │
│  │ - Analytics & Reports                               │  │
│  └──────────────────┬───────────────────────────────────┘  │
│                     │                                       │
│  ┌──────────────────▼───────────────────────────────────┐  │
│  │ Business Logic Layer                                 │  │
│  │ ┌───────────────────────────────────────────────┐   │  │
│  │ │ HybridPredictor                               │   │  │
│  │ │ - Naive Bayes (60% weight)                    │   │  │
│  │ │ - Rule-based (40% weight)                     │   │  │
│  │ │ - Combines predictions                        │   │  │
│  │ └───────────────────────────────────────────────┘   │  │
│  │ ┌───────────────────────────────────────────────┐   │  │
│  │ │ Utility Functions                             │   │  │
│  │ │ - Analytics calculation                       │   │  │
│  │ │ - Report generation                           │   │  │
│  │ │ - Data export                                 │   │  │
│  │ └───────────────────────────────────────────────┘   │  │
│  └──────────────────┬───────────────────────────────────┘  │
│                     │                                       │
│  ┌──────────────────▼───────────────────────────────────┐  │
│  │ Data Access Layer (Models & ORM)                     │  │
│  │ - Disease, Symptom, DiseaseSymptom                   │  │
│  │ - UserSubmission, SubmissionSymptom                  │  │
│  │ - DiseasePrediction                                  │  │
│  └──────────────────┬───────────────────────────────────┘  │
│                     │                                       │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│              Database (SQLite/PostgreSQL)                   │
│  - User data                                                │
│  - Disease & Symptom definitions                           │
│  - Prediction history                                      │
│  - ML model training data                                  │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow - Prediction Process

```
1. User Form Input
   │
   └─► Validation (age, severity, etc.)
       │
       └─► Prepare Feature Vector
           │
           └─► ML Engine (HybridPredictor)
               │
               ├─► Naive Bayes Prediction (60%)
               │   └─► Load trained model
               │   └─► Calculate probabilities
               │
               └─► Rule-based Prediction (40%)
                   └─► Match symptoms
                   └─► Calculate scores
                   └─► Apply user history bonus
               │
               └─► Combine & Weight Predictions
                   │
                   └─► Calculate Severity Score
                       │
                       └─► Generate Recommendations
                           │
                           └─► Return Results to Frontend
```

## 📡 API Documentation

### Base URL
```
http://localhost:8000/api
```

### Authentication
All endpoints except `/api/diseases/` and `/api/symptoms/` require JWT authentication.

**Headers:**
```
Authorization: Bearer <access_token>
```

### Core Endpoints

#### 1. Diseases
```
GET    /api/diseases/          - List all diseases
GET    /api/diseases/{id}/     - Get disease details
```

#### 2. Symptoms
```
GET    /api/symptoms/          - List all symptoms
GET    /api/symptoms/{id}/     - Get symptom details
```

#### 3. Predictions
```
POST   /api/predictions/predict/                      - Make prediction
GET    /api/predictions/history/                      - Get history (paginated)
GET    /api/predictions/analytics/                    - Get analytics
GET    /api/predictions/comparison_report/            - Compare periods
GET    /api/predictions/recommendations_based_on_history/ - Get recommendations
POST   /api/predictions/train_model/                  - Train ML model (admin)
GET    /api/predictions/export_data/?format=csv|json - Export data
POST   /api/predictions/generate_report/              - Generate report
```

### Prediction Request Example

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

### Prediction Response Example

```json
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

## 🤖 How the Hybrid Prediction System Works

### 1. **Naive Bayes Component (60% weight)**
- Trained on disease-symptom relationships from the database
- Learns from historical user submissions
- Uses symptom severity as feature values
- Outputs probability-based predictions for all diseases

**Training Data:**
- Disease-symptom definitions with weights (1-10)
- Historical user submissions (last 1000)
- Feature vectors representing symptom profiles

### 2. **Rule-Based Component (40% weight)**
- Matches input symptoms against disease profiles
- Calculates scores based on:
  - Symptom match percentage (40%)
  - Weighted severity matching (60%)
  - User history bonus (optional)
- Returns ranked diseases by confidence

### 3. **Final Prediction**
- Combines both approaches with weighted averaging:
  ```
  Final Score = (ML Score × 0.6) + (Rule Score × 0.4)
  ```
- Returns top 3 diseases with combined confidence scores
- Calculates severity category (NORMAL/MODERATE/RISKY)
- Generates personalized recommendations

## 📚 Database Schema

### Core Models

**Disease**
- id (Primary Key)
- name (CharField, unique)
- description (TextField)
- lifestyle_tips (TextField)
- diet_advice (TextField)
- medical_advice (TextField)
- created_at (DateTimeField)

**Symptom**
- id (Primary Key)
- name (CharField, unique)
- description (TextField)
- created_at (DateTimeField)

**DiseaseSymptom** (Junction Table)
- disease (ForeignKey → Disease)
- symptom (ForeignKey → Symptom)
- weight (IntegerField, 1-10)

**UserSubmission**
- id (Primary Key)
- user (ForeignKey → User)
- name, age, gender (Personal Info)
- height, weight, bmi (Physical Metrics)
- occupation, existing_diseases, allergies, medications (Medical Info)
- smoking, alcohol, diet, sleep_hours, exercise_frequency, stress_level (Lifestyle)
- severity_score, severity_category (Results)
- created_at (DateTimeField)

**SubmissionSymptom** (Junction Table)
- submission (ForeignKey → UserSubmission)
- symptom (ForeignKey → Symptom)
- severity (IntegerField, 1-10)
- duration (CharField)
- onset (CharField: SUDDEN/GRADUAL)

**DiseasePrediction**
- submission (ForeignKey → UserSubmission)
- disease (ForeignKey → Disease)
- confidence_score (FloatField, 0-100)
- rank (IntegerField)

## 🔧 Configuration & Customization

### Backend Configuration

#### settings.py Environment Variables
```python
DEBUG = True  # Set to False in production
SECRET_KEY = 'your-secret-key'
ALLOWED_HOSTS = ['localhost', '127.0.0.1']
```

#### CORS Settings
```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # Frontend URL
]
```

#### JWT Settings
```python
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
}
```

### Frontend Configuration

#### .env.local
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 📖 Usage Examples

### 1. Make a Disease Prediction
```bash
curl -X POST http://localhost:8000/api/predictions/predict/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John",
    "age": 30,
    "gender": "M",
    "height": 175,
    "weight": 70,
    "symptoms": [{"id": 1, "severity": 8, "duration": "3 days", "onset": "SUDDEN"}]
  }'
```

### 2. Get Health Analytics
```bash
curl http://localhost:8000/api/predictions/analytics/?days=30 \
  -H "Authorization: Bearer <token>"
```

### 3. Generate Health Report
```bash
curl -X POST http://localhost:8000/api/predictions/generate_report/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "format": "pdf",
    "start_date": "2024-09-01",
    "end_date": "2024-10-21"
  }'
```

## 🧪 Testing

### Backend Tests
```bash
cd backend
python manage.py test
```

### Frontend Tests
```bash
cd frontend
npm run test
```

## 📦 Deployment

### Backend Deployment (Production)
1. Update settings.py:
   ```python
   DEBUG = False
   ALLOWED_HOSTS = ['yourdomain.com']
   ```

2. Use PostgreSQL instead of SQLite

3. Set up environment variables for:
   - SECRET_KEY
   - DATABASE_URL
   - CORS_ALLOWED_ORIGINS

4. Deploy using:
   - Gunicorn (WSGI server)
   - Nginx (reverse proxy)
   - Supervisor (process management)

### Frontend Deployment
1. Build production bundle:
   ```bash
   npm run build
   ```

2. Deploy to Vercel, Netlify, or traditional hosting

## 🛡️ Security Considerations

- ✅ JWT authentication with HTTP-only cookies
- ✅ CORS configured for specific origins
- ✅ CSRF protection enabled
- ✅ Password validation and hashing
- ✅ User data privacy and encryption
- ⚠️ TODO: Add rate limiting
- ⚠️ TODO: Implement data encryption at rest
- ⚠️ TODO: Add audit logging

## 🚦 Performance Optimization

- **ML Model Caching**: Trained models cached in memory
- **Database Indexing**: Indexes on frequently queried fields
- **Frontend Optimization**: Code splitting, lazy loading, image optimization
- **API Response Pagination**: Limit/offset pagination for large datasets
- **Database Query Optimization**: Prefetch/select_related in Django ORM

## 📈 Future Enhancements

1. **Advanced ML Features**
   - Random Forest classifier
   - Neural networks for pattern recognition
   - Personalized model fine-tuning per user

2. **Feature Additions**
   - Real-time chatbot for symptom questions
   - Integration with medical databases (ICD-10)
   - Prescription recommendations
   - Doctor appointment booking

3. **Mobile App**
   - React Native / Flutter application
   - Offline support
   - Push notifications

4. **Analytics Dashboard**
   - Admin analytics
   - Epidemiological tracking
   - Disease outbreak detection

## 📞 Support & Contributions

For issues, feature requests, or contributions, please create an issue or submit a pull request.

## 📄 License

This project is licensed under the MIT License - see LICENSE file for details.

---

**Last Updated**: November 2024  
**Version**: 1.0.0

# Health-Tracker

This repository contains a Health-Tracker application with separate frontend and backend folders. This README explains how to set up and run both parts locally (development) and build them for production.

## Prerequisites

- Node.js (>= 16) and npm or Yarn
- Git
- (Optional) Docker & Docker Compose if you prefer containerized setup
- (Optional) A database (PostgreSQL or MongoDB) depending on the backend configuration

## Repository layout

- /frontend  - the frontend application (React/Vue/Angular — adjust to your stack)
- /backend   - the backend application (Node/Express, or similar)

If your project uses different folders, update the paths below accordingly.

---

## Frontend — Local development

1. Open a terminal and navigate to the frontend folder:

   ```bash
   cd frontend
   ```

2. Install dependencies:

   Using npm:
   ```bash
   npm install
   ```

   Or using Yarn:
   ```bash
   yarn install
   ```

3. Create a .env file in the frontend folder (if required) based on the example below:

   Example .env
   ```env
   REACT_APP_API_URL=http://localhost:4000/api
   # other REACT_APP_* variables your app expects
   ```

4. Start the development server:

   ```bash
   npm start
   # or
   yarn start
   ```

   The frontend dev server typically runs at http://localhost:3000. Adjust the port if your project uses a different default.

5. Build for production:

   ```bash
   npm run build
   # or
   yarn build
   ```

   The production-ready static files will be written to the `build` (or `dist`) folder.

---

## Backend — Local development

1. Open a terminal and navigate to the backend folder:

   ```bash
   cd backend
   ```

2. Install dependencies:

   ```bash
   npm install
   # or
   yarn install
   ```

3. Create a .env file in the backend folder with required environment variables. Example:

   Example .env
   ```env
   PORT=4000
   NODE_ENV=development
   DATABASE_URL=postgres://user:password@localhost:5432/health_tracker_db
   # Or for MongoDB:
   # MONGODB_URI=mongodb://localhost:27017/health_tracker_db
   JWT_SECRET=your_jwt_secret_here
   # Any other variables your backend requires
   ```

4. Database setup (example PostgreSQL / MongoDB instructions):

   - PostgreSQL:
     - Create a database and a user with privileges.
     - Run any migrations or seeders your project provides. For example, if you use Knex or Sequelize:
       ```bash
       npx knex migrate:latest
       # or
       npx sequelize db:migrate
       ```

   - MongoDB:
     - Ensure mongod is running and the MONGODB_URI is set correctly.
     - Run any seed scripts if provided.

5. Start the backend server in development:

   ```bash
   npm run dev
   # or
   yarn dev
   ```

   The backend typically listens on the port specified in your .env (e.g., 4000).

6. Start the backend in production:

   ```bash
   npm start
   # or, if you use a build step (TypeScript):
   npm run build && npm start
   ```

---

## Running frontend and backend together

Option A — Run them in separate terminals

- Start the backend in one terminal (cd backend && npm run dev)
- Start the frontend in another terminal (cd frontend && npm start)

Option B — Root-level script (optional)

If you want to start both with a single command, you can install `concurrently` at the repository root and add a script:

```json
"scripts": {
  "dev": "concurrently \"cd backend && npm run dev\" \"cd frontend && npm start\""
}
```

Then run:
```bash
npm run dev
```

Option C — Docker & Docker Compose

Create a docker-compose.yml at the repo root (example skeleton):

```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "4000:4000"
    env_file:
      - ./backend/.env
    depends_on:
      - db

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_API_URL=http://localhost:4000/api

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: health_tracker_db
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - db-data:/var/lib/postgresql/data

volumes:
  db-data:
```

Adjust the compose file to match your app's details.

---

## Environment variable examples

Frontend (.env)
```env
REACT_APP_API_URL=http://localhost:4000/api
```

Backend (.env)
```env
PORT=4000
NODE_ENV=development
DATABASE_URL=postgres://user:password@localhost:5432/health_tracker_db
JWT_SECRET=some-secret
```

Never commit .env files with secrets to the repository. Keep them out of version control.

---

## Troubleshooting

- "Frontend cannot reach backend": Verify REACT_APP_API_URL and that the backend server is running and CORS is configured correctly.
- "Database connection errors": Check DATABASE_URL / MONGODB_URI, ensure the database is running and credentials are correct.
- "Port already in use": change the PORT in .env or stop the process using that port.
- Check package.json scripts in frontend/backend if the commands above differ.

---

## Tests

If your project has tests, run them from the respective folder:

```bash
cd backend
npm test

cd frontend
npm test
```

---

## Contributing

If you want to contribute, open a pull request describing your changes. Follow any code style or linting rules in the repository.

---

## Contact

If you have questions, open an issue in this repository or contact the maintainers.
