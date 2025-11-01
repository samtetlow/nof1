# 🐛 Debug Railway Backend - Step by Step

## The 500 Error Means Your Railway Backend is Crashing

Let's figure out exactly why.

---

## 🔍 **Step 1: Check Railway Deployment Status**

### Go to Railway Dashboard

1. Visit: https://railway.app/dashboard
2. Click on your **n-of-1** project
3. Look at the top - what does it say?

**Possible statuses:**

| Status | What it means | Action |
|--------|---------------|--------|
| 🟢 **Active** | Backend is running | Check logs for errors |
| 🔴 **Crashed** | Backend failed to start | Check build/deploy logs |
| 🟡 **Building** | Still deploying | Wait a few minutes |
| ⏸️ **Sleeping** | Inactive (free tier) | First request wakes it up |

---

## 🔍 **Step 2: Check Railway Logs**

### View Runtime Logs

1. In Railway Dashboard, click **"Deployments"** tab
2. Click **"View Logs"** or the latest deployment
3. Scroll to the **bottom** (most recent logs)

### Common Error Messages & Fixes:

#### ❌ Error: `ModuleNotFoundError: No module named 'openai'`
**Cause:** Dependencies didn't install

**Fix:**
1. Verify `requirements.txt` exists in your GitHub repo
2. Railway Dashboard → Settings → **"Redeploy"**
3. Watch build logs to ensure packages install

---

#### ❌ Error: `openai.OpenAIError: The api_key client option must be set`
**Cause:** OPENAI_API_KEY not set or wrong format

**Fix:**
1. Railway Dashboard → **Variables** tab
2. Check `OPENAI_API_KEY` exists and has value starting with `sk-`
3. If missing, add it
4. If wrong, update it
5. Wait 2 minutes for auto-redeploy

---

#### ❌ Error: `config.json not found` or `Failed to load config`
**Cause:** This is actually NORMAL - the app should fall back to env vars

**Check:** Do you have `OPENAI_API_KEY` in Railway Variables?
- If YES → This warning is OK, app will use env var
- If NO → Add `OPENAI_API_KEY` to Railway Variables

---

#### ❌ Error: `Address already in use` or `failed to bind to 0.0.0.0:8000`
**Cause:** Port configuration issue

**Fix:** Check your `Procfile`:
```
web: uvicorn app:app --host 0.0.0.0 --port $PORT --timeout-keep-alive 600
```

Must use `$PORT` (not `8000`). Railway assigns the port dynamically.

---

#### ❌ Error: `Application startup failed` or `ImportError`
**Cause:** Code or dependency issue

**Check:**
1. Did you push latest code to GitHub?
2. Is `requirements.txt` complete?
3. Are all your Python files pushed?

**Files that MUST be in GitHub:**
- `app.py`
- `data_sources.py`
- `confirmation_engine.py`
- `validation_engine.py`
- `theme_search.py`
- `requirements.txt`
- `Procfile`
- `railway.json`
- `runtime.txt`

---

#### ❌ Error: `sqlite3.OperationalError: database is locked`
**Cause:** SQLite issues on Railway (file-based DB on cloud)

**Fix - Option A:** Use Railway PostgreSQL (recommended)
1. Railway Dashboard → **"+ New"** → **"Database"** → **"PostgreSQL"**
2. Railway auto-sets `DATABASE_URL`
3. App will use PostgreSQL instead of SQLite
4. Redeploy

**Fix - Option B:** Keep SQLite but accept limitations
- Database resets on each deploy
- Need to re-seed companies after deploy
- OK for testing, not for production

---

## 🔍 **Step 3: Check Build Logs**

### View Build Process

1. Railway Dashboard → **Deployments**
2. Click on latest deployment
3. Look for **"Build Logs"** section

### What Success Looks Like:
```
✓ Collecting fastapi==0.104.1
✓ Collecting uvicorn==0.24.0
✓ Collecting openai>=1.54.0
✓ Successfully installed fastapi-0.104.1 ...
✓ Build completed
```

### What Failure Looks Like:
```
✗ ERROR: Could not find a version that satisfies...
✗ ERROR: No matching distribution found for...
✗ Build failed
```

**If build fails:**
- Check `requirements.txt` syntax
- Check Python version is 3.11.9
- Try manual redeploy

---

## 🔍 **Step 4: Test Backend Directly**

### Get Your Railway URL

1. Railway Dashboard → **Settings** → **Networking**
2. Copy your domain (e.g., `https://web-production-xxxxx.up.railway.app`)

### Test Endpoints

**Test 1: Health Check**
```
https://your-railway-url.up.railway.app/docs
```
- ✅ Should show FastAPI Swagger UI
- ❌ If 500 error → Backend crashed, check logs
- ❌ If 404 → Wrong URL
- ❌ If timeout → Backend not responding

**Test 2: Root Endpoint**
```
https://your-railway-url.up.railway.app/
```
- ✅ Should show: `{"message":"n of 1 API is running"}`
- ❌ If 500 → Backend crashed

**Test 3: Simple API Call**
```
https://your-railway-url.up.railway.app/api/companies/search
```
- ✅ Should return JSON (might be `[]` if no companies)
- ❌ If 500 → Database or app issue

---

## 🔍 **Step 5: Check All Environment Variables**

### Required Variables

Railway Dashboard → **Variables** tab should have:

```
OPENAI_API_KEY=sk-proj-...
PORT=8000
PYTHON_VERSION=3.11.9
```

### Verify Format:

**OPENAI_API_KEY:**
- ✅ Starts with `sk-proj-` or `sk-`
- ✅ Long string (50+ characters)
- ❌ Has spaces or quotes (remove them)
- ❌ Says "your_key_here" (needs real key)

**PORT:**
- ✅ Should be `8000` (Railway overrides this internally)

**PYTHON_VERSION:**
- ✅ Must be `3.11.9` (matches runtime.txt)

---

## 🔍 **Step 6: Check Frontend Configuration**

Even though error is backend, verify frontend is pointing to right place:

### Vercel Environment Variables

1. Vercel Dashboard → Your Project → **Settings** → **Environment Variables**
2. Check: `REACT_APP_API_URL`
3. Should be: `https://your-railway-url.up.railway.app`
4. ⚠️ **NO trailing slash!**

**Wrong:**
```
https://your-railway-url.up.railway.app/  ← Extra slash!
```

**Right:**
```
https://your-railway-url.up.railway.app
```

---

## 📋 **Quick Diagnostic Checklist**

Go through this list:

- [ ] Railway deployment shows "Active" (not "Crashed")
- [ ] Railway logs show "Application startup complete"
- [ ] `OPENAI_API_KEY` is in Railway Variables
- [ ] `OPENAI_API_KEY` starts with `sk-` 
- [ ] `/docs` endpoint loads in browser
- [ ] Root endpoint returns JSON message
- [ ] Procfile uses `$PORT` (not `8000`)
- [ ] All Python files are in GitHub repo
- [ ] `requirements.txt` is in GitHub repo
- [ ] `REACT_APP_API_URL` in Vercel matches Railway URL

---

## 🆘 **Still Stuck? Get These Details**

If none of the above fixes work, collect this information:

### 1. Railway Deployment Status
```
Railway Dashboard → What does the status say?
- Active / Crashed / Building / Failed?
```

### 2. Last 20 Lines of Railway Logs
```
Railway Dashboard → Deployments → View Logs → Copy last 20 lines
```

### 3. Build Logs Status
```
Railway Dashboard → Deployments → Build Logs → Did build succeed?
```

### 4. Environment Variables
```
Railway Variables tab → Screenshot or list what's there
(Hide the actual API key value, just confirm it exists)
```

### 5. Test Results
```
Visit: https://your-railway-url.up.railway.app/docs
What happens? (Swagger UI / 500 error / 404 / timeout)
```

---

## 🎯 **Most Likely Issues (90% of cases)**

### Issue #1: Missing or Invalid OPENAI_API_KEY
**Solution:** Add valid key to Railway Variables

### Issue #2: Dependencies Not Installed
**Solution:** Redeploy from Railway Settings

### Issue #3: Code Not Pushed to GitHub
**Solution:** Commit and push all files

### Issue #4: Wrong Python Version
**Solution:** Ensure PYTHON_VERSION=3.11.9

### Issue #5: Port Binding Issue
**Solution:** Check Procfile uses `$PORT`

---

## ✅ **Success Criteria**

You know it's working when:

1. ✅ Railway status shows "Active" (green)
2. ✅ `/docs` endpoint loads Swagger UI
3. ✅ Railway logs show "Application startup complete"
4. ✅ No error messages in Railway logs
5. ✅ Root endpoint returns JSON message
6. ✅ Frontend loads without "Network Error"

---

## 🔧 **Quick Fix Commands**

If you need to commit/push code:

```bash
cd /Users/samtetlow/Cursor/nof1

# Check what's not committed
git status

# Add all core files
git add app.py requirements.txt Procfile runtime.txt railway.json
git add data_sources.py confirmation_engine.py validation_engine.py theme_search.py

# Commit and push
git commit -m "Fix Railway deployment"
git push origin n-of-1-production
```

Railway will auto-redeploy when you push.

---

**Start with Step 1 and work through systematically!** 🔍

