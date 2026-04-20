# HackFlow Deployment Guide

## Prerequisites

1. **Google Cloud Account** with billing enabled
2. **Supabase Project** created
3. **Google OAuth Credentials** (for Google sign-in)

---

## Step 1: Configure Supabase

1. Go to [Supabase Dashboard](https://supabase.com)
2. Create a new project
3. Note your:
   - `SUPABASE_URL` (Project URL)
   - `SUPABASE_KEY` (anon public key)
   - `SUPABASE_SERVICE_KEY` (service_role key, keep secret!)

---

## Step 2: Configure Google OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create OAuth credentials:
   - APIs & Services > Credentials
   - Create OAuth Client ID
   - Application type: Web application
   - Authorized redirect URIs:
     ```
     https://YOUR-CLOUD-RUN-URL.auth.google/callback
     ```
3. Note your:
   - `GOOGLE_CLIENT_ID`
   - `GOOGLE_CLIENT_SECRET`

---

## Step 3: Build and Deploy

### Option A: Using gcloud CLI

```bash
# Set your project
gcloud config set project YOUR-PROJECT-ID

# Build the image
gcloud builds submit --tag gcr.io/YOUR-PROJECT-ID/hackflow

# Deploy to Cloud Run
gcloud run deploy hackflow \
  --image gcr.io/YOUR-PROJECT-ID/hackflow \
  --platform managed \
  --region asia-south2 \
  --allow-unauthenticated \
  --service-account hackflow@YOUR-PROJECT-ID.iam.gserviceaccount.com

# Set environment variables
gcloud run services update hackflow \
  --update-env-vars "\
SUPABASE_URL=https://xxx.supabase.co,\
SUPABASE_KEY=xxx,\
SUPABASE_SERVICE_KEY=xxx,\
SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))'),\
GOOGLE_CLIENT_ID=xxx,\
GOOGLE_CLIENT_SECRET=xxx,\
GOOGLE_REDIRECT_URI=https://xxx.run.app/auth/google/callback,\
FLASK_ENV=production,\
SESSION_COOKIE_SECURE=true,\
SESSION_COOKIE_SAMESITE=None" \
  --region asia-south2
```

### Option B: Using Cloud Run UI

1. Go to [Cloud Run](https://console.cloud.google.com/run)
2. Click "Create Service"
3. Select your container image
4. Configure:
   - Region: asia-south2 (or your preferred)
   - Authentication: Allow unauthenticated
5. Set Environment Variables in the Container tab
6. Click Deploy

---

## Step 4: Verify Deployment

```bash
# Check health
curl https://YOUR-URL/health

# Check liveness
curl https://YOUR-URL/health/liveness
```

Expected response:
```json
{"status": "healthy", "service": "hackflow"}
```

---

## Environment Variables Summary

| Variable | Required | Description |
|----------|:--------:|-------------|
| `SUPABASE_URL` | Yes | Supabase project URL |
| `SUPABASE_KEY` | Yes | Supabase anon key |
| `SUPABASE_SERVICE_KEY` | Yes | Supabase service role key |
| `SECRET_KEY` | Yes | Flask secret (generate random) |
| `GOOGLE_CLIENT_ID` | No* | Google OAuth Client ID |
| `GOOGLE_CLIENT_SECRET` | No* | Google OAuth Secret |
| `GOOGLE_REDIRECT_URI` | No* | OAuth callback URL |
| `FLASK_ENV` | No | production |
| `PORT` | No | 8080 (Cloud Run) |
| `SESSION_COOKIE_SECURE` | No | true |
| `SESSION_COOKIE_SAMESITE` | No | None |
| `BCRYPT_LOG_ROUNDS` | No | 12 |
| `WTF_CSRF_ENABLED` | No | true |

* Required only if using Google OAuth

---

## Local Development

```bash
# Clone and setup
git clone https://github.com/TheMukeshDev/HackFlow.git
cd HackFlow

# Create .env from example
cp .env.example .env

# Edit .env with your values
nano .env

# Run locally
python run.py
```

---

## Troubleshooting

### Container fails to start
- Check environment variables are set correctly
- Check logs: `gcloud logs read --service hackflow`

### Health check fails
- Verify Supabase is accessible from Cloud Run
- Check firewall rules

### Session issues
- Ensure `SESSION_COOKIE_SECURE=true` in production
- Ensure `SESSION_COOKIE_SAMESITE=None` for cross-domain

---

## Security Checklist

- [ ] Use strong SECRET_KEY (32+ hex characters)
- [ ] Enable SESSION_COOKIE_SECURE=true
- [ ] Enable WTF_CSRF_ENABLED=true
- [ ] Use SESSION_COOKIE_SAMESITE=None
- [ ] Don't commit .env to Git
- [ ] Rotate keys periodically