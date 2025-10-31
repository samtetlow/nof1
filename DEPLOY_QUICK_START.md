# 🚀 Quick Start: Deploy to Railway & Vercel

## ⚡ Fast Track (5 Steps)

### 1️⃣ Commit Your Code (2 minutes)

```bash
cd /Users/samtetlow/Cursor/nof1

# Add all relevant changes
git add app.py requirements.txt
git add frontend/src/
git add .github/ .coveragerc pytest.ini scripts/ tests/
git add *.md *.sh *.txt

# Exclude sensitive files (already in .gitignore)
# - config.json
# - *.db files
# - *.log files
# - *.pid files

# Commit
git commit -m "Production ready - v2.0 with full pipeline"

# Push to GitHub
git push origin n-of-1-production
```

---

### 2️⃣ Deploy Backend to Railway (5 minutes)

**A. Create Project**
- Go to: https://railway.app/dashboard
- Click: **"New Project"** → **"Deploy from GitHub repo"**
- Select: `nof1` repository
- Branch: `n-of-1-production`

**B. Add Environment Variables**

Go to **Variables** tab and add:

```
OPENAI_API_KEY=sk-...your-key...
PORT=8000
PYTHON_VERSION=3.11.9
```

**C. Get Your Backend URL**

- Go to **Settings** → **Networking**
- Click: **"Generate Domain"**
- Copy the URL: `https://web-production-xxxxx.up.railway.app`

**D. Verify It Works**

Visit: `https://your-url.up.railway.app/docs`

You should see the FastAPI documentation interface!

---

### 3️⃣ Update Frontend Config (1 minute)

Edit: `frontend/vercel.json`

```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "build",
  "framework": "create-react-app",
  "env": {
    "REACT_APP_API_URL": "https://your-railway-url.up.railway.app"
  }
}
```

Replace `your-railway-url` with the actual Railway URL from Step 2C.

```bash
# Commit the update
git add frontend/vercel.json
git commit -m "Update frontend API URL for production"
git push origin n-of-1-production
```

---

### 4️⃣ Deploy Frontend to Vercel (5 minutes)

**A. Create Project**
- Go to: https://vercel.com/dashboard
- Click: **"Add New Project"**
- Select: `nof1` repository from GitHub
- Branch: `n-of-1-production`

**B. Configure Build**

- **Framework Preset**: Create React App
- **Root Directory**: `frontend`
- **Build Command**: `npm run build`
- **Output Directory**: `build`

**C. Add Environment Variable**

In **Environment Variables** section:

```
Name: REACT_APP_API_URL
Value: https://your-railway-url.up.railway.app
```

**D. Deploy**

Click **"Deploy"** and wait 2-3 minutes.

**E. Get Your Frontend URL**

Vercel will give you a URL like: `https://nof1-xyz.vercel.app`

---

### 5️⃣ Test Everything (2 minutes)

**A. Test Backend**
```bash
curl https://your-railway-url.up.railway.app/docs
```

**B. Test Frontend**
1. Visit: `https://your-vercel-url.vercel.app`
2. Click **"Company Manager"** → **"Seed Sample Companies"**
3. Go to **"Solicitation Analysis"**
4. Upload a test solicitation
5. Click **"Run Full Pipeline Analysis"**
6. Verify results appear!

---

## ✅ Success Checklist

- [ ] Backend deployed to Railway
- [ ] Backend `/docs` endpoint accessible
- [ ] Frontend deployed to Vercel
- [ ] Frontend loads in browser
- [ ] Can seed sample companies
- [ ] Can upload and parse solicitation
- [ ] Full pipeline runs and shows results
- [ ] Results display with scores and recommendations

---

## 🔧 Optional: Better CORS Security

After deployment, you can tighten security by updating CORS in `app.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # For local development
        "https://your-app.vercel.app",  # Your production frontend
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Then commit and push - Railway auto-deploys!

---

## 📊 Cost Summary

| Service | Free Tier | Paid Tier |
|---------|-----------|-----------|
| **Railway** | $5 credit/month (~500 hours) | ~$20-40/month |
| **Vercel** | Unlimited bandwidth | $20/month Pro |
| **OpenAI API** | Pay per use | ~$0.002/request |
| **Total** | ~FREE for testing | ~$40-60/month production |

---

## 🆘 Quick Troubleshooting

### ❌ Backend Error: "Application failed to start"
- Check Railway logs
- Verify `OPENAI_API_KEY` is set
- Make sure `requirements.txt` is committed

### ❌ Frontend Error: "Network Error"
- Verify `REACT_APP_API_URL` in Vercel environment variables
- Check backend is running: visit `/docs` endpoint
- Check CORS settings in `app.py`

### ❌ Frontend Loads But API Fails
- Open browser console (F12)
- Look for CORS errors
- Verify API URL is correct (no trailing slash)

### ❌ Pipeline Times Out
- Increase timeout in `frontend/src/services/api.ts` (currently 10 min)
- Check Railway logs for backend errors
- Try with `enrich: false` for faster results

---

## 📚 Full Documentation

- **Complete Guide**: `DEPLOYMENT_CHECKLIST.md`
- **Environment Setup**: `RAILWAY_ENV_TEMPLATE.txt` and `VERCEL_ENV_TEMPLATE.txt`
- **Testing**: Run `./PREPARE_DEPLOY.sh` to check everything before deploying
- **API Docs**: Once deployed, visit `/docs` on your backend URL

---

## 🎉 You're Live!

Your n-of-1 Platform is now running in production!

- **Frontend**: https://your-app.vercel.app
- **Backend API**: https://your-app.up.railway.app
- **API Docs**: https://your-app.up.railway.app/docs

Share the frontend URL with your team! 🚀

---

**Questions?** Check the troubleshooting section or review the logs:
- Railway: Dashboard → Your Project → Logs
- Vercel: Dashboard → Your Project → Deployments → Logs

