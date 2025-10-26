# ⚡ Quick Deploy - 15 Minutes

## Step-by-Step Deployment

### 1️⃣ Push to GitHub (2 minutes)

```bash
cd /Users/samtetlow/Cursor/nof1
git add .
git commit -m "Ready for deployment"
git push origin main
```

---

### 2️⃣ Deploy Backend on Railway (5 minutes)

1. **Go to:** https://railway.app
2. **Click:** "Start a New Project" → "Deploy from GitHub repo"
3. **Select:** your `nof1` repository
4. **Add Environment Variables:**
   ```
   OPENAI_API_KEY=sk-proj-YOUR_KEY_HERE
   PORT=8000
   ```
5. **Generate Domain:** Settings → "Generate Domain"
6. **Copy URL:** e.g., `https://nof1-production.up.railway.app`

✅ Backend is live at: `https://your-url.railway.app/docs`

---

### 3️⃣ Deploy Frontend on Vercel (5 minutes)

1. **Go to:** https://vercel.com
2. **Click:** "Add New Project" → Import GitHub repo
3. **Configure:**
   - Root Directory: `frontend`
   - Framework: Create React App
   - Build Command: `npm run build`
   - Output Directory: `build`
4. **Environment Variables:**
   ```
   REACT_APP_API_URL=https://your-railway-backend-url.railway.app
   ```
5. **Deploy**

✅ Frontend is live at: `https://your-app.vercel.app`

---

### 4️⃣ Connect Custom Domain (3 minutes)

1. **In Vercel:** Settings → Domains → Add `nof1.yourdomain.com`
2. **Update DNS:** Add CNAME record pointing to Vercel
3. **Wait:** 2-5 minutes for SSL certificate

✅ Your app is live at: `https://nof1.yourdomain.com`

---

### 5️⃣ Update Backend CORS (2 minutes)

Edit `app.py` line 673:

```python
allow_origins=[
    "http://localhost:3000",
    "https://nof1.yourdomain.com",  # Your custom domain
    "https://your-app.vercel.app"   # Your Vercel domain
],
```

Push update:
```bash
git add app.py
git commit -m "Add production domains to CORS"
git push origin main
```

Railway will auto-redeploy in 1-2 minutes.

---

## ✅ You're Done!

🎉 **Your app is live at:** `https://nof1.yourdomain.com`

Test it by uploading a solicitation and seeing results!

---

## 🔍 Quick Checks

- ✅ Backend API docs: `https://your-backend.railway.app/docs`
- ✅ Frontend loads: `https://nof1.yourdomain.com`
- ✅ Can upload PDF and see results
- ✅ Companies are returned from search

---

## 📞 Need Help?

**Check logs:**
- Railway: Your project → "View Logs"
- Vercel: Your project → "Logs"
- Browser: F12 → Console tab

**Common fixes:**
- CORS error → Add your domain to app.py allow_origins
- 500 error → Check Railway logs for Python errors
- Can't connect → Verify REACT_APP_API_URL in Vercel env vars

