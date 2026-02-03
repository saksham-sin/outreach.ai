# Outreach.AI

AI-powered email outreach platform that automates personalized cold email campaigns with intelligent scheduling, follow-ups, and reply detection.

## What is Outreach.AI?

Outreach.AI helps you run email campaigns at scale. Create campaigns, upload leads, generate AI-powered emails, and let the system automatically send emails and manage follow-ups. The platform detects replies automatically and stops follow-ups when prospects respond.

## Features

- ✅ **Campaign Builder** - Create email campaigns with a simple wizard
- ✅ **Lead Management** - Import leads from CSV, manage lists
- ✅ **AI Email Generation** - Generate personalized emails using OpenAI GPT
- ✅ **Automated Scheduling** - Schedule emails with automatic follow-ups
- ✅ **Reply Detection** - Automatically detect and stop follow-ups when replies arrive
- ✅ **Email Delivery** - Send via Resend
- ✅ **Magic Link Auth** - Passwordless authentication
- ✅ **Email Timeline** - View email history for each lead

## Quick Start

### Prerequisites

- **Python** 3.11+
- **Node.js** 18+
- **PostgreSQL** 15+
- **OpenAI API Key** (for AI email generation)
- **Resend** account (for email sending)

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your API keys and database URL

# Run database migrations
alembic upgrade head

# Start the API server
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`  
Swagger docs: `http://localhost:8000/docs`

### 2. Background Worker (new terminal)

```bash
cd backend
source venv/bin/activate  # or .\venv\Scripts\activate on Windows

# Run the background worker for email processing
python -m app.services.worker
```

### 3. Frontend Setup (new terminal)

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at `http://localhost:5173`

### 4. Database Setup

Create a PostgreSQL database:

```bash
createdb outreach_ai
```

Or using Railway:

```bash
npm install -g @railway/cli
railway login
railway init
railway up
```

---

## How to Use

### 1. Create Account
- Go to `http://localhost:5173`
- Enter your email and click "Send Magic Link"
- Check your email and click the link to sign in

### 2. Create Campaign
- Click "New Campaign" in the dashboard
- Follow the wizard:
  1. **Campaign Details** - Name, description, email subject
  2. **Upload Leads** - Import CSV with lead information
  3. **Create Template** - Write email body or generate with AI
  4. **Configure Follow-ups** - Set delays and follow-up sequences
  5. **Review & Launch** - Verify and launch the campaign

### 3. Monitor Campaign
- View campaign status on the dashboard
- Check email delivery status
- Monitor replies and engagement
- View email timeline for each lead

---

## Environment Variables

Create `.env` file in `backend/` directory with these variables:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/outreach_ai

# Security
SECRET_KEY=your-secret-key-here

# OpenAI
OPENAI_API_KEY=sk-your-key-here

# Email (Resend)
RESEND_API_KEY=re_your_key_here
RESEND_FROM_DOMAIN=example.com

# Dual Sender Configuration
EMAIL_AUTH_FROM_ADDRESS=no-reply@example.com
EMAIL_AUTH_FROM_NAME=Your App Name
EMAIL_OUTREACH_FROM_ADDRESS=hello@example.com
EMAIL_OUTREACH_FROM_NAME=Your App Name
EMAIL_OUTREACH_REPLY_TO=hello@example.com

# URLs
APP_BASE_URL=http://localhost:8000
FRONTEND_URL=http://localhost:5173

# Frontend
VITE_BACKEND_HOST=http://localhost:8000
```

See `.env.example` for all available options.
