# Match Score Algorithm

## Overview
The Match Score shows how well a company aligns with the solicitation requirements. It's calculated using a weighted algorithm that evaluates multiple factors.

## Scoring Components

### 1. Technical Capability Match (40% weight)
**What it measures:** Does the company have the required technical skills?

**How it works:**
- Extracts technical capabilities from solicitation (e.g., "biosensors & diagnostics", "vaccine & therapeutics")
- Searches company description, capabilities, and profile for these terms
- Score = (Number of matching capabilities / Total required capabilities) × 0.4

**Example:**
- Solicitation needs: biosensors, vaccine development, IoT monitoring
- Company profile mentions: "biosensor technology", "vaccine research"
- Match: 2 out of 3 capabilities = 67% × 0.4 = **26.7% of final score**

### 2. Problem Area Alignment (30% weight)
**What it measures:** Does the company address the specific problems mentioned in the solicitation?

**How it works:**
- Extracts key problems/challenges from solicitation
- Identifies important keywords from these problems (nouns, technical terms)
- Checks if company profile addresses these problems
- Score = (Matching problem keywords / Total problem keywords) × 0.3

**Example:**
- Solicitation problems: "early pathogen detection", "disease surveillance", "automated decontamination"
- Company mentions: "pathogen", "detection", "surveillance", "diagnostic"
- Match: 4 out of 8 keywords = 50% × 0.3 = **15% of final score**

### 3. Keyword Coverage (20% weight)
**What it measures:** How many of the search keywords appear in the company profile?

**How it works:**
- Uses the extracted search keywords from solicitation analysis
- Counts how many appear in company name, description, capabilities
- Score = (Matching keywords / Total keywords) × 0.2

**Example:**
- Keywords: agriculture, animal health, biosecurity, poultry, avian
- Company profile contains: "animal health", "biosecurity", "poultry"
- Match: 3 out of 5 keywords = 60% × 0.2 = **12% of final score**

### 4. Source Credibility (10% weight)
**What it measures:** How credible is the company data?

**How it works:**
- Multiple data sources = higher credibility
- Base confidence from search API
- Score = (Number of sources × 2%) + (Base confidence × 5%), capped at 10%

**Example:**
- Found via: ChatGPT search
- Base confidence: 85%
- Score: (1 source × 2%) + (0.85 × 5%) = **6.25% of final score**

## Total Score Calculation

**Final Match Score = Sum of all components (capped at 100%)**

### Complete Example: Poultry Biosecurity Company

| Component | Calculation | Score |
|-----------|-------------|-------|
| Technical Capabilities | 3/4 matches × 0.4 | 30.0% |
| Problem Alignment | 6/10 keywords × 0.3 | 18.0% |
| Keyword Coverage | 4/6 keywords × 0.2 | 13.3% |
| Source Credibility | 1 source + 85% confidence | 6.3% |
| **TOTAL MATCH SCORE** | | **67.6%** |

## Score Interpretation

- **80-100%**: Excellent match - Company strongly aligns with all requirements
- **60-79%**: Good match - Company meets most requirements with minor gaps
- **40-59%**: Fair match - Company has relevant experience but missing some requirements
- **20-39%**: Borderline match - Company has limited alignment
- **0-19%**: Poor match - Company doesn't align with requirements

## What Makes a High Score?

1. ✅ Company profile explicitly mentions the technical capabilities needed
2. ✅ Company description addresses the specific problems/challenges
3. ✅ Company has relevant keywords in their business description
4. ✅ Company found through multiple credible sources

## What Lowers the Score?

1. ❌ Generic company description without specific technical terms
2. ❌ No mention of problem areas from solicitation
3. ❌ Few matching keywords
4. ❌ Limited data sources / low confidence

## Algorithm Benefits

- **Transparent**: Each component has a clear weight and purpose
- **Balanced**: No single factor dominates (largest weight is 40%)
- **Domain-agnostic**: Works for any solicitation type (biotech, IT, manufacturing, etc.)
- **Fair**: Companies get partial credit for partial matches
- **Explainable**: Can show why a company scored high or low

