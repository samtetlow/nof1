# GitHub Secrets Setup Guide

## 📋 Step-by-Step Instructions

### 1. Navigate to GitHub Secrets

1. Go to your GitHub repository: https://github.com/YOUR_USERNAME/nof1
2. Click **Settings** (top menu)
3. In the left sidebar, click **Secrets and variables** → **Actions**
4. Click **New repository secret** button

---

## 🔑 Secrets to Add

### Backend Secrets (Railway)

#### RAILWAY_TOKEN
**How to get it:**
1. Go to https://railway.app/
2. Click your profile (bottom left)
3. Click **Account Settings**
4. Click **Tokens** tab
5. Click **Create Token**
6. Copy the token

**In GitHub:**
- Name: `RAILWAY_TOKEN`
- Value: `[paste your Railway token]`

---

#### RAILWAY_PROJECT_ID
**How to get it:**
1. Go to https://railway.app/
2. Open your `nof1` project
3. Click **Settings** (in project)
4. Look for **Project ID** (or in the URL: railway.app/project/YOUR_PROJECT_ID)
5. Copy the ID

**In GitHub:**
- Name: `RAILWAY_PROJECT_ID`
- Value: `[paste your project ID]`

---

#### STAGING_BACKEND_URL
**Your Railway staging backend URL**

**In GitHub:**
- Name: `STAGING_BACKEND_URL`
- Value: `https://your-staging-backend.up.railway.app`
- *(If you don't have staging yet, use your current Railway URL for now)*

---

#### PRODUCTION_BACKEND_URL
**Your Railway production backend URL**

**In GitHub:**
- Name: `PRODUCTION_BACKEND_URL`
- Value: `https://web-production-978ba.up.railway.app`
- *(This is your current Railway deployment)*

---

### Frontend Secrets (Vercel)

#### VERCEL_TOKEN
**How to get it:**
1. Go to https://vercel.com/
2. Click your profile (top right)
3. Click **Settings**
4. Click **Tokens** (left sidebar)
5. Click **Create Token**
6. Name it "GitHub Actions CI/CD"
7. Set expiration (or no expiration)
8. Copy the token

**In GitHub:**
- Name: `VERCEL_TOKEN`
- Value: `[paste your Vercel token]`

---

#### VERCEL_ORG_ID
**How to get it:**
1. Go to https://vercel.com/
2. Click your profile → **Settings**
3. Look for **Your ID** or run in terminal:
   ```bash
   npx vercel whoami
   ```
4. Or find it in `.vercel/project.json` in your frontend folder

**In GitHub:**
- Name: `VERCEL_ORG_ID`
- Value: `[paste your Vercel org ID]`

---

#### VERCEL_PROJECT_ID
**How to get it:**
1. Go to https://vercel.com/
2. Open your `nof1` project
3. Click **Settings**
4. Look for **Project ID**
5. Or check `.vercel/project.json` in your frontend folder

**In GitHub:**
- Name: `VERCEL_PROJECT_ID`
- Value: `[paste your Vercel project ID]`

---

#### STAGING_FRONTEND_URL
**Your Vercel staging URL**

**In GitHub:**
- Name: `STAGING_FRONTEND_URL`
- Value: `https://your-staging-frontend.vercel.app`
- *(If you don't have staging yet, use your current Vercel URL for now)*

---

#### PRODUCTION_FRONTEND_URL
**Your Vercel production URL**

**In GitHub:**
- Name: `PRODUCTION_FRONTEND_URL`
- Value: `https://nof1-bauu.vercel.app`
- *(This is your current Vercel deployment)*

---

### API Keys

#### OPENAI_API_KEY
**Your OpenAI API key for running tests**

**In GitHub:**
- Name: `OPENAI_API_KEY`
- Value: `your-openai-api-key-here`

---

## ✅ Verification Checklist

After adding all secrets, you should have these 10 secrets:

- [ ] `RAILWAY_TOKEN`
- [ ] `RAILWAY_PROJECT_ID`
- [ ] `STAGING_BACKEND_URL`
- [ ] `PRODUCTION_BACKEND_URL`
- [ ] `VERCEL_TOKEN`
- [ ] `VERCEL_ORG_ID`
- [ ] `VERCEL_PROJECT_ID`
- [ ] `STAGING_FRONTEND_URL`
- [ ] `PRODUCTION_FRONTEND_URL`
- [ ] `OPENAI_API_KEY`

---

## 🚀 Testing the Setup

### 1. Push to the Branch
```bash
cd /Users/samtetlow/Cursor/nof1
git push origin n-of-1-production
```

### 2. Watch GitHub Actions
1. Go to your GitHub repository
2. Click **Actions** tab
3. You should see workflows starting:
   - "Backend CI"
   - "Frontend CI"
   - "Deploy to Staging" (if enabled)

### 3. Check for Errors
- Green ✅ = Success
- Red ❌ = Check logs for missing secrets or other issues

---

## 🆘 Troubleshooting

### If workflows fail with "Secret not found":
1. Double-check secret names (they're case-sensitive)
2. Make sure there are no spaces in secret names
3. Verify you added them to the correct repository

### If you can't find Railway Project ID:
1. Open Railway project
2. Look at the URL: `railway.app/project/abc-123-xyz`
3. The ID is `abc-123-xyz`

### If you can't find Vercel IDs:
Run in your frontend directory:
```bash
cd /Users/samtetlow/Cursor/nof1/frontend
npx vercel link
```
Then check `.vercel/project.json`

---

## 📝 Quick Copy Template

Here's a template you can fill out before adding to GitHub:

```
RAILWAY_TOKEN=
RAILWAY_PROJECT_ID=
STAGING_BACKEND_URL=
PRODUCTION_BACKEND_URL=https://web-production-978ba.up.railway.app
VERCEL_TOKEN=
VERCEL_ORG_ID=
VERCEL_PROJECT_ID=
STAGING_FRONTEND_URL=
PRODUCTION_FRONTEND_URL=https://nof1-bauu.vercel.app
OPENAI_API_KEY=your-openai-api-key-here
```

---

**Once all secrets are added, your CI/CD pipeline will be fully operational!** 🎉




