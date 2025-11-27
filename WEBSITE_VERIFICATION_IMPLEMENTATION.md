# Website Verification and Match Score Enhancement

## Overview

This document describes the implementation of deep website crawl verification and contextual solicitation alignment analysis that updates match scores based on website content verification.

## Implementation Details

### 1. Deep Website Crawling

The `WebsiteValidator` class (`website_validator.py`) performs comprehensive multi-page website crawling:

- **Crawl Depth**: Up to 3 levels deep from the homepage
- **Page Limit**: Up to 10 pages per website
- **Content Extraction**: From each page:
  - Title and meta descriptions
  - Main body text (up to 5,000 chars per page)
  - Headings (H1, H2, H3)
  - Services/capabilities sections
  - About sections
  - Keywords from meta tags

- **Link Prioritization**: Prioritizes crawling important pages (services, capabilities, solutions, about, expertise, technology)

- **Data Aggregation**: Combines content from all crawled pages into a comprehensive dataset:
  - Combined main text (up to 20,000 characters)
  - All unique headings (up to 50)
  - Combined services and about sections
  - Unique keywords (up to 30)

### 2. Solicitation Alignment Analysis

The `_analyze_solicitation_alignment()` method performs deep contextual analysis:

**AI-Powered Analysis** (when OpenAI API key is available):
- Analyzes all crawled website content against solicitation requirements
- Evaluates:
  - Required capabilities match/mismatch
  - Technical requirements alignment
  - Problem area coverage
  - Overall alignment score (0.0 to 1.0)
- Returns structured JSON with:
  - `overall_alignment_score`: Overall match quality (0.0-1.0)
  - `capability_matches`: List of confirmed capabilities with evidence
  - `capability_gaps`: List of missing capabilities with severity
  - `problem_area_coverage`: Coverage scores for each problem area
  - `technical_evidence`: Specific technical evidence found
  - `confidence`: Analysis confidence level

**Keyword-Based Fallback** (when AI unavailable):
- Performs keyword matching across all crawled content
- Calculates alignment score based on capability matches
- Identifies capability gaps

### 3. Match Score Updates

The `/api/match-with-confirmation` endpoint now:

1. **Performs Deep Website Verification**:
   - Crawls company website (multiple pages)
   - Analyzes website content against solicitation requirements
   - Calculates solicitation alignment score

2. **Updates Match Score Based on Website Verification**:
   - **Website Alignment Boost/Penalty**: 
     - Base adjustment: `(alignment_score - 0.5) * 0.2` (±10% max)
     - High alignment (>0.8): Additional +5% boost
     - Low alignment (<0.3): Additional -10% penalty
   
   - **Unverified Websites**:
     - No website or inaccessible: -5% penalty
     - No website URL: -10% penalty

3. **Returns Enhanced Results**:
   - `match_score`: Updated score with website verification
   - `original_match_score`: Original score before website verification
   - `website_verified`: Boolean indicating if website was verified
   - `website_alignment_score`: Solicitation alignment score (0.0-1.0)
   - `website_validation`: Detailed validation data including:
     - `accessible`: Whether website was accessible
     - `pages_crawled`: Number of pages crawled
     - `validation_score`: Overall validation score
     - `solicitation_alignment`: Full alignment analysis
     - `capability_matches`: Confirmed capabilities from website
     - `capability_gaps`: Missing capabilities identified

### 4. Integration Points

**Confirmation Engine** (`confirmation_engine.py`):
- Always performs website validation for all matches
- Creates a `website_validation` confirmation factor
- Includes website validation results in `ConfirmationResult`

**Match Endpoint** (`app.py`):
- Extracts website validation from confirmation results
- Calculates solicitation alignment score
- Adjusts match scores based on website verification
- Returns comprehensive website verification data

## Score Adjustment Formula

```
Base Match Score = Original matching engine score

If website verified and accessible:
  alignment_score = solicitation_alignment.overall_alignment_score
  website_boost = (alignment_score - 0.5) * 0.2  # ±10% range
  adjusted_score = base_score + website_boost
  
  If alignment_score >= 0.8:
    adjusted_score += 0.05  # +5% bonus
  Else if alignment_score < 0.3:
    adjusted_score -= 0.1    # -10% penalty

Else (no website or inaccessible):
  adjusted_score = base_score * 0.95  # -5% penalty
  If no website URL:
    adjusted_score = base_score * 0.90  # -10% penalty

Final Score = clamp(adjusted_score, 0.0, 1.0)
```

## Benefits

1. **Enhanced Accuracy**: Match scores now reflect real-world website verification
2. **Contextual Alignment**: Deep analysis ensures website content aligns with solicitation requirements
3. **Comprehensive Coverage**: Multi-page crawling captures full company capabilities
4. **Transparency**: Detailed alignment data helps users understand match quality
5. **Confidence Boosting**: High alignment scores boost confidence in matches
6. **Risk Mitigation**: Low alignment scores flag potential mismatches

## Example Response

```json
{
  "company_id": "abc-123",
  "company_name": "Example Corp",
  "match_score": 0.87,  // Updated with website verification
  "original_match_score": 0.82,  // Original before verification
  "website_verified": true,
  "website_alignment_score": 0.85,
  "website_validation": {
    "accessible": true,
    "pages_crawled": 7,
    "validation_score": 0.82,
    "solicitation_alignment": {
      "overall_alignment_score": 0.85,
      "capability_matches": [
        {
          "capability": "Cloud Computing",
          "evidence": "Found extensive AWS and Azure experience on services page",
          "confidence": 0.9
        }
      ],
      "capability_gaps": [
        {
          "capability": "Machine Learning",
          "reason": "Not found in website content",
          "severity": 0.7
        }
      ]
    }
  }
}
```

## Configuration

- **Max Pages**: Configurable via `WebsiteValidator(max_pages=10)`
- **Max Depth**: Configurable via `WebsiteValidator(max_depth=3)`
- **OpenAI API**: Required for advanced AI-powered alignment analysis (falls back to keyword matching if unavailable)

## Anti-Hallucination Safeguards

The system includes comprehensive safeguards to prevent hallucinations and ensure only verified content is used:

### 1. Content Validation Checks

Before using any website content for scoring, the system validates:

- **Minimum Content Requirements**:
  - At least 200 characters of main text
  - At least 500 characters total content
  - At least 2 headings
  - At least 1 successfully crawled page

- **Boilerplate Detection**:
  - Rejects pages with "coming soon", "under construction", "404", etc.
  - Checks for meaningful content vs. empty/minimal pages

- **Content Quality Checks**:
  - Word diversity ratio (must be >30% unique words)
  - Rejects repetitive or low-quality content

### 2. Hallucination Detection

The AI alignment analysis includes multiple hallucination detection checks:

- **Capability Match Verification**: 
  - Verifies that AI-identified capabilities actually appear in website content
  - Penalizes matches without evidence in crawled pages
  - Checks for specific website references in evidence

- **Evidence Quality Checks**:
  - Detects vague/boilerplate evidence ("generally", "likely", "may")
  - Verifies technical evidence is specific and plausible
  - Flags generic evidence patterns

- **Score Reasonableness**:
  - Detects high alignment scores with minimal content (likely hallucinated)
  - Validates that content was verified before analysis
  - Checks for content validation flags

### 3. Penalties Applied

**Unverified Content Penalty**:
- If content fails validation: Website marked as inaccessible
- If content not verified: -30% match score penalty
- Prevents using unverified data for scoring

**Hallucination Penalty**:
- Detected hallucinations: Up to 30% reduction in match score
- Applied to alignment score: Reduces overall alignment by penalty amount
- Logged warnings for transparency

**Content Verification Requirements**:
- Website must pass content validation before use
- AI analysis must verify content before generating alignment
- Both checks must pass for website verification to count

### 4. Safeguard Flow

```
1. Crawl Website
   ↓
2. Validate Content Quality
   ├─ Pass → Continue
   └─ Fail → Reject (mark as inaccessible)
   ↓
3. Extract Capabilities
   ↓
4. Analyze Solicitation Alignment (AI)
   ↓
5. Detect Hallucinations
   ├─ Low Penalty → Use with minor adjustment
   └─ High Penalty → Apply significant reduction
   ↓
6. Verify Content Confirmation
   ├─ Verified → Use for scoring
   └─ Unverified → Apply -30% penalty
```

## Performance Considerations

- Deep crawling adds latency (typically 5-15 seconds per company)
- Crawling is performed asynchronously to avoid blocking
- Rate limiting: 0.5 second delay between page requests
- Timeout: 15 seconds per page, 20 seconds total per website
- Content validation adds minimal overhead (~100ms)

