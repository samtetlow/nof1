"""
website_validator.py
Website Validation Module - Tests companies against their websites
Identifies differences and suggests partnering opportunities
"""

import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import asyncio

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
    1. Scrapes and analyzes company website
    2. Compares website content with claimed capabilities
    3. Identifies gaps and mismatches
    4. Suggests partnering opportunities based on gaps
    """
    
    def __init__(self, openai_api_key: Optional[str] = None):
        """Initialize website validator with optional AI enhancement"""
        self.openai_client = None
        if openai_api_key and openai:
            try:
                self.openai_client = openai.OpenAI(api_key=openai_api_key)
                logger.info("✓ OpenAI initialized for website validation")
            except Exception as e:
                logger.warning(f"Could not initialize OpenAI: {e}")
    
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
        
        # Scrape and analyze website
        website_data = await self._scrape_website(website_url)
        
        if not website_data.get("accessible"):
            return self._create_inaccessible_website_result(
                company_name, website_url, company_data, solicitation_data
            )
        
        # Extract capabilities from website
        website_capabilities = await self._extract_website_capabilities(
            website_data, company_name
        )
        
        # Compare claimed vs website capabilities
        gaps = await self._identify_gaps(
            company_data, 
            website_capabilities,
            solicitation_data,
            website_data
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
        
        # Calculate validation score
        validation_score = self._calculate_validation_score(
            confirmed_capabilities,
            gaps,
            company_data
        )
        
        # Generate summary
        summary = self._generate_summary(
            company_name,
            validation_score,
            confirmed_capabilities,
            gaps,
            partnering_opportunities
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
            raw_website_data=website_data
        )
    
    async def _scrape_website(self, url: str) -> Dict[str, Any]:
        """Scrape and extract key information from website"""
        if not httpx or not BeautifulSoup:
            logger.warning("httpx or BeautifulSoup not available")
            return {"accessible": False, "error": "Dependencies not installed"}
        
        try:
            # Normalize URL
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                response = await client.get(url)
                
                if response.status_code != 200:
                    return {"accessible": False, "status_code": response.status_code}
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract key elements
                data = {
                    "accessible": True,
                    "url": str(response.url),
                    "title": soup.title.string if soup.title else "",
                    "meta_description": self._extract_meta_description(soup),
                    "main_text": self._extract_main_text(soup),
                    "headings": self._extract_headings(soup),
                    "services": self._extract_services_section(soup),
                    "about": self._extract_about_section(soup),
                    "keywords": self._extract_keywords(soup)
                }
                
                logger.info(f"✓ Successfully scraped website: {url}")
                return data
                
        except httpx.TimeoutException:
            logger.warning(f"Website timeout: {url}")
            return {"accessible": False, "error": "Timeout"}
        except Exception as e:
            logger.warning(f"Website scraping error for {url}: {e}")
            return {"accessible": False, "error": str(e)}
    
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
        """Extract capabilities from website content using AI analysis"""
        
        # First, try keyword-based extraction
        keyword_capabilities = self._extract_capabilities_by_keywords(website_data)
        
        # If OpenAI is available, use AI to extract more sophisticated capabilities
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
    
    def _extract_capabilities_by_keywords(self, website_data: Dict[str, Any]) -> List[str]:
        """Extract capabilities using keyword matching"""
        capabilities = []
        
        # Combine relevant text
        text = " ".join([
            website_data.get("title", ""),
            website_data.get("meta_description", ""),
            website_data.get("services", ""),
            website_data.get("about", ""),
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
        """Use AI to extract capabilities from website content"""
        
        try:
            # Prepare website content for analysis
            content = f"""
Company: {company_name}
Title: {website_data.get('title', '')}
Description: {website_data.get('meta_description', '')}
Services: {website_data.get('services', '')[:500]}
About: {website_data.get('about', '')[:500]}
Headings: {', '.join(website_data.get('headings', [])[:10])}
"""
            
            prompt = f"""Analyze this company website content and extract their key capabilities and service offerings.

{content}

List 5-10 specific capabilities this company offers. Be concise and specific.
Format as a simple comma-separated list."""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing company websites and identifying their core capabilities."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
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
        
        # Check for capability mismatches
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
                # Also check in raw website text
                main_text = website_data.get("main_text", "").lower()
                if claimed_lower in main_text or any(word in main_text for word in claimed_lower.split() if len(word) > 4):
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
        company_data: Dict[str, Any]
    ) -> float:
        """Calculate overall validation score (0.0 to 1.0)"""
        
        claimed_capabilities = company_data.get("capabilities", [])
        
        if not claimed_capabilities:
            return 0.5  # Neutral if no claims
        
        # Base score from confirmation rate
        confirmation_rate = len(confirmed_capabilities) / len(claimed_capabilities)
        
        # Penalty for gaps (weighted by severity)
        if gaps:
            avg_gap_severity = sum(gap.severity for gap in gaps) / len(gaps)
            gap_penalty = avg_gap_severity * 0.3  # Max 30% penalty
        else:
            gap_penalty = 0.0
        
        # Calculate final score
        score = confirmation_rate * 0.7 + (1.0 - gap_penalty) * 0.3
        
        return max(0.0, min(1.0, score))  # Clamp to [0, 1]
    
    def _generate_summary(
        self,
        company_name: str,
        validation_score: float,
        confirmed_capabilities: List[str],
        gaps: List[WebsiteGap],
        partnering_opportunities: List[Dict[str, Any]]
    ) -> str:
        """Generate human-readable summary"""
        
        parts = []
        
        # Score assessment
        if validation_score >= 0.8:
            parts.append(f"✓ STRONG VALIDATION ({validation_score:.0%})")
        elif validation_score >= 0.6:
            parts.append(f"⚠ MODERATE VALIDATION ({validation_score:.0%})")
        else:
            parts.append(f"✗ WEAK VALIDATION ({validation_score:.0%})")
        
        # Confirmed capabilities
        if confirmed_capabilities:
            parts.append(f"\nConfirmed on Website ({len(confirmed_capabilities)}): {', '.join(confirmed_capabilities[:3])}")
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


