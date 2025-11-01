# 🔧 Troubleshooting: 500 Internal Server Error

## Error Message
```
500: INTERNAL_SERVER_ERROR
Code: FUNCTION_INVOCATION_FAILED
```

This means your **Railway backend** is crashing or not responding correctly.

---

## ✅ **Quick Fix Checklist**

### 1. Check Railway Environment Variables ⚠️ **MOST COMMON ISSUE**

Go to Railway Dashboard → Your Project → **Variables** tab

**Required variables:**
```
OPENAI_API_KEY=sk-...your-actual-key...
PORT=8000
PYTHON_VERSION=3.11.9
```

**If OPENAI_API_KEY is missing or wrong:**
- Add/fix it in Railway Variables
- Railway auto-redeploys in 1-2 minutes
- ✅ This fixes 90% of 500 errors!

---

### 2. Check Railway Logs 🔍

**How to access:**
1. Railway Dashboard → Your Project
2. Click **"Deployments"** or **"Logs"**
3. Look at the most recent logs

**Common error messages and fixes:**

#### Error: "No module named 'anthropic'" or "No module named 'openai'"
**Fix:** Your dependencies didn't install properly.

1. Check if `requirements.txt` was committed to git
2. In Railway, go to Settings → Redeploy
3. Watch build logs to ensure packages install

#### Error: "API key not configured" or "OPENAI_API_KEY"
**Fix:** Add OPENAI_API_KEY to Railway Variables

```
OPENAI_API_KEY=sk-...your-key...
```

#### Error: "Failed to load config" or "config.json not found"
**Fix:** This is actually OK! The app should fall back to environment variables.

Make sure OPENAI_API_KEY is in Railway Variables (not config.json).

#### Error: "Database locked" or "sqlite3.OperationalError"
**Fix:** SQLite might have permission issues on Railway.

**Option A - Use Railway PostgreSQL (Recommended for production):**
1. Railway Dashboard → Your Project
2. Click "+ New" → "Database" → "PostgreSQL"
3. Railway will auto-set DATABASE_URL
4. Redeploy

**Option B - Keep SQLite (for testing):**
- The database will recreate on each deploy
- You'll need to re-seed companies each time
- OK for testing, not ideal for production

#### Error: "Address already in use" or "Port 8000"
**Fix:** Check your Procfile and railway.json

Procfile should be:
```
web: uvicorn app:app --host 0.0.0.0 --port $PORT --timeout-keep-alive 600
```

Make sure it uses `$PORT` (environment variable), not `8000` hardcoded.

#### Error: "Application startup failed"
**Fix:** Check Python version

Railway Variable should have:
```
PYTHON_VERSION=3.11.9
```

---

### 3. Check Railway Build Logs 📦

**How to access:**
1. Railway Dashboard → Your Project → Deployments
2. Click on the latest deployment
3. View **"Build Logs"**

**What to look for:**
- ✅ "Successfully installed fastapi uvicorn..."
- ✅ "Build completed"
- ❌ "ERROR: Could not find a version..."
- ❌ "Build failed"

**If build fails:**
- Check `requirements.txt` is committed
- Check Python version is 3.11.9
- Try manual redeploy: Settings → Redeploy

---

### 4. Test Backend Directly 🌐

**Get your Railway backend URL:**
- Railway Dashboard → Your Project → Settings → Networking
- Copy the domain (e.g., `https://web-production-xxxxx.up.railway.app`)

**Test these URLs in your browser:**

1. **Health Check:** `https://your-railway-url.up.railway.app/docs`
   - ✅ Should show FastAPI Swagger UI
   - ❌ If 500 error, check Railway logs

2. **Root endpoint:** `https://your-railway-url.up.railway.app/`
   - ✅ Should show: `{"message": "n of 1 API is running"}`
   - ❌ If blank or 500, backend isn't starting

3. **Test API:** `https://your-railway-url.up.railway.app/api/companies/search`
   - ✅ Should return JSON (might be empty array)
   - ❌ If 500, database or app issue

**From terminal:**
```bash
# Replace with your actual Railway URL
BACKEND_URL="https://your-railway-url.up.railway.app"

# Test health
curl $BACKEND_URL/docs

# Test root
curl $BACKEND_URL/

# Test API endpoint
curl $BACKEND_URL/api/companies/search
```

---

### 5. Check Vercel Frontend Configuration 🎨

**Verify environment variable:**
1. Vercel Dashboard → Your Project → Settings → Environment Variables
2. Check: `REACT_APP_API_URL`
3. Should be: `https://your-railway-url.up.railway.app`
4. **Important:** NO trailing slash!

**If you changed it:**
- Go to Deployments tab
- Click "Redeploy" on latest deployment
- Wait 2-3 minutes

---

## 🔄 **Step-by-Step Resolution**

### Step 1: Fix Railway Backend First

1. **Check Environment Variables** (Railway Variables tab)
   ```
   OPENAI_API_KEY=sk-...
   PORT=8000
   PYTHON_VERSION=3.11.9
   ```

2. **Check Railway Logs** (Deployments → View Logs)
   - Read the error messages
   - Apply fixes from above

3. **Test Backend Directly**
   - Visit: `https://your-railway-url.up.railway.app/docs`
   - Should see Swagger UI

### Step 2: Verify Frontend Points to Backend

1. **Check Vercel Environment Variable**
   - REACT_APP_API_URL = your Railway URL

2. **Redeploy Frontend**
   - Vercel Dashboard → Deployments → Redeploy

3. **Test Frontend**
   - Visit your Vercel URL
   - Check browser console (F12) for errors

---

## 🐛 **Still Not Working?**

### Get Detailed Error Information

**1. Check Railway Deployment Status**
```
Railway Dashboard → Your Project → Deployments
```
Look for:
- ❌ "Build Failed" (check build logs)
- ❌ "Deployment Failed" (check deploy logs)
- ⚠️ "Crashed" (check runtime logs)
- ✅ "Active" (backend should be working)

**2. Check Browser Console**
```
1. Open your Vercel frontend URL
2. Press F12 (Developer Tools)
3. Go to "Console" tab
4. Look for errors:
   - CORS errors → Check backend CORS settings
   - Network errors → Check REACT_APP_API_URL
   - 500 errors → Backend is crashing
```

**3. Check Railway Runtime Logs**
```
Railway Dashboard → Your Project → View Logs

Look for:
- "Application startup complete" ✅
- "ERROR: ..." ❌
- "Exception: ..." ❌
- Repeated crashes ❌
```

---

## 📊 **Quick Diagnostic Table**

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `/docs` shows 500 | Backend crashed | Check Railway logs |
| `/docs` shows 404 | Wrong URL | Verify Railway domain |
| Frontend shows nothing | CORS issue | Check backend CORS |
| "Network Error" in browser | Wrong API URL | Check REACT_APP_API_URL |
| Build failed | Missing packages | Check requirements.txt |
| "API key" error in logs | Missing env var | Add OPENAI_API_KEY |
| Works then crashes | Timeout/memory | Check Railway resource limits |

---

## 🆘 **Need More Help?**

### Share These Details:

1. **Railway Logs** (last 20 lines):
   - Railway Dashboard → Logs → Copy recent errors

2. **Browser Console Errors**:
   - F12 → Console tab → Copy any red errors

3. **URLs**:
   - Railway backend URL: `https://...`
   - Vercel frontend URL: `https://...`

4. **Environment Variables Set**:
   - OPENAI_API_KEY: ✅ or ❌
   - PORT: ✅ or ❌
   - REACT_APP_API_URL: ✅ or ❌

---

## ✅ **Success Indicators**

You know it's working when:

1. ✅ Railway logs show: "Application startup complete"
2. ✅ `/docs` endpoint loads Swagger UI
3. ✅ Browser console has no errors
4. ✅ Frontend loads without "Network Error"
5. ✅ Can seed companies successfully
6. ✅ Can upload and parse solicitation

---

## 🎯 **Most Likely Fix**

**90% of 500 errors are caused by missing OPENAI_API_KEY!**

1. Go to Railway Dashboard
2. Click Variables tab
3. Add: `OPENAI_API_KEY=sk-your-actual-key`
4. Wait 2 minutes for auto-redeploy
5. Test: `https://your-url.up.railway.app/docs`

If that works, your frontend will start working too! 🎉

