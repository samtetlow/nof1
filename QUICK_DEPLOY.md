# ⚡ Quick Deploy - Render + Vercel (5 Minutes)

## 🚀 Step 1: Deploy Backend to Render (3 minutes)

### 1.1 Push to GitHub
```bash
cd /Users/samtetlow/Cursor/nof1
git add .
git commit -m "Ready for deployment"
git push origin main
```

### 1.2 Deploy on Render
1. Go to: https://dashboard.render.com
2. Click **"New +"** → **"Blueprint"**
3. Connect GitHub → Select your `nof1` repository
4. Render will detect `render.yaml` automatically
5. Click **"Apply"** → Wait 5-10 minutes

### 1.3 Add Environment Variables
After deployment starts:
1. Go to your service → **"Environment"** tab
2. Add these variables:

```
OPENAI_API_KEY=sk-proj-...your-key...
GOOGLE_API_KEY=AIza...your-key...
GOOGLE_SEARCH_ENGINE_ID=your-search-engine-id
```

3. Click **"Save Changes"** (auto-redeploys)

### 1.4 Get Your Backend URL
- Service page → Copy the URL (e.g., `https://nof1-backend-jecb.onrender.com`)
- **SAVE THIS URL** - you'll need it for Vercel!

---

## 🎨 Step 2: Deploy Frontend to Vercel (2 minutes)

### 2.1 Update Frontend Config
The `frontend/vercel.json` already has the backend URL placeholder. After you get your Render URL, update it:

```bash
# Edit frontend/vercel.json and replace the API URL
# Or set it via Vercel dashboard (easier)
```

### 2.2 Deploy on Vercel
1. Go to: https://vercel.com/new
2. Click **"Import Git Repository"**
3. Connect GitHub → Select your `nof1` repository
4. Configure:
   - **Framework Preset**: Create React App
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `build`
5. Click **"Environment Variables"** → Add:
   ```
   REACT_APP_API_URL=https://nof1-backend-jecb.onrender.com
   ```
   (Replace with YOUR actual Render backend URL)
6. Click **"Deploy"**

---

## ✅ Step 3: Verify (1 minute)

### Test Backend
```bash
curl https://nof1-backend-jecb.onrender.com/health
```

Should return: `{"status":"ok",...}`

### Test Frontend
Visit your Vercel URL (e.g., `https://nof1.vercel.app`)

---

## 🔧 Troubleshooting

**Backend not starting?**
- Check Render logs: Service → Logs tab
- Verify `OPENAI_API_KEY` is set
- Check build logs for errors

**Frontend can't connect?**
- Verify `REACT_APP_API_URL` in Vercel matches your Render URL
- Check browser console (F12) for errors
- Make sure backend is running (not sleeping)

**Free tier sleeping?**
- Render free tier sleeps after 15 min inactivity
- First request after sleep takes ~30 seconds
- Upgrade to Starter ($7/month) for always-on

---

## 📋 Quick Checklist

- [ ] Code pushed to GitHub
- [ ] Backend deployed on Render
- [ ] `OPENAI_API_KEY` set in Render
- [ ] Backend URL copied
- [ ] Frontend deployed on Vercel
- [ ] `REACT_APP_API_URL` set in Vercel
- [ ] Both services running
- [ ] Test upload works

---

**Total Time**: ~5 minutes  
**Cost**: Free (or $7/month for Render Starter)
