# 🚀 N of 1 Platform - Quick Reference Card

## ⚡ 10-Second Start

1. Open http://localhost:3000
2. Drag a file OR paste a URL
3. Click "Run Full Pipeline Analysis"
4. **Done!** See your results

---

## 🎯 Two Input Methods

### Method 1: Drag & Drop (Fastest)
```
┌─────────────────────────────────────┐
│  📁  Drag & Drop Your File Here     │
│                                     │
│        [Browse Files]               │
│                                     │
│  Supports: TXT, PDF, DOC, DOCX     │
└─────────────────────────────────────┘
```
✅ **When to use**: You have the file locally  
⚡ **Speed**: Instant parsing  

### Method 2: Paste URL (Most Convenient)
```
┌─────────────────────────────────────┐
│  https://sam.gov/opp/...            │
│                                     │
│        [Fetch & Parse]              │
└─────────────────────────────────────┘
```
✅ **When to use**: Browsing SAM.gov or FedBizOpps  
⚡ **Speed**: 2-3 seconds to fetch  

---

## 📊 What Gets Extracted Automatically

| Field | Example |
|-------|---------|
| **Solicitation #** | `W912BU-23-R-0015` |
| **Title** | `Cybersecurity Services for Cloud Infrastructure` |
| **Agency** | `Department of Defense` |
| **NAICS Codes** | `541512, 541519` |
| **Set-Asides** | `Small Business, SDVOSB` |
| **Clearance** | `Secret` |
| **Capabilities** | `cloud, cybersecurity, devops, kubernetes` |
| **Keywords** | `security, encryption, compliance, audit` |

**All fields extracted in <2 seconds!**

---

## 🔧 Configuration Options

### Data Enrichment Toggle
```
[ OFF ]  Basic matching only (fast)
[ ON  ]  Pull from 10+ external sources (comprehensive)
```

**Sources when ON:**
- USASpending.gov (past contracts)
- NIH Reporter (research funding)
- SBIR.gov (SBIR/STTR awards)
- USPTO (patents)
- AI analysis (Claude, ChatGPT)

### Top Companies Slider
```
1 ──────●────────────── 20
   Fast               Thorough
```

**Recommended:**
- `1-5`: Quick check
- `5-10`: Standard analysis
- `10-20`: Comprehensive evaluation

---

## 📈 Reading Results

### Company Cards Show:
```
┌────────────────────────────────────────┐
│ 🏢 CyberTech Solutions Inc.            │
│                                        │
│ ⭐ Match Score: 92%                    │
│ ✅ Validation: EXCELLENT               │
│ ⚠️  Risk Level: LOW                    │
│                                        │
│ Strengths: 5 | Weaknesses: 2          │
│ Opportunities: 4 | Threats: 1         │
│                                        │
│ 💡 Recommendation: PURSUE              │
└────────────────────────────────────────┘
```

### Score Breakdown
- **80-100%**: Excellent match, highly recommended
- **60-79%**: Good match, worth pursuing with some gaps
- **40-59%**: Fair match, significant gaps to address
- **0-39%**: Poor match, not recommended

### Risk Levels
- 🟢 **LOW**: Minimal concerns, ready to bid
- 🟡 **MEDIUM**: Some gaps, addressable with preparation
- 🔴 **HIGH**: Major concerns, risky to pursue

---

## 🎯 Common Workflows

### Workflow 1: Evaluate One Solicitation
```
1. Paste SAM.gov URL
2. Click "Fetch & Parse"
3. Review extracted fields (auto-populated)
4. Enable enrichment toggle
5. Set to 5 companies
6. Click "Run Full Pipeline Analysis"
7. Review top 5 matches
```
⏱️ **Time: ~15 seconds**

### Workflow 2: Batch Analysis
```
For each solicitation:
1. Drop file → auto-parses
2. Click "Run Full Pipeline Analysis"
3. Review results
4. Click "Start Over"
```
⏱️ **Time per solicitation: ~8 seconds**

### Workflow 3: Deep Dive (Single Company)
```
1. Upload solicitation
2. Enable enrichment
3. Set to 20 companies
4. Run analysis
5. Expand each company for:
   - Full SWOT analysis
   - Risk assessment details
   - Specific recommendations
   - Score component breakdown
```
⏱️ **Time: ~30 seconds**

---

## 🛠️ Troubleshooting

### "Could not extract sufficient text from URL"
**Solution:**  
- Download the file manually
- Use drag & drop instead
- Or copy text and paste directly

### "No companies found"
**Solution:**  
- Seed sample companies first
- Click "Company Manager" tab
- Click "Seed Sample Companies"

### Parsing seems incomplete
**Solution:**  
- Use the "Refine Details" section
- Manually add missing fields
- Keywords and capabilities can be edited

### Results taking too long
**Solution:**  
- Disable enrichment for faster results
- Reduce number of companies to analyze
- Close other browser tabs

---

## 📱 Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl/Cmd + V` | Paste file content |
| `Tab` | Navigate between fields |
| `Enter` in URL field | Trigger fetch |
| `Esc` | Close expanded sections |

---

## 🎨 Visual Status Indicators

### Success States
- ✅ Green banner = Parsing successful
- 🟢 Green badge = Excellent score
- 💚 Green button = Ready to analyze

### Warning States
- 🟡 Yellow badge = Medium risk
- ⚠️ Warning icon = Gaps identified

### Error States
- 🔴 Red badge = High risk
- ❌ Red icon = Critical issues

---

## 📚 Need More Help?

- **Detailed Guide**: See `UPDATED_INPUT_GUIDE.md`
- **Full Documentation**: See `README.md`
- **API Reference**: http://localhost:8000/docs
- **Architecture**: See `ARCHITECTURE.md`

---

## 💡 Pro Tips

1. **SAM.gov URLs work best** - Direct links to solicitations
2. **Drag & drop is fastest** - No clicking needed
3. **Enable enrichment for important bids** - More data = better decisions
4. **Start with 5 companies** - Good balance of speed and coverage
5. **Use collapsible sections** - Keep interface clean
6. **Export results** - Copy/paste from results view
7. **Multiple tabs** - Compare solicitations side-by-side

---

## 🎉 You're Ready!

**Start analyzing solicitations in 10 seconds:**

1. **Open**: http://localhost:3000
2. **Drop**: Your solicitation file
3. **Click**: "Run Full Pipeline Analysis"
4. **Win**: See your ranked matches!

**That's it!** 🚀


