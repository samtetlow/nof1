"""
website_validator.py
Website Validation Module - Tests companies against their websites
Identifies differences and suggests partnering opportunities
Enhanced with deep website crawling for comprehensive analysis
"""

import logging
import re
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import asyncio
from urllib.parse import urljoin, urlparse, urlunparse

try:
    import httpx
    from bs4 import BeautifulSoup
except ImportError:
    httpx = None
    BeautifulSoup = None

try:
    import openai
except ImportError:
    openai = None

logger = logging.getLogger(__name__)


class GapType(Enum):
    """Types of gaps between company profile and website"""
    CAPABILITY_MISSING = "capability_missing"
    EXPERIENCE_MISMATCH = "experience_mismatch"
    CERTIFICATION_UNVERIFIED = "certification_unverified"
    TECHNICAL_EXPERTISE_GAP = "technical_expertise_gap"
    MARKET_FOCUS_DIFFERENT = "market_focus_different"


@dataclass
class WebsiteGap:
    """Represents a gap between claimed capabilities and website"""
    gap_type: GapType
    description: str
    claimed_value: str
    website_value: str
    severity: float  # 0.0 (minor) to 1.0 (major)
    partnering_opportunity: Optional[str] = None


@dataclass
class WebsiteValidationResult:
    """Result of website validation"""
    company_name: str
    website_url: str
    website_accessible: bool
    validation_score: float  # 0.0 to 1.0 - how well website matches claims
    gaps_found: List[WebsiteGap]
    confirmed_capabilities: List[str]
    website_capabilities: List[str]
    partnering_opportunities: List[Dict[str, Any]]
    summary: str
    raw_website_data: Dict[str, Any] = field(default_factory=dict)


class WebsiteValidator:
    """
    Website Validator - Tests companies against their websites
    
    Functionality:
    1. Deep crawls company website (multiple pages)
    2. Extracts comprehensive content from all crawled pages
    3. Analyzes content against solicitation requirements
    4. Compares website content with claimed capabilities
    5. Identifies gaps and mismatches
    6. Suggests partnering opportunities based on gaps
    """
    
    def __init__(self, openai_api_key: Optional[str] = None, max_pages: int = 10, max_depth: int = 3):
        """
        Initialize website validator with optional AI enhancement
        
        Args:
            openai_api_key: OpenAI API key for AI-powered analysis
            max_pages: Maximum number of pages to crawl (default: 10)
            max_depth: Maximum crawl depth from homepage (default: 3)
        """
        self.openai_client = None
        if openai_api_key and openai:
            try:
                self.openai_client = openai.OpenAI(api_key=openai_api_key)
                logger.info("✓ OpenAI initialized for website validation")
            except Exception as e:
                logger.warning(f"Could not initialize OpenAI: {e}")
        
        self.max_pages = max_pages
        self.max_depth = max_depth
    
    async def quick_validate_website_url(self, url: str) -> bool:
        """
        Quick first-page validation to check if URL has meaningful content
        
        This is a lightweight check (first page only) to verify the website
        has actual content before including it in "why a match" results.
        
        Returns:
            True if website has valid content, False otherwise
        """
        if not url:
            return False
        
        # Check for invalid string values (None, null, N/A, etc. as strings)
        url_str = str(url).strip()
        invalid_values = ['none', 'null', 'nil', 'n/a', 'na', 'undefined', '']
        if url_str.lower() in invalid_values:
            logger.debug(f"Quick validation failed: Invalid string value '{url_str}'")
            return False
        
        # Minimum length check
        if len(url_str) < 4:
            logger.debug(f"Quick validation failed: URL too short '{url_str}'")
            return False
        
        # Check if URL looks like a valid domain before normalizing
        url_for_check = url_str.lower()
        if url_for_check.startswith(('http://', 'https://')):
            url_for_check = url_for_check.split('://', 1)[1]
        url_for_check = url_for_check.split('/')[0].split('?')[0].split('#')[0]
        
        # Must have at least one dot and valid TLD
        if '.' not in url_for_check or len(url_for_check.split('.')[-1]) < 2:
            logger.debug(f"Quick validation failed: Doesn't look like valid domain '{url_str}'")
            return False
        
        if not httpx or not BeautifulSoup:
            logger.warning("httpx or BeautifulSoup not available for quick validation")
            return False
        
        try:
            # Normalize URL (only after validation)
            if not url_str.startswith(('http://', 'https://')):
                url = 'https://' + url_str
            else:
                url = url_str
            
            # Quick timeout for first page only
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                response = await client.get(url)
                
                if response.status_code != 200:
                    logger.debug(f"Quick validation failed: HTTP {response.status_code} for {url}")
                    return False
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract basic content
                title = soup.title.string if soup.title else ""
                main_text = self._extract_main_text(soup)
                headings = self._extract_headings(soup)
                
                # Check minimum content requirements (lighter than full validation)
                MIN_TEXT_LENGTH = 100  # At least 100 chars
                MIN_HEADINGS = 1  # At least 1 heading
                
                if len(main_text) < MIN_TEXT_LENGTH:
                    logger.debug(f"Quick validation failed: Insufficient text ({len(main_text)} < {MIN_TEXT_LENGTH}) for {url}")
                    return False
                
                if len(headings) < MIN_HEADINGS:
                    logger.debug(f"Quick validation failed: No headings found for {url}")
                    return False
                
                # Check for boilerplate
                text_lower = main_text.lower()
                boilerplate_patterns = ["coming soon", "under construction", "page not found", "404", "error loading"]
                if any(pattern in text_lower for pattern in boilerplate_patterns):
                    logger.debug(f"Quick validation failed: Boilerplate content detected for {url}")
                    return False
                
                logger.info(f"✓ Quick validation passed for {url}")
                return True
                
        except httpx.TimeoutException:
            logger.debug(f"Quick validation timeout for {url}")
            return False
        except Exception as e:
            logger.debug(f"Quick validation error for {url}: {e}")
            return False
    
    async def validate_company_website(
        self,
        company_data: Dict[str, Any],
        solicitation_data: Dict[str, Any],
        enrichment_data: Optional[Dict[str, Any]] = None
    ) -> WebsiteValidationResult:
        """
        Validate company by testing against their website
        
        Args:
            company_data: Company profile with claimed capabilities
            solicitation_data: Solicitation requirements
            enrichment_data: Optional enriched data from other sources
        
        Returns:
            WebsiteValidationResult with gaps and partnering opportunities
        """
        company_name = company_data.get("name", "Unknown")
        website_url = company_data.get("website", "")
        
        logger.info(f"Validating website for {company_name}: {website_url}")
        
        # If no website, return early with gaps
        if not website_url:
            return self._create_no_website_result(company_name, company_data, solicitation_data)
        
        # Deep crawl website (multiple pages)
        logger.info(f"Starting deep crawl of {website_url} (max {self.max_pages} pages, depth {self.max_depth})")
        crawled_data = await self._deep_crawl_website(website_url)
        
        if not crawled_data.get("accessible"):
            return self._create_inaccessible_website_result(
                company_name, website_url, company_data, solicitation_data
            )
        
        # Critical check: Only proceed if content is validated (anti-hallucination)
        if not crawled_data.get("content_validated", False):
            logger.warning(f"⚠ Rejecting website validation for {company_name}: Content not validated")
            return self._create_invalid_content_result(
                company_name, website_url, company_data, solicitation_data
            )
        
        # Extract capabilities from all crawled pages
        website_capabilities = await self._extract_website_capabilities(
            crawled_data, company_name
        )
        
        # Analyze against solicitation requirements
        solicitation_alignment = await self._analyze_solicitation_alignment(
            crawled_data, solicitation_data, company_name
        )
        
        # Compare claimed vs website capabilities (using all crawled data)
        gaps = await self._identify_gaps(
            company_data, 
            website_capabilities,
            solicitation_data,
            crawled_data
        )
        
        # Identify confirmed capabilities
        confirmed_capabilities = self._identify_confirmed_capabilities(
            company_data,
            website_capabilities
        )
        
        # Generate partnering opportunities based on gaps
        partnering_opportunities = await self._generate_partnering_opportunities(
            gaps,
            company_data,
            solicitation_data,
            website_capabilities
        )
        
        # Calculate validation score (including solicitation alignment)
        validation_score = self._calculate_validation_score(
            confirmed_capabilities,
            gaps,
            company_data,
            solicitation_alignment
        )
        
        # Generate summary (with deep crawl info)
        summary = self._generate_summary(
            company_name,
            validation_score,
            confirmed_capabilities,
            gaps,
            partnering_opportunities,
            crawled_data,
            solicitation_alignment
        )
        
        return WebsiteValidationResult(
            company_name=company_name,
            website_url=website_url,
            website_accessible=True,
            validation_score=validation_score,
            gaps_found=gaps,
            confirmed_capabilities=confirmed_capabilities,
            website_capabilities=website_capabilities,
            partnering_opportunities=partnering_opportunities,
            summary=summary,
            raw_website_data={
                **crawled_data,
                "solicitation_alignment": solicitation_alignment,
                "pages_crawled": len(crawled_data.get("pages", []))
            }
        )
    
    async def _deep_crawl_website(self, start_url: str) -> Dict[str, Any]:
        """
        Deep crawl website starting from homepage
        
        Crawls multiple pages following internal links to build comprehensive
        understanding of company capabilities and alignment with solicitation.
        """
        if not httpx or not BeautifulSoup:
            logger.warning("httpx or BeautifulSoup not available")
            return {"accessible": False, "error": "Dependencies not installed"}
        
        try:
            # Normalize URL
            if not start_url.startswith(('http://', 'https://')):
                start_url = 'https://' + start_url
            
            parsed_start = urlparse(start_url)
            base_domain = f"{parsed_start.scheme}://{parsed_start.netloc}"
            
            visited_urls: Set[str] = set()
            pages_data: List[Dict[str, Any]] = []
            urls_to_visit: List[Tuple[str, int]] = [(start_url, 0)]  # (url, depth)
            
            async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
                while urls_to_visit and len(pages_data) < self.max_pages:
                    current_url, depth = urls_to_visit.pop(0)
                    
                    # Skip if already visited or too deep
                    if current_url in visited_urls or depth > self.max_depth:
                        continue
                    
                    # Only crawl same domain
                    parsed_current = urlparse(current_url)
                    if parsed_current.netloc != parsed_start.netloc:
                        continue
                    
                    try:
                        logger.info(f"Crawling page {len(pages_data) + 1}/{self.max_pages}: {current_url} (depth {depth})")
                        response = await client.get(current_url, timeout=15.0)
                        
                        if response.status_code != 200:
                            continue
                        
                        visited_urls.add(current_url)
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # Extract page data
                        page_data = {
                            "url": str(response.url),
                            "title": soup.title.string if soup.title else "",
                            "meta_description": self._extract_meta_description(soup),
                            "main_text": self._extract_main_text(soup),
                            "headings": self._extract_headings(soup),
                            "services": self._extract_services_section(soup),
                            "about": self._extract_about_section(soup),
                            "keywords": self._extract_keywords(soup),
                            "depth": depth
                        }
                        
                        # Quick validation: Skip pages with no meaningful content
                        if len(page_data["main_text"]) < 50 and len(page_data["headings"]) == 0:
                            logger.debug(f"Skipping page with insufficient content: {current_url}")
                            continue
                        
                        pages_data.append(page_data)
                        
                        # Extract links for further crawling (if not at max depth)
                        if depth < self.max_depth:
                            links = self._extract_internal_links(soup, base_domain, current_url)
                            for link in links:
                                if link not in visited_urls:
                                    urls_to_visit.append((link, depth + 1))
                        
                    except httpx.TimeoutException:
                        logger.warning(f"Timeout crawling: {current_url}")
                        continue
                    except Exception as e:
                        logger.warning(f"Error crawling {current_url}: {e}")
                        continue
                    
                    # Small delay to be respectful
                    await asyncio.sleep(0.5)
            
            if not pages_data:
                return {"accessible": False, "error": "No pages could be crawled"}
            
            # Aggregate data from all pages
            aggregated_data = self._aggregate_crawled_data(pages_data, start_url)
            
            # Validate that we have meaningful content (anti-hallucination check)
            content_valid = self._validate_content_quality(aggregated_data)
            aggregated_data["content_validated"] = content_valid
            
            if not content_valid:
                logger.warning(f"⚠ Website content validation failed for {start_url} - insufficient meaningful content")
                aggregated_data["accessible"] = False
                aggregated_data["error"] = "Insufficient meaningful content found"
                return aggregated_data
            
            logger.info(f"✓ Successfully crawled {len(pages_data)} pages from {start_url} (content validated)")
            
            return aggregated_data
                
        except Exception as e:
            logger.error(f"Deep crawl error for {start_url}: {e}")
            return {"accessible": False, "error": str(e)}
    
    def _extract_internal_links(self, soup: Any, base_domain: str, current_url: str) -> List[str]:
        """Extract internal links from page for further crawling"""
        links = []
        try:
            for anchor in soup.find_all('a', href=True):
                href = anchor['href']
                
                # Skip non-HTTP links
                if href.startswith(('mailto:', 'tel:', 'javascript:', '#')):
                    continue
                
                # Convert relative to absolute URL
                absolute_url = urljoin(current_url, href)
                parsed = urlparse(absolute_url)
                
                # Only include same-domain links
                if parsed.netloc == urlparse(base_domain).netloc:
                    # Remove fragments and query params for deduplication
                    clean_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', '', ''))
                    if clean_url not in links:
                        links.append(clean_url)
            
            # Prioritize important pages (services, about, capabilities, solutions)
            priority_keywords = ['service', 'capabilit', 'solution', 'about', 'what-we-do', 'expertise', 'technology']
            priority_links = [l for l in links if any(kw in l.lower() for kw in priority_keywords)]
            other_links = [l for l in links if l not in priority_links]
            
            # Return priority links first, then others
            return priority_links[:5] + other_links[:10]  # Limit to prevent too many links
            
        except Exception as e:
            logger.warning(f"Error extracting links: {e}")
            return []
    
    def _validate_content_quality(self, aggregated_data: Dict[str, Any]) -> bool:
        """
        Validate that crawled content is meaningful and not empty/boilerplate
        
        Anti-hallucination check: Ensures we have real, substantial content
        before using it for scoring or analysis.
        """
        # Minimum content thresholds
        MIN_MAIN_TEXT_LENGTH = 200  # At least 200 chars of main text
        MIN_TOTAL_CONTENT = 500  # At least 500 chars total
        MIN_HEADINGS = 2  # At least 2 headings
        MIN_PAGES = 1  # At least 1 page successfully crawled
        
        main_text = aggregated_data.get("main_text", "")
        total_length = aggregated_data.get("total_content_length", 0)
        headings = aggregated_data.get("headings", [])
        pages_crawled = aggregated_data.get("pages_crawled", 0)
        
        # Check minimum content requirements
        if len(main_text) < MIN_MAIN_TEXT_LENGTH:
            logger.warning(f"Content validation failed: Main text too short ({len(main_text)} < {MIN_MAIN_TEXT_LENGTH})")
            return False
        
        if total_length < MIN_TOTAL_CONTENT:
            logger.warning(f"Content validation failed: Total content too short ({total_length} < {MIN_TOTAL_CONTENT})")
            return False
        
        if len(headings) < MIN_HEADINGS:
            logger.warning(f"Content validation failed: Too few headings ({len(headings)} < {MIN_HEADINGS})")
            return False
        
        if pages_crawled < MIN_PAGES:
            logger.warning(f"Content validation failed: No pages crawled ({pages_crawled} < {MIN_PAGES})")
            return False
        
        # Check for boilerplate/empty content patterns
        text_lower = main_text.lower()
        
        # Common boilerplate patterns that indicate empty/minimal content
        boilerplate_patterns = [
            "coming soon",
            "under construction",
            "this page is empty",
            "no content available",
            "page not found",
            "404",
            "error loading"
        ]
        
        # If content is mostly boilerplate, reject it
        boilerplate_ratio = sum(1 for pattern in boilerplate_patterns if pattern in text_lower) / len(boilerplate_patterns)
        if boilerplate_ratio > 0.3:  # More than 30% boilerplate
            logger.warning(f"Content validation failed: Too much boilerplate content detected")
            return False
        
        # Check for meaningful word diversity (not just repeated words)
        words = text_lower.split()
        unique_words = set(words)
        if len(words) > 0:
            diversity_ratio = len(unique_words) / len(words)
            if diversity_ratio < 0.3:  # Less than 30% unique words (likely repetitive)
                logger.warning(f"Content validation failed: Low word diversity ({diversity_ratio:.2%})")
                return False
        
        return True
    
    def _aggregate_crawled_data(self, pages_data: List[Dict[str, Any]], start_url: str) -> Dict[str, Any]:
        """Aggregate data from all crawled pages into comprehensive dataset"""
        
        # Combine all text content
        all_titles = [p.get("title", "") for p in pages_data if p.get("title")]
        all_descriptions = [p.get("meta_description", "") for p in pages_data if p.get("meta_description")]
        all_main_text = " ".join([p.get("main_text", "") for p in pages_data])
        all_headings = []
        for p in pages_data:
            all_headings.extend(p.get("headings", []))
        all_services = " ".join([p.get("services", "") for p in pages_data if p.get("services")])
        all_about = " ".join([p.get("about", "") for p in pages_data if p.get("about")])
        all_keywords = []
        for p in pages_data:
            all_keywords.extend(p.get("keywords", []))
        
        # Remove duplicates while preserving order
        seen_headings = set()
        unique_headings = []
        for h in all_headings:
            h_lower = h.lower()
            if h_lower not in seen_headings:
                seen_headings.add(h_lower)
                unique_headings.append(h)
        
        seen_keywords = set()
        unique_keywords = []
        for k in all_keywords:
            k_lower = k.lower()
            if k_lower not in seen_keywords:
                seen_keywords.add(k_lower)
                unique_keywords.append(k)
        
        return {
            "accessible": True,
            "url": start_url,
            "pages_crawled": len(pages_data),
            "pages": pages_data,
            "title": all_titles[0] if all_titles else "",
            "meta_description": " ".join(all_descriptions[:3]),  # Combine top descriptions
            "main_text": all_main_text[:20000],  # Limit total text to 20k chars
            "headings": unique_headings[:50],  # Top 50 unique headings
            "services": all_services[:5000],  # Combined services text
            "about": all_about[:5000],  # Combined about text
            "keywords": unique_keywords[:30],  # Top 30 unique keywords
            "total_content_length": len(all_main_text)
        }
    
    async def _scrape_website(self, url: str) -> Dict[str, Any]:
        """Legacy single-page scrape (kept for backward compatibility)"""
        # This now just calls deep crawl with max_pages=1
        result = await self._deep_crawl_website(url)
        if result.get("accessible") and result.get("pages"):
            # Return first page data in old format
            first_page = result["pages"][0]
            return {
                "accessible": True,
                "url": first_page.get("url", url),
                "title": first_page.get("title", ""),
                "meta_description": first_page.get("meta_description", ""),
                "main_text": first_page.get("main_text", ""),
                "headings": first_page.get("headings", []),
                "services": first_page.get("services", ""),
                "about": first_page.get("about", ""),
                "keywords": first_page.get("keywords", [])
            }
        return result
    
    def _extract_meta_description(self, soup: Any) -> str:
        """Extract meta description from HTML"""
        try:
            meta = soup.find('meta', attrs={'name': 'description'})
            if meta and meta.get('content'):
                return meta['content']
            meta = soup.find('meta', attrs={'property': 'og:description'})
            if meta and meta.get('content'):
                return meta['content']
        except:
            pass
        return ""
    
    def _extract_main_text(self, soup: Any) -> str:
        """Extract main body text from HTML"""
        try:
            # Remove script and style elements
            for script in soup(['script', 'style', 'nav', 'footer', 'header']):
                script.decompose()
            
            # Get text
            text = soup.get_text(separator=' ', strip=True)
            
            # Clean up whitespace
            text = re.sub(r'\s+', ' ', text)
            
            # Limit to first 5000 characters
            return text[:5000]
        except:
            return ""
    
    def _extract_headings(self, soup: Any) -> List[str]:
        """Extract all headings from HTML"""
        try:
            headings = []
            for tag in ['h1', 'h2', 'h3']:
                for heading in soup.find_all(tag):
                    text = heading.get_text(strip=True)
                    if text and len(text) > 2:
                        headings.append(text)
            return headings[:20]  # Limit to top 20
        except:
            return []
    
    def _extract_services_section(self, soup: Any) -> str:
        """Try to find and extract services/capabilities section"""
        try:
            # Look for common services section markers
            services_keywords = ['services', 'capabilities', 'solutions', 'offerings', 'what we do']
            
            for keyword in services_keywords:
                # Try to find section by heading
                section = soup.find(['h1', 'h2', 'h3', 'div', 'section'], 
                                   string=re.compile(keyword, re.IGNORECASE))
                if section:
                    # Get parent or next sibling content
                    parent = section.parent
                    if parent:
                        text = parent.get_text(separator=' ', strip=True)
                        return text[:1000]
            
            return ""
        except:
            return ""
    
    def _extract_about_section(self, soup: Any) -> str:
        """Try to find and extract about section"""
        try:
            about_keywords = ['about us', 'about', 'who we are', 'our company', 'our story']
            
            for keyword in about_keywords:
                section = soup.find(['h1', 'h2', 'h3', 'div', 'section'], 
                                   string=re.compile(keyword, re.IGNORECASE))
                if section:
                    parent = section.parent
                    if parent:
                        text = parent.get_text(separator=' ', strip=True)
                        return text[:1000]
            
            return ""
        except:
            return ""
    
    def _extract_keywords(self, soup: Any) -> List[str]:
        """Extract keywords from meta tags"""
        try:
            meta = soup.find('meta', attrs={'name': 'keywords'})
            if meta and meta.get('content'):
                keywords = [k.strip() for k in meta['content'].split(',')]
                return keywords[:20]
        except:
            pass
        return []
    
    async def _extract_website_capabilities(
        self,
        website_data: Dict[str, Any],
        company_name: str
    ) -> List[str]:
        """Extract capabilities from all crawled website pages using AI analysis"""
        
        # First, try keyword-based extraction from all pages
        keyword_capabilities = self._extract_capabilities_by_keywords(website_data)
        
        # If OpenAI is available, use AI to extract more sophisticated capabilities from all content
        if self.openai_client:
            ai_capabilities = await self._extract_capabilities_with_ai(
                website_data,
                company_name
            )
            
            # Combine and deduplicate
            all_capabilities = keyword_capabilities + ai_capabilities
            # Deduplicate (case-insensitive)
            seen = set()
            unique_capabilities = []
            for cap in all_capabilities:
                cap_lower = cap.lower()
                if cap_lower not in seen:
                    seen.add(cap_lower)
                    unique_capabilities.append(cap)
            
            return unique_capabilities
        
        return keyword_capabilities
    
    async def _analyze_solicitation_alignment(
        self,
        website_data: Dict[str, Any],
        solicitation_data: Dict[str, Any],
        company_name: str
    ) -> Dict[str, Any]:
        """
        Deep analysis of website content against solicitation requirements
        
        Uses AI to comprehensively analyze all crawled pages against:
        - Required capabilities
        - Technical requirements
        - Problem areas
        - Key priorities
        """
        alignment_result = {
            "overall_alignment_score": 0.0,
            "capability_matches": [],
            "capability_gaps": [],
            "technical_alignment": {},
            "problem_area_coverage": {},
            "evidence_found": [],
            "confidence": 0.0
        }
        
        if not self.openai_client:
            # Fallback to keyword matching if no AI
            return self._analyze_alignment_keyword_based(website_data, solicitation_data)
        
        try:
            # Prepare comprehensive website content
            all_content = f"""
COMPANY: {company_name}

WEBSITE CONTENT (from {website_data.get('pages_crawled', 1)} pages):
Title: {website_data.get('title', '')}
Description: {website_data.get('meta_description', '')}
Headings: {', '.join(website_data.get('headings', [])[:30])}
Services: {website_data.get('services', '')[:2000]}
About: {website_data.get('about', '')[:2000]}
Main Content: {website_data.get('main_text', '')[:5000]}
"""
            
            # Prepare solicitation requirements
            required_capabilities = solicitation_data.get("required_capabilities", [])
            technical_requirements = solicitation_data.get("technical_requirements", [])
            problem_areas = solicitation_data.get("problem_areas", [])
            keywords = solicitation_data.get("keywords", [])
            solicitation_title = solicitation_data.get("title", "")
            
            solicitation_context = f"""
SOLICITATION: {solicitation_title}

REQUIRED CAPABILITIES:
{chr(10).join([f"- {cap}" for cap in required_capabilities[:15]])}

TECHNICAL REQUIREMENTS:
{chr(10).join([f"- {req}" for req in technical_requirements[:10]])}

PROBLEM AREAS:
{chr(10).join([f"- {area}" for area in problem_areas[:10]])}

KEYWORDS: {', '.join(keywords[:20])}
"""
            
            prompt = f"""Analyze how well this company's website aligns with the solicitation requirements.

{all_content}

{solicitation_context}

Provide a comprehensive analysis:
1. Which required capabilities are clearly demonstrated on the website? (list specific evidence)
2. Which required capabilities are missing or unclear? (list gaps)
3. How well does the website address the problem areas? (rate 0-1.0)
4. What technical evidence supports their ability to meet requirements? (specific examples)
5. Overall alignment score (0.0 to 1.0) - how well does the website demonstrate they can meet this solicitation?

Format as JSON with fields:
- overall_alignment_score (float 0.0-1.0)
- capability_matches (array of objects with: capability, evidence, confidence)
- capability_gaps (array of objects with: capability, reason, severity)
- problem_area_coverage (object with coverage scores for each problem area)
- technical_evidence (array of specific technical evidence found)
- confidence (float 0.0-1.0)"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing company websites against government solicitation requirements. Provide detailed, evidence-based analysis."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.3
            )
            
            result = response.choices[0].message.content.strip()
            
            # Parse JSON response
            import json
            if result.startswith("```json"):
                result = result[7:]
            if result.startswith("```"):
                result = result[3:]
            if result.endswith("```"):
                result = result[:-3]
            result = result.strip()
            
            try:
                alignment_result = json.loads(result)
                
                # Anti-hallucination check: Validate AI response quality
                hallucination_penalty = self._detect_hallucinations(alignment_result, website_data, solicitation_data)
                alignment_result["hallucination_penalty"] = hallucination_penalty
                alignment_result["content_verified"] = hallucination_penalty < 0.3  # Low penalty = verified
                
                # Apply penalty to alignment score if hallucinations detected
                if hallucination_penalty > 0:
                    original_score = alignment_result.get('overall_alignment_score', 0.0)
                    alignment_result['overall_alignment_score'] = max(0.0, original_score - hallucination_penalty)
                    logger.warning(f"⚠ Applied hallucination penalty of {hallucination_penalty:.1%} to alignment score")
                
                logger.info(f"✓ Solicitation alignment analysis complete: {alignment_result.get('overall_alignment_score', 0.0):.1%} (penalty: {hallucination_penalty:.1%})")
            except json.JSONDecodeError:
                logger.warning("AI returned non-JSON alignment analysis, using keyword fallback")
                alignment_result = self._analyze_alignment_keyword_based(website_data, solicitation_data)
                alignment_result["hallucination_penalty"] = 0.0  # No penalty for fallback
                alignment_result["content_verified"] = True  # Keyword-based is verified
            
        except Exception as e:
            logger.warning(f"AI alignment analysis failed: {e}, using keyword fallback")
            alignment_result = self._analyze_alignment_keyword_based(website_data, solicitation_data)
            alignment_result["hallucination_penalty"] = 0.0
            alignment_result["content_verified"] = True
        
        return alignment_result
    
    def _detect_hallucinations(
        self,
        alignment_result: Dict[str, Any],
        website_data: Dict[str, Any],
        solicitation_data: Dict[str, Any]
    ) -> float:
        """
        Detect potential hallucinations in AI-generated alignment analysis
        
        Returns a penalty score (0.0 to 1.0) indicating likelihood of hallucination.
        Higher penalty = more likely to be hallucinated.
        """
        penalty = 0.0
        
        # Check 1: Verify capability matches have evidence in actual website content
        capability_matches = alignment_result.get("capability_matches", [])
        website_text = " ".join([
            website_data.get("main_text", ""),
            website_data.get("services", ""),
            website_data.get("about", ""),
            " ".join(website_data.get("headings", []))
        ]).lower()
        
        unverified_matches = 0
        for match in capability_matches:
            capability = match.get("capability", "").lower()
            evidence = match.get("evidence", "").lower()
            
            # Check if capability or key terms appear in website content
            capability_terms = [term for term in capability.split() if len(term) > 3]
            found_in_content = any(term in website_text for term in capability_terms)
            
            # Check if evidence mentions specific website content
            evidence_has_website_refs = any(ref in evidence for ref in ["page", "section", "website", "site", "content"])
            
            if not found_in_content and not evidence_has_website_refs:
                unverified_matches += 1
        
        if capability_matches:
            unverified_ratio = unverified_matches / len(capability_matches)
            if unverified_ratio > 0.5:  # More than 50% unverified
                penalty += 0.3 * unverified_ratio
                logger.warning(f"Hallucination check: {unverified_ratio:.0%} of capability matches lack website evidence")
        
        # Check 2: Verify technical evidence is specific and plausible
        technical_evidence = alignment_result.get("technical_evidence", [])
        if technical_evidence:
            vague_evidence = 0
            for evidence in technical_evidence:
                evidence_text = str(evidence).lower()
                # Vague indicators (likely hallucinated)
                vague_terms = ["generally", "likely", "probably", "may", "could", "appears", "seems"]
                if any(term in evidence_text for term in vague_terms):
                    vague_evidence += 1
            
            vague_ratio = vague_evidence / len(technical_evidence) if technical_evidence else 0
            if vague_ratio > 0.4:  # More than 40% vague
                penalty += 0.2 * vague_ratio
                logger.warning(f"Hallucination check: {vague_ratio:.0%} of technical evidence is vague")
        
        # Check 3: Verify alignment score is reasonable given website content quality
        alignment_score = alignment_result.get("overall_alignment_score", 0.0)
        content_length = website_data.get("total_content_length", 0)
        
        # If alignment score is very high but content is minimal, likely hallucinated
        if alignment_score > 0.8 and content_length < 1000:
            penalty += 0.3
            logger.warning(f"Hallucination check: High alignment score ({alignment_score:.1%}) with minimal content ({content_length} chars)")
        
        # Check 4: Verify content was actually validated
        content_validated = website_data.get("content_validated", False)
        if not content_validated:
            penalty += 0.4  # Significant penalty for unvalidated content
            logger.warning("Hallucination check: Website content was not validated before analysis")
        
        # Check 5: Verify evidence strings are not generic/boilerplate
        evidence_found = alignment_result.get("evidence_found", [])
        if evidence_found:
            generic_evidence = 0
            generic_phrases = [
                "the website mentions",
                "according to the website",
                "the company offers",
                "based on the content"
            ]
            for evidence in evidence_found:
                evidence_str = str(evidence).lower()
                if any(phrase in evidence_str for phrase in generic_phrases):
                    generic_evidence += 1
            
            generic_ratio = generic_evidence / len(evidence_found) if evidence_found else 0
            if generic_ratio > 0.6:  # More than 60% generic
                penalty += 0.2 * generic_ratio
                logger.warning(f"Hallucination check: {generic_ratio:.0%} of evidence is generic/boilerplate")
        
        return min(1.0, penalty)  # Cap penalty at 1.0
    
    def _analyze_alignment_keyword_based(
        self,
        website_data: Dict[str, Any],
        solicitation_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fallback keyword-based alignment analysis"""
        
        required_capabilities = solicitation_data.get("required_capabilities", [])
        keywords = solicitation_data.get("keywords", [])
        
        # Combine all website text
        all_text = " ".join([
            website_data.get("title", ""),
            website_data.get("meta_description", ""),
            website_data.get("main_text", ""),
            website_data.get("services", ""),
            website_data.get("about", ""),
            " ".join(website_data.get("headings", []))
        ]).lower()
        
        capability_matches = []
        capability_gaps = []
        
        for cap in required_capabilities:
            cap_lower = cap.lower()
            # Check if capability or its keywords appear in website
            if cap_lower in all_text or any(word in all_text for word in cap_lower.split() if len(word) > 4):
                capability_matches.append({
                    "capability": cap,
                    "evidence": "Found in website content",
                    "confidence": 0.7
                })
            else:
                capability_gaps.append({
                    "capability": cap,
                    "reason": "Not found in website content",
                    "severity": 0.8
                })
        
        # Calculate alignment score
        if required_capabilities:
            alignment_score = len(capability_matches) / len(required_capabilities)
        else:
            alignment_score = 0.5
        
        return {
            "overall_alignment_score": alignment_score,
            "capability_matches": capability_matches,
            "capability_gaps": capability_gaps,
            "technical_alignment": {},
            "problem_area_coverage": {},
            "evidence_found": [],
            "confidence": 0.6
        }
    
    def _extract_capabilities_by_keywords(self, website_data: Dict[str, Any]) -> List[str]:
        """Extract capabilities using keyword matching from all crawled pages"""
        capabilities = []
        
        # Combine relevant text from all pages
        text = " ".join([
            website_data.get("title", ""),
            website_data.get("meta_description", ""),
            website_data.get("services", ""),
            website_data.get("about", ""),
            website_data.get("main_text", "")[:10000],  # Include main text from all pages
            " ".join(website_data.get("headings", []))
        ]).lower()
        
        # Common capability keywords
        capability_patterns = {
            "software development": ["software development", "custom software", "application development"],
            "cloud computing": ["cloud", "aws", "azure", "gcp", "cloud computing"],
            "cybersecurity": ["cybersecurity", "cyber security", "information security", "infosec"],
            "data analytics": ["data analytics", "data analysis", "business intelligence", "big data"],
            "artificial intelligence": ["artificial intelligence", "ai", "machine learning", "ml", "deep learning"],
            "devops": ["devops", "ci/cd", "continuous integration"],
            "mobile development": ["mobile app", "ios", "android", "mobile development"],
            "web development": ["web development", "website", "web application"],
            "consulting": ["consulting", "advisory", "strategic consulting"],
            "systems integration": ["systems integration", "integration services"],
            "it infrastructure": ["it infrastructure", "infrastructure management"],
            "research": ["research", "r&d", "research and development"],
            "engineering": ["engineering", "hardware engineering", "systems engineering"],
        }
        
        for capability, keywords in capability_patterns.items():
            for keyword in keywords:
                if keyword in text:
                    capabilities.append(capability.title())
                    break
        
        return capabilities
    
    async def _extract_capabilities_with_ai(
        self,
        website_data: Dict[str, Any],
        company_name: str
    ) -> List[str]:
        """Use AI to extract capabilities from all crawled website pages"""
        
        try:
            pages_crawled = website_data.get('pages_crawled', 1)
            
            # Prepare comprehensive website content from all pages
            content = f"""
Company: {company_name}
Pages Crawled: {pages_crawled}

Title: {website_data.get('title', '')}
Description: {website_data.get('meta_description', '')}
Services: {website_data.get('services', '')[:2000]}
About: {website_data.get('about', '')[:2000]}
Headings: {', '.join(website_data.get('headings', [])[:30])}
Main Content (sample): {website_data.get('main_text', '')[:3000]}
"""
            
            prompt = f"""Analyze this company website (crawled from {pages_crawled} pages) and extract their key capabilities and service offerings.

{content}

List 10-15 specific capabilities this company offers based on ALL the content from multiple pages. Be comprehensive and specific.
Format as a simple comma-separated list."""
            
            prompt = f"""Analyze this company website content and extract their key capabilities and service offerings.

{content}

List 5-10 specific capabilities this company offers. Be concise and specific.
Format as a simple comma-separated list."""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing company websites and identifying their core capabilities. Analyze comprehensively across all pages."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=400,
                temperature=0.3
            )
            
            result = response.choices[0].message.content.strip()
            
            # Parse comma-separated capabilities
            capabilities = [cap.strip() for cap in result.split(',')]
            # Clean up any numbering or bullets
            capabilities = [re.sub(r'^\d+[\.\)]\s*', '', cap) for cap in capabilities]
            capabilities = [re.sub(r'^[-•]\s*', '', cap) for cap in capabilities]
            
            return [cap for cap in capabilities if cap and len(cap) > 2]
            
        except Exception as e:
            logger.warning(f"AI capability extraction failed: {e}")
            return []
    
    async def _identify_gaps(
        self,
        company_data: Dict[str, Any],
        website_capabilities: List[str],
        solicitation_data: Dict[str, Any],
        website_data: Dict[str, Any]
    ) -> List[WebsiteGap]:
        """Identify gaps between claimed capabilities and website"""
        
        gaps = []
        
        # Get claimed capabilities
        claimed_capabilities = company_data.get("capabilities", [])
        required_capabilities = solicitation_data.get("required_capabilities", [])
        
        # Convert to lowercase for comparison
        website_caps_lower = set(cap.lower() for cap in website_capabilities)
        
        # Check for capability mismatches (using all crawled content)
        for claimed_cap in claimed_capabilities:
            claimed_lower = claimed_cap.lower()
            
            # Check if this capability is mentioned on website
            found_on_website = False
            for website_cap in website_caps_lower:
                # Fuzzy matching - check for substring or similar keywords
                if claimed_lower in website_cap or website_cap in claimed_lower:
                    found_on_website = True
                    break
            
            if not found_on_website:
                # Check in all website text from all crawled pages
                all_website_text = " ".join([
                    website_data.get("main_text", ""),
                    website_data.get("services", ""),
                    website_data.get("about", ""),
                    " ".join(website_data.get("headings", []))
                ]).lower()
                
                if claimed_lower in all_website_text or any(word in all_website_text for word in claimed_lower.split() if len(word) > 4):
                    found_on_website = True
            
            if not found_on_website:
                # Calculate severity based on whether it's required
                is_required = any(
                    claimed_lower in req.lower() or req.lower() in claimed_lower
                    for req in required_capabilities
                )
                severity = 0.8 if is_required else 0.5
                
                gaps.append(WebsiteGap(
                    gap_type=GapType.CAPABILITY_MISSING,
                    description=f"Claimed capability '{claimed_cap}' not found on website",
                    claimed_value=claimed_cap,
                    website_value="Not mentioned",
                    severity=severity
                ))
        
        # Check for required capabilities missing from both claims and website
        claimed_caps_lower = set(cap.lower() for cap in claimed_capabilities)
        
        for req_cap in required_capabilities:
            req_lower = req_cap.lower()
            
            # Check if it's in claimed capabilities
            in_claimed = any(req_lower in claimed or claimed in req_lower 
                           for claimed in claimed_caps_lower)
            
            # Check if it's on website
            in_website = any(req_lower in website or website in req_lower 
                           for website in website_caps_lower)
            
            if not in_claimed and not in_website:
                gaps.append(WebsiteGap(
                    gap_type=GapType.TECHNICAL_EXPERTISE_GAP,
                    description=f"Required capability '{req_cap}' missing from both profile and website",
                    claimed_value="Not claimed",
                    website_value="Not found",
                    severity=1.0  # High severity - missing required capability
                ))
        
        # Check for certifications mentioned in profile but not on website
        claimed_certs = company_data.get("certifications", [])
        website_text = website_data.get("main_text", "").lower()
        
        for cert in claimed_certs:
            if cert.lower() not in website_text:
                gaps.append(WebsiteGap(
                    gap_type=GapType.CERTIFICATION_UNVERIFIED,
                    description=f"Certification '{cert}' claimed but not verified on website",
                    claimed_value=cert,
                    website_value="Not verified",
                    severity=0.6
                ))
        
        return gaps
    
    def _identify_confirmed_capabilities(
        self,
        company_data: Dict[str, Any],
        website_capabilities: List[str]
    ) -> List[str]:
        """Identify capabilities that are confirmed by website"""
        
        confirmed = []
        claimed_capabilities = company_data.get("capabilities", [])
        
        website_caps_lower = set(cap.lower() for cap in website_capabilities)
        
        for claimed_cap in claimed_capabilities:
            claimed_lower = claimed_cap.lower()
            
            # Check for match
            for website_cap in website_caps_lower:
                if claimed_lower in website_cap or website_cap in claimed_lower:
                    confirmed.append(claimed_cap)
                    break
        
        return confirmed
    
    async def _generate_partnering_opportunities(
        self,
        gaps: List[WebsiteGap],
        company_data: Dict[str, Any],
        solicitation_data: Dict[str, Any],
        website_capabilities: List[str]
    ) -> List[Dict[str, Any]]:
        """Generate partnering opportunity suggestions based on gaps"""
        
        opportunities = []
        
        # Focus on high-severity gaps that represent real capability shortfalls
        critical_gaps = [gap for gap in gaps if gap.severity >= 0.7]
        
        if not critical_gaps:
            return opportunities
        
        # If OpenAI is available, use AI to generate smart suggestions
        if self.openai_client:
            opportunities = await self._generate_partnering_opportunities_with_ai(
                critical_gaps,
                company_data,
                solicitation_data,
                website_capabilities
            )
        else:
            # Fallback: Generate basic suggestions
            for gap in critical_gaps:
                if gap.gap_type == GapType.CAPABILITY_MISSING:
                    opportunities.append({
                        "gap": gap.claimed_value,
                        "opportunity_type": "Capability Partnership",
                        "suggestion": f"Partner with a company that has strong {gap.claimed_value} capabilities to fill this gap",
                        "priority": "High" if gap.severity >= 0.8 else "Medium"
                    })
                elif gap.gap_type == GapType.TECHNICAL_EXPERTISE_GAP:
                    opportunities.append({
                        "gap": gap.claimed_value,
                        "opportunity_type": "Technical Partnership",
                        "suggestion": f"Form a teaming arrangement with a firm specialized in {gap.claimed_value}",
                        "priority": "Critical"
                    })
        
        return opportunities
    
    async def _generate_partnering_opportunities_with_ai(
        self,
        gaps: List[WebsiteGap],
        company_data: Dict[str, Any],
        solicitation_data: Dict[str, Any],
        website_capabilities: List[str]
    ) -> List[Dict[str, Any]]:
        """Use AI to generate smart partnering opportunity suggestions"""
        
        try:
            company_name = company_data.get("name", "the company")
            solicitation_title = solicitation_data.get("title", "this solicitation")
            
            gaps_description = "\n".join([
                f"- {gap.description} (Severity: {gap.severity:.0%})"
                for gap in gaps
            ])
            
            website_caps_str = ", ".join(website_capabilities) if website_capabilities else "None identified"
            
            prompt = f"""Analyze gaps between a company's profile and their website to suggest partnering opportunities.

Company: {company_name}
Solicitation: {solicitation_title}

Identified Gaps:
{gaps_description}

Verified Website Capabilities:
{website_caps_str}

Based on these gaps, suggest 2-4 specific partnering opportunities that would strengthen their bid. For each opportunity:
1. What type of partner they should seek (specific capability/expertise)
2. Why this partnership would be strategic
3. Priority level (Critical/High/Medium)

Format as JSON array with fields: gap, partner_type, rationale, priority"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert in government contracting and strategic partnerships. Provide actionable, specific suggestions."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.7
            )
            
            content = response.choices[0].message.content.strip()
            
            # Try to parse as JSON
            import json
            
            # Remove markdown code blocks if present
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            try:
                opportunities = json.loads(content)
                
                # Validate and format
                formatted_opportunities = []
                for opp in opportunities:
                    if isinstance(opp, dict):
                        formatted_opportunities.append({
                            "gap": opp.get("gap", "Unknown"),
                            "opportunity_type": opp.get("partner_type", "Partnership"),
                            "suggestion": opp.get("rationale", ""),
                            "priority": opp.get("priority", "Medium")
                        })
                
                return formatted_opportunities
                
            except json.JSONDecodeError:
                logger.warning("AI returned non-JSON partnering suggestions")
                # Fall back to text parsing
                return self._parse_opportunities_from_text(content, gaps)
            
        except Exception as e:
            logger.warning(f"AI partnering opportunity generation failed: {e}")
            return []
    
    def _parse_opportunities_from_text(
        self,
        text: str,
        gaps: List[WebsiteGap]
    ) -> List[Dict[str, Any]]:
        """Parse partnering opportunities from plain text response"""
        # Simple fallback parser
        opportunities = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if line and len(line) > 20:
                # Try to extract opportunity from line
                if any(keyword in line.lower() for keyword in ['partner', 'team', 'collaborate']):
                    opportunities.append({
                        "gap": gaps[0].claimed_value if gaps else "Multiple gaps",
                        "opportunity_type": "Strategic Partnership",
                        "suggestion": line,
                        "priority": "High"
                    })
        
        return opportunities[:4]  # Limit to 4
    
    def _calculate_validation_score(
        self,
        confirmed_capabilities: List[str],
        gaps: List[WebsiteGap],
        company_data: Dict[str, Any],
        solicitation_alignment: Optional[Dict[str, Any]] = None
    ) -> float:
        """Calculate overall validation score (0.0 to 1.0)"""
        
        claimed_capabilities = company_data.get("capabilities", [])
        
        if not claimed_capabilities:
            # If no claimed capabilities, use solicitation alignment if available
            if solicitation_alignment:
                return solicitation_alignment.get("overall_alignment_score", 0.5)
            return 0.5  # Neutral if no claims
        
        # Base score from confirmation rate
        confirmation_rate = len(confirmed_capabilities) / len(claimed_capabilities)
        
        # Penalty for gaps (weighted by severity)
        if gaps:
            avg_gap_severity = sum(gap.severity for gap in gaps) / len(gaps)
            gap_penalty = avg_gap_severity * 0.3  # Max 30% penalty
        else:
            gap_penalty = 0.0
        
        # Base score calculation
        base_score = confirmation_rate * 0.7 + (1.0 - gap_penalty) * 0.3
        
        # Enhance with solicitation alignment if available
        if solicitation_alignment:
            alignment_score = solicitation_alignment.get("overall_alignment_score", 0.0)
            # Weighted combination: 60% base score, 40% solicitation alignment
            score = (base_score * 0.6) + (alignment_score * 0.4)
        else:
            score = base_score
        
        return max(0.0, min(1.0, score))  # Clamp to [0, 1]
    
    def _generate_summary(
        self,
        company_name: str,
        validation_score: float,
        confirmed_capabilities: List[str],
        gaps: List[WebsiteGap],
        partnering_opportunities: List[Dict[str, Any]],
        website_data: Optional[Dict[str, Any]] = None,
        solicitation_alignment: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate human-readable summary with deep crawl information"""
        
        parts = []
        
        # Pages crawled info
        pages_crawled = website_data.get("pages_crawled", 1) if website_data else 1
        if pages_crawled > 1:
            parts.append(f"🔍 DEEP CRAWL: Analyzed {pages_crawled} pages")
        
        # Score assessment
        if validation_score >= 0.8:
            parts.append(f"✓ STRONG VALIDATION ({validation_score:.0%})")
        elif validation_score >= 0.6:
            parts.append(f"⚠ MODERATE VALIDATION ({validation_score:.0%})")
        else:
            parts.append(f"✗ WEAK VALIDATION ({validation_score:.0%})")
        
        # Solicitation alignment if available
        if solicitation_alignment:
            alignment_score = solicitation_alignment.get("overall_alignment_score", 0.0)
            parts.append(f"\n📋 SOLICITATION ALIGNMENT: {alignment_score:.0%}")
            
            matches = solicitation_alignment.get("capability_matches", [])
            if matches:
                parts.append(f"  ✓ {len(matches)} required capabilities confirmed on website")
            
            gaps_list = solicitation_alignment.get("capability_gaps", [])
            if gaps_list:
                parts.append(f"  ⚠ {len(gaps_list)} required capabilities not found")
        
        # Confirmed capabilities
        if confirmed_capabilities:
            parts.append(f"\n✅ CONFIRMED CAPABILITIES ({len(confirmed_capabilities)}): {', '.join(confirmed_capabilities[:3])}")
            if len(confirmed_capabilities) > 3:
                parts.append(f" + {len(confirmed_capabilities) - 3} more")
        
        # Gaps
        if gaps:
            critical_gaps = [g for g in gaps if g.severity >= 0.7]
            if critical_gaps:
                parts.append(f"\n\n⚠️ CRITICAL GAPS FOUND ({len(critical_gaps)}):")
                for gap in critical_gaps[:3]:
                    parts.append(f"\n  • {gap.description}")
        
        # Partnering opportunities
        if partnering_opportunities:
            parts.append(f"\n\n🤝 PARTNERING OPPORTUNITIES ({len(partnering_opportunities)}):")
            for opp in partnering_opportunities[:3]:
                parts.append(f"\n  • {opp.get('opportunity_type', 'Partnership')}: {opp.get('suggestion', '')[:100]}")
        
        return "".join(parts)
    
    def _create_no_website_result(
        self,
        company_name: str,
        company_data: Dict[str, Any],
        solicitation_data: Dict[str, Any]
    ) -> WebsiteValidationResult:
        """Create result for company with no website"""
        
        gaps = [
            WebsiteGap(
                gap_type=GapType.MARKET_FOCUS_DIFFERENT,
                description="No website available for validation",
                claimed_value="Website expected",
                website_value="None",
                severity=0.7
            )
        ]
        
        return WebsiteValidationResult(
            company_name=company_name,
            website_url="",
            website_accessible=False,
            validation_score=0.3,
            gaps_found=gaps,
            confirmed_capabilities=[],
            website_capabilities=[],
            partnering_opportunities=[],
            summary=f"⚠ NO WEBSITE - Cannot validate {company_name} claims against website"
        )
    
    def _create_inaccessible_website_result(
        self,
        company_name: str,
        website_url: str,
        company_data: Dict[str, Any],
        solicitation_data: Dict[str, Any]
    ) -> WebsiteValidationResult:
        """Create result for inaccessible website"""
        
        gaps = [
            WebsiteGap(
                gap_type=GapType.MARKET_FOCUS_DIFFERENT,
                description=f"Website {website_url} is not accessible",
                claimed_value="Accessible website",
                website_value="Inaccessible",
                severity=0.6
            )
        ]
        
        return WebsiteValidationResult(
            company_name=company_name,
            website_url=website_url,
            website_accessible=False,
            validation_score=0.4,
            gaps_found=gaps,
            confirmed_capabilities=[],
            website_capabilities=[],
            partnering_opportunities=[],
            summary=f"⚠ WEBSITE INACCESSIBLE - Cannot validate {company_name} against {website_url}"
        )
    
    def _create_invalid_content_result(
        self,
        company_name: str,
        website_url: str,
        company_data: Dict[str, Any],
        solicitation_data: Dict[str, Any]
    ) -> WebsiteValidationResult:
        """Create result for website with invalid/unverified content (anti-hallucination)"""
        
        gaps = [
            WebsiteGap(
                gap_type=GapType.MARKET_FOCUS_DIFFERENT,
                description=f"Website {website_url} content failed validation (insufficient/boilerplate content)",
                claimed_value="Valid website content",
                website_value="Invalid/unverified content",
                severity=0.8  # High severity - we can't trust unverified content
            )
        ]
        
        return WebsiteValidationResult(
            company_name=company_name,
            website_url=website_url,
            website_accessible=False,  # Mark as inaccessible since content is invalid
            validation_score=0.2,  # Low score for unverified content
            gaps_found=gaps,
            confirmed_capabilities=[],
            website_capabilities=[],
            partnering_opportunities=[],
            summary=f"⚠ CONTENT NOT VERIFIED - Website content for {company_name} failed validation checks (anti-hallucination safeguard)"
        )


