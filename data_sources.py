"""
Data source integrations for the N-of-1 platform.
Connects to external APIs and databases for company and contract data.
"""

import logging
import re
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel
import json

# Import external libraries with error handling
try:
    import httpx
except ImportError:
    httpx = None

try:
    import anthropic
except ImportError:
    anthropic = None

try:
    import openai
except ImportError:
    openai = None

logger = logging.getLogger(__name__)


class EnrichmentResult(BaseModel):
    """Result from enriching company data with external sources"""
    company_name: str
    data_sources: List[str]
    enrichment_data: Dict[str, Any]
    confidence_score: float
    last_updated: datetime


class DataSourceManager:
    """Manages connections to external data sources"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize data source connections based on config"""
        self.config = config
        self.sources = {}
        self._initialize_sources()
    
    def _initialize_sources(self):
        """Initialize available data sources"""
        # ChatGPT/OpenAI
        if self.config.get("chatgpt", {}).get("api_key"):
            logger.info("Enabling ChatGPT data source")
            self.sources["chatgpt"] = ChatGPTSource(
                api_key=self.config["chatgpt"]["api_key"],
                model=self.config["chatgpt"].get("model", "gpt-3.5-turbo")
            )
        
        # Google Custom Search
        if self.config.get("google", {}).get("api_key"):
            logger.info("Enabling Google data source")
            self.sources["google"] = GoogleSource(
                api_key=self.config["google"]["api_key"],
                search_engine_id=self.config["google"].get("search_engine_id")
            )
        
        # Claude/Anthropic
        if self.config.get("claude", {}).get("api_key"):
            logger.info("Enabling Claude data source")
            self.sources["claude"] = ClaudeSource(
                api_key=self.config["claude"]["api_key"]
            )
        
        # Pitchbook
        if self.config.get("pitchbook", {}).get("api_key"):
            logger.info("Enabling Pitchbook data source")
            self.sources["pitchbook"] = PitchbookSource(
                api_key=self.config["pitchbook"]["api_key"]
            )
        
        # HubSpot
        if self.config.get("hubspot", {}).get("api_key"):
            logger.info("Enabling HubSpot data source")
            self.sources["hubspot"] = HubSpotSource(
                api_key=self.config["hubspot"]["api_key"]
            )
        
        # USASpending.gov (public API, no key required)
        logger.info("Enabling USASpending.gov data source")
        self.sources["usaspending"] = USASpendingSource()
        
        # NIH Reporter (public API)
        logger.info("Enabling NIH Reporter data source")
        self.sources["nih"] = NIHReporterSource()
        
        # SBIR.gov (public API)
        logger.info("Enabling SBIR.gov data source")
        self.sources["sbir"] = SBIRSource()
        
        # USPTO (public API)
        logger.info("Enabling USPTO data source")
        self.sources["uspto"] = USPTOSource()
        
        logger.info(f"Initialized {len(self.sources)} data sources: {list(self.sources.keys())}")
    
    async def enrich_company(self, company_name: str, company_data: Optional[Dict] = None) -> EnrichmentResult:
        """Enrich company data from multiple sources"""
        enrichment_data = {}
        data_sources_used = []
        
        # Query each available source
        for source_name, source in self.sources.items():
            try:
                logger.info(f"Querying {source_name} for {company_name}")
                source_data = await source.get_company_data(company_name, company_data)
                if source_data:
                    enrichment_data[source_name] = source_data
                    data_sources_used.append(source_name)
            except Exception as e:
                logger.error(f"Error querying {source_name}: {e}")
        
        # Calculate confidence based on number of sources and data quality
        confidence = min(len(data_sources_used) * 0.15, 1.0)
        
        return EnrichmentResult(
            company_name=company_name,
            data_sources=data_sources_used,
            enrichment_data=enrichment_data,
            confidence_score=confidence,
            last_updated=datetime.now()
        )
    
    async def search_contracts(self, query: str, filters: Optional[Dict] = None) -> List[Dict]:
        """Search for contracts across data sources"""
        all_results = []
        
        for source_name, source in self.sources.items():
            try:
                if hasattr(source, 'search_contracts'):
                    logger.info(f"Searching contracts in {source_name}")
                    results = await source.search_contracts(query, filters)
                    all_results.extend(results)
            except Exception as e:
                logger.error(f"Error searching {source_name}: {e}")
        
        return all_results


# Individual data source classes

class ChatGPTSource:
    """ChatGPT/OpenAI integration"""
    
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
        if openai is None:
            raise ImportError("openai library not installed")
        self.client = openai.OpenAI(
            api_key=api_key,
            timeout=300.0,  # 5 minute timeout
            max_retries=3  # Retry failed requests up to 3 times
        )
        self.model = model
    
    async def get_company_data(self, company_name: str, company_data: Optional[Dict] = None) -> Dict:
        """Get company insights from ChatGPT"""
        try:
            prompt = f"Provide key information about {company_name} including industry, size, capabilities, and recent activities. Be concise."
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a business intelligence assistant providing factual company information."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300
            )
            
            return {
                "insights": response.choices[0].message.content,
                "model": self.model
            }
        except Exception as e:
            logger.error(f"ChatGPT company data error: {e}")
            return {}
    
    async def search_contracts(self, query: str, filters: Optional[Dict] = None) -> List[Dict]:
        """Use ChatGPT to suggest relevant companies based on themes"""
        try:
            if not filters or not filters.get('themes'):
                logger.warning("No themes provided to ChatGPT search")
                return []
            
            themes = filters.get('themes', {})
            requested_companies = filters.get('max_companies', 10) if filters else 10
            # GPT-4o-mini supports 4096 completion tokens (not 16K!)
            # With ~200 tokens per company + 500 buffer, max is ~18 companies
            # Cap at 18 to stay within token limits
            max_companies = max(1, min(requested_companies, 18))
            if requested_companies > 18:
                logger.warning(f"⚠️ Requested {requested_companies} companies, but capped at 18 due to GPT-4o-mini token limit (4096 max)")
            company_type = filters.get('company_type', 'for-profit') if filters else 'for-profit'
            company_size = filters.get('company_size', 'all') if filters else 'all'
            
            problem_statement = themes.get('problem_statement', '')
            problem_areas = themes.get('problem_areas', []) or []
            key_priorities = themes.get('key_priorities', []) or []
            technical_capabilities = themes.get('technical_capabilities', []) or []
            search_keywords = themes.get('search_keywords', []) or []
            
            # Validation: Ensure we have enough information to search
            if not problem_areas and not search_keywords and not technical_capabilities:
                logger.warning("Insufficient theme data for ChatGPT search")
                return []
            
            # Build type requirement
            type_requirement = ""
            if company_type == "academic-nonprofit":
                type_requirement = "\n\n**CRITICAL TYPE REQUIREMENT: ONLY suggest ACADEMIC INSTITUTIONS, UNIVERSITIES, RESEARCH CENTERS, NON-PROFIT ORGANIZATIONS, or 501(c)(3) entities. This is a strict requirement. DO NOT include for-profit companies, corporations, or commercial contractors.**"
            else:  # for-profit
                type_requirement = "\n\n**CRITICAL TYPE REQUIREMENT: ONLY suggest FOR-PROFIT COMPANIES, CORPORATIONS, or COMMERCIAL CONTRACTORS. This is a strict requirement. DO NOT include academic institutions, universities, non-profits, or research centers.**"
            
            # Build size requirement
            size_requirement = ""
            if company_size == "small":
                size_requirement = "\n\n**CRITICAL SIZE REQUIREMENT: ONLY suggest companies with 500 EMPLOYEES OR FEWER. This is a strict requirement - companies must be small businesses (≤500 employees). Include small business certified companies, SBA 8(a), woman-owned, veteran-owned, or other qualifying small contractors. Absolutely DO NOT include any large corporations, Fortune 500 companies, or firms with more than 500 employees.**"
            elif company_size == "large":
                size_requirement = "\n\n**CRITICAL SIZE REQUIREMENT: ONLY suggest companies with MORE THAN 500 EMPLOYEES. This is a strict requirement - companies must be large businesses (>500 employees). Include Fortune 500, major corporations, large established firms. Absolutely DO NOT include small businesses, startups, or firms with 500 or fewer employees.**"
            else:  # company_size == "all"
                size_requirement = "\n\n**SIZE REQUIREMENT: Include companies of ALL SIZES - both small businesses (≤500 employees) AND large corporations (>500 employees). Provide a diverse mix of company sizes in your suggestions.**"
            
            prompt = f"""You are helping identify companies for a government solicitation. Be VERY SPECIFIC and match companies to the exact domain and requirements below.

SOLICITATION FOCUS:
{problem_statement[:500] if problem_statement else 'Not specified'}

SPECIFIC PROBLEM AREAS (CRITICAL - Match companies to these exact problems):
{chr(10).join([f"• {area}" for area in problem_areas[:5]])}

KEY PRIORITIES:
{chr(10).join([f"• {priority}" for priority in key_priorities[:5]])}

REQUIRED TECHNICAL CAPABILITIES:
{chr(10).join([f"• {cap.get('area', cap) if isinstance(cap, dict) else cap}" for cap in technical_capabilities[:5]])}

SEARCH KEYWORDS: {', '.join(search_keywords[:10])}{type_requirement}{size_requirement}

Based on the EXACT requirements above, suggest EXACTLY {max_companies} REAL companies that specialize in this specific domain. DO NOT suggest generic IT contractors unless they have specific expertise in these areas. YOU MUST return exactly {max_companies} companies - no more, no less.

For each company, provide:
1. Company name (real companies with expertise in THIS specific domain)
2. Brief description (focused on their relevance to THIS solicitation)
3. Why they're a perfect match for THESE specific requirements
4. Website (if known)
5. Key capabilities (matching the requirements above)

Return ONLY a JSON array with fields: name, description, match_reason, website, capabilities
DO NOT include any markdown formatting or code blocks, just the raw JSON array."""
            
            # Calculate max_tokens based on requested companies
            # Rough estimate: ~200 tokens per company entry (name, description, match_reason, website, capabilities)
            # Add 500 buffer for JSON structure
            estimated_tokens = (max_companies * 200) + 500
            # CRITICAL: GPT-4o-mini supports max 4096 completion tokens (not 16K!)
            # Cap at 4096 to avoid API errors
            max_tokens_needed = min(estimated_tokens, 4096)
            
            # If max_tokens would be too high, reduce the number of companies requested
            # Reserve 500 tokens for JSON structure, so we have ~3596 tokens for companies
            # That's about 17-18 companies max (3596 / 200 = ~18)
            max_companies_by_tokens = (max_tokens_needed - 500) // 200
            if max_companies > max_companies_by_tokens:
                logger.warning(f"⚠️ Requested {max_companies} companies but token limit allows only {max_companies_by_tokens} (max_tokens={max_tokens_needed})")
                max_companies = max_companies_by_tokens
                # Recalculate with reduced company count
                estimated_tokens = (max_companies * 200) + 500
                max_tokens_needed = min(estimated_tokens, 4096)
            
            logger.info(f"Using max_tokens={max_tokens_needed} for {max_companies} companies (GPT-4o-mini, capped at 4096)")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert at identifying companies for government contracts. You have deep knowledge of companies across all industries including healthcare, biotech, agriculture, cybersecurity, manufacturing, energy, and more. Be specific and match companies to the exact domain requirements."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens_needed,
                temperature=0.7
            )
            
            content = response.choices[0].message.content.strip()
            
            # Remove markdown code blocks if present
            if content.startswith("```json"):
                content = content[7:]  # Remove ```json
            if content.startswith("```"):
                content = content[3:]  # Remove ```
            if content.endswith("```"):
                content = content[:-3]  # Remove trailing ```
            content = content.strip()
            
            # Validate content before parsing
            if not content or len(content) < 10:
                logger.error("ChatGPT returned empty or invalid response")
                return []
            
            try:
                companies = json.loads(content)
            except json.JSONDecodeError as e:
                logger.error(f"ChatGPT JSON parsing error: {e}")
                logger.error(f"Content preview: {content[:300]}...")
                
                # Try multiple recovery strategies
                # Strategy 1: Extract JSON array
                json_match = re.search(r'\[.*\]', content, re.DOTALL)
                if json_match:
                    try:
                        companies = json.loads(json_match.group(0))
                        logger.info("✓ Successfully extracted JSON from response")
                    except Exception as ex:
                        logger.warning(f"Strategy 1 failed: {ex}")
                        # Strategy 2: Fix common JSON errors (trailing commas, incomplete objects)
                        try:
                            fixed_content = json_match.group(0)
                            # Remove trailing commas before ] or }
                            fixed_content = re.sub(r',\s*([}\]])', r'\1', fixed_content)
                            # Try to find where JSON is incomplete and truncate
                            # Count open vs closed braces
                            open_count = fixed_content.count('{')
                            close_count = fixed_content.count('}')
                            if open_count > close_count:
                                # JSON is incomplete - try to close it
                                logger.info(f"JSON incomplete: {open_count} open braces, {close_count} close braces")
                                # Find the last complete object
                                last_complete = fixed_content.rfind('},')
                                if last_complete > 0:
                                    fixed_content = fixed_content[:last_complete+1] + '\n]'
                                    logger.info("✓ Truncated to last complete object")
                            
                            companies = json.loads(fixed_content)
                            logger.info(f"✓ Successfully fixed and parsed JSON - recovered {len(companies)} companies")
                        except Exception as ex2:
                            logger.error(f"Strategy 2 failed: {ex2}")
                            return []
                else:
                    logger.error("No JSON array found in response")
                    return []
            
            # Validate it's a list
            if not isinstance(companies, list):
                logger.error(f"ChatGPT returned non-list: {type(companies)}")
                return []
            
            logger.info(f"✓ ChatGPT returned valid JSON with {len(companies)} companies")
            
            # Format results
            results = []
            for idx, company in enumerate(companies):
                if not isinstance(company, dict):
                    logger.warning(f"Skipping non-dict company entry: {type(company)}")
                    continue
                
                company_name = company.get('name', '').strip()
                if not company_name:
                    logger.warning(f"Skipping company {idx+1} with empty name")
                    continue
                
                results.append({
                    'name': company_name,  # Use 'name' for consistency
                    'company_name': company_name,
                    'description': company.get('description', '').strip(),
                    'match_reason': company.get('match_reason', '').strip(),
                    'website': company.get('website', '').strip(),
                    'capabilities': company.get('capabilities', []) if isinstance(company.get('capabilities'), list) else [],
                    'source': 'chatgpt',
                    'confidence': 0.7
                })
            
            logger.info(f"ChatGPT suggested {len(results)} valid companies")
            return results
            
        except Exception as e:
            logger.error(f"ChatGPT company search error: {type(e).__name__}: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Check for specific error types
            if "rate_limit" in str(e).lower():
                logger.error("⚠️ RATE LIMIT EXCEEDED - Try again in a moment")
            elif "timeout" in str(e).lower():
                logger.error("⚠️ REQUEST TIMEOUT - API took too long to respond")
            elif "authentication" in str(e).lower() or "api_key" in str(e).lower():
                logger.error("⚠️ API KEY INVALID - Check your OpenAI API key")
            
            return []


class GoogleSource:
    """Google Custom Search integration"""
    
    def __init__(self, api_key: str, search_engine_id: str):
        self.api_key = api_key
        self.search_engine_id = search_engine_id
    
    async def get_company_data(self, company_name: str, company_data: Optional[Dict] = None) -> Dict:
        """Search Google for company information"""
        if httpx is None:
            return {}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://www.googleapis.com/customsearch/v1",
                    params={
                        "key": self.api_key,
                        "cx": self.search_engine_id,
                        "q": f"{company_name} company"
                    }
                )
                data = response.json()
                return {
                    "search_results": data.get("items", [])[:3]
                }
        except Exception as e:
            logger.error(f"Google search error: {e}")
            return {}


class ClaudeSource:
    """Anthropic Claude integration"""
    
    def __init__(self, api_key: str):
        if anthropic is None:
            raise ImportError("anthropic library not installed")
        self.client = anthropic.Anthropic(api_key=api_key)
    
    async def get_company_data(self, company_name: str, company_data: Optional[Dict] = None) -> Dict:
        """Get company analysis from Claude"""
        try:
            message = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=300,
                messages=[{
                    "role": "user",
                    "content": f"Provide a brief analysis of {company_name}, including their core business, key capabilities, and market position."
                }]
            )
            
            return {
                "analysis": message.content[0].text
            }
        except Exception as e:
            logger.error(f"Claude error: {e}")
            return {}


class PitchbookSource:
    """Pitchbook integration"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.pitchbook.com/v1"
    
    async def get_company_data(self, company_name: str, company_data: Optional[Dict] = None) -> Dict:
        """Get company data from Pitchbook"""
        if httpx is None:
            return {}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/companies/search",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    params={"name": company_name}
                )
                return response.json()
        except Exception as e:
            logger.error(f"Pitchbook error: {e}")
            return {}


class HubSpotSource:
    """HubSpot integration for internal company list"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    async def get_company_data(self, company_name: str, company_data: Optional[Dict] = None) -> Dict:
        """Get company data from HubSpot"""
        if httpx is None:
            return {}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.hubapi.com/companies/v2/companies/search",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    params={"q": company_name}
                )
                return response.json()
        except Exception as e:
            logger.error(f"HubSpot error: {e}")
            return {}


class USASpendingSource:
    """USASpending.gov integration (public API)"""
    
    async def get_company_data(self, company_name: str, company_data: Optional[Dict] = None) -> Dict:
        """Get contract history from USASpending.gov"""
        if httpx is None:
            return {}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.usaspending.gov/api/v2/search/spending_by_award/",
                    json={
                        "filters": {
                            "keywords": [company_name]
                        },
                        "limit": 10
                    }
                )
                return response.json()
        except Exception as e:
            logger.error(f"USASpending error: {e}")
            return {}


class NIHReporterSource:
    """NIH Reporter integration"""
    
    async def get_company_data(self, company_name: str, company_data: Optional[Dict] = None) -> Dict:
        """Get NIH grants and research data"""
        if httpx is None:
            return {}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.reporter.nih.gov/v2/projects/search",
                    json={
                        "criteria": {
                            "org_names": [company_name]
                        },
                        "limit": 10
                    }
                )
                return response.json()
        except Exception as e:
            logger.error(f"NIH Reporter error: {e}")
            return {}


class SBIRSource:
    """SBIR.gov integration"""
    
    async def get_company_data(self, company_name: str, company_data: Optional[Dict] = None) -> Dict:
        """Get SBIR/STTR award data"""
        # Note: SBIR.gov doesn't have a simple public API
        # This would require web scraping or manual data import
        return {"note": "SBIR data requires manual import"}


class USPTOSource:
    """USPTO patent search integration"""
    
    async def get_company_data(self, company_name: str, company_data: Optional[Dict] = None) -> Dict:
        """Get patent data from USPTO"""
        if httpx is None:
            return {}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://developer.uspto.gov/ibd-api/v1/application/grants",
                    params={
                        "searchText": company_name,
                        "rows": 10
                    }
                )
                return response.json()
        except Exception as e:
            logger.error(f"USPTO error: {e}")
            return {}

