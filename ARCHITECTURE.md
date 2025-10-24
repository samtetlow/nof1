# N-of-1 Platform Architecture

## System Overview

The N-of-1 platform is a comprehensive government contracting opportunity matching system that uses a 6-module pipeline to evaluate company-solicitation alignment.

## Module Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     SOLICITATION INPUT                          │
│           (Raw text or structured requirements)                 │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│  MODULE 1-3: DATA SOURCE INTEGRATIONS (data_sources.py)        │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Google     │  │    Claude    │  │   ChatGPT    │         │
│  │   Search     │  │     AI       │  │     AI       │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ USASpending  │  │NIH Reporter │  │   SBIR.gov   │         │
│  │    .gov      │  │   Grants    │  │   Awards     │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   HubSpot    │  │  Pitchbook   │  │   USPTO      │         │
│  │     CRM      │  │   (Manual)   │  │   Patents    │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                  │
│  Output: EnrichmentResult objects with confidence scores        │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│  MODULE 4: MATCHING ENGINE (app.py - MatchingEngine class)     │
│                                                                  │
│  Scoring Dimensions (Weighted):                                 │
│  ┌─────────────────────────────────────────────────────┐       │
│  │ • NAICS Alignment              (20%)                │       │
│  │ • Capabilities Match           (25%)                │       │
│  │ • Past Performance             (20%)                │       │
│  │ • Size Status Compliance       (10%)                │       │
│  │ • Security Clearance           (10%)                │       │
│  │ • Location Alignment           (5%)                 │       │
│  │ • Keyword Overlap              (10%)                │       │
│  └─────────────────────────────────────────────────────┘       │
│                                                                  │
│  Hard Requirements:                                              │
│  • Set-aside compliance (caps at 0.49 if not met)              │
│  • Security clearance (caps at 0.49 if missing)                │
│                                                                  │
│  Output: Match score + strengths + gaps                         │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│  MODULE 5: CONFIRMATION ENGINE (confirmation_engine.py)         │
│                                                                  │
│  Confirmation Factors:                                          │
│  ┌─────────────────────────────────────────────────────┐       │
│  │ 1. Past Performance Confirmation                    │       │
│  │    → USASpending contracts                          │       │
│  │    → NIH grants                                     │       │
│  │    → SBIR awards                                    │       │
│  │                                                      │       │
│  │ 2. Capability Verification                          │       │
│  │    → AI analysis (Claude/ChatGPT)                   │       │
│  │    → Google search validation                       │       │
│  │    → HubSpot internal data                          │       │
│  │                                                      │       │
│  │ 3. Certification Validation                         │       │
│  │    → SBIR (confirms small business)                 │       │
│  │    → Size indicators                                │       │
│  │                                                      │       │
│  │ 4. Size & Clearance Confirmation                    │       │
│  │    → Employee count validation                      │       │
│  │    → Past classified work                           │       │
│  │                                                      │       │
│  │ 5. Market Presence Assessment                       │       │
│  │    → Web presence (Google)                          │       │
│  │    → Patents (USPTO)                                │       │
│  │    → Funding data                                   │       │
│  │                                                      │       │
│  │ 6. Technical Expertise Verification                 │       │
│  │    → Patent alignment                               │       │
│  │    → Research track record                          │       │
│  │    → SBIR Phase II achievements                     │       │
│  └─────────────────────────────────────────────────────┘       │
│                                                                  │
│  Output: ConfirmationResult with status + confidence + evidence │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│  MODULE 6: VALIDATION ENGINE (validation_engine.py)             │
│                                                                  │
│  Validation Components (Weighted):                              │
│  ┌─────────────────────────────────────────────────────┐       │
│  │ • Match Quality               (30%)                 │       │
│  │ • Confirmation Quality        (25%)                 │       │
│  │ • Data Reliability            (15%)                 │       │
│  │ • Risk Assessment             (15%)                 │       │
│  │ • Strategic Fit               (15%)                 │       │
│  └─────────────────────────────────────────────────────┘       │
│                                                                  │
│  Risk Analysis:                                                 │
│  • Past performance gaps                                        │
│  • Capability mismatches                                        │
│  • Clearance issues                                             │
│  • Set-aside non-compliance                                     │
│  • Data quality concerns                                        │
│  • Capacity constraints                                         │
│                                                                  │
│  SWOT Generation:                                               │
│  • Strengths (from confirmations)                               │
│  • Weaknesses (from gaps)                                       │
│  • Opportunities (strategic alignment)                          │
│  • Threats (identified risks)                                   │
│                                                                  │
│  Output: ValidationResult with final score + recommendation     │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                      FINAL OUTPUT                                │
│                                                                  │
│  • Validation Score (0.0 - 1.0)                                 │
│  • Validation Level (Excellent → Rejected)                      │
│  • Risk Level (Low → Critical)                                  │
│  • Go/No-Go Recommendation                                      │
│  • Detailed SWOT Analysis                                       │
│  • Recommended Actions                                          │
│  • Decision Rationale                                           │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

### Input Layer
- **Solicitation Data**: Requirements, NAICS, set-asides, clearances
- **Company Database**: Internal profiles with capabilities
- **Configuration**: API keys, matching weights

### Processing Layer

#### 1. Data Enrichment (Modules 1-3)
```python
DataSourceManager.enrich_company_all_sources()
  ├─ Google: Web presence validation
  ├─ Claude/ChatGPT: AI-powered analysis
  ├─ USASpending: Federal contracts
  ├─ NIH Reporter: Research grants
  ├─ SBIR: Innovation awards
  ├─ HubSpot: Internal CRM data
  └─ USPTO: Patent portfolio
```

#### 2. Matching (Module 4)
```python
MatchingEngine.score()
  ├─ Calculate dimension scores
  ├─ Apply weights
  ├─ Check hard requirements
  └─ Generate strengths/gaps
```

#### 3. Confirmation (Module 5)
```python
ConfirmationEngine.confirm_match()
  ├─ Verify each factor with enriched data
  ├─ Build evidence lists
  ├─ Identify contradictions
  └─ Calculate overall confidence
```

#### 4. Validation (Module 6)
```python
ValidationEngine.validate()
  ├─ Evaluate all components
  ├─ Assess risks
  ├─ Generate SWOT
  ├─ Calculate final score
  └─ Produce recommendation
```

### Output Layer
- **JSON Response**: Comprehensive analysis
- **Database Storage**: Match history (optional)
- **Action Items**: Next steps for user

## API Architecture

### RESTful Endpoints

```
GET  /                          # API info
GET  /docs                      # Interactive documentation

# Company Management
POST /api/companies             # Create company
GET  /api/companies/{id}        # Get company
GET  /api/companies/search      # Search companies

# Solicitation Management
POST /api/solicitations         # Create solicitation
POST /api/solicitations/parse   # Parse raw text
GET  /api/solicitations/{id}    # Get solicitation

# Basic Matching (Module 4 only)
POST /api/match                 # Traditional matching

# Enhanced Pipeline
POST /api/enrich-company        # Modules 1-3 only
POST /api/match-with-confirmation  # Modules 4-5
POST /api/full-pipeline         # Modules 1-6 (COMPLETE)

# Configuration
GET  /api/weights               # Get matching weights
PUT  /api/weights               # Update weights
POST /seed                      # Load sample data
```

## Data Models

### Core Models

```python
# Company Profile
CompanyORM
  ├─ company_id (PK)
  ├─ name
  ├─ naics_codes (JSON)
  ├─ capabilities (JSON)
  ├─ socioeconomic_status (JSON)
  ├─ security_clearances (JSON)
  ├─ size
  └─ ... (15+ fields)

# Solicitation
SolicitationORM
  ├─ job_id (PK)
  ├─ solicitation_id
  ├─ naics_codes (JSON)
  ├─ set_asides (JSON)
  ├─ required_capabilities (JSON)
  ├─ security_clearance
  └─ ... (17+ fields)

# Past Contracts
PastContractORM
  ├─ id (PK)
  ├─ company_id (FK)
  ├─ agency
  ├─ value_usd
  └─ ...
```

### Result Models

```python
# Module 4 Output
MatchResult
  ├─ score (float)
  ├─ strengths (List[str])
  ├─ gaps (List[str])
  └─ recommendation (str)

# Module 5 Output
ConfirmationResult
  ├─ overall_status (ConfirmationStatus)
  ├─ overall_confidence (float)
  ├─ factors (List[ConfirmationFactor])
  ├─ summary (str)
  └─ enrichment_sources_used (List[str])

# Module 6 Output
ValidationResult
  ├─ validation_score (float)
  ├─ validation_level (ValidationLevel)
  ├─ risk_level (RiskLevel)
  ├─ recommendation (str)
  ├─ strengths/weaknesses/opportunities/risks
  ├─ recommended_actions (List[str])
  └─ decision_rationale (str)
```

## Configuration

### Environment Variables
```bash
DATABASE_URL=sqlite:///./nof1.db
CONFIG_PATH=./config.json
WEIGHTS_PATH=./weights.yaml
```

### Config File (config.json)
```json
{
  "data_sources": {
    "google": {"api_key": "..."},
    "claude": {"api_key": "..."},
    "chatgpt": {"api_key": "..."},
    "hubspot": {"api_key": "..."}
  }
}
```

## Scoring Thresholds

### Match Score (Module 4)
- **0.75+**: Recommended
- **0.50-0.74**: Borderline
- **< 0.50**: Not Recommended

### Validation Level (Module 6)
- **0.85+**: Excellent
- **0.70-0.84**: Good
- **0.55-0.69**: Acceptable
- **0.40-0.54**: Marginal
- **0.25-0.39**: Poor
- **< 0.25**: Rejected

### Risk Level
- **Low**: < 3 risks, score > 0.7
- **Medium**: 3-4 risks, score 0.5-0.7
- **High**: 5+ risks, score 0.3-0.5
- **Critical**: Critical issues (clearance, set-aside)

## Async Processing

The pipeline uses `async/await` for:
- Parallel API calls to data sources
- Non-blocking I/O operations
- Efficient processing of multiple companies

```python
# Concurrent enrichment
results = await asyncio.gather(
    google_source.enrich(),
    claude_source.enrich(),
    usaspending_source.enrich(),
    ...
)
```

## Error Handling

Each module gracefully handles:
- Missing API keys (continues with available sources)
- API failures (logs error, continues processing)
- Missing data (adjusts confidence scores)
- Invalid inputs (HTTP 400 responses)

## Performance Considerations

- **Enrichment**: 5-15 seconds per company (parallel API calls)
- **Matching**: < 100ms per company
- **Confirmation**: < 1 second (processes enrichment results)
- **Validation**: < 1 second (final calculations)

**Total Pipeline**: ~10-20 seconds per company with full enrichment

## Security

- API keys stored in config.json (gitignored)
- No external data sharing beyond enrichment queries
- Local SQLite database for sensitive company data
- Optional PostgreSQL for production deployment

## Extensibility

### Adding New Data Sources
1. Create class inheriting from `DataSourceBase`
2. Implement `enrich_company()` and `search_contracts()`
3. Add to `DataSourceManager._initialize_sources()`
4. Add API key to config.json

### Adding Confirmation Factors
1. Add new method in `ConfirmationEngine`
2. Add factor to `confirm_match()` workflow
3. Update weights in `__init__()`

### Adding Validation Components
1. Add new method in `ValidationEngine`
2. Add component to `validate()` workflow
3. Update weights in `__init__()`

## Deployment

### Development
```bash
uvicorn app:app --reload
```

### Production
```bash
gunicorn app:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Docker (Future)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Testing Strategy

### Unit Tests (Future)
- Individual module scoring
- Data source parsing
- Edge cases

### Integration Tests (Future)
- Full pipeline flow
- API endpoint responses
- Database operations

### Manual Testing
```bash
# Test with sample data
curl -X POST http://localhost:8000/seed
curl -X POST http://localhost:8000/api/full-pipeline -d @test_solicitation.json
```

## Monitoring & Logging

- Request logging (FastAPI middleware)
- Module execution timing
- API call success rates
- Error tracking

```python
logger.info(f"Processing {company.name} through full pipeline")
logger.error(f"Google search error for {company_name}: {e}")
```

## Future Enhancements

1. **Caching Layer**: Redis for enrichment results
2. **Batch Processing**: Queue system for bulk analysis
3. **ML Models**: Replace rule-based scoring with ML
4. **Real-time Updates**: WebSocket for live results
5. **Advanced Analytics**: Historical trend analysis
6. **Custom Reporting**: PDF generation for proposals
7. **Team Collaboration**: User accounts and permissions
8. **SAM.gov Integration**: Direct solicitation ingestion

---

**Architecture Version**: 2.0  
**Last Updated**: October 2025


