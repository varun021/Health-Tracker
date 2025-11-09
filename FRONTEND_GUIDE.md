# Frontend Development Guide - Roji Health Predictor

## Table of Contents
1. [Project Overview](#project-overview)
2. [Technology Stack](#technology-stack)
3. [Project Setup](#project-setup)
4. [Folder Structure](#folder-structure)
5. [Key Technologies Explained](#key-technologies-explained)
6. [Component Architecture](#component-architecture)
7. [State Management](#state-management)
8. [Authentication Flow](#authentication-flow)
9. [API Integration](#api-integration)
10. [Styling & Themes](#styling--themes)
11. [Development Workflow](#development-workflow)

---

## Project Overview

The Roji frontend is a modern, responsive web application built with **Next.js 15** and **React 19**. It provides a user-friendly interface for:
- Symptom assessment and submission
- Disease prediction viewing
- Health analytics and history tracking
- Report generation and data export
- User authentication and profile management

### Key Features
- **Server-side Rendering**: Fast initial page load with SSR
- **Client-side Interactivity**: Smooth React components
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Accessibility**: Radix UI ensures WCAG compliance
- **Type Safety**: JavaScript with JSDoc for better DX
- **State Management**: Global state with Zustand
- **Dark Mode**: Theme switching support

---

## Technology Stack

### Core Framework
- **Next.js 15.5.6**: React meta-framework for production
- **React 19.1.0**: UI library with hooks and concurrent features
- **Turbopack**: Ultra-fast build tool (replaces Webpack)

### Styling & UI
- **Tailwind CSS v4**: Utility-first CSS framework
- **Radix UI**: Unstyled, accessible component primitives
- **shadcn/ui**: Pre-built components using Radix + Tailwind
- **Lucide React**: Beautiful SVG icons
- **Tabler Icons**: Additional icon set
- **TW Animate CSS**: Tailwind animation utilities

### State & Data Management
- **Zustand**: Lightweight state management
- **Axios**: HTTP client for API calls
- **Zod**: TypeScript-first schema validation
- **TanStack React Table**: Advanced table component

### UI Enhancements
- **Sonner**: Toast notifications
- **Embla Carousel**: React carousel/slider
- **dnd-kit**: Drag and drop toolkit
- **next-themes**: Theme management

### Development Tools
- **Biome**: Fast linter and formatter
- **PostCSS**: CSS transformation

---

## Project Setup

### Prerequisites
```bash
Node.js 18+
npm 9+ or yarn 1.22+
```

### 1. Install Dependencies
```bash
cd frontend
npm install
```

### 2. Environment Configuration
Create `.env.local`:
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=Roji
```

### 3. Run Development Server
```bash
npm run dev
```

Server runs on: `http://localhost:3000`

### 4. Build for Production
```bash
npm run build
npm start
```

### 5. Code Quality
```bash
# Lint code
npm run lint

# Format code
npm run format
```

---

## Folder Structure

```
frontend/
├── app/                              # Next.js App Router
│   ├── (auth)/                       # Auth routes (not in URL)
│   │   ├── login/
│   │   │   └── page.jsx              # Login page
│   │   ├── signup/
│   │   │   └── page.jsx              # Signup page
│   │   └── auth/
│   │       └── page.jsx              # Auth redirect
│   ├── dashboard/
│   │   └── page.jsx                  # Main dashboard
│   ├── layout.jsx                    # Root layout
│   └── page.jsx                      # Home page
│
├── components/                       # React components
│   ├── ui/                           # Reusable UI components
│   │   ├── button.jsx
│   │   ├── card.jsx
│   │   ├── dialog.jsx
│   │   ├── dropdown-menu.jsx
│   │   ├── form.jsx
│   │   ├── input.jsx
│   │   ├── label.jsx
│   │   ├── sidebar.jsx
│   │   ├── tabs.jsx
│   │   └── ...
│   ├── auth/
│   │   ├── protected-route.jsx       # Route protection wrapper
│   │   ├── login-form.jsx
│   │   ├── signup-form.jsx
│   │   └── ...
│   ├── symptom/
│   │   ├── UserForm.jsx              # Main prediction form
│   │   ├── SymptomInput.jsx
│   │   ├── ResultsDisplay.jsx
│   │   └── ...
│   ├── app-sidebar.jsx               # Main navigation sidebar
│   ├── site-header.jsx               # Top header
│   ├── chart-area-interactive.jsx    # Analytics charts
│   ├── section-cards.jsx             # Dashboard cards
│   └── ...
│
├── lib/                              # Utility functions
│   ├── stores/                       # Zustand stores
│   │   ├── navigation-store.js       # Navigation state
│   │   └── useAuthStore.js           # Auth state
│   ├── utils.js                      # Helper functions
│   ├── cn.js                         # Class merging
│   └── ...
│
├── styles/                           # Global styles
│   ├── globals.css                   # Global CSS
│   └── ...
│
├── public/                           # Static assets
│   ├── images/
│   └── icons/
│
├── hooks/                            # Custom React hooks (optional)
│   └── useApi.js                     # API fetching hook
│
├── .env.local                        # Environment variables
├── next.config.mjs                   # Next.js configuration
├── tailwind.config.js                # Tailwind configuration
├── postcss.config.mjs                # PostCSS configuration
├── jsconfig.json                     # JavaScript config
├── biome.json                        # Biome linter config
├── package.json
└── README.md
```

---

## Key Technologies Explained

### 1. Next.js App Router
Modern file-based routing with server and client components.

**Key files:**
- `page.jsx` - Route pages
- `layout.jsx` - Shared layouts
- `error.jsx` - Error boundaries
- `loading.jsx` - Suspense fallbacks

**Example structure:**
```
app/
├── dashboard/
│   └── page.jsx          # /dashboard
├── (auth)/
│   ├── login/
│   │   └── page.jsx      # /login
│   └── signup/
│       └── page.jsx      # /signup
└── layout.jsx            # Root layout
```

### 2. React Components (Client-side)
Use `"use client"` directive for interactivity.

```javascript
"use client"

import { useState } from 'react'

export default function MyComponent() {
  const [count, setCount] = useState(0)
  
  return (
    <div>
      <p>Count: {count}</p>
      <button onClick={() => setCount(count + 1)}>Increment</button>
    </div>
  )
}
```

### 3. Radix UI + shadcn/ui
Pre-built, accessible components.

```javascript
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Dialog, DialogContent, DialogHeader } from "@/components/ui/dialog"

export default function Form() {
  return (
    <Dialog>
      <DialogContent>
        <DialogHeader>Create Account</DialogHeader>
        <Input placeholder="Email" />
        <Button>Submit</Button>
      </DialogContent>
    </Dialog>
  )
}
```

### 4. Tailwind CSS
Utility-first CSS for rapid styling.

```javascript
<div className="flex gap-4 p-6 bg-white rounded-lg shadow-md">
  <h1 className="text-2xl font-bold text-gray-900">Title</h1>
  <p className="text-gray-600">Description</p>
</div>
```

### 5. Zustand State Management
Lightweight, hook-based state.

```javascript
// stores/useAuthStore.js
import { create } from 'zustand'

const useAuthStore = create((set) => ({
  user: null,
  token: null,
  setUser: (user) => set({ user }),
  setToken: (token) => set({ token }),
  logout: () => set({ user: null, token: null })
}))

export default useAuthStore

// Usage in component
import useAuthStore from '@/stores/useAuthStore'

export default function Profile() {
  const { user, logout } = useAuthStore()
  
  return (
    <div>
      <p>Welcome, {user?.name}</p>
      <button onClick={logout}>Logout</button>
    </div>
  )
}
```

### 6. Axios API Client
```javascript
// API configuration
import axios from 'axios'

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  headers: {
    'Content-Type': 'application/json'
  },
  withCredentials: true
})

// Add auth token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export default api
```

---

## Component Architecture

### Page Components (app/ directory)

#### dashboard/page.jsx
Main dashboard with prediction form.

```javascript
"use client"

import ProtectedRoute from '@/components/auth/protected-route'
import { AppSidebar } from "@/components/app-sidebar"
import UserForm from '@/components/symptom/UserForm'
import { SidebarProvider, SidebarInset } from "@/components/ui/sidebar"

export default function DashboardPage() {
  return (
    <ProtectedRoute>
      <SidebarProvider>
        <AppSidebar />
        <SidebarInset>
          <UserForm />
        </SidebarInset>
      </SidebarProvider>
    </ProtectedRoute>
  )
}
```

### Feature Components

#### UserForm Component
Main form for disease prediction.

```javascript
"use client"

import { useState } from 'react'
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import api from '@/lib/api'

export default function UserForm() {
  const [formData, setFormData] = useState({
    name: '',
    age: '',
    gender: '',
    symptoms: []
  })
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    
    try {
      const response = await api.post('/api/predictions/predict/', formData)
      setResults(response.data)
    } catch (error) {
      console.error('Prediction error:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <Input
        placeholder="Name"
        value={formData.name}
        onChange={(e) => setFormData({...formData, name: e.target.value})}
      />
      
      <Button type="submit" disabled={loading}>
        {loading ? 'Predicting...' : 'Get Prediction'}
      </Button>
      
      {results && <ResultsDisplay results={results} />}
    </form>
  )
}
```

#### ResultsDisplay Component
Display prediction results.

```javascript
"use client"

export default function ResultsDisplay({ results }) {
  return (
    <div className="space-y-4">
      <div className="p-4 bg-blue-50 rounded-lg">
        <h2 className="text-lg font-semibold">Primary Prediction</h2>
        <p className="text-2xl font-bold text-blue-600">
          {results.submission.primary_prediction}
        </p>
        <p className="text-sm text-gray-600">
          Severity: {results.submission.severity_category}
        </p>
      </div>

      <div className="space-y-2">
        <h3 className="font-semibold">All Predictions</h3>
        {results.predicted_diseases.map((disease, idx) => (
          <div key={idx} className="p-3 border rounded-lg">
            <p className="font-medium">{disease.name}</p>
            <p className="text-sm text-gray-600">
              Confidence: {disease.confidence_score}%
            </p>
          </div>
        ))}
      </div>

      <div className="space-y-2">
        <h3 className="font-semibold">Recommendations</h3>
        <div>
          <p className="font-medium text-sm">Lifestyle Tips:</p>
          <ul className="list-disc pl-5">
            {results.recommendations.lifestyle_tips.map((tip, idx) => (
              <li key={idx} className="text-sm text-gray-600">{tip}</li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  )
}
```

### UI Components (components/ui/)

Reusable, unstyled components from Radix UI + Tailwind.

```javascript
// components/ui/button.jsx
import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cn } from "@/lib/utils"

const Button = React.forwardRef(({ className, asChild = false, ...props }, ref) => {
  const Comp = asChild ? Slot : "button"
  return (
    <Comp
      className={cn(
        "inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium",
        "bg-primary text-primary-foreground hover:bg-primary/90",
        "h-10 px-4 py-2 transition-colors",
        className
      )}
      ref={ref}
      {...props}
    />
  )
})

Button.displayName = "Button"
export { Button }
```

---

## State Management

### Zustand Stores

#### 1. Auth Store (stores/useAuthStore.js)
```javascript
import { create } from 'zustand'
import api from '@/lib/api'

const useAuthStore = create((set) => ({
  user: null,
  token: null,
  isLoading: false,
  error: null,

  // Actions
  login: async (email, password) => {
    set({ isLoading: true })
    try {
      const response = await api.post('/api/users/login/', { email, password })
      set({ user: response.data.user, token: response.data.access })
      localStorage.setItem('access_token', response.data.access)
    } catch (error) {
      set({ error: error.message })
    } finally {
      set({ isLoading: false })
    }
  },

  signup: async (email, password, name) => {
    // Similar implementation
  },

  logout: () => {
    set({ user: null, token: null })
    localStorage.removeItem('access_token')
  },

  setUser: (user) => set({ user }),
}))

export default useAuthStore
```

#### 2. Navigation Store (stores/navigation-store.js)
```javascript
import { create } from 'zustand'

export const useNavigationStore = create((set) => ({
  activeComponent: null,
  
  setActiveComponent: (component) => set({ activeComponent: component }),
  
  resetComponent: () => set({ activeComponent: null })
}))
```

---

## Authentication Flow

### Protected Route Wrapper
```javascript
"use client"

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import useAuthStore from '@/stores/useAuthStore'

export default function ProtectedRoute({ children }) {
  const router = useRouter()
  const { user, token } = useAuthStore()

  useEffect(() => {
    if (!token || !user) {
      router.push('/login')
    }
  }, [token, user, router])

  if (!token || !user) {
    return <div>Loading...</div>
  }

  return children
}
```

### Login Flow
```javascript
"use client"

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import useAuthStore from '@/stores/useAuthStore'
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"

export default function LoginForm() {
  const router = useRouter()
  const { login, isLoading } = useAuthStore()
  const [credentials, setCredentials] = useState({ email: '', password: '' })
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      await login(credentials.email, credentials.password)
      router.push('/dashboard')
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <Input
        type="email"
        placeholder="Email"
        value={credentials.email}
        onChange={(e) => setCredentials({...credentials, email: e.target.value})}
      />
      <Input
        type="password"
        placeholder="Password"
        value={credentials.password}
        onChange={(e) => setCredentials({...credentials, password: e.target.value})}
      />
      {error && <p className="text-red-600 text-sm">{error}</p>}
      <Button type="submit" disabled={isLoading}>
        {isLoading ? 'Logging in...' : 'Login'}
      </Button>
    </form>
  )
}
```

---

## API Integration

### Axios Setup (lib/api.js)
```javascript
import axios from 'axios'

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  headers: {
    'Content-Type': 'application/json'
  },
  withCredentials: true
})

// Request interceptor
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api
```

### API Hook (hooks/useApi.js)
```javascript
import { useState, useEffect } from 'react'
import api from '@/lib/api'

export function useApi(url, options = {}) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await api.get(url, options)
        setData(response.data)
      } catch (err) {
        setError(err)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [url])

  return { data, loading, error }
}

// Usage
export default function Analytics() {
  const { data, loading } = useApi('/api/predictions/analytics/?days=30')
  
  if (loading) return <div>Loading...</div>
  
  return <div>{data?.overview?.total_predictions} predictions</div>
}
```

---

## Styling & Themes

### Tailwind Configuration (tailwind.config.js)
```javascript
export default {
  content: [
    "./app/**/*.{js,jsx}",
    "./components/**/*.{js,jsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: 'hsl(var(--primary))',
        destructive: 'hsl(var(--destructive))',
      },
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)',
      },
    },
  },
  plugins: [],
}
```

### CSS Variables (styles/globals.css)
```css
:root {
  --background: 0 0% 100%;
  --foreground: 222.2 84% 4.9%;
  --primary: 222.2 47.6% 11.2%;
  --primary-foreground: 210 40% 98%;
  --destructive: 0 84.2% 60.2%;
}

@media (prefers-color-scheme: dark) {
  :root {
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;
    --primary: 210 40% 98%;
    --primary-foreground: 222.2 47.6% 11.2%;
  }
}
```

### Theme Provider (layout.jsx)
```javascript
import { ThemeProvider } from "next-themes"

export default function RootLayout({ children }) {
  return (
    <html suppressHydrationWarning>
      <body>
        <ThemeProvider attribute="class" defaultTheme="system">
          {children}
        </ThemeProvider>
      </body>
    </html>
  )
}
```

---

## Development Workflow

### Code Quality

```bash
# Lint code
npm run lint

# Format code with Biome
npm run format

# Type check (if using TypeScript)
npm run type-check
```

### Build Process

```bash
# Development (with hot reload)
npm run dev

# Production build
npm run build

# Start production server
npm start

# Analyze bundle
npm run build --analyze
```

### Git Workflow

1. Create feature branch
   ```bash
   git checkout -b feature/new-feature
   ```

2. Make changes and format
   ```bash
   npm run format
   npm run lint
   ```

3. Commit changes
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

4. Push and create PR
   ```bash
   git push origin feature/new-feature
   ```

---

## Performance Optimization

### 1. Code Splitting
Next.js automatically code-splits routes.

### 2. Image Optimization
```javascript
import Image from 'next/image'

<Image
  src="/hero.jpg"
  alt="Hero"
  width={1200}
  height={600}
  priority
/>
```

### 3. Dynamic Imports
```javascript
import dynamic from 'next/dynamic'

const HeavyComponent = dynamic(() => import('./HeavyComponent'), {
  loading: () => <p>Loading...</p>
})
```

### 4. Route Prefetching
```javascript
import { useRouter } from 'next/navigation'

const router = useRouter()
// Prefetch on hover
<button onMouseEnter={() => router.prefetch('/dashboard')}>
  Dashboard
</button>
```

---

## Best Practices

1. **Use Server Components** by default
2. **Minimize Client Components** - only use "use client" when needed
3. **Keep Components Small** - easier to test and maintain
4. **Use TypeScript/JSDoc** - better IDE support
5. **Optimize Images** - use Next.js Image component
6. **Implement Error Boundaries** - catch React errors
7. **Use Suspense** - for async data loading
8. **Responsive Design** - mobile-first approach
9. **Accessibility** - ARIA labels, keyboard navigation
10. **Security** - validate inputs, use HTTPS

---

## Deployment

### Environment Variables (.env.production)
```bash
NEXT_PUBLIC_API_URL=https://api.example.com
```

### Build & Deploy
```bash
# Build
npm run build

# Deploy to Vercel (easiest)
vercel

# Or manually
npm start
```

### Performance Monitoring
- Use Next.js Analytics
- Monitor Core Web Vitals
- Use Vercel Speed Insights

---

**Last Updated**: November 2024  
**Version**: 1.0.0
