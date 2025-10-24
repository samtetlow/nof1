# Quick Start Guide

Get your N-of-1 Enhanced Platform running in 5 minutes!

## 🚀 Installation (2 minutes)

```bash
# 1. Navigate to project
cd /Users/samtetlow/Cursor/nof1

# 2. Activate virtual environment (already created)
source venv/bin/activate

# 3. Install any new dependencies
pip install -r requirements.txt

# 4. (Optional) Set up API keys
cp config.json.example config.json
# Edit config.json with your API keys
```

## ▶️ Start the Server (30 seconds)

```bash
uvicorn app:app --reload
```

Server starts at: **http://localhost:8000**

## 📖 View Documentation (30 seconds)

Open in browser:
- **Interactive API Docs**: http://localhost:8000/docs
- **API Info**: http://localhost:8000

## 🧪 Test with Sample Data (2 minutes)

### Step 1: Load Sample Companies

```bash
curl -X POST http://localhost:8000/seed
```

**Result**: Creates 3 sample companies:
- Aegis Cyber Solutions (cybersecurity)
- Helio Bioinformatics (genomics)
- Atlas Systems Integration (systems integration)

### Step 2: Run Full Pipeline Analysis

```bash
curl -X POST http://localhost:8000/api/full-pipeline \
  -H "Content-Type: application/json" \
  -d '{
    "solicitation": {
      "title": "Cybersecurity Services for Federal Agency",
      "agency": "Department of Defense",
      "naics_codes": ["541512"],
      "set_asides": ["Small Business", "SDVOSB"],
      "security_clearance": "Secret",
      "required_capabilities": ["cybersecurity", "incident response", "zero trust"],
      "keywords": ["siem", "soar", "threat detection", "security operations"]
    },
    "enrich": false,
    "top_k": 3
  }'
```

**Note**: `enrich: false` runs without external API calls (instant results)

### Step 3: Review Results

The response includes:
- ✅ **Match scores** for each company
- ✅ **Confirmation status** and confidence
- ✅ **Validation score** and level
- ✅ **Risk assessment**
- ✅ **SWOT analysis**
- ✅ **Recommended actions**
- ✅ **Go/no-go recommendation**

## 🔑 Enable External Data Sources (Optional)

For full enrichment capabilities:

### 1. Get API Keys

**Free/Easy:**
- No keys needed for: USASpending.gov, NIH Reporter, SBIR.gov, USPTO

**Paid Services:**
- **Claude**: https://console.anthropic.com/
- **OpenAI (ChatGPT)**: https://platform.openai.com/
- **Google Custom Search**: https://developers.google.com/custom-search
- **HubSpot**: https://app.hubspot.com/

### 2. Update config.json

```bash
cp config.json.example config.json
nano config.json  # or use your favorite editor
```

Add your keys:
```json
{
  "data_sources": {
    "claude": {
      "api_key": "sk-ant-api03-xxxxx"
    },
    "chatgpt": {
      "api_key": "sk-xxxxx"
    }
  }
}
```

### 3. Run with Enrichment

```bash
curl -X POST http://localhost:8000/api/full-pipeline \
  -H "Content-Type: application/json" \
  -d '{
    "solicitation": {...},
    "enrich": true,
    "top_k": 3
  }'
```

## 📊 Common Workflows

### Workflow 1: Evaluate Your Company

```bash
# Get your company ID
curl http://localhost:8000/api/companies/search?q=YourCompanyName

# Run full analysis
curl -X POST http://localhost:8000/api/full-pipeline \
  -H "Content-Type: application/json" \
  -d '{
    "company_id": "YOUR_COMPANY_ID",
    "solicitation": {
      "title": "Opportunity Title",
      "naics_codes": ["541512"],
      "required_capabilities": ["capability1", "capability2"]
    },
    "enrich": true
  }'
```

### Workflow 2: Add Your Company

```bash
curl -X POST http://localhost:8000/api/companies \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Your Company Name",
    "naics_codes": ["541512", "541519"],
    "size": "Small",
    "socioeconomic_status": ["8(a)", "WOSB"],
    "capabilities": ["cloud computing", "devops", "cybersecurity"],
    "security_clearances": ["Secret"],
    "locations": ["va", "dc"],
    "employees": 50,
    "annual_revenue": 5000000,
    "description": "Your company description",
    "keywords": ["aws", "kubernetes", "security"],
    "website": "https://yourcompany.com"
  }'
```

### Workflow 3: Parse Solicitation Text

```bash
curl -X POST http://localhost:8000/api/solicitations/parse \
  -H "Content-Type: application/json" \
  -d '{
    "raw_text": "NAICS Code: 541512. This is a Small Business set-aside requiring Secret clearance for cloud migration services..."
  }'
```

## 🎯 Understanding the Results

### Validation Levels
- **Excellent (0.85+)**: ✅ Strongly recommend - proceed with confidence
- **Good (0.70-0.84)**: ✅ Recommend - good fit
- **Acceptable (0.55-0.69)**: ⚠️ Conditional - proceed with caution
- **Marginal (0.40-0.54)**: ⚠️ Evaluate carefully
- **Poor/Rejected (< 0.40)**: ❌ Do not pursue

### Risk Levels
- **Low**: Minimal concerns
- **Medium**: Some manageable risks
- **High**: Significant risks requiring mitigation
- **Critical**: Deal-breaker issues

### Key Metrics
- **Match Score**: Initial alignment (0-1.0)
- **Confirmation Score**: External validation (0-1.0)
- **Validation Score**: Final comprehensive score (0-1.0)
- **Alignment %**: Overall fit percentage
- **Confidence %**: Data quality confidence

## 🐛 Troubleshooting

### Issue: Import Errors
```bash
# Solution: Reinstall dependencies
pip install -r requirements.txt
```

### Issue: Config Not Loading
```bash
# Check file exists
ls config.json

# Validate JSON
python -c "import json; print(json.load(open('config.json')))"
```

### Issue: Slow Responses
- **Without enrichment** (`enrich: false`): < 1 second
- **With enrichment** (`enrich: true`): 10-20 seconds (external API calls)
- Reduce `top_k` to analyze fewer companies

### Issue: API Key Errors
- Source works without key: `{"error": "API key not configured"}`
- Module continues with available sources
- Check config.json for correct key format

## 📚 Next Steps

1. **Read full documentation**: `README.md`
2. **Understand architecture**: `ARCHITECTURE.md`
3. **Add your companies**: Use `/api/companies` endpoint
4. **Configure data sources**: Set up API keys in `config.json`
5. **Customize weights**: Adjust matching importance via `/api/weights`
6. **Explore API docs**: http://localhost:8000/docs

## 💡 Pro Tips

1. **Start without enrichment** to understand the pipeline
2. **Add one API key at a time** to see its impact
3. **Use the interactive docs** at `/docs` for easy testing
4. **Check logs** for detailed pipeline execution info
5. **Save good solicitation examples** for future testing

## 🎓 Learning Path

1. ✅ **Basic**: Run with sample data (no enrichment)
2. ✅ **Intermediate**: Add your company, test matching
3. ✅ **Advanced**: Enable API keys, full enrichment
4. ✅ **Expert**: Customize weights, integrate with your workflow

## 📞 Support

- **API Documentation**: http://localhost:8000/docs
- **Architecture Details**: See `ARCHITECTURE.md`
- **Code Comments**: Check module docstrings
- **Examples**: See `README.md` use cases

---

**You're ready to go!** Start the server and visit http://localhost:8000/docs 🚀


