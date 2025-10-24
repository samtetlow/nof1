# n of 1 — Enhanced Reverse Search Platform v2.0

**An intelligent 6-module pipeline for government contracting opportunity matching with external data enrichment, confirmation analysis, and comprehensive validation.**

## 🎯 Overview

This application provides an advanced reverse search platform for government contracting. Instead of companies searching for opportunities, solicitations are analyzed and matched against a database of companies through a sophisticated 6-module pipeline that validates alignment through multiple external data sources.

### 🚀 Enhanced 6-Module Pipeline

1. **Module 1-3: Data Source Integrations**
   - Google Custom Search
   - AI Analysis (Claude, ChatGPT)
   - Government Contracts (USASpending.gov, NIH Reporter, SBIR.gov)
   - Company Data (HubSpot CRM, Pitchbook, AngelList)
   - Innovation Metrics (USPTO Patents)

2. **Module 4: Matching Engine**
   - Multi-factor scoring across 7 dimensions
   - NAICS, capabilities, past performance, size status, clearances, location, keywords
   - Configurable weights for custom prioritization

3. **Module 5: Confirmation Engine**
   - Verifies claimed capabilities through external data
   - Confirms past performance via contract databases
   - Validates certifications and compliance
   - Assesses market presence and reputation
   - Identifies contradictions or red flags

4. **Module 6: Validation Engine**
   - Comprehensive risk assessment
   - SWOT analysis (Strengths, Weaknesses, Opportunities, Threats)
   - Final validation scoring and recommendation
   - Detailed action items
   - Go/no-go decision rationale

### ✨ Key Features

- **🎯 Drag & Drop Input**: Modern interface for instant solicitation upload
- **🔗 URL Fetching**: Paste SAM.gov or FedBizOpps links for automatic content extraction
- **🤖 Smart Auto-Parsing**: Automatically extracts 8+ key fields from any format
- **📊 Intelligent Matching**: 7-factor algorithm with configurable weights
- **🌐 External Data Enrichment**: Pulls data from 10+ sources to verify claims
- **✅ Confirmation Analysis**: Cross-references company profiles with real-world data
- **🎯 Validation Scoring**: Comprehensive alignment assessment with risk levels
- **🧠 AI-Powered Analysis**: Leverages Claude and ChatGPT for deep company insights
- **📝 Contract Verification**: Validates past performance through USASpending.gov, NIH, SBIR
- **⚡ Lightning Fast**: From solicitation to results in 10-15 seconds
- **🔍 Risk Assessment**: Identifies critical gaps and compliance issues

## 📦 Installation

### Prerequisites

- Python 3.8+
- API Keys (optional, for enhanced features):
  - Google Custom Search API
  - Anthropic Claude API
  - OpenAI API
  - HubSpot CRM API

### Setup

1. **Clone or navigate to the repository:**
```bash
cd /Users/samtetlow/Cursor/nof1
```

2. **Create a virtual environment:**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Configure API keys (optional):**
```bash
cp config.json.example config.json
# Edit config.json with your API keys
```

## 🏃 Running the Application

Start the FastAPI server:

```bash
uvicorn app:app --reload
```

The server will start at `http://localhost:8000`

### Interactive API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🎮 Quick Start

### 1. Access the Frontend

The easiest way to use the platform is through the React frontend:

```bash
cd frontend
npm start
```

Then open http://localhost:3000 in your browser.

**Using the Interface:**
1. **Choose input method**: Select "Upload / Drag & Drop" or "Paste URL"
2. **Input solicitation**: 
   - Drag a file onto the drop zone, OR
   - Paste a SAM.gov URL and click "Fetch & Parse"
3. **Review extraction**: See all fields auto-extracted in seconds
4. **Configure options**: Toggle enrichment, set number of companies
5. **Run analysis**: Click "Run Full Pipeline Analysis"
6. **View results**: See ranked companies with scores, SWOT, risks, recommendations

### 2. Seed Sample Data (First Time Only)

Populate the database with sample companies:

```bash
curl -X POST http://localhost:8000/seed
```

Or use the "Seed Sample Companies" button in the frontend's Company Manager tab.

### 3. API Usage (Advanced)

You can also use the API directly for integration into other tools:

**Parse a solicitation from URL:**
```bash
curl -X POST http://localhost:8000/api/solicitations/fetch-url \
  -H "Content-Type: application/json" \
  -d '{"url": "https://sam.gov/opp/..."}'
```

**Run the complete 6-module analysis:**
```bash
curl -X POST http://localhost:8000/api/full-pipeline \
  -H "Content-Type: application/json" \
  -d '{
    "solicitation": {
      "title": "Cybersecurity Services",
      "agency": "Department of Defense",
      "naics_codes": ["541512"],
      "set_asides": ["Small Business", "SDVOSB"],
      "security_clearance": "Secret",
      "required_capabilities": ["cybersecurity", "incident response", "zero trust"],
      "keywords": ["siem", "soar", "threat detection"]
    },
    "enrich": true,
    "top_k": 5
  }'
```

**Response includes:**
- Match scores for top companies
- Confirmation analysis with evidence
- Validation scores and risk levels
- Strengths, weaknesses, opportunities, and risks (SWOT)
- Recommended actions
- Go/no-go recommendations

### 3. Enrich Company Data

Enrich a specific company from external sources:

```bash
curl -X POST http://localhost:8000/api/enrich-company \
  -H "Content-Type: application/json" \
  -d '{
    "company_id": "YOUR_COMPANY_ID",
    "sources": ["usaspending", "uspto", "claude"]
  }'
```

### 4. Match with Confirmation

Run matching with confirmation analysis (no validation):

```bash
curl -X POST http://localhost:8000/api/match-with-confirmation \
  -H "Content-Type: application/json" \
  -d '{
    "solicitation": {
      "title": "Cloud Migration Services",
      "agency": "GSA",
      "naics_codes": ["541512"],
      "required_capabilities": ["aws", "azure", "cloud migration"]
    },
    "enrich": true,
    "top_k": 10
  }'
```

## 📊 API Endpoints

### Basic Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/companies` | POST | Create a company |
| `/api/companies/{id}` | GET | Get company details |
| `/api/companies/search` | GET | Search companies |
| `/api/solicitations` | POST | Create a solicitation |
| `/api/solicitations/parse` | POST | Parse raw solicitation text |
| `/api/match` | POST | Basic matching (Module 4 only) |
| `/seed` | POST | Seed sample data |

### Enhanced Pipeline Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/enrich-company` | POST | Enrich company from external sources |
| `/api/match-with-confirmation` | POST | Match + Enrich + Confirm (Modules 4-5) |
| `/api/full-pipeline` | POST | **Full 6-module pipeline (RECOMMENDED)** |

## 🔧 Configuration

### API Keys

Create a `config.json` file (copy from `config.json.example`):

```json
{
  "data_sources": {
    "google": {
      "api_key": "YOUR_GOOGLE_API_KEY",
      "search_engine_id": "YOUR_SEARCH_ENGINE_ID"
    },
    "claude": {
      "api_key": "YOUR_ANTHROPIC_API_KEY"
    },
    "chatgpt": {
      "api_key": "YOUR_OPENAI_API_KEY"
    },
    "hubspot": {
      "api_key": "YOUR_HUBSPOT_API_KEY"
    }
  }
}
```

### Data Sources

#### Free APIs (No Key Required)
- **USASpending.gov**: Federal contract data
- **NIH Reporter**: Health research grants
- **SBIR.gov**: Small business innovation awards
- **USPTO PatentsView**: Patent data

#### Paid/Restricted APIs
- **Google Custom Search**: Web presence verification
- **Claude (Anthropic)**: AI-powered company analysis
- **ChatGPT (OpenAI)**: AI-powered company analysis
- **HubSpot**: Internal CRM data

#### Manual Upload Required
- **Pitchbook**: Funding and valuation data
- **AngelList**: Startup data

## 🔄 Pipeline Flow

```
Solicitation Input
       ↓
[Module 4: Matching Engine]
   → Initial scoring based on profile data
       ↓
[Modules 1-3: Data Enrichment]
   → Fetch from Google, AI, USASpending, etc.
       ↓
[Module 5: Confirmation Engine]
   → Verify claims against external data
   → Identify contradictions
   → Build evidence base
       ↓
[Module 6: Validation Engine]
   → Risk assessment
   → SWOT analysis
   → Final scoring
   → Go/no-go recommendation
       ↓
Comprehensive Results with Actions
```

## 📈 Scoring System

### Match Score (Module 4)
- **0.75-1.0**: Recommended
- **0.50-0.74**: Borderline
- **0.00-0.49**: Not Recommended

### Confirmation Status (Module 5)
- **Confirmed**: Strong external evidence
- **Partially Confirmed**: Some evidence
- **Unconfirmed**: Weak evidence
- **Contradicted**: Evidence contradicts claims
- **Insufficient Data**: Not enough data

### Validation Level (Module 6)
- **Excellent** (0.85+): Strongly recommend
- **Good** (0.70-0.84): Recommend
- **Acceptable** (0.55-0.69): Conditional recommend
- **Marginal** (0.40-0.54): Evaluate carefully
- **Poor** (0.25-0.39): Not recommended
- **Rejected** (< 0.25): Do not pursue

### Risk Levels
- **Low**: Minimal concerns
- **Medium**: Some manageable risks
- **High**: Significant risks requiring mitigation
- **Critical**: Deal-breaker issues

## 🎯 Use Cases

### 1. Opportunity Qualification
Quickly assess whether your company should pursue a specific opportunity:
```bash
# Run full pipeline with your company
POST /api/full-pipeline
{
  "company_id": "your-company-id",
  "solicitation": {...}
}
```

### 2. Competitive Intelligence
Analyze which competitors are best positioned for an opportunity:
```bash
# Run pipeline on all companies
POST /api/full-pipeline
{
  "solicitation": {...},
  "top_k": 10
}
```

### 3. Capability Gap Analysis
Identify what's missing from your company profile:
```bash
# Review validation_result.weaknesses and recommended_actions
```

### 4. Due Diligence
Verify company claims before teaming agreements:
```bash
# Enrich and confirm specific company
POST /api/match-with-confirmation
{
  "company_id": "partner-company-id",
  "solicitation": {...}
}
```

## 📁 Project Structure

```
nof1/
├── app.py                      # Main FastAPI application with all endpoints
├── data_sources.py             # Modules 1-3: External API integrations
├── confirmation_engine.py      # Module 5: Confirmation analysis
├── validation_engine.py        # Module 6: Final validation and scoring
├── requirements.txt            # Python dependencies
├── config.json.example         # Example configuration file
├── config.json                 # Your API keys (create from example)
├── README.md                   # This file
├── base                        # Original design document
├── nof1.db                     # SQLite database (created on first run)
└── weights.yaml               # Optional: Custom matching weights
```

## 🔐 Security & Privacy

- API keys are stored in `config.json` (excluded from git via `.gitignore`)
- All external API calls are logged
- Company data is stored locally in SQLite
- No data is shared with external services except for enrichment queries

## 🧪 Example Response

Full pipeline response includes:

```json
{
  "solicitation_summary": {...},
  "companies_evaluated": 10,
  "top_matches_analyzed": 5,
  "results": [
    {
      "company_name": "Aegis Cyber Solutions",
      "match_score": 0.87,
      "confirmation_score": 0.82,
      "validation_score": 0.85,
      "validation_level": "excellent",
      "risk_level": "low",
      "recommendation": "✓ STRONGLY RECOMMEND - Proceed with proposal",
      "strengths": [
        "NAICS match",
        "Capabilities aligned",
        "Secret clearance confirmed",
        "Past DoD contracts verified"
      ],
      "weaknesses": [],
      "opportunities": [
        "Strong strategic alignment for long-term partnership"
      ],
      "risks": [],
      "recommended_actions": [
        "Prepare proposal highlighting confirmed strengths",
        "Gather supporting documentation for past performance"
      ],
      "decision_rationale": "..."
    }
  ]
}
```

## 🚀 Advanced Features

### Custom Matching Weights

Adjust the importance of different matching factors:

```bash
curl -X PUT http://localhost:8000/api/weights \
  -H "Content-Type: application/json" \
  -d '{
    "naics": 0.25,
    "capabilities": 0.30,
    "past_performance": 0.20,
    "size_status": 0.10,
    "clearance": 0.10,
    "location": 0.03,
    "keywords": 0.02
  }'
```

### Database Migration

To use PostgreSQL instead of SQLite:

```bash
export DATABASE_URL="postgresql://user:password@localhost/nof1"
uvicorn app:app --reload
```

## 📚 Data Source Details

### Government Databases
- **USASpending.gov**: 20+ million federal contracts
- **NIH Reporter**: $40+ billion in annual grants
- **SBIR.gov**: 200,000+ innovation awards

### AI Analysis
- **Claude**: Deep capability and market analysis
- **ChatGPT**: Company profiling and technical assessment

### Company Intelligence
- **Google**: Web presence and reputation
- **HubSpot**: Internal relationship history
- **USPTO**: Patent portfolio analysis

## 🐛 Troubleshooting

### API Key Issues
```
Error: "API key not configured"
```
**Solution**: Create `config.json` from `config.json.example` and add your API keys

### Import Errors
```
ModuleNotFoundError: No module named 'anthropic'
```
**Solution**: Run `pip install -r requirements.txt`

### Slow Performance
- External API calls can take 5-15 seconds per company
- Use `enrich: false` for faster results (no external data)
- Consider caching enrichment results

## 🤝 Contributing

This is a custom application. To extend:

1. Add new data sources in `data_sources.py`
2. Enhance confirmation logic in `confirmation_engine.py`
3. Adjust validation criteria in `validation_engine.py`
4. Update matching weights in `app.py`

## 📄 License

Internal use MVP/demo application.

## 🎓 Support

For questions or issues:
- Check the interactive API docs at `/docs`
- Review the code comments in each module
- Test with sample data using `/seed` endpoint

---

**Version 2.0** - Enhanced with Confirmation & Validation Engines  
Built for intelligent government contracting opportunity analysis
