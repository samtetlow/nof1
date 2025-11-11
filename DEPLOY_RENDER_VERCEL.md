# 🚀 Deploy to Render + Vercel - Complete Guide

## Overview
- **Backend (Python/FastAPI)** → Render.com
- **Frontend (React)** → Vercel.com

---

## PART 1: Deploy Backend to Render

### Step 1: Prepare Git Repository

**Before deploying, you need your code in a Git repository:**

```bash
# Navigate to project
cd /Users/samtetlow/Cursor/nof1

# Check git status
git status

# If not initialized, initialize git
git init

# Add all files
git add .

# Commit
git commit -m "Prepare for Render and Vercel deployment"

# Create GitHub repo and push (if not already done)
# Go to github.com, create new repo "nof1"
# Then:
git remote add origin https://github.com/YOUR_USERNAME/nof1.git
git branch -M main
git push -u origin main
```

### Step 2: Create Render Service

1. **Go to Render Dashboard:**
   - Visit: https://dashboard.render.com/
   - Click **"New +"** → **"Web Service"**

2. **Connect Repository:**
   - Click **"Connect GitHub"** (or use existing connection)
   - Select your **nof1** repository

3. **Configure Service:**

   ```
   Name: nof1-backend
   Region: Oregon (US West) or closest to you
   Branch: main
   Root Directory: (leave blank - use root)
   Runtime: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: uvicorn app:app --host 0.0.0.0 --port $PORT --timeout-keep-alive 600
   ```

4. **Select Plan:**
   - **Free** (for testing)
   - Or **Starter ($7/month)** (for production - more reliable)

### Step 3: Add Environment Variables

In Render dashboard, scroll down to **"Environment Variables"** and add:

```
OPENAI_API_KEY=your_openai_key_here
DATABASE_URL=sqlite:///./nof1.db
```

**Optional (if you have them):**
```
ANTHROPIC_API_KEY=your_anthropic_key
GOOGLE_API_KEY=your_google_key
PITCHBOOK_API_KEY=your_pitchbook_key
HUBSPOT_API_KEY=your_hubspot_key
```

### Step 4: Deploy Backend

1. Click **"Create Web Service"**
2. Wait 5-10 minutes for deployment
3. Once deployed, you'll get a URL like:
   ```
   https://nof1-backend.onrender.com
   ```
4. **SAVE THIS URL** - you'll need it for Vercel!

### Step 5: Test Backend

Visit these URLs to test:
```
https://nof1-backend.onrender.com/health
https://nof1-backend.onrender.com/docs
```

You should see:
- `/health` → `{"status":"ok",...}`
- `/docs` → Interactive API documentation

---

## PART 2: Deploy Frontend to Vercel

### Step 1: Update Frontend Configuration

The frontend needs to know your new Render backend URL.

**Update `frontend/vercel.json`:**

Replace the Railway URL with your new Render URL:

```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "build",
  "framework": "create-react-app",
  "env": {
    "REACT_APP_API_URL": "https://nof1-backend.onrender.com"
  }
}
```

**Commit this change:**
```bash
cd /Users/samtetlow/Cursor/nof1
git add frontend/vercel.json
git commit -m "Update API URL for Render backend"
git push
```

### Step 2: Create Vercel Project

1. **Go to Vercel:**
   - Visit: https://vercel.com/new
   - Sign up if you haven't already

2. **Import Repository:**
   - Click **"Import Git Repository"**
   - Connect to GitHub
   - Select your **nof1** repository

3. **Configure Project:**

   ```
   Framework Preset: Create React App
   Root Directory: frontend
   Build Command: npm run build
   Output Directory: build
   Install Command: npm install
   ```

4. **Add Environment Variable:**

   Click **"Environment Variables"** section:
   
   **Name:** `REACT_APP_API_URL`
   
   **Value:** `https://nof1-backend.onrender.com` (YOUR RENDER URL)
   
   **Environments:** ✓ Production ✓ Preview ✓ Development

### Step 3: Deploy Frontend

1. Click **"Deploy"**
2. Wait 2-3 minutes
3. You'll get a URL like:
   ```
   https://nof1.vercel.app
   ```

### Step 4: Test Full System

1. Visit your Vercel URL: `https://nof1.vercel.app`
2. Upload a test solicitation
3. Verify it processes correctly

---

## Post-Deployment Checklist

### ✅ Backend (Render)
- [ ] Service is running (green status)
- [ ] `/health` endpoint responds
- [ ] `/docs` page loads
- [ ] Environment variables are set
- [ ] Database is working

### ✅ Frontend (Vercel)
- [ ] Site loads successfully
- [ ] Can upload solicitations
- [ ] API calls work (check browser console F12)
- [ ] Results display correctly

### ✅ Integration
- [ ] Frontend successfully calls backend
- [ ] No CORS errors
- [ ] File uploads work
- [ ] Analysis completes

---

## Troubleshooting

### Backend Issues

**Problem:** Service keeps restarting
- Check Render logs: Dashboard → nof1-backend → Logs
- Look for Python errors
- Verify `requirements.txt` has all dependencies

**Problem:** Database errors
- Render's free tier disk is ephemeral (resets on restart)
- Consider upgrading to Starter plan for persistent disk
- Or use external database (PostgreSQL)

**Problem:** Timeout errors
- Increase timeout in Start Command (already set to 600s)
- Check for long-running operations

### Frontend Issues

**Problem:** "Failed to fetch" errors
- Check browser console (F12)
- Verify `REACT_APP_API_URL` is correct
- Test backend URL directly

**Problem:** CORS errors
- Backend already configured for CORS (`allow_origins=["*"]`)
- If still issues, check Render logs

**Problem:** Build fails
- Check Vercel build logs
- Verify all npm dependencies are in `package.json`
- Try deleting `node_modules` and rebuilding locally

### Update API URL After Deployment

**If you need to change backend URL:**

1. **Vercel:**
   - Go to Dashboard → nof1 → Settings → Environment Variables
   - Update `REACT_APP_API_URL`
   - Redeploy: Deployments → Latest → ⋯ → Redeploy

2. **Render:**
   - Dashboard → nof1-backend → Environment
   - Update variables
   - Service auto-redeploys

---

## Cost Summary

### Free Tier
- **Render Free:** Backend hosting (sleeps after 15 min inactivity)
- **Vercel Free:** Frontend hosting (unlimited bandwidth)
- **Total:** $0/month

### Production Tier (Recommended)
- **Render Starter:** $7/month (persistent disk, no sleep)
- **Vercel Pro:** $20/month (optional, adds features)
- **Total:** $7-27/month

---

## Quick Commands Reference

```bash
# Update code and redeploy
git add .
git commit -m "Update message"
git push

# Render: Auto-redeploys on push
# Vercel: Auto-redeploys on push

# View logs
# Render: Dashboard → Service → Logs
# Vercel: Dashboard → Project → Deployments → View Function Logs

# Rollback deployment
# Render: Dashboard → Service → Previous Deploy → Promote
# Vercel: Dashboard → Deployments → Previous → Promote to Production
```

---

## Success! 🎉

Your n of 1 platform is now deployed:

- **Frontend:** https://nof1.vercel.app
- **Backend:** https://nof1-backend.onrender.com
- **API Docs:** https://nof1-backend.onrender.com/docs

Share your frontend URL with users and start processing solicitations!

---

## Next Steps

1. **Custom Domain** (optional):
   - Vercel: Settings → Domains → Add Domain
   - Render: Settings → Custom Domain

2. **Monitoring:**
   - Set up uptime monitoring (UptimeRobot, Pingdom)
   - Enable Render email alerts

3. **Database Backup** (if using Render Starter):
   - Regular database exports
   - Store backups externally

4. **API Keys:**
   - Ensure all API keys are in Render environment variables
   - Never commit API keys to Git

---

Need help? Check:
- Render Docs: https://render.com/docs
- Vercel Docs: https://vercel.com/docs


