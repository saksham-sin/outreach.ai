# Railway Deployment Guide

## Overview
This project deploys 3 separate services on Railway:
1. **Backend API** - FastAPI application
2. **Worker** - Background email job processor
3. **Frontend** - React application
4. **Postgres** - Database (Railway template)

---

## Step-by-Step Deployment

### 1. Create New Railway Project
```bash
# Login to Railway
railway login

# Create new project
railway init
```

### 2. Add PostgreSQL Database
1. In Railway dashboard → Click **"+ New"**
2. Select **"Database"** → **"Add PostgreSQL"**
3. Wait for provisioning to complete
4. Note: Database will be automatically accessible via private network

### 3. Deploy Backend Service
1. In Railway dashboard → Click **"+ New"**
2. Select **"GitHub Repo"** → Choose your repository
3. Service will auto-detect and use root `Dockerfile`
4. **Configure Variables:**
   - Click on service → **"Variables"** tab
   - Click **"+ New Variable"**
   - Add each variable below:

   ```bash
   # Database - Use Reference
   DATABASE_URL=${{Postgres.DATABASE_URL}}
   
   # Auth
   SECRET_KEY=<generate-with: openssl rand -hex 32>
   ACCESS_TOKEN_EXPIRE_DAYS=7
   MAGIC_LINK_EXPIRE_MINUTES=15
   
   # OpenAI
   OPENAI_API_KEY=sk-...
   OPENAI_MODEL=gpt-4o-mini
   
   # Email Provider
   EMAIL_PROVIDER=resend
   EMAIL_FROM_ADDRESS=noreply@yourdomain.com
   EMAIL_FROM_NAME=Your App Name
   
   # Resend (if using)
   RESEND_API_KEY=re_...
   RESEND_FROM_DOMAIN=yourdomain.com
   
   # Postmark (if using)
   POSTMARK_SERVER_TOKEN=...
   POSTMARK_INBOUND_ADDRESS=...
   
   # URLs - Get these AFTER deployment
   APP_BASE_URL=https://<backend-service>.railway.app
   FRONTEND_URL=https://<frontend-service>.railway.app
   
   # Webhook Security
   WEBHOOK_USERNAME=webhook_user
   WEBHOOK_PASSWORD=<generate-random-password>
   
   # Worker Config
   WORKER_POLL_INTERVAL_SECONDS=5
   MAX_RETRY_ATTEMPTS=3
   REPLY_MODE=simulated
   ```

5. **Deploy Settings:**
   - Healthcheck Path: `/health`
   - Port: Auto-detected (Railway sets `PORT` env var)

6. Click **"Deploy"**

### 4. Deploy Worker Service
1. Click **"+ New"** → **"GitHub Repo"** → Same repository
2. Service will detect Dockerfile again
3. **Override Start Command:**
   - Go to **"Settings"** tab
   - Find **"Start Command"** or **"Custom Start Command"**
   - Enter:
     ```bash
     bash -c "cd /app/backend && python -m app.services.worker"
     ```

4. **Configure Variables:**
   - Click **"Variables"** → **"+ New Variable"**
   - **Copy ALL variables from Backend service** (they need the same config)
   - Or use **"Reference"** → Select Backend service → Select each variable

5. **Important:** No healthcheck needed (worker doesn't expose HTTP)

6. Click **"Deploy"**

### 5. Deploy Frontend Service
1. Click **"+ New"** → **"GitHub Repo"** → Same repository
2. **Set Root Directory:**
   - Go to **"Settings"** tab
   - Set **"Root Directory"** to: `frontend`
   
3. Railway will auto-detect Node.js and run:
   ```bash
   npm install
   npm run build
   npm run preview  # or use a static server
   ```

4. **Configure Variables:**
   - Click **"Variables"** → **"+ New Variable"**
   - Add:
     ```bash
     # Get backend URL from backend service settings
     VITE_API_BASE_URL=https://<backend-service>.railway.app/api
     VITE_POLL_INTERVAL_MS=30000
     VITE_MAX_FOLLOWUPS=3
     VITE_ENABLE_SIMULATED_REPLY=true
     ```

5. **Set Build Command** (if needed):
   - Settings → **"Build Command"**: `npm run build`
   - Settings → **"Start Command"**: `npm run preview`

6. Click **"Deploy"**

### 6. Update URLs (After All Services Deploy)
Once all services are deployed, you'll get their URLs:
- Backend: `https://<backend-name>.railway.app`
- Frontend: `https://<frontend-name>.railway.app`

**Update these environment variables:**

1. **Backend Service Variables:**
   - `APP_BASE_URL` → Backend URL
   - `FRONTEND_URL` → Frontend URL

2. **Frontend Service Variables:**
   - `VITE_API_BASE_URL` → Backend URL + `/api`

3. **Redeploy** both services after updating URLs

---

## Verify Deployment

### Check Backend
```bash
curl https://<backend-url>.railway.app/health
# Should return: {"status":"healthy"}
```

### Check Frontend
Open in browser: `https://<frontend-url>.railway.app`

### Check Logs
In Railway dashboard:
- Click each service
- View **"Deployments"** tab
- Click latest deployment to see logs

---

## Database Migrations

Migrations run automatically on backend startup via Dockerfile:
```dockerfile
CMD ["bash", "-c", "cd /app/backend && python -m alembic upgrade head && python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
```

To run migrations manually:
```bash
# From Railway CLI
railway run python -m alembic upgrade head
```

---

## Troubleshooting

### Backend won't start
- Check logs for database connection errors
- Verify `DATABASE_URL` references Postgres service correctly
- Check all required env vars are set

### Worker not processing jobs
- Check worker logs for errors
- Verify worker service is running (not crashed)
- Ensure `DATABASE_URL` is set correctly

### Frontend can't reach backend
- Check CORS settings in backend
- Verify `FRONTEND_URL` in backend matches frontend domain
- Check `VITE_API_BASE_URL` in frontend points to backend

### Database connection fails
- Ensure `DATABASE_URL` uses Railway reference: `${{Postgres.DATABASE_URL}}`
- Check Postgres service is running
- Verify services are in same project (for private networking)

---

## Cost Optimization

Railway free tier includes:
- $5 worth of usage per month
- After that, pay-as-you-go

**Tips:**
- Use 1 replica per service (default)
- Scale down/pause non-production services
- Monitor usage in Railway dashboard

---

## Environment Variables Reference

### Backend & Worker (Shared)
| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | Postgres connection | `${{Postgres.DATABASE_URL}}` |
| `SECRET_KEY` | JWT signing key | `openssl rand -hex 32` |
| `OPENAI_API_KEY` | OpenAI API key | `sk-...` |
| `EMAIL_PROVIDER` | Email service | `resend` or `postmark` |
| `RESEND_API_KEY` | Resend key | `re_...` |
| `APP_BASE_URL` | Backend URL | `https://api.railway.app` |
| `FRONTEND_URL` | Frontend URL | `https://app.railway.app` |

### Frontend Only
| Variable | Description | Example |
|----------|-------------|---------|
| `VITE_API_BASE_URL` | Backend API URL | `https://api.railway.app/api` |
| `VITE_POLL_INTERVAL_MS` | Poll frequency | `30000` |

---

## Next Steps

1. ✅ Deploy all 3 services
2. ✅ Configure environment variables
3. ✅ Update URLs after deployment
4. ✅ Test backend health endpoint
5. ✅ Test frontend loads
6. ✅ Create a campaign and verify worker processes it
7. 🔒 Set up custom domain (optional)
8. 📊 Monitor logs and metrics

---

## Support

- Railway Docs: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- Project Issues: https://github.com/yourusername/yourrepo/issues
