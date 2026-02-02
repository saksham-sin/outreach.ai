# Outreach.AI

**AI-Powered Email Outreach Platform** – Automate personalized cold email campaigns at scale with intelligent follow-ups, reply detection, and seamless scheduling.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Project Structure](#project-structure)
- [API Documentation](#api-documentation)
- [Development Guide](#development-guide)
- [Deployment](#deployment)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

---

## 🎯 Overview

Outreach.AI is a production-ready SaaS platform for managing AI-powered email outreach campaigns. It combines intelligent email generation with automated scheduling, follow-up management, and reply detection to help teams scale their outreach efforts efficiently.

The platform features a modern React frontend with an intuitive campaign wizard, backed by a FastAPI backend that handles AI email generation, campaign orchestration, and email delivery through enterprise-grade providers (Postmark/Resend).

---

## ✨ Features

### Campaign Management
- **Campaign Wizard**: Step-by-step campaign creation with real-time preview
- **Multi-Campaign Support**: Manage multiple campaigns simultaneously
- **Campaign Actions**: Launch, pause, resume, duplicate campaigns
- **Campaign Analytics**: Track performance metrics and engagement

### Lead Management
- **CSV Import**: Bulk import leads with custom field mapping
- **Lead Enrichment**: Support for custom variables and personalization
- **Cross-Campaign Copy**: Transfer leads between campaigns
- **Lead Status Tracking**: Monitor email delivery and engagement status

### AI Email Generation
- **OpenAI Integration**: Generate personalized email templates using GPT models
- **Variable Substitution**: Dynamic content with `{{variable}}` syntax
- **Template Management**: Save and reuse email templates
- **Preview System**: Real-time preview with variable highlighting

### Email Delivery & Automation
- **Multi-Provider Support**: Postmark and Resend email providers
- **Automated Follow-ups**: Schedule follow-up emails with configurable delays
- **Smart Scheduling**: Respect timezone-aware delays between emails
- **Retry Logic**: Automatic retry for failed deliveries with exponential backoff

### Reply Detection & Management
- **Webhook Integration**: Real-time reply detection via Postmark/Resend webhooks
- **Auto-Stop Follow-ups**: Automatically halt sequences when replies are received
- **Reply Tracking**: Monitor conversation threads and engagement

### Authentication & Security
- **Magic Link Auth**: Passwordless authentication via email
- **JWT Tokens**: Secure API authentication with token refresh
- **Webhook Security**: HTTP Basic Auth for webhook endpoints
- **User Profiles**: Custom signature and company information

### Background Processing
- **Worker Service**: Dedicated background worker for email processing
- **Job Scheduling**: Queue-based job management with status tracking
- **Timezone Support**: Proper timezone handling for global campaigns
- **Rate Limiting**: Configurable sending limits and delays

---

## 🛠 Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL with SQLAlchemy & SQLModel ORM
- **Migrations**: Alembic for database version control
- **AI/LLM**: LangChain + OpenAI GPT-4
- **Email Providers**: Postmark (primary), Resend (alternative)
- **Authentication**: JWT with magic link authentication
- **Async**: AsyncIO for concurrent operations
- **HTTP Client**: HTTPX for async API calls

### Frontend
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite for fast development and optimized builds
- **Styling**: TailwindCSS for utility-first styling
- **Routing**: React Router v6 for SPA navigation
- **Rich Text**: TiptapEditor for email template editing
- **Code Editor**: CodeMirror for HTML editing
- **HTTP Client**: Axios for API communication
- **Notifications**: React Hot Toast for user feedback
- **CSV Parsing**: PapaParse for lead imports

### Infrastructure
- **Deployment**: Railway (cloud platform)
- **Database**: PostgreSQL (managed instance)
- **Environment**: Docker containerization support
- **Monitoring**: Structured logging with Python logging

---

## 🏗 Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Campaign   │  │     Lead     │  │   Template   │          │
│  │    Wizard    │  │  Management  │  │    Editor    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP/REST API
┌────────────────────────────▼────────────────────────────────────┐
│                      Backend (FastAPI)                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │     API      │  │   Services   │  │  Background  │          │
│  │    Routes    │  │   (Business  │  │    Worker    │          │
│  │              │  │     Logic)   │  │              │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│         │                  │                  │                  │
│         └──────────┬───────┴──────────────────┘                  │
│                    │                                             │
│  ┌─────────────────▼─────────────────┐                          │
│  │    Infrastructure Layer            │                          │
│  │  • Database (PostgreSQL)           │                          │
│  │  • Email Providers (Postmark)      │                          │
│  │  • LLM (OpenAI via LangChain)      │                          │
│  └────────────────────────────────────┘                          │
└─────────────────────────────────────────────────────────────────┘
                             │
                    ┌────────┴────────┐
                    │                 │
         ┌──────────▼────────┐  ┌────▼─────────┐
         │   Email Provider  │  │   OpenAI     │
         │  (Postmark/       │  │     API      │
         │   Resend)         │  │              │
         └───────────────────┘  └──────────────┘
```

### Database Schema

The application uses PostgreSQL with the following main entities:

- **Users**: User accounts with authentication and profile information
- **Campaigns**: Email campaigns with scheduling and status tracking
- **Leads**: Target recipients with custom fields
- **EmailTemplates**: Reusable email templates with AI-generated content
- **EmailJobs**: Scheduled email tasks with delivery tracking
- **CampaignTags**: Tags for organizing and categorizing campaigns

### Background Worker Flow

```
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│  Scheduler   │─────▶│  Job Queue   │─────▶│    Worker    │
│  (Campaign   │      │  (Pending    │      │  (Process &  │
│   Service)   │      │    Jobs)     │      │    Send)     │
└──────────────┘      └──────────────┘      └──────┬───────┘
                                                    │
                                            ┌───────▼───────┐
                                            │ Email Provider│
                                            │   (Postmark)  │
                                            └───────────────┘
```

---

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

### Required Software
- **Python**: 3.11 or higher
- **Node.js**: 18.x or higher
- **npm**: 9.x or higher (comes with Node.js)
- **PostgreSQL**: 15.x or higher
- **Git**: For version control

### Required API Keys & Services
- **OpenAI API Key**: For AI email generation ([Get API key](https://platform.openai.com/api-keys))
- **Postmark Account**: For email sending and webhooks ([Sign up](https://postmarkapp.com))
  - OR **Resend Account**: Alternative email provider ([Sign up](https://resend.com))
- **PostgreSQL Database**: Local or managed instance

### Optional Tools
- **Docker**: For containerized deployment
- **Railway CLI**: For deployment to Railway platform
- **pgAdmin**: PostgreSQL management GUI

---

## 📦 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/outreach.ai.git
cd outreach.ai
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
.\venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install
```

### 4. Database Setup

```bash
# Create PostgreSQL database
createdb outreach_db

# Or using psql:
psql -U postgres
CREATE DATABASE outreach_db;
\q
```

---

## ⚙️ Configuration

### Backend Environment Variables

Create a `.env` file in the `backend/` directory:

```env
# ===== Database Configuration =====
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/outreach_db

# ===== Authentication =====
SECRET_KEY=your-super-secret-key-generate-with-openssl-rand-hex-32
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# ===== OpenAI Configuration =====
OPENAI_API_KEY=sk-your-openai-api-key-here

# ===== Email Provider Configuration =====
# Choose: "postmark" or "resend"
EMAIL_PROVIDER=postmark

# Postmark Settings (if using Postmark)
POSTMARK_SERVER_TOKEN=your-postmark-server-token
POSTMARK_INBOUND_ADDRESS=reply@inbound.yourdomain.com
FROM_EMAIL=campaigns@yourdomain.com
FROM_NAME=Your Company Name

# Resend Settings (if using Resend)
RESEND_API_KEY=re_your-resend-api-key
RESEND_FROM_DOMAIN=yourdomain.com

# ===== Application URLs =====
APP_BASE_URL=http://localhost:8000
FRONTEND_URL=http://localhost:5173

# ===== Webhook Security =====
WEBHOOK_USERNAME=webhook_user
WEBHOOK_PASSWORD=generate-strong-password-here

# ===== Worker Configuration =====
WORKER_POLL_INTERVAL_SECONDS=10
WORKER_BATCH_SIZE=10
WORKER_MAX_RETRIES=3
WORKER_RETRY_DELAY_SECONDS=60

# ===== Logging =====
LOG_LEVEL=INFO
```

### Generate Secret Key

```bash
# Generate a secure random secret key
python -c "import secrets; print(secrets.token_hex(32))"
```

### Frontend Environment Variables

Create a `.env` file in the `frontend/` directory:

```env
VITE_API_URL=http://localhost:8000
```

### Database Migrations

Run migrations to set up the database schema:

```bash
cd backend

# Run all pending migrations
alembic upgrade head

# Check migration status
alembic current

# View migration history
alembic history --verbose
```

---

## 🚀 Running the Application

### Development Mode

#### 1. Start the Backend API

```bash
cd backend

# Activate virtual environment
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux

# Run the FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`  
API documentation: `http://localhost:8000/docs`

#### 2. Start the Background Worker

Open a new terminal:

```bash
cd backend

# Activate virtual environment
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux

# Run the worker
python -m app.services.worker
```

The worker processes scheduled email jobs in the background.

#### 3. Start the Frontend

Open a new terminal:

```bash
cd frontend

# Start development server
npm run dev
```

The frontend will be available at `http://localhost:5173`

### Production Mode

#### Backend

```bash
cd backend

# Run with Gunicorn (recommended for production)
gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

#### Frontend

```bash
cd frontend

# Build for production
npm run build

# Preview production build
npm run preview

# Or serve with a static file server
npx serve -s dist -l 3000
```

---

## 📁 Project Structure

```
outreach.ai/
├── backend/                        # FastAPI backend
│   ├── alembic/                    # Database migrations
│   │   ├── versions/               # Migration scripts
│   │   │   ├── 001_initial.py
│   │   │   ├── 002_timezone_support.py
│   │   │   ├── 003_add_composite_indexes.py
│   │   │   ├── 004_add_delay_minutes.py
│   │   │   └── 7dba13c5edeb_add_user_profile.py
│   │   └── env.py                  # Alembic environment config
│   ├── app/
│   │   ├── api/                    # API layer
│   │   │   ├── routes/             # API route handlers
│   │   │   │   ├── auth.py         # Authentication endpoints
│   │   │   │   ├── campaigns.py    # Campaign management
│   │   │   │   ├── leads.py        # Lead management
│   │   │   │   ├── templates.py    # Template management
│   │   │   │   ├── jobs.py         # Job status endpoints
│   │   │   │   └── webhooks.py     # Email webhooks
│   │   │   └── dependencies.py     # Dependency injection
│   │   ├── core/                   # Core configuration
│   │   │   ├── config.py           # Settings & environment
│   │   │   ├── constants.py        # Application constants
│   │   │   └── prompts.py          # AI prompt templates
│   │   ├── domain/                 # Domain logic
│   │   │   └── enums.py            # Enumerations
│   │   ├── infrastructure/         # Infrastructure layer
│   │   │   ├── database.py         # Database connection
│   │   │   ├── email_factory.py    # Email provider factory
│   │   │   ├── email_provider.py   # Email provider interface
│   │   │   ├── postmark_provider.py # Postmark implementation
│   │   │   ├── resend_provider.py  # Resend implementation
│   │   │   └── llm.py              # OpenAI/LangChain
│   │   ├── models/                 # Database models
│   │   │   ├── base.py             # Base model classes
│   │   │   ├── user.py             # User model
│   │   │   ├── campaign.py         # Campaign model
│   │   │   ├── lead.py             # Lead model
│   │   │   ├── email_template.py   # Template model
│   │   │   ├── email_job.py        # Email job model
│   │   │   └── campaign_tag.py     # Tag model
│   │   ├── services/               # Business logic
│   │   │   ├── auth_service.py     # Authentication logic
│   │   │   ├── campaign_service.py # Campaign orchestration
│   │   │   ├── lead_service.py     # Lead management
│   │   │   ├── template_service.py # Template operations
│   │   │   ├── job_service.py      # Job processing
│   │   │   └── worker.py           # Background worker
│   │   └── main.py                 # Application entry point
│   ├── requirements.txt            # Python dependencies
│   ├── alembic.ini                 # Alembic configuration
│   ├── README.md                   # Backend documentation
│   ├── TESTING_GUIDE.md            # Testing documentation
│   ├── test_reliability_fixes.py   # Test suite
│   └── validate_fixes.py           # Validation script
├── frontend/                       # React frontend
│   ├── src/
│   │   ├── api/                    # API client
│   │   │   ├── client.ts           # Axios client config
│   │   │   ├── authApi.ts          # Auth API calls
│   │   │   ├── campaignsApi.ts     # Campaign API
│   │   │   ├── leadsApi.ts         # Lead API
│   │   │   ├── templatesApi.ts     # Template API
│   │   │   └── jobsApi.ts          # Job API
│   │   ├── auth/                   # Authentication
│   │   │   ├── AuthContext.tsx     # Auth state management
│   │   │   └── ProtectedRoute.tsx  # Route protection
│   │   ├── campaigns/              # Campaign wizard
│   │   │   ├── CampaignWizard.tsx  # Main wizard component
│   │   │   ├── CampaignWizardContext.tsx # Wizard state
│   │   │   ├── WizardStep1.tsx     # Basic info
│   │   │   ├── WizardStep2.tsx     # Lead import
│   │   │   ├── WizardStep3.tsx     # Template creation
│   │   │   ├── WizardStep4.tsx     # Follow-up config
│   │   │   └── WizardStep5.tsx     # Review & launch
│   │   ├── components/             # Reusable components
│   │   │   ├── Button.tsx          # Button component
│   │   │   ├── Input.tsx           # Input field
│   │   │   ├── Select.tsx          # Dropdown select
│   │   │   ├── Modal.tsx           # Modal dialog
│   │   │   ├── Spinner.tsx         # Loading spinner
│   │   │   ├── StatusBadge.tsx     # Status indicator
│   │   │   ├── RichTextEditor.tsx  # Tiptap editor
│   │   │   ├── HtmlEditor.tsx      # CodeMirror editor
│   │   │   ├── EmailPreviewModal.tsx # Email preview
│   │   │   ├── TagInput.tsx        # Tag input field
│   │   │   └── Header.tsx          # App header
│   │   ├── pages/                  # Page components
│   │   ├── hooks/                  # Custom React hooks
│   │   ├── types/                  # TypeScript types
│   │   ├── App.tsx                 # Root component
│   │   ├── main.tsx                # App entry point
│   │   └── index.css               # Global styles
│   ├── package.json                # Node dependencies
│   ├── vite.config.ts              # Vite configuration
│   ├── tsconfig.json               # TypeScript config
│   ├── tailwind.config.js          # Tailwind config
│   ├── postcss.config.js           # PostCSS config
│   └── index.html                  # HTML template
├── sample_leads.csv                # Sample lead data
├── railway-docs.txt                # Railway deployment docs
└── README.md                       # This file
```

---

## 📚 API Documentation

### Interactive API Docs

Once the backend is running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Key API Endpoints

#### Authentication
```
POST   /api/auth/request-magic-link    # Request magic link
POST   /api/auth/verify-magic-link     # Verify magic link
GET    /api/auth/me                    # Get current user
PUT    /api/auth/me                    # Update user profile
```

#### Campaigns
```
GET    /api/campaigns                  # List campaigns
POST   /api/campaigns                  # Create campaign
GET    /api/campaigns/{id}             # Get campaign details
PUT    /api/campaigns/{id}             # Update campaign
DELETE /api/campaigns/{id}             # Delete campaign
POST   /api/campaigns/{id}/launch      # Launch campaign
POST   /api/campaigns/{id}/pause       # Pause campaign
POST   /api/campaigns/{id}/resume      # Resume campaign
POST   /api/campaigns/{id}/duplicate   # Duplicate campaign
```

#### Leads
```
GET    /api/campaigns/{id}/leads       # List campaign leads
POST   /api/campaigns/{id}/leads       # Add lead to campaign
POST   /api/campaigns/{id}/leads/import # Import leads from CSV
PUT    /api/leads/{id}                 # Update lead
DELETE /api/leads/{id}                 # Delete lead
POST   /api/leads/copy                 # Copy leads between campaigns
```

#### Templates
```
GET    /api/templates                  # List templates
POST   /api/templates                  # Create template
POST   /api/templates/generate         # Generate template with AI
GET    /api/templates/{id}             # Get template
PUT    /api/templates/{id}             # Update template
DELETE /api/templates/{id}             # Delete template
```

#### Email Jobs
```
GET    /api/campaigns/{id}/jobs        # List campaign jobs
GET    /api/jobs/{id}                  # Get job details
```

#### Webhooks
```
POST   /api/webhooks/postmark/inbound  # Postmark inbound webhook
POST   /api/webhooks/resend/inbound    # Resend inbound webhook
```

---

## 👨‍💻 Development Guide

### Creating Database Migrations

```bash
# Create a new migration
alembic revision -m "description of change"

# Auto-generate migration from model changes
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Rollback to specific version
alembic downgrade <revision_id>
```

### Code Style & Linting

#### Backend (Python)
```bash
# Install development dependencies
pip install black flake8 mypy

# Format code
black app/

# Lint code
flake8 app/

# Type checking
mypy app/
```

#### Frontend (TypeScript)
```bash
# Lint code
npm run lint

# Type checking
npx tsc --noEmit
```

### Environment Variables Best Practices

1. **Never commit `.env` files** to version control
2. **Use `.env.example`** as a template for required variables
3. **Rotate secrets regularly** in production environments
4. **Use different values** for development and production
5. **Document all variables** with clear descriptions

### API Design Principles

- **RESTful conventions**: Use proper HTTP methods and status codes
- **Consistent naming**: Use snake_case for Python, camelCase for TypeScript
- **Error handling**: Return structured error responses with details
- **Validation**: Use Pydantic models for request/response validation
- **Documentation**: Add docstrings and OpenAPI descriptions

### Database Best Practices

- **Use migrations** for all schema changes
- **Add indexes** for frequently queried columns
- **Use transactions** for multi-step operations
- **Soft deletes** for important data (when applicable)
- **Composite indexes** for multi-column queries

---

## 🚢 Deployment

### Railway Deployment

Railway is the recommended platform for deploying Outreach.AI. See `railway-docs.txt` for complete documentation.

#### Quick Deploy to Railway

1. **Install Railway CLI**:
```bash
npm install -g @railway/cli
```

2. **Login to Railway**:
```bash
railway login
```

3. **Initialize Project**:
```bash
railway init
```

4. **Add PostgreSQL**:
```bash
railway add postgresql
```

5. **Set Environment Variables**:
```bash
railway variables set OPENAI_API_KEY=sk-...
railway variables set POSTMARK_SERVER_TOKEN=...
railway variables set SECRET_KEY=...
# ... set all other variables
```

6. **Deploy**:
```bash
railway up
```

#### Railway Configuration Files

Create a `railway.toml` in the project root:

```toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "uvicorn app.main:app --host 0.0.0.0 --port $PORT"
healthcheckPath = "/health"
healthcheckTimeout = 30
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10
```

### Docker Deployment

#### Backend Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Frontend Dockerfile

```dockerfile
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

#### Docker Compose

```yaml
version: '3.8'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: outreach_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  backend:
    build: ./backend
    environment:
      DATABASE_URL: postgresql+asyncpg://postgres:postgres@db:5432/outreach_db
    env_file:
      - ./backend/.env
    ports:
      - "8000:8000"
    depends_on:
      - db

  worker:
    build: ./backend
    command: python -m app.services.worker
    environment:
      DATABASE_URL: postgresql+asyncpg://postgres:postgres@db:5432/outreach_db
    env_file:
      - ./backend/.env
    depends_on:
      - db

  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend

volumes:
  postgres_data:
```

Run with: `docker-compose up -d`

### Production Checklist

- [ ] Set strong `SECRET_KEY` and `WEBHOOK_PASSWORD`
- [ ] Use managed PostgreSQL database
- [ ] Configure proper CORS origins
- [ ] Set up SSL/TLS certificates
- [ ] Configure email provider DNS records (SPF, DKIM, DMARC)
- [ ] Set up monitoring and logging
- [ ] Configure backup strategy for database
- [ ] Set up rate limiting on API endpoints
- [ ] Review and adjust worker configuration
- [ ] Test webhook endpoints with real providers
- [ ] Configure production-grade logging
- [ ] Set up error tracking (Sentry, etc.)

---

## 🧪 Testing

### Backend Tests

```bash
cd backend

# Run all tests
python -m pytest

# Run specific test file
python -m pytest test_reliability_fixes.py

# Run with coverage
python -m pytest --cov=app --cov-report=html

# Run validation script
python validate_fixes.py
```

### Frontend Tests

```bash
cd frontend

# Run tests (if configured)
npm test

# Type checking
npx tsc --noEmit
```

### Manual Testing

1. **Authentication Flow**:
   - Request magic link
   - Check email inbox
   - Click magic link
   - Verify authentication

2. **Campaign Creation**:
   - Create new campaign through wizard
   - Import leads from CSV
   - Generate email template with AI
   - Configure follow-up schedule
   - Launch campaign

3. **Email Delivery**:
   - Verify emails are sent
   - Check email provider dashboard
   - Test reply detection webhook
   - Verify follow-up scheduling

4. **Worker Processing**:
   - Monitor worker logs
   - Verify job status updates
   - Test retry logic
   - Check error handling

### Testing Guide

See `backend/TESTING_GUIDE.md` for comprehensive testing documentation including:
- Test scenarios
- Expected behaviors
- Timezone testing
- Error handling validation
- Worker testing procedures

---

## 🔧 Troubleshooting

### Common Issues

#### Database Connection Errors

**Problem**: `Could not connect to database`

**Solutions**:
```bash
# Check PostgreSQL is running
# Windows:
Get-Service postgresql*

# macOS:
brew services list

# Linux:
systemctl status postgresql

# Verify DATABASE_URL format
# Correct: postgresql+asyncpg://user:pass@host:5432/dbname
```

#### Email Provider Errors

**Problem**: `Email sending failed`

**Solutions**:
- Verify API keys are correct
- Check email provider dashboard for quota limits
- Ensure FROM_EMAIL domain is verified
- Review webhook endpoint accessibility

#### Worker Not Processing Jobs

**Problem**: Worker running but jobs stuck in pending

**Solutions**:
```bash
# Check worker logs for errors
python -m app.services.worker

# Verify database connection in worker
# Check WORKER_POLL_INTERVAL_SECONDS setting
# Ensure no conflicting worker instances
```

#### Migration Issues

**Problem**: `Migration conflicts or failures`

**Solutions**:
```bash
# Check current migration state
alembic current

# View migration history
alembic history

# Stamp database to specific revision (be careful!)
alembic stamp head

# Rollback and reapply
alembic downgrade -1
alembic upgrade head
```

#### CORS Errors in Frontend

**Problem**: `CORS policy blocking requests`

**Solutions**:
- Verify `FRONTEND_URL` in backend `.env`
- Check CORS middleware configuration in `main.py`
- Ensure frontend is accessing correct API URL

#### OpenAI Rate Limits

**Problem**: `OpenAI API rate limit exceeded`

**Solutions**:
- Upgrade OpenAI plan for higher limits
- Implement request throttling
- Cache generated templates
- Use batch processing for template generation

### Debug Mode

Enable debug logging:

```env
# Backend .env
LOG_LEVEL=DEBUG
```

View detailed logs:
```bash
# Backend
uvicorn app.main:app --reload --log-level debug

# Worker
python -m app.services.worker  # Check console output
```

### Health Check Endpoints

```bash
# API health check
curl http://localhost:8000/health

# Database connection check
curl http://localhost:8000/api/health/db
```

---

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

### Development Workflow

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/your-feature-name`
3. **Make your changes** with clear commit messages
4. **Write/update tests** for your changes
5. **Run tests** and ensure they pass
6. **Update documentation** if needed
7. **Submit a pull request** with detailed description

### Code Review Process

- All PRs require review before merging
- Address review comments promptly
- Keep PRs focused and reasonably sized
- Ensure CI/CD checks pass

### Commit Message Guidelines

```
type(scope): brief description

Detailed explanation of changes if needed.

Fixes #123
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

### Branch Naming

- Features: `feature/description`
- Bugs: `fix/description`
- Docs: `docs/description`
- Refactor: `refactor/description`

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 📞 Support

### Documentation
- **Backend**: See `backend/README.md`
- **Testing**: See `backend/TESTING_GUIDE.md`
- **Railway**: See `railway-docs.txt`

### Getting Help
- **Issues**: Open an issue on GitHub
- **Discussions**: Join GitHub discussions
- **Email**: support@outreach.ai (if applicable)

### Resources
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [Postmark API](https://postmarkapp.com/developer)
- [OpenAI API](https://platform.openai.com/docs)
- [Railway Documentation](https://docs.railway.com/)

---

## 🙏 Acknowledgments

- **FastAPI** for the excellent Python web framework
- **React** and **Vite** for modern frontend development
- **OpenAI** for powerful language models
- **Postmark** for reliable email delivery
- **Railway** for seamless cloud deployment
- The open-source community for amazing tools and libraries

---

## 🗺️ Roadmap

### Upcoming Features
- [ ] Email analytics dashboard with open/click tracking
- [ ] A/B testing for email templates
- [ ] Advanced segmentation and filtering
- [ ] Calendar integration for send time optimization
- [ ] Multi-user team support with role-based access
- [ ] Email warm-up sequences
- [ ] Integration with CRM platforms
- [ ] Custom domain support for email sending
- [ ] Mobile app (React Native)
- [ ] Advanced AI features (sentiment analysis, response suggestions)

### Known Issues
- See GitHub Issues for current bugs and feature requests

---

**Built with ❤️ by the Outreach.AI team**

For the latest updates, visit our [GitHub repository](https://github.com/yourusername/outreach.ai).
