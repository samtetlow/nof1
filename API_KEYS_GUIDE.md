# 🔑 API Keys Setup Guide

## Required API Keys for Theme-Based Search

### ✅ Essential (Recommended)

#### 1. **Google Custom Search API** 🔍
**Why**: Best for discovering companies, capabilities, and public information  
**Cost**: Free tier: 100 queries/day, Paid: $5 per 1,000 queries

**How to get**:
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Enable "Custom Search API"
4. Go to Credentials → Create API Key
5. Create a [Custom Search Engine](https://programmablesearchengine.google.com/)
6. Get your Search Engine ID

**Add to config.json**:
```json
"google": {
  "api_key": "AIzaSy...",
  "search_engine_id": "a12b3c4d5e..."
}
```

---

#### 2. **USASpending.gov API** 🏛️
**Why**: Official federal contract data - essential for past performance  
**Cost**: **FREE** ✅ No API key needed!

**How to use**:
- Already built-in, just works
- Public API, no authentication required
- Searches federal contract awards by company, NAICS, keywords

**Add to config.json**:
```json
"usaspending": {
  "enabled": true
}
```

---

### ⭐ Highly Recommended

#### 3. **Claude (Anthropic) API** 🤖
**Why**: Best AI for analyzing solicitations and company fit  
**Cost**: Pay-as-you-go, ~$0.01-0.03 per analysis

**How to get**:
1. Go to [Anthropic Console](https://console.anthropic.com/)
2. Sign up / Log in
3. Go to API Keys
4. Create a new API key

**Add to config.json**:
```json
"anthropic": {
  "api_key": "sk-ant-..."
}
```

---

#### 4. **OpenAI API** (Alternative to Claude) 🧠
**Why**: Alternative AI for analysis, good for embeddings  
**Cost**: Pay-as-you-go, ~$0.01-0.02 per analysis

**How to get**:
1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Sign up / Log in
3. Go to API Keys
4. Create a new secret key

**Add to config.json**:
```json
"openai": {
  "api_key": "sk-..."
}
```

---

### 💼 Optional (Business Data)

#### 5. **Pitchbook API** 💰
**Why**: Access to 3M+ private companies, funding data, investors, M&A  
**Cost**: Requires Pitchbook subscription + API access (enterprise)

**How to get**:
1. Log in to [my.pitchbook.com](https://my.pitchbook.com/)
2. Go to Settings → API Access
3. Request API credentials from your account manager
4. Generate API key

**API Documentation**: https://my.pitchbook.com/api/documentation/overview

**What you get**:
- Company search by name, industry, technology, location
- Detailed company profiles (description, employees, headquarters)
- Complete funding history (rounds, amounts, valuations, dates)
- Investor information (VCs, angels, strategics)
- Technologies, verticals, and market categories
- M&A and exit data

**Add to config.json**:
```json
"pitchbook": {
  "api_key": "pb_live_..."
}
```

**Use in theme search**: Automatically searches for companies by technical focus areas and keywords!

---

#### 6. **HubSpot CRM API** 📊
**Why**: Access your internal company database and notes  
**Cost**: Included with HubSpot subscription

**How to get**:
1. Log in to your HubSpot account
2. Settings → Integrations → API Key
3. Generate private app token

**Add to config.json**:
```json
"hubspot": {
  "api_key": "pat-na1-..."
}
```

---

### 🆓 Free Government Data (No Keys Needed)

#### 6. **NIH Reporter API** 🔬
**Why**: NIH grants and research funding data  
**Cost**: **FREE** ✅

**Already configured** - just works!

---

#### 7. **SBIR.gov API** 💡
**Why**: SBIR/STTR awards, small business innovation  
**Cost**: **FREE** ✅

**Already configured** - just works!

---

#### 8. **USPTO API** 📜
**Why**: Patent data for innovation metrics  
**Cost**: **FREE** ✅

**Already configured** - just works!

---

## 📋 Quick Setup Checklist

### Minimum Setup (Free)
- [ ] USASpending.gov (already enabled)
- [ ] NIH Reporter (already enabled)
- [ ] SBIR.gov (already enabled)

**Result**: Can search government contracts, grants, SBIR awards ✅

---

### Recommended Setup ($5-10/month)
- [ ] USASpending.gov ✅
- [ ] NIH Reporter ✅
- [ ] SBIR.gov ✅
- [ ] Google Custom Search API ($5/month for 1,000 searches)
- [ ] Claude or OpenAI ($5/month for moderate usage)

**Result**: Full search across web + government data + AI analysis ✅

---

### Enterprise Setup (Full Features)
- [ ] All free APIs ✅
- [ ] Google Custom Search ✅
- [ ] Claude & OpenAI ✅
- [ ] HubSpot (if you have it) ✅

**Result**: Complete theme-based discovery + AI + internal data ✅

---

## 🚀 Installation Steps

### 1. Create config.json

```bash
cp config.json.example config.json
nano config.json  # or use any text editor
```

### 2. Add Your API Keys

```json
{
  "data_sources": {
    "google": {
      "api_key": "YOUR_KEY_HERE",
      "search_engine_id": "YOUR_ID_HERE"
    },
    "anthropic": {
      "api_key": "YOUR_KEY_HERE"
    },
    "openai": {
      "api_key": "YOUR_KEY_HERE"
    },
    "hubspot": {
      "api_key": "YOUR_KEY_HERE"
    },
    "usaspending": {
      "enabled": true
    },
    "nih": {
      "enabled": true
    },
    "sbir": {
      "enabled": true
    }
  }
}
```

### 3. Test the Setup

```bash
# Restart backend
pkill -f "uvicorn app:app"
cd /Users/samtetlow/Cursor/nof1
source venv/bin/activate
uvicorn app:app --reload
```

### 4. Test Theme Search

```bash
curl -X POST http://localhost:8000/api/search-companies-by-themes \
  -H "Content-Type: application/json" \
  -d '{
    "themes": {
      "technical_focus": [
        {"area": "cybersecurity", "mentions": 15},
        {"area": "cloud", "mentions": 12}
      ],
      "keyword_analysis": {
        "core_topics": [
          {"term": "security", "count": 20},
          {"term": "cloud", "count": 18}
        ]
      }
    },
    "max_results": 10
  }'
```

---

## 💡 Cost Estimates

### Scenario 1: Analyze 10 solicitations/month (FREE)
- USASpending, NIH, SBIR: **$0**
- **Total: $0/month** ✅

### Scenario 2: Analyze 50 solicitations/month (LOW COST)
- USASpending, NIH, SBIR: **$0**
- Google (500 searches): **$2.50**
- Claude (50 analyses): **$1.50**
- **Total: $4/month** ✅

### Scenario 3: Analyze 200 solicitations/month (STANDARD)
- USASpending, NIH, SBIR: **$0**
- Google (2,000 searches): **$10**
- Claude (200 analyses): **$6**
- **Total: $16/month** ✅

### Scenario 4: Heavy usage (1,000 solicitations/month)
- USASpending, NIH, SBIR: **$0**
- Google (10,000 searches): **$50**
- Claude (1,000 analyses): **$30**
- **Total: $80/month** ✅

**ROI**: If one successful match saves 10+ hours of manual research, this pays for itself immediately!

---

## 🎯 What Each API Provides

| API | What You Get | Best For |
|-----|-------------|----------|
| **Google** | Web search, company websites, news | Discovering new companies, capabilities |
| **USASpending** | Federal contracts, past performance | Verifying experience, contract history |
| **NIH Reporter** | Research grants, R&D projects | Academic/research capabilities |
| **SBIR** | SBIR/STTR awards, innovation | Small business innovation, tech startups |
| **Claude/OpenAI** | AI analysis, natural language | Understanding fit, analyzing gaps |
| **HubSpot** | Your internal CRM data | Companies you already know |
| **USPTO** | Patents, intellectual property | Innovation metrics, R&D strength |

---

## ✅ Next Steps

1. **Start with free APIs** (USASpending, NIH, SBIR) - no setup needed!
2. **Add Google** if you want web discovery ($5/month)
3. **Add Claude** if you want AI analysis ($5/month)
4. **Test with a real solicitation** and see results
5. **Scale up** based on usage

---

## 🆘 Need Help?

### Common Issues

**"Google API returns 403"**
- Check API key is valid
- Ensure Custom Search API is enabled in Google Cloud Console
- Verify Search Engine ID is correct

**"No results from USASpending"**
- This is a public API, should always work
- Check internet connection
- Verify the search terms aren't too specific

**"Claude/OpenAI timeout"**
- These APIs can be slow (3-10 seconds)
- Increase timeout in config if needed
- Consider caching results

---

## 🎉 You're Ready!

With just the **FREE APIs** (USASpending, NIH, SBIR), you can already search thousands of companies with government contracts and grants.

Add **Google + Claude** for ~$10/month to unlock the full power of theme-based discovery!

