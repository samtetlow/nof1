# Deploy Frontend to Vercel

## Quick Deploy Steps

### 1. Go to Vercel
Visit: https://vercel.com/new

### 2. Import Project
- Click **"Import Git Repository"**
- Connect to GitHub (if not already connected)
- Select: **samtetlow/nof1**

### 3. Configure Project Settings

**Root Directory:**
```
frontend
```

**Framework Preset:**
```
Create React App
```

**Build Command:**
```
npm run build
```

**Output Directory:**
```
build
```

### 4. Add Environment Variable

Click **"Environment Variables"** section:

**Name:**
```
REACT_APP_API_URL
```

**Value:**
```
https://web-production-978ba.up.railway.app
```

**Environments:** Check all (Production, Preview, Development)

### 5. Deploy

Click **"Deploy"** button

---

## After Deployment

Vercel will give you a URL like:
```
https://nof1-frontend.vercel.app
```

Or with your custom domain:
```
https://your-custom-domain.com
```

Test it by:
1. Visiting the URL
2. Uploading a PDF solicitation
3. Verifying it processes correctly

---

## Troubleshooting

### If you get CORS errors:
The Railway backend is already configured to allow all origins:
```python
allow_origins=["*"]
```

### If API calls fail:
1. Check the browser console (F12)
2. Verify the Railway backend URL is correct
3. Test the backend directly: https://web-production-978ba.up.railway.app

### Update Environment Variable:
1. Go to Vercel Dashboard
2. Select your project
3. Go to Settings → Environment Variables
4. Update `REACT_APP_API_URL`
5. Redeploy

---

## Alternative: Deploy via Vercel CLI

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
cd frontend
vercel --prod

# Follow prompts and set:
# - Root directory: ./
# - Build command: npm run build
# - Output directory: build
# - Environment variable: REACT_APP_API_URL=https://web-production-978ba.up.railway.app
```

