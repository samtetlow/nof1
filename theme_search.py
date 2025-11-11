"""
theme_search.py
Theme-based company search across multiple data sources
Uses extracted solicitation themes to find matching companies
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from data_sources import DataSourceManager, EnrichmentResult
import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class ThemeBasedSearch:
    """Search for companies based on solicitation themes across multiple sources"""
    
    def __init__(self, data_source_manager: DataSourceManager):
        self.dsm = data_source_manager
        
    async def search_by_themes(self, themes: Dict[str, Any], max_companies: int = 20, company_type: str = "for-profit", company_size: str = "all") -> List[Dict[str, Any]]:
        """
        Search for companies matching the solicitation themes
        
        Args:
            themes: Extracted themes from solicitation (technical_focus, keywords, etc.)
            max_companies: Maximum number of companies to return
            company_type: Filter by company type ('for-profit', 'academic-nonprofit')
            company_size: Filter by company size ('all', 'small', 'large')
            
        Returns:
            List of discovered companies with relevance scores
        """
        logger.info(f"Starting theme-based search for {max_companies} companies (type: {company_type}, size: {company_size})")
        
        discovered_companies = []
        
        # Extract search terms from themes
        search_terms = self._build_search_terms(themes)
        logger.info(f"Generated {len(search_terms)} search terms from themes")
        
        # Search across all available sources in parallel
        search_tasks = []
        
        # 1. Google Search for each technical focus area
        if "google" in self.dsm.sources:
            for term in search_terms[:5]:  # Top 5 terms
                search_tasks.append(self._search_google(term))
        
        # 2. USASpending.gov for companies with relevant contracts
        if "usaspending" in self.dsm.sources:
            search_tasks.append(self._search_usaspending(search_terms))
        
        # 3. NIH Reporter for companies with relevant grants
        if "nih_reporter" in self.dsm.sources:
            search_tasks.append(self._search_nih(search_terms))
        
        # 4. SBIR.gov for companies with relevant SBIR awards
        if "sbir" in self.dsm.sources:
            search_tasks.append(self._search_sbir(search_terms))
        
        # 5. Pitchbook for private company data and funding
        if "pitchbook" in self.dsm.sources:
            search_tasks.append(self._search_pitchbook(search_terms, themes))
        
        # 6. ChatGPT for AI-powered company recommendations
        if "chatgpt" in self.dsm.sources:
            search_tasks.append(self._search_chatgpt(themes, max_companies, company_type, company_size))
        
        # Execute all searches in parallel
        if search_tasks:
            results = await asyncio.gather(*search_tasks, return_exceptions=True)
            
            # Process results
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Search error: {result}")
                    continue
                if result:
                    discovered_companies.extend(result)
        else:
            logger.warning("No data sources enabled for search")
        
        # Deduplicate and score companies
        unique_companies = self._deduplicate_companies(discovered_companies)
        
        # Score relevance based on theme matches
        scored_companies = self._score_companies(unique_companies, themes)
        
        # Sort by relevance and return top N
        sorted_companies = sorted(scored_companies, key=lambda x: x['relevance_score'], reverse=True)
        
        logger.info(f"Found {len(sorted_companies)} unique companies")
        return sorted_companies[:max_companies]
    
    def _build_search_terms(self, themes: Dict[str, Any]) -> List[str]:
        """Build search terms from extracted themes"""
        terms = []
        
        # Technical capabilities (highest priority)
        if themes.get('technical_capabilities'):
            for cap in themes['technical_capabilities'][:5]:  # Top 5
                area = cap.get('area', '')
                if area:
                    terms.append(area)
        
        # Search keywords (pre-built from themes)
        if themes.get('search_keywords'):
            terms.extend(themes['search_keywords'][:10])
        
        # Problem areas (extract key nouns)
        if themes.get('problem_areas'):
            for problem in themes['problem_areas'][:3]:
                # Extract key terms from problem statements
                words = problem.split()[:5]  # First 5 words
                terms.extend([w for w in words if len(w) > 4])
        
        # Key priorities (extract key terms)
        if themes.get('key_priorities'):
            for priority in themes['key_priorities'][:3]:
                words = priority.split()[:5]
                terms.extend([w for w in words if len(w) > 4])
        
        # Remove duplicates and filter out common words
        unique_terms = list(set([t.lower() for t in terms if t]))
        stop_words = {'that', 'this', 'with', 'from', 'have', 'their', 'about', 'would', 'there'}
        filtered_terms = [t for t in unique_terms if t not in stop_words]
        
        return filtered_terms[:20]  # Return top 20 terms
    
    async def _search_google(self, search_term: str) -> List[Dict[str, Any]]:
        """Search Google for companies with specific capabilities"""
        logger.info(f"Searching Google for: {search_term}")
        
        try:
            query = f"{search_term} government contractor capabilities past performance"
            
            # Use the Google source's search functionality
            # Note: This is a simplified version - would need to parse results better
            result = await self.dsm.sources["google"].enrich_company(query, {})
            
            companies = []
            if result.data and 'search_results' in result.data:
                for item in result.data['search_results']:
                    # Extract potential company names from titles and snippets
                    company_name = self._extract_company_name(item.get('title', ''))
                    if company_name:
                        companies.append({
                            'name': company_name,
                            'source': 'google',
                            'relevance': search_term,
                            'snippet': item.get('snippet', ''),
                            'url': item.get('link', ''),
                            'confidence': 0.6
                        })
            
            logger.info(f"Google found {len(companies)} potential companies for '{search_term}'")
            return companies
        except Exception as e:
            logger.error(f"Google search error for '{search_term}': {e}")
            return []
    
    async def _search_usaspending(self, search_terms: List[str]) -> List[Dict[str, Any]]:
        """Search USASpending.gov for companies with relevant contracts"""
        logger.info(f"Searching USASpending.gov for {len(search_terms)} terms")
        
        try:
            companies = []
            
            # Search for contracts containing any of our key terms
            for term in search_terms[:10]:  # Top 10 terms
                contracts = await self.dsm.sources["usaspending"].search_contracts("", {
                    'keyword': term,
                    'limit': 5
                })
                
                for contract in contracts:
                    company_name = contract.get('recipient_name') or contract.get('contractor_name')
                    if company_name:
                        companies.append({
                            'name': company_name,
                            'source': 'usaspending',
                            'relevance': term,
                            'contract_value': contract.get('award_amount', 0),
                            'naics': contract.get('naics_code', ''),
                            'description': contract.get('description', ''),
                            'confidence': 0.9  # High confidence from official data
                        })
            
            logger.info(f"USASpending found {len(companies)} companies")
            return companies
        except Exception as e:
            logger.error(f"USASpending search error: {e}")
            return []
    
    async def _search_nih(self, search_terms: List[str]) -> List[Dict[str, Any]]:
        """Search NIH Reporter for companies with relevant grants"""
        logger.info(f"Searching NIH Reporter for {len(search_terms)} terms")
        
        try:
            companies = []
            
            for term in search_terms[:10]:
                grants = await self.dsm.sources["nih_reporter"].search_contracts("", {
                    'keyword': term,
                    'limit': 5
                })
                
                for grant in grants:
                    org_name = grant.get('organization_name')
                    if org_name:
                        companies.append({
                            'name': org_name,
                            'source': 'nih',
                            'relevance': term,
                            'grant_amount': grant.get('award_amount', 0),
                            'project_title': grant.get('project_title', ''),
                            'confidence': 0.85
                        })
            
            logger.info(f"NIH found {len(companies)} organizations")
            return companies
        except Exception as e:
            logger.error(f"NIH search error: {e}")
            return []
    
    async def _search_sbir(self, search_terms: List[str]) -> List[Dict[str, Any]]:
        """Search SBIR.gov for companies with relevant awards"""
        logger.info(f"Searching SBIR.gov for {len(search_terms)} terms")
        
        try:
            companies = []
            
            for term in search_terms[:10]:
                awards = await self.dsm.sources["sbir"].search_contracts("", {
                    'keyword': term,
                    'limit': 5
                })
                
                for award in awards:
                    company_name = award.get('company_name')
                    if company_name:
                        companies.append({
                            'name': company_name,
                            'source': 'sbir',
                            'relevance': term,
                            'award_amount': award.get('award_amount', 0),
                            'phase': award.get('phase', ''),
                            'agency': award.get('agency', ''),
                            'confidence': 0.9
                        })
            
            logger.info(f"SBIR found {len(companies)} companies")
            return companies
        except Exception as e:
            logger.error(f"SBIR search error: {e}")
            return []
    
    async def _search_chatgpt(self, themes: Dict[str, Any], max_companies: int = 10, company_type: str = "for-profit", company_size: str = "all") -> List[Dict[str, Any]]:
        """Use ChatGPT to suggest relevant companies"""
        logger.info(f"Using ChatGPT to discover up to {max_companies} matching companies (type: {company_type}, size: {company_size})")
        
        try:
            # Request 50% more companies than needed to account for deduplication/filtering
            # Minimum of max_companies, maximum of max_companies * 1.5 (capped at 300)
            requested_count = max(max_companies, min(int(max_companies * 1.5), 300))
            logger.info(f"Requesting {requested_count} companies from ChatGPT (will return top {max_companies})")
            
            # Call ChatGPT's search_contracts with themes, max count, type, and size filter
            chatgpt_results = await self.dsm.sources["chatgpt"].search_contracts(
                "", 
                {'themes': themes, 'max_companies': requested_count, 'company_type': company_type, 'company_size': company_size}
            )
            
            companies = []
            for result in chatgpt_results:
                company = {
                    'name': result.get('name', 'Unknown'),
                    'description': result.get('description', ''),
                    'website': result.get('website', ''),
                    'capabilities': result.get('capabilities', []),
                    'source': 'chatgpt',
                    'match_reason': result.get('match_reason', ''),
                    'confidence': 0.85
                }
                companies.append(company)
            
            logger.info(f"ChatGPT suggested {len(companies)} companies")
            return companies
            
        except Exception as e:
            logger.error(f"ChatGPT search error: {e}")
            return []
    
    async def _search_pitchbook(self, search_terms: List[str], themes: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search Pitchbook for companies matching themes"""
        logger.info(f"Searching Pitchbook for {len(search_terms)} terms")
        
        try:
            companies = []
            
            # Extract technical focus areas as technologies/verticals
            technologies = []
            if themes.get('technical_focus'):
                for focus in themes['technical_focus'][:5]:
                    area = focus.get('area', '')
                    technologies.append(area)
                    if focus.get('key_terms'):
                        technologies.extend(focus['key_terms'][:3])
            
            # Search Pitchbook with filters
            results = await self.dsm.sources["pitchbook"].search_contracts("", {
                'keyword': ' '.join(search_terms[:5]),
                'technologies': technologies[:10],
                'limit': 20
            })
            
            for result in results:
                companies.append({
                    'name': result.get('name'),
                    'source': 'pitchbook',
                    'relevance': 'theme match',
                    'description': result.get('description'),
                    'website': result.get('website'),
                    'industry': result.get('industry'),
                    'location': result.get('location'),
                    'employee_count': result.get('employee_count'),
                    'total_funding': result.get('total_funding'),
                    'last_funding_date': result.get('last_funding_date'),
                    'technologies': result.get('technologies', []),
                    'confidence': 0.85
                })
            
            logger.info(f"Pitchbook found {len(companies)} companies")
            return companies
        except Exception as e:
            logger.error(f"Pitchbook search error: {e}")
            return []
    
    def _extract_company_name(self, text: str) -> Optional[str]:
        """Extract potential company name from text"""
        import re
        
        # Common patterns for company names
        patterns = [
            r'^([A-Z][A-Za-z\s&,\.]+(?:Inc|LLC|Corp|Corporation|Ltd|Limited|LLP))',
            r'([A-Z][A-Za-z\s&,\.]+(?:Solutions|Systems|Technologies|Tech|Consulting|Services))',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                name = match.group(1).strip()
                if len(name) > 3 and len(name) < 100:
                    return name
        
        return None
    
    def _deduplicate_companies(self, companies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate companies and merge their data"""
        if not companies:
            return []
        
        seen = {}
        
        for company in companies:
            if not isinstance(company, dict):
                logger.warning(f"Skipping non-dict company in deduplication: {type(company)}")
                continue
                
            name = company.get('name', '').lower().strip()
            if not name:
                logger.warning("Skipping company with empty name in deduplication")
                continue
            
            if name in seen:
                # Merge data - keep highest confidence, combine sources
                existing = seen[name]
                existing_sources = existing.get('sources', [])
                if not isinstance(existing_sources, list):
                    existing_sources = [existing.get('source', '')]
                
                if company.get('source'):
                    existing_sources.append(company['source'])
                existing['sources'] = list(set(existing_sources))  # Unique sources
                existing['confidence'] = max(existing.get('confidence', 0), company.get('confidence', 0))
                
                # Merge additional data (prefer non-empty values)
                for key, value in company.items():
                    if value and (key not in existing or not existing[key]):
                        existing[key] = value
            else:
                seen[name] = company.copy()  # Make a copy to avoid mutation issues
                company['sources'] = [company.get('source', '')] if company.get('source') else []
        
        result = list(seen.values())
        logger.debug(f"Deduplicated {len(companies)} companies to {len(result)} unique")
        return result
    
    def _score_companies(self, companies: List[Dict[str, Any]], themes: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Score companies based on how well they match solicitation themes
        
        Scoring Algorithm:
        1. Technical Capability Match (40%) - Does company have required technical skills?
        2. Problem Area Alignment (30%) - Does company address the specific problems?
        3. Keyword Coverage (20%) - How many search keywords match?
        4. Source Credibility (10%) - Quality/number of data sources
        """
        
        # Extract scoring criteria from themes
        required_capabilities = set()
        if themes.get('technical_capabilities'):
            for cap in themes['technical_capabilities']:
                cap_area = cap.get('area', '') if isinstance(cap, dict) else str(cap)
                required_capabilities.add(cap_area.lower())
        
        problem_keywords = set()
        if themes.get('problem_areas'):
            for problem in themes['problem_areas'][:5]:
                # Extract key nouns/terms from problem areas
                words = problem.lower().split()
                problem_keywords.update([w for w in words if len(w) > 4])
        
        search_keywords = set()
        if themes.get('search_keywords'):
            search_keywords.update([kw.lower() for kw in themes['search_keywords'][:15]])
        
        # Score each company
        for company in companies:
            # Build searchable text from company info
            company_text = ' '.join([
                company.get('name', ''),
                company.get('description', ''),
                company.get('snippet', ''),
                company.get('match_reason', ''),
                ' '.join(company.get('capabilities', []))
            ]).lower()
            
            # 1. Technical Capability Match (40%)
            capability_score = 0.0
            if required_capabilities:
                capability_matches = sum(1 for cap in required_capabilities if cap in company_text)
                capability_score = min(capability_matches / max(len(required_capabilities), 1), 1.0) * 0.4
            else:
                capability_score = 0.2  # Default if no capabilities specified
            
            # 2. Problem Area Alignment (30%)
            problem_score = 0.0
            if problem_keywords:
                problem_matches = sum(1 for keyword in problem_keywords if keyword in company_text)
                problem_score = min(problem_matches / max(len(problem_keywords), 1), 1.0) * 0.3
            else:
                problem_score = 0.15  # Default if no problems specified
            
            # 3. Keyword Coverage (20%)
            keyword_score = 0.0
            if search_keywords:
                keyword_matches = sum(1 for kw in search_keywords if kw in company_text)
                keyword_score = min(keyword_matches / max(len(search_keywords), 1), 1.0) * 0.2
            else:
                keyword_score = 0.1  # Default if no keywords
            
            # 4. Source Credibility (10%)
            source_score = 0.0
            num_sources = len(company.get('sources', []))
            base_confidence = company.get('confidence', 0.5)
            source_score = (min(num_sources * 0.02, 0.05) + base_confidence * 0.05)
            
            # Calculate total score
            total_score = capability_score + problem_score + keyword_score + source_score
            
            company['relevance_score'] = min(total_score, 1.0)
            company['score_breakdown'] = {
                'capability_match': capability_score,
                'problem_alignment': problem_score,
                'keyword_coverage': keyword_score,
                'source_credibility': source_score
            }
            
            logger.debug(f"Scored {company.get('name', 'Unknown')}: {total_score:.2f} "
                        f"(cap:{capability_score:.2f}, prob:{problem_score:.2f}, "
                        f"kw:{keyword_score:.2f}, src:{source_score:.2f})")
        
        return companies
    
    async def _basic_web_search(self, search_terms: List[str], themes: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Perform basic web search using publicly available sources
        This is a fallback when no API keys are configured
        """
        companies = []
        
        try:
            # Use DuckDuckGo HTML search (no API key required)
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                for term in search_terms[:3]:  # Limit to 3 searches
                    try:
                        query = f"{term} government contractor federal"
                        url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"
                        
                        headers = {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                        }
                        
                        response = await client.get(url, headers=headers)
                        if response.status_code == 200:
                            soup = BeautifulSoup(response.text, 'html.parser')
                            
                            # Extract search results
                            results = soup.find_all('div', class_='result')[:5]  # Top 5 results
                            
                            for idx, result in enumerate(results):
                                try:
                                    # Try multiple selectors for title and snippet
                                    title_elem = result.find('a', class_='result__a') or result.find('h2') or result.find('a')
                                    snippet_elem = result.find('a', class_='result__snippet') or result.find('div', class_='result__snippet')
                                    
                                    if title_elem:
                                        title = title_elem.get_text(strip=True)
                                        link = title_elem.get('href', '')
                                        
                                        # Get snippet if available
                                        snippet = snippet_elem.get_text(strip=True) if snippet_elem else title
                                        
                                        # Extract company name from title (try multiple methods)
                                        company_name = title.split('-')[0].split('|')[0].split(':')[0].strip()
                                        
                                        # If name is too short or generic, use a better extraction
                                        if len(company_name) < 3 or company_name.lower() in ['www', 'http', 'https']:
                                            # Try to extract from URL
                                            if link and 'http' in link:
                                                domain = link.split('//')[-1].split('/')[0]
                                                company_name = domain.replace('www.', '').split('.')[0].title()
                                            else:
                                                company_name = f"Company {idx+1} - {term.title()}"
                                        
                                        # Ensure we have a valid company name
                                        if not company_name or len(company_name) < 2:
                                            company_name = f"Contractor #{idx+1} ({term})"
                                        
                                        company = {
                                            'id': f"web_{hash(company_name + str(idx))}",
                                            'name': company_name,
                                            'description': snippet if snippet else f"Government contractor specializing in {term}",
                                            'snippet': snippet,
                                            'website': link if link else '',
                                            'capabilities': [term, 'government contracting'],
                                            'sources': ['web_search'],
                                            'confidence': 0.6,
                                            'match_reason': f"Found via web search for '{term}' - Specializes in government contracting",
                                            'project_title': title
                                        }
                                        companies.append(company)
                                        logger.debug(f"Extracted company: {company_name}")
                                        
                                except Exception as e:
                                    logger.warning(f"Error parsing result: {e}")
                                    continue
                        
                        # Small delay between searches to be respectful
                        await asyncio.sleep(0.5)
                        
                    except Exception as e:
                        logger.warning(f"Web search error for '{term}': {e}")
                        continue
            
            logger.info(f"Found {len(companies)} companies via basic web search")
            
        except Exception as e:
            logger.error(f"Basic web search failed: {e}")
        
        return companies

