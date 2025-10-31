# 🚀 Deployment Checklist for Railway & Vercel

## ✅ Pre-Deployment Checklist

### 1. Code Preparation
- [ ] All changes committed to git
- [ ] `.gitignore` properly configured (excludes config.json, .env, *.db)
- [ ] No sensitive data in repository
- [ ] Backend tests passing
- [ ] Frontend builds successfully

### 2. Backend (Railway) Configuration Files
- [x] `Procfile` exists
- [x] `requirements.txt` up to date
- [x] `runtime.txt` specifies Python 3.11.9
- [x] `railway.json` configured
- [x] CORS configured to allow all origins (will update after deployment)

### 3. Frontend (Vercel) Configuration Files
- [x] `vercel.json` exists in frontend directory
- [x] `package.json` properly configured
- [x] Build command: `npm run build`
- [x] Output directory: `build`

### 4. Environment Variables to Set

#### Railway Backend Environment Variables:
```
OPENAI_API_KEY=your_openai_key_here
PORT=8000
PYTHON_VERSION=3.11.9
DATABASE_URL=<railway will auto-provide if using Railway PostgreSQL>
```

#### Vercel Frontend Environment Variables:
```
REACT_APP_API_URL=https://your-railway-backend.up.railway.app
```

### 5. Git Repository Status
Current branch: `n-of-1-production`

**Modified files to commit:**
- `app.py` - Main backend application
- `frontend/src/components/ResultsDisplay.tsx`
- `frontend/src/components/SolicitationForm.tsx`
- `frontend/src/services/api.ts`
- `requirements.txt`

**New files to add:**
- `.coveragerc`
- `.github/` - CI/CD workflows
- `CI_CD_SETUP.md`
- `GITHUB_SECRETS_SETUP.md`
- `PHASE_1_COMPLETE.md`
- `START_BACKEND_VISIBLE.sh`
- `pytest.ini`
- `scripts/` - Utility scripts
- `test_confirmation.py`
- `test_full_api.sh`
- `test_live_api.py`
- `tests/` - Test suite

**Files to ignore (not commit):**
- `backend.log` - Log file
- `backend.pid` - Process ID file
- `nof1.db` - Local database

---

## 📋 Deployment Steps (DO NOT RUN YET - JUST PREPARED)

### Step 1: Commit and Push Code

```bash
cd /Users/samtetlow/Cursor/nof1

# Add all relevant files
git add app.py
git add frontend/src/components/ResultsDisplay.tsx
git add frontend/src/components/SolicitationForm.tsx
git add frontend/src/services/api.ts
git add requirements.txt

# Add new test infrastructure
git add .coveragerc .github/ pytest.ini
git add scripts/ tests/
git add test_confirmation.py test_full_api.sh test_live_api.py

# Add documentation
git add CI_CD_SETUP.md GITHUB_SECRETS_SETUP.md PHASE_1_COMPLETE.md
git add START_BACKEND_VISIBLE.sh

# Commit
git commit -m "Prepare for production deployment - v2.0 with confirmation and validation engines"

# Push to GitHub
git push origin n-of-1-production
```

### Step 2: Deploy Backend to Railway

1. **Go to Railway Dashboard**
   - Visit: https://railway.app/dashboard
   - Click "New Project"

2. **Deploy from GitHub**
   - Select "Deploy from GitHub repo"
   - Choose repository: `nof1`
   - Branch: `n-of-1-production`

3. **Set Environment Variables**
   - Go to Variables tab
   - Add:
     ```
     OPENAI_API_KEY=<your_key>
     PORT=8000
     PYTHON_VERSION=3.11.9
     ```

4. **Generate Domain**
   - Go to Settings > Networking
   - Click "Generate Domain"
   - Copy the URL (e.g., `https://nof1-production-xyz.up.railway.app`)

5. **Verify Deployment**
   - Visit: `https://your-backend-url.up.railway.app/docs`
   - Should see FastAPI Swagger documentation

### Step 3: Deploy Frontend to Vercel

1. **Update Backend URL in Frontend**
   ```bash
   # Update the vercel.json file with your Railway backend URL
   # Edit: /Users/samtetlow/Cursor/nof1/frontend/vercel.json
   ```

2. **Go to Vercel Dashboard**
   - Visit: https://vercel.com/dashboard
   - Click "Add New Project"

3. **Import from GitHub**
   - Select repository: `nof1`
   - Branch: `n-of-1-production`

4. **Configure Project**
   - Framework Preset: `Create React App`
   - Root Directory: `frontend`
   - Build Command: `npm run build`
   - Output Directory: `build`

5. **Set Environment Variables**
   - Add variable:
     ```
     REACT_APP_API_URL=https://your-railway-backend.up.railway.app
     ```

6. **Deploy**
   - Click "Deploy"
   - Wait for build to complete (2-3 minutes)

7. **Get Production URL**
   - Vercel will provide a URL like: `https://nof1-xyz.vercel.app`

### Step 4: Update Backend CORS (Optional but Recommended)

For better security, update CORS to only allow your Vercel frontend:

```python
# In app.py, update the CORS middleware:
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Local development
        "https://your-app.vercel.app",  # Production frontend
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Then commit and push:
```bash
git add app.py
git commit -m "Update CORS for production frontend"
git push origin n-of-1-production
```

Railway will auto-deploy the update.

---

## 🧪 Post-Deployment Verification

### Test Backend
```bash
# Health check
curl https://your-backend.railway.app/docs

# Test seed endpoint
curl -X POST https://your-backend.railway.app/seed

# Test parse solicitation
curl -X POST https://your-backend.railway.app/api/solicitations/parse \
  -H "Content-Type: application/json" \
  -d '{"raw_text": "Test solicitation for cybersecurity services. NAICS: 541512"}'
```

### Test Frontend
1. Visit your Vercel URL
2. Upload a test solicitation
3. Run the full pipeline
4. Verify results display correctly

### Monitor Logs
- **Railway Logs**: Check for any backend errors
- **Vercel Logs**: Check for build or runtime errors
- **Browser Console**: Check for API connection issues

---

## 🔧 Configuration Summary

### Railway Backend
- **Start Command**: `uvicorn app:app --host 0.0.0.0 --port $PORT --timeout-keep-alive 600`
- **Python Version**: 3.11.9
- **Dependencies**: Installed from `requirements.txt`
- **Database**: SQLite (file-based, persists with Railway volumes)

### Vercel Frontend
- **Framework**: React (Create React App)
- **Build**: `npm run build`
- **Output**: `build/` directory
- **API Calls**: Proxied to Railway backend via `REACT_APP_API_URL`

---

## 💡 Quick Reference Commands

### Local Testing Before Deploy
```bash
# Test backend
cd /Users/samtetlow/Cursor/nof1
source venv/bin/activate
python app.py

# Test frontend
cd /Users/samtetlow/Cursor/nof1/frontend
npm start
```

### View Git Status
```bash
git status
git diff
```

### Create GitHub Repository (if not already done)
```bash
# If you need to create a new repository
git remote add origin https://github.com/yourusername/nof1.git
git branch -M n-of-1-production
git push -u origin n-of-1-production
```

---

## ⚠️ Important Notes

1. **Database**: Railway SQLite database will be ephemeral unless you add a volume. For production, consider upgrading to Railway PostgreSQL.

2. **API Keys**: Never commit `config.json` or `.env` files. Always use environment variables in production.

3. **Costs**:
   - Railway: $5/month free credit, then ~$20-40/month
   - Vercel: Free for personal projects, $20/month for Pro
   - OpenAI API: Pay-as-you-go (~$0.002 per request)

4. **Cold Starts**: First request after inactivity may be slow (5-10 seconds) on free tier.

5. **Timeouts**: Backend configured for 10-minute timeout for long-running pipeline operations.

---

## 📞 Troubleshooting

### Issue: Backend won't start on Railway
- Check Railway logs for error messages
- Verify all environment variables are set
- Ensure `requirements.txt` has all dependencies

### Issue: Frontend can't connect to backend
- Verify `REACT_APP_API_URL` is set in Vercel
- Check CORS settings in `app.py`
- Test backend `/docs` endpoint directly

### Issue: Pipeline times out
- Increase timeout in frontend `api.ts` (currently 10 minutes)
- Check Railway logs for backend errors
- Consider optimizing enrichment sources

---

## ✅ Ready to Deploy?

Once you've reviewed this checklist:

1. Run the git commands in **Step 1** to commit and push
2. Follow **Step 2** to deploy on Railway
3. Update `frontend/vercel.json` with Railway URL
4. Follow **Step 3** to deploy on Vercel
5. Test everything works!

---

**Created**: October 31, 2024
**Status**: READY FOR DEPLOYMENT
**Version**: 2.0 (Confirmation + Validation Engines)

