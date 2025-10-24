# 🚀 START HERE - N of 1 Platform

## ⚡ 30-Second Quick Start

### Is everything already running?

**Yes?** → Open http://localhost:3000 and drag a file!

**No?** → Run these 2 commands:

```bash
# Terminal 1 (Backend)
cd /Users/samtetlow/Cursor/nof1
source venv/bin/activate
uvicorn app:app --reload

# Terminal 2 (Frontend)
cd /Users/samtetlow/Cursor/nof1/frontend
npm start
```

Then open http://localhost:3000

---

## 🎯 First Time Using This?

### What This Platform Does
**Input:** A government solicitation (RFP, RFI, BAA, etc.)  
**Output:** Ranked list of companies that match, with detailed analysis

**Use it for:**
- Finding the best company for a solicitation
- Analyzing bid fit before pursuing
- Getting SWOT analysis and recommendations
- Validating company claims with real data

---

## 📋 Your First Analysis (1 Minute)

### Step 1: Open the Platform
```
http://localhost:3000
```

### Step 2: Get Sample Data
Option A: Use our sample file
```bash
# Already exists: sample_solicitation.txt
# Just drag it into the interface!
```

Option B: Use a real SAM.gov link
```
1. Go to https://sam.gov
2. Find any solicitation
3. Copy the URL
4. Paste into platform
```

### Step 3: Input the Solicitation

**Method A - Drag & Drop:**
1. Drag `sample_solicitation.txt` onto the big drop zone
2. Watch it auto-parse (2 seconds)
3. Done!

**Method B - URL:**
1. Click "Paste URL" button
2. Paste SAM.gov link
3. Click "Fetch & Parse"
4. Done!

### Step 4: Run Analysis
1. Review the auto-extracted fields (they're usually perfect!)
2. Toggle "Enable External Data Enrichment" if you want comprehensive analysis
3. Set slider to 5 companies
4. Click **"Run Full Pipeline Analysis"**
5. Wait 5-10 seconds
6. **See your results!**

---

## 📊 What You'll See in Results

### For Each Company:
- **Match Score** - How well they fit (0-100%)
- **Validation Level** - EXCELLENT/GOOD/FAIR/POOR
- **Risk Level** - LOW 🟢 / MEDIUM 🟡 / HIGH 🔴
- **SWOT Analysis** - Strengths, Weaknesses, Opportunities, Threats
- **Recommendation** - PURSUE / CAUTION / DO NOT PURSUE
- **Action Items** - Specific steps to take

### Example Result:
```
#1 🏢 CyberTech Solutions Inc.
⭐ Match Score: 92%
✅ Validation: EXCELLENT
⚠️ Risk Level: LOW 🟢

💪 Strengths (5):
• Strong past performance in DOD cybersecurity
• All required certifications
• Technical expertise in cloud security
• Active Secret clearances
• Recent similar contract with DHS

💡 Recommendation: PURSUE - STRONG FIT
```

---

## 🎓 Learn More (Choose Your Path)

### Just Want to Use It? (5 min)
→ Read: `QUICK_REFERENCE.md`  
→ Then: Start analyzing real solicitations!

### Want to Understand Everything? (30 min)
→ Read: `WHATS_NEW.md` (what's new in v2.1)  
→ Read: `UPDATED_INPUT_GUIDE.md` (comprehensive guide)  
→ Read: `README.md` (full documentation)

### Visual Learner? (10 min)
→ Read: `VISUAL_DEMO.md` (ASCII mockups and demos)

### Developer? (1 hour)
→ Read: `ARCHITECTURE.md` (system design)  
→ Read: `CHANGELOG.md` (technical changes)  
→ Read: `FILES_CHANGED.md` (code inventory)  
→ Visit: http://localhost:8000/docs (API reference)

---

## 🛠️ Common Issues

### "Servers aren't running"
```bash
# Backend
cd /Users/samtetlow/Cursor/nof1
source venv/bin/activate
uvicorn app:app --reload

# Frontend (new terminal)
cd /Users/samtetlow/Cursor/nof1/frontend
npm start
```

### "No companies found"
```bash
# Seed sample companies first
curl -X POST http://localhost:8000/seed
```

Or use the "Seed Sample Companies" button in the frontend.

### "URL fetch failed"
- Download the file manually
- Use drag & drop instead
- SAM.gov pages work best

### "Parsing didn't extract everything"
- Click "▼ Step 4: Refine Details (Optional)"
- Manually add missing fields
- Still works fine!

---

## 📍 Important URLs

| What | URL | Purpose |
|------|-----|---------|
| **Frontend** | http://localhost:3000 | Main interface |
| **Backend** | http://localhost:8000 | API server |
| **API Docs** | http://localhost:8000/docs | Interactive API |
| **Alt Docs** | http://localhost:8000/redoc | Alternative format |

---

## 💡 Pro Tips

### For Speed:
- **Drag & drop is fastest** - No clicking needed
- **URL is most convenient** - When browsing SAM.gov
- **Disable enrichment** - If you just want quick scores
- **Start with 5 companies** - Good balance of speed/coverage

### For Accuracy:
- **Enable enrichment** - Pulls data from 10+ sources
- **Analyze 10-20 companies** - More thorough evaluation
- **Review refinement section** - Catch any parsing errors
- **Check SWOT details** - Expand each company card

### For Efficiency:
- **Use keyboard shortcuts** - Tab to navigate, Enter to submit
- **Keep frontend tab open** - Quick switching
- **Bookmark http://localhost:3000** - One-click access
- **Use the same terminal sessions** - Don't restart servers

---

## 📞 Need Help?

### Quick Answers (1 min)
→ `QUICK_REFERENCE.md`

### Detailed Help (10 min)
→ `UPDATED_INPUT_GUIDE.md`

### Visual Guide (5 min)
→ `VISUAL_DEMO.md`

### Everything (30 min)
→ `README.md` (main docs)

### Technical Deep Dive (1 hour)
→ All docs + http://localhost:8000/docs

---

## 🎉 You're Ready!

**Everything you need to know:**

1. **Open**: http://localhost:3000
2. **Drag**: A solicitation file (or paste URL)
3. **Click**: "Run Full Pipeline Analysis"
4. **Win**: See ranked companies in 10 seconds!

**That's literally it!** 🚀

The platform handles everything else:
- ✅ Parsing
- ✅ Extraction
- ✅ Matching
- ✅ Confirmation
- ✅ Validation
- ✅ Scoring
- ✅ SWOT analysis
- ✅ Recommendations

**Just drag, click, and get results!**

---

## 🎯 What to Analyze

### Good Starting Points:
- **Sample file**: `sample_solicitation.txt` (included)
- **SAM.gov**: https://sam.gov/search/
- **Recent RFPs**: Filter by your industry
- **SBIR topics**: https://www.sbir.gov/
- **Email attachments**: Any solicitation PDFs

### What Works Best:
- ✅ Federal RFPs
- ✅ SBIR/STTR solicitations
- ✅ BAAs (Broad Agency Announcements)
- ✅ Sources Sought notices
- ✅ Any structured solicitation text

---

## 🚀 Your Journey Starts Now!

### Minute 1:
Open http://localhost:3000

### Minute 2:
Drag `sample_solicitation.txt`

### Minute 3:
Click "Run Full Pipeline Analysis"

### Minute 4:
**See your first results!** 🎉

### Minute 5+:
Analyze real solicitations and win more bids!

---

**Welcome to N of 1 Platform v2.1** 🎊

**Let's find the perfect company for your next solicitation!** 💼✨

---

## One-Line Summary

> **Drag a solicitation → Get ranked companies → Win more bids** 🏆

**That's the platform.** 

**Now go use it!** 🚀


