# 🚀 N of 1 Platform - Deployment Guide

## Railway Deployment (Recommended - Simple & Fast)

### Prerequisites
- GitHub account
- Railway account (sign up at https://railway.app)
- Your OpenAI API key

---

## 📦 Step 1: Prepare Your Code

1. **Push to GitHub:**
```bash
cd /Users/samtetlow/Cursor/nof1
git add .
git commit -m "Prepare for Railway deployment"
git push origin main
```

---

## 🚂 Step 2: Deploy Backend on Railway

### A. Create Railway Project

1. Go to https://railway.app
2. Click "Start a New Project"
3. Select "Deploy from GitHub repo"
4. Choose your `nof1` repository
5. Railway will auto-detect it's a Python app

### B. Configure Environment Variables

In Railway dashboard, go to **Variables** tab and add:

```
OPENAI_API_KEY=your_openai_api_key_here
PORT=8000
PYTHON_VERSION=3.11.9
```

### C. Configure Build Settings

Railway should auto-detect these from `Procfile`, but verify:
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 600`

### D. Generate Domain

1. Go to **Settings** tab
2. Click "Generate Domain"
3. Copy your backend URL (e.g., `https://nof1-production.up.railway.app`)

---

## 🌐 Step 3: Deploy Frontend on Vercel

### A. Prepare Frontend for Production

Update `/Users/samtetlow/Cursor/nof1/frontend/.env.production`:

```bash
REACT_APP_API_URL=https://your-backend-url.railway.app
```

Replace `your-backend-url.railway.app` with your Railway backend URL.

### B. Deploy to Vercel

1. Go to https://vercel.com
2. Click "Add New Project"
3. Import your GitHub repository
4. Configure:
   - **Framework Preset:** Create React App
   - **Root Directory:** `frontend`
   - **Build Command:** `npm run build`
   - **Output Directory:** `build`
5. Add Environment Variable:
   - `REACT_APP_API_URL` = your Railway backend URL

### C. Configure Custom Domain

1. In Vercel dashboard, go to **Settings > Domains**
2. Add your custom domain (e.g., `nof1.yourdomain.com`)
3. Follow DNS configuration instructions
4. Vercel will auto-provision SSL certificate

---

## 🔧 Step 4: Update Backend CORS

Once you have your frontend URL, update the backend:

Edit `/Users/samtetlow/Cursor/nof1/app.py`:

```python
# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Keep for local dev
        "https://nof1.yourdomain.com",  # Your production domain
        "https://your-app.vercel.app"  # Your Vercel domain
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Commit and push:
```bash
git add app.py
git commit -m "Update CORS for production domain"
git push origin main
```

Railway will auto-deploy the update.

---

## ✅ Step 5: Verify Deployment

1. **Backend Health Check:**
   - Visit: `https://your-backend.railway.app/docs`
   - You should see the FastAPI Swagger UI

2. **Frontend Check:**
   - Visit: `https://nof1.yourdomain.com`
   - Upload a solicitation and test the full flow

---

## 🔐 Security Checklist

- ✅ API keys stored in Railway environment variables (not in code)
- ✅ CORS configured for your specific domain
- ✅ HTTPS enabled (automatic on Railway & Vercel)
- ✅ config.json NOT committed to GitHub (add to .gitignore)

---

## 📊 Monitoring & Logs

### Railway Logs
- Go to your Railway project
- Click "View Logs" to see real-time backend logs
- Monitor for errors or API issues

### Vercel Logs
- Go to your Vercel project
- Click "Logs" to see frontend deployment logs

---

## 💰 Cost Estimate

### Free Tier (Development/Testing)
- **Railway:** $5 free credit/month (~500 hours)
- **Vercel:** Unlimited bandwidth, 100 GB/month
- **Total:** FREE for moderate use

### Paid Tier (Production)
- **Railway:** ~$20-40/month (depends on usage)
- **Vercel:** $20/month Pro plan
- **OpenAI API:** Pay-as-you-go (~$0.002 per request)

---

## 🆘 Troubleshooting

### Backend Issues

**Problem:** 500 Internal Server Error
- Check Railway logs for error details
- Verify all environment variables are set
- Check that `config.json` has correct structure

**Problem:** CORS errors
- Verify frontend URL is in CORS allow_origins
- Make sure you pushed updated app.py

### Frontend Issues

**Problem:** "Network Error" or API not connecting
- Verify REACT_APP_API_URL is correct in Vercel environment variables
- Check that backend is running (visit /docs endpoint)
- Verify CORS settings on backend

---

## 🔄 Making Updates

After making code changes:

```bash
git add .
git commit -m "Your update message"
git push origin main
```

Both Railway and Vercel will auto-deploy the changes (takes 1-3 minutes).

---

## 📞 Support

If you encounter issues:
1. Check Railway logs for backend errors
2. Check browser console for frontend errors
3. Verify all environment variables are set correctly
4. Test backend independently at /docs endpoint

---

## 🎉 You're Live!

Your N of 1 platform is now accessible at:
- **Frontend:** https://nof1.yourdomain.com
- **Backend API:** https://your-backend.railway.app

Share the frontend URL with your users!

