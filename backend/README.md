# AI Email Outreach Backend

A production-ready backend for AI-powered email outreach campaigns.

## Features

- **Campaign Management**: Create, launch, pause, resume, and duplicate campaigns
- **Lead Management**: Import leads via CSV, copy between campaigns
- **AI Email Generation**: Generate personalized email templates using OpenAI
- **Email Delivery**: Send real emails via Postmark with tracking
- **Follow-up Scheduling**: Automatic follow-up emails with configurable delays
- **Reply Detection**: Automatically stop follow-ups when replies are detected
- **Magic Link Auth**: Passwordless authentication via email

## Tech Stack

- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL with SQLModel/SQLAlchemy
- **AI**: OpenAI via LangChain
- **Email**: Postmark (sending + inbound webhooks)
- **Auth**: JWT-based magic link authentication

## Quick Start

### 1. Prerequisites

- Python 3.11+
- PostgreSQL database
- Postmark account
- OpenAI API key

### 2. Setup

```bash
# Clone and navigate to backend
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your credentials
```

### 3. Configure Environment Variables

Edit `.env` with your actual values:

```env
# Database
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/outreach_db

# Authentication
SECRET_KEY=your-secret-key-generate-with-openssl-rand-hex-32

# OpenAI
OPENAI_API_KEY=sk-your-openai-api-key

# Postmark
POSTMARK_SERVER_TOKEN=your-postmark-server-token
POSTMARK_INBOUND_ADDRESS=reply@yourdomain.com
FROM_EMAIL=notifications@yourdomain.com

# App URLs
APP_BASE_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000

# Webhook Security
WEBHOOK_USERNAME=webhook_user
WEBHOOK_PASSWORD=webhook_secret_password
```

### 4. Database Setup

```bash
# Create PostgreSQL database
createdb outreach_db

# Run migrations
alembic upgrade head
```

### 5. Run the Server

```bash
# Development
uvicorn app.main:app --reload

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

- API docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

## API Endpoints

### Authentication
- `POST /api/auth/magic-link` - Request magic link email
- `POST /api/auth/verify` - Verify magic link, get access token
- `GET /api/auth/me` - Get current user

### Campaigns
- `POST /api/campaigns` - Create campaign
- `GET /api/campaigns` - List campaigns
- `GET /api/campaigns/{id}` - Get campaign with stats
- `PATCH /api/campaigns/{id}` - Update campaign (DRAFT only)
- `POST /api/campaigns/{id}/launch` - Launch campaign
- `POST /api/campaigns/{id}/pause` - Pause campaign
- `POST /api/campaigns/{id}/resume` - Resume campaign
- `POST /api/campaigns/{id}/duplicate` - Duplicate campaign

### Leads
- `POST /api/campaigns/{id}/leads` - Create single lead
- `GET /api/campaigns/{id}/leads` - List leads
- `POST /api/campaigns/{id}/leads/import` - Import CSV
- `POST /api/campaigns/{id}/leads/copy` - Copy from another campaign

### Templates
- `POST /api/campaigns/{id}/templates` - Create template manually
- `GET /api/campaigns/{id}/templates` - List templates
- `PATCH /api/campaigns/{id}/templates/{id}` - Update template
- `POST /api/campaigns/{id}/templates/generate` - Generate with AI
- `POST /api/campaigns/{id}/templates/generate-all` - Generate all steps
- `POST /api/campaigns/{id}/templates/{id}/rewrite` - Rewrite with AI

### Webhooks (Postmark)
- `POST /api/webhooks/postmark/inbound` - Handle reply emails
- `POST /api/webhooks/postmark/bounce` - Handle bounces
- `POST /api/webhooks/postmark/delivery` - Handle deliveries

## Postmark Setup

### 1. Configure Sender

1. Log in to Postmark
2. Go to Sender Signatures
3. Add and verify your sending domain/email

### 2. Configure Inbound

1. Go to your Server > Inbound
2. Set up inbound processing
3. Configure webhook URL: `https://yourdomain.com/api/webhooks/postmark/inbound`
4. Add HTTP Basic Auth credentials (same as `WEBHOOK_USERNAME`/`WEBHOOK_PASSWORD`)

### 3. Configure Tracking Webhooks

1. Go to your Server > Webhooks
2. Add webhooks for:
   - Bounce: `https://yourdomain.com/api/webhooks/postmark/bounce`
   - Delivery: `https://yourdomain.com/api/webhooks/postmark/delivery`
3. Add HTTP Basic Auth to each

## Project Structure

```
backend/
├── app/
│   ├── api/
│   │   ├── dependencies.py    # Auth, DB session dependencies
│   │   └── routes/            # API route handlers
│   ├── core/
│   │   ├── config.py          # Settings from environment
│   │   ├── constants.py       # Application constants
│   │   └── prompts.py         # LLM prompts
│   ├── domain/
│   │   └── enums.py           # Status enums
│   ├── infrastructure/
│   │   ├── database.py        # DB engine and sessions
│   │   ├── postmark.py        # Postmark email client
│   │   └── llm.py             # LangChain/OpenAI client
│   ├── models/                # SQLModel database models
│   ├── services/              # Business logic
│   │   ├── auth_service.py
│   │   ├── campaign_service.py
│   │   ├── lead_service.py
│   │   ├── template_service.py
│   │   ├── job_service.py
│   │   └── worker.py          # Background job processor
│   └── main.py                # FastAPI app entry point
├── alembic/                   # Database migrations
├── .env.example
├── requirements.txt
└── README.md
```

## How It Works

### Campaign Workflow

1. **Create Campaign** (DRAFT status)
   - Define name, pitch, and tone
   
2. **Import Leads**
   - Upload CSV with email, first_name, company
   
3. **Generate Templates**
   - AI generates personalized email templates
   - Edit/rewrite as needed
   
4. **Launch Campaign**
   - Transitions to ACTIVE status
   - Creates email jobs for all leads
   
5. **Background Worker**
   - Polls every 60 seconds
   - Sends due emails via Postmark
   - Schedules follow-ups after successful sends
   
6. **Reply Detection**
   - Postmark webhook receives inbound emails
   - Lead marked as REPLIED
   - Future jobs automatically skipped

### Email Job States

- `PENDING` - Scheduled, waiting to send
- `SENT` - Successfully sent
- `FAILED` - All retry attempts exhausted
- `SKIPPED` - Lead replied or campaign paused

### Lead States

- `PENDING` - Not yet contacted
- `CONTACTED` - At least one email sent
- `REPLIED` - Reply detected (terminal)
- `FAILED` - All sends failed (terminal)

## Development

### Running Tests

```bash
pytest
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Deployment

### Environment Variables for Production

Ensure all `.env` variables are set in your deployment environment:

```bash
# Generate a secure secret key
openssl rand -hex 32
```

### Recommended PaaS

- **Render**: Easy deployment with managed PostgreSQL
- **Railway**: Similar to Render, good DX
- **Fly.io**: More control, global edge deployment

### Health Checks

Configure your PaaS to use `/health` endpoint for health checks.

## License

MIT
