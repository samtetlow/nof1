# 🔧 Vercel Environment Variable Fix

## The Problem

React environment variables (like `REACT_APP_API_URL`) are **baked into the build** at build time. If the variable isn't set when Vercel builds, it defaults to `http://localhost:8000`.

## The Fix

### Step 1: Set Environment Variable in Vercel Dashboard

**CRITICAL**: The `vercel.json` env section may not be enough. You MUST set it in the dashboard:

1. Go to: https://vercel.com/dashboard
2. Select your project
3. Go to **Settings** → **Environment Variables**
4. Add/Update:
   - **Name**: `REACT_APP_API_URL`
   - **Value**: `https://nof1-backend-jecb.onrender.com`
   - **Environments**: ✅ Production ✅ Preview ✅ Development
5. Click **Save**

### Step 2: Force Rebuild

After setting the variable, you MUST rebuild:

**Option A: Manual Redeploy**
1. Go to **Deployments** tab
2. Click **⋯** (three dots) on latest deployment
3. Click **Redeploy**
4. Make sure "Use existing Build Cache" is **UNCHECKED**

**Option B: Push a Change**
```bash
# Make a small change to trigger rebuild
echo "// Rebuild trigger" >> frontend/src/services/api.ts
git add frontend/src/services/api.ts
git commit -m "Trigger Vercel rebuild with correct API URL"
git push
```

### Step 3: Verify

After rebuild, check the deployed frontend:

1. Visit: https://nof1.streamlineclimate.com/
2. Open browser console (F12)
3. Check Network tab when making a request
4. API calls should go to: `https://nof1-backend-jecb.onrender.com`

## Why This Happens

- **Local**: Uses `.env` file or environment variable → Works
- **Vercel**: Needs variable set in dashboard → Must rebuild after setting

## Quick Test

After rebuild, open browser console on the deployed site and run:
```javascript
console.log('API URL:', process.env.REACT_APP_API_URL);
```

If it shows `undefined` or `http://localhost:8000`, the variable wasn't set correctly or the build didn't pick it up.

