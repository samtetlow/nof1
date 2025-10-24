# 📋 Changelog - N of 1 Platform

## Version 2.1.0 (October 24, 2025)

### 🎯 Major Feature: Redesigned Solicitation Input

#### New Capabilities

**1. Drag & Drop File Upload**
- Visual drop zone with hover states
- Supports TXT, PDF, DOC, DOCX (up to 10MB)
- Automatic parsing on file drop
- Real-time file name display
- Clear visual feedback throughout

**2. URL Fetching**
- Paste SAM.gov or FedBizOpps URLs directly
- Automatic content extraction via HTTP
- HTML parsing with BeautifulSoup4
- Cleans scripts, styles, and whitespace
- Returns both raw text and parsed fields

**3. Enhanced Auto-Parsing**
- Extracts 8+ key fields automatically:
  - Solicitation ID/number
  - Title
  - Agency
  - NAICS codes (multiple)
  - Set-asides (multiple)
  - Security clearance requirements
  - Required capabilities (technical keywords)
  - General keywords (frequency analysis)
- Regex-based extraction patterns
- Intelligent stop-word filtering
- Context-aware field detection

#### UI/UX Improvements

**Progressive Disclosure**
- Step-by-step interface (1-2-3-4)
- Collapsible refinement section
- Default to most common workflow
- Hide complexity until needed

**Visual Feedback**
- Success banners (green) for parsed data
- Loading states during fetch/parse
- File name display with clear button
- Toggle buttons for input modes
- Progress indicators

**Smart Defaults**
- Upload/Drag & Drop is default mode
- Auto-parse on file upload
- Pre-filled fields after parsing
- Suggested configurations

#### Backend Additions

**New API Endpoint**
```
POST /api/solicitations/fetch-url
```
- Accepts: `{"url": "https://..."}`
- Returns: `{"success": true, "text": "...", "parsed": {...}}`
- Uses `httpx` for async HTTP
- Uses `BeautifulSoup4` for HTML parsing
- Error handling with helpful suggestions

**Enhanced Parser Function**
```python
def parse_solicitation_text(text: str) -> Dict[str, Any]
```
- Multiple regex patterns per field type
- Fallback strategies for each field
- Technical keyword extraction
- Frequency-based keyword analysis
- Stop-word filtering
- Character limits for safety

#### Dependencies Added
```
beautifulsoup4==4.12.2  # HTML parsing
```

#### Files Modified
- `frontend/src/components/SolicitationForm.tsx` - Complete redesign
- `frontend/src/services/api.ts` - Added `fetchSolicitationFromUrl()`
- `app.py` - Added `/api/solicitations/fetch-url` endpoint
- `requirements.txt` - Added beautifulsoup4

#### Documentation Created
- `UPDATED_INPUT_GUIDE.md` - Comprehensive guide for new features
- `QUICK_REFERENCE.md` - One-page quick reference card
- `CHANGELOG.md` - This file

#### Documentation Updated
- `README.md` - Updated features list and quick start

---

## Version 2.0.0 (October 23, 2025)

### 🚀 Major Release: Full React Frontend

#### New Features
- Complete React/TypeScript frontend
- Tailwind CSS styling
- Dashboard with tabs
- Real-time analysis results
- Company management interface
- Score visualizations
- Interactive API documentation link

#### Components Created
- `Dashboard.tsx` - Main container
- `SolicitationForm.tsx` - Input form
- `ResultsDisplay.tsx` - Results viewer
- `CompanyManager.tsx` - Company CRUD
- `ScoreVisualization.tsx` - Charts and graphs

---

## Version 1.5.0 (October 22, 2025)

### ✨ Enhanced with Validation Engine

#### New Modules
- **Validation Engine** - Final scoring and recommendations
  - Comprehensive risk assessment
  - SWOT analysis
  - Go/no-go decisions
  - Action items

#### Files Created
- `validation_engine.py`
- `ARCHITECTURE.md`
- `IMPLEMENTATION_SUMMARY.md`

---

## Version 1.0.0 (October 21, 2025)

### 🎉 Initial Release

#### Core Features
- FastAPI backend
- SQLite database
- Company management
- Solicitation parsing
- Matching engine (7 factors)
- Confirmation engine
- Data source integrations

#### Supported Data Sources
- Google Custom Search
- Claude AI
- ChatGPT
- USASpending.gov
- NIH Reporter
- SBIR.gov
- USPTO
- HubSpot
- Pitchbook
- AngelList

---

## Upgrade Path

### From 2.0.x to 2.1.0
1. Pull latest changes
2. Install new dependency:
   ```bash
   pip install beautifulsoup4==4.12.2
   ```
3. Restart backend:
   ```bash
   pkill -f "uvicorn app:app"
   uvicorn app:app --reload
   ```
4. Frontend updates automatically (hot reload)

### From 1.x to 2.0
1. Pull latest changes
2. Install frontend dependencies:
   ```bash
   cd frontend
   npm install
   ```
3. Start frontend:
   ```bash
   npm start
   ```

---

## Known Issues

### Version 2.1.0
- URL fetching may fail for pages requiring authentication
- PDF parsing quality depends on PDF structure
- Some SAM.gov pages have dynamic content (use file upload as fallback)

### Workarounds
- **Protected URLs**: Download file manually, use drag & drop
- **Poor PDF extraction**: Copy text manually, paste as raw text
- **Dynamic content**: Use browser DevTools to copy rendered HTML

---

## Roadmap

### Version 2.2.0 (Planned)
- [ ] Batch file upload (multiple solicitations)
- [ ] Export results to Excel/PDF
- [ ] Save analysis history
- [ ] Email notifications
- [ ] Custom weighting UI

### Version 2.3.0 (Planned)
- [ ] Real-time SAM.gov integration
- [ ] Automated daily scans
- [ ] Company profile builder
- [ ] Team collaboration features
- [ ] Advanced filtering

### Version 3.0.0 (Planned)
- [ ] Machine learning for better matching
- [ ] Historical performance tracking
- [ ] Predictive analytics
- [ ] Mobile app
- [ ] Multi-tenant support

---

## Migration Notes

### Breaking Changes (2.1.0)
- None - fully backward compatible

### Deprecations
- None yet

### Security Updates
- None in this release

---

## Contributors
- Sam Tetlow - Product Owner & Lead Developer
- AI Assistant (Claude) - Code Generation & Documentation

---

## Support
For issues, questions, or feature requests, please see:
- `README.md` - Full documentation
- `QUICK_REFERENCE.md` - Quick start guide
- `UPDATED_INPUT_GUIDE.md` - Input feature details
- API Docs: http://localhost:8000/docs


