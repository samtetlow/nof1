"""
confirmation_engine.py
Confirmation Engine - Verifies and confirms alignment between matches
Uses enriched data from external sources to validate matching results
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class ConfirmationStatus(Enum):
    """Status of confirmation check"""
    CONFIRMED = "confirmed"
    PARTIALLY_CONFIRMED = "partially_confirmed"
    UNCONFIRMED = "unconfirmed"
    CONTRADICTED = "contradicted"
    INSUFFICIENT_DATA = "insufficient_data"


@dataclass
class ConfirmationFactor:
    """Individual factor in confirmation analysis"""
    factor_name: str
    status: ConfirmationStatus
    confidence: float
    evidence: List[str]
    contradictions: List[str] = field(default_factory=list)
    weight: float = 1.0


@dataclass
class ConfirmationResult:
    """Result of confirmation engine analysis"""
    company_id: str
    company_name: str
    solicitation_id: str
    overall_status: ConfirmationStatus
    overall_confidence: float
    factors: List[ConfirmationFactor]
    enrichment_sources_used: List[str]
    summary: str
    timestamp: datetime
    detailed_analysis: Dict[str, Any] = field(default_factory=dict)


class ConfirmationEngine:
    """
    Confirmation Engine - Module 5 in the pipeline
    
    Takes matching results and enriched data from external sources to:
    1. Verify claimed capabilities exist in real-world data
    2. Confirm past performance through contract databases
    3. Validate company attributes (size, certifications, clearances)
    4. Check for contradictions or red flags
    5. Assess confidence in the match quality
    """
    
    def __init__(self, weights: Optional[Dict[str, float]] = None):
        # Weights for different confirmation factors
        self.weights = weights or {
            "past_performance_confirmation": 0.25,
            "capability_verification": 0.25,
            "certification_validation": 0.15,
            "size_clearance_confirmation": 0.15,
            "market_presence": 0.10,
            "technical_expertise": 0.10
        }
    
    async def confirm_match(
        self,
        company_data: Dict[str, Any],
        solicitation_data: Dict[str, Any],
        match_result: Dict[str, Any],
        enrichment_data: Dict[str, Any]
    ) -> ConfirmationResult:
        """
        Main confirmation method - analyzes match using enriched data
        
        Args:
            company_data: Company profile from database
            solicitation_data: Solicitation requirements
            match_result: Initial matching engine results
            enrichment_data: Data from external sources (data_sources module)
        
        Returns:
            ConfirmationResult with detailed verification
        """
        
        factors = []
        sources_used = list(enrichment_data.keys())
        
        # 1. Confirm past performance through contract databases
        past_perf_factor = await self._confirm_past_performance(
            company_data, solicitation_data, enrichment_data
        )
        factors.append(past_perf_factor)
        
        # 2. Verify capabilities through multiple sources
        capability_factor = await self._verify_capabilities(
            company_data, solicitation_data, enrichment_data
        )
        factors.append(capability_factor)
        
        # 3. Validate certifications and compliance
        cert_factor = await self._validate_certifications(
            company_data, solicitation_data, enrichment_data
        )
        factors.append(cert_factor)
        
        # 4. Confirm size status and clearances
        size_clear_factor = await self._confirm_size_and_clearance(
            company_data, solicitation_data, enrichment_data
        )
        factors.append(size_clear_factor)
        
        # 5. Assess market presence and reputation
        market_factor = await self._assess_market_presence(
            company_data, enrichment_data
        )
        factors.append(market_factor)
        
        # 6. Verify technical expertise
        tech_factor = await self._verify_technical_expertise(
            company_data, solicitation_data, enrichment_data
        )
        factors.append(tech_factor)
        
        # Calculate overall confirmation status and confidence
        overall_status, overall_confidence = self._calculate_overall_confirmation(factors)
        
        # Generate summary
        summary = self._generate_summary(factors, overall_status, overall_confidence)
        
        return ConfirmationResult(
            company_id=company_data.get("company_id", ""),
            company_name=company_data.get("name", ""),
            solicitation_id=solicitation_data.get("job_id", ""),
            overall_status=overall_status,
            overall_confidence=overall_confidence,
            factors=factors,
            enrichment_sources_used=sources_used,
            summary=summary,
            timestamp=datetime.now(),
            detailed_analysis={
                "match_score": match_result.get("score", 0.0),
                "enrichment_quality": self._assess_enrichment_quality(enrichment_data),
                "data_completeness": self._assess_data_completeness(company_data, enrichment_data)
            }
        )
    
    async def _confirm_past_performance(
        self,
        company_data: Dict,
        solicitation_data: Dict,
        enrichment_data: Dict
    ) -> ConfirmationFactor:
        """Confirm past performance through contract databases"""
        
        evidence = []
        contradictions = []
        confidence = 0.0
        
        # Check USASpending.gov data
        if "usaspending" in enrichment_data:
            usa_data = enrichment_data["usaspending"].data
            if usa_data and not enrichment_data["usaspending"].error:
                contracts = usa_data.get("recent_contracts", [])
                total_value = usa_data.get("total_value", 0)
                
                if contracts:
                    evidence.append(f"Found {len(contracts)} federal contracts in USASpending.gov")
                    evidence.append(f"Total contract value: ${total_value:,.2f}")
                    confidence += 0.4
                    
                    # Check for relevant agencies
                    sol_agency = solicitation_data.get("agency", "").lower()
                    agencies = [c.get("awarding_agency", "").lower() for c in contracts]
                    if sol_agency and any(sol_agency in agency for agency in agencies):
                        evidence.append(f"Previous work with {sol_agency.upper()}")
                        confidence += 0.2
        
        # Check NIH Reporter for health/research grants
        if "nih_reporter" in enrichment_data:
            nih_data = enrichment_data["nih_reporter"].data
            if nih_data and not enrichment_data["nih_reporter"].error:
                grants = nih_data.get("recent_grants", [])
                if grants:
                    evidence.append(f"Found {len(grants)} NIH research grants")
                    confidence += 0.3
        
        # Check SBIR awards
        if "sbir" in enrichment_data:
            sbir_data = enrichment_data["sbir"].data
            if sbir_data and not enrichment_data["sbir"].error:
                awards = sbir_data.get("recent_awards", [])
                if awards:
                    evidence.append(f"Found {len(awards)} SBIR/STTR awards")
                    phases = sbir_data.get("phases", [])
                    if "Phase II" in phases or "Phase III" in phases:
                        evidence.append("Company has advanced to Phase II/III SBIR")
                        confidence += 0.3
                    else:
                        confidence += 0.2
        
        # Check for contradictions
        if company_data.get("description", ""):
            if not evidence:
                if "extensive government experience" in company_data["description"].lower():
                    contradictions.append("Claims government experience but no contracts found in public databases")
                    confidence = max(0, confidence - 0.3)
        
        # Determine status
        if confidence >= 0.7:
            status = ConfirmationStatus.CONFIRMED
        elif confidence >= 0.4:
            status = ConfirmationStatus.PARTIALLY_CONFIRMED
        elif contradictions:
            status = ConfirmationStatus.CONTRADICTED
        elif not evidence:
            status = ConfirmationStatus.INSUFFICIENT_DATA
        else:
            status = ConfirmationStatus.UNCONFIRMED
        
        return ConfirmationFactor(
            factor_name="past_performance_confirmation",
            status=status,
            confidence=min(1.0, confidence),
            evidence=evidence,
            contradictions=contradictions,
            weight=self.weights["past_performance_confirmation"]
        )
    
    async def _verify_capabilities(
        self,
        company_data: Dict,
        solicitation_data: Dict,
        enrichment_data: Dict
    ) -> ConfirmationFactor:
        """Verify capabilities through AI analysis and market data"""
        
        evidence = []
        contradictions = []
        confidence = 0.0
        
        claimed_capabilities = set(cap.lower() for cap in company_data.get("capabilities", []))
        required_capabilities = set(cap.lower() for cap in solicitation_data.get("required_capabilities", []))
        
        # Check AI analysis (Claude, ChatGPT)
        ai_sources = ["claude", "chatgpt"]
        for source in ai_sources:
            if source in enrichment_data:
                ai_data = enrichment_data[source].data
                if ai_data and not enrichment_data[source].error:
                    ai_capabilities = ai_data.get("capabilities", [])
                    if isinstance(ai_capabilities, list):
                        ai_cap_set = set(cap.lower() for cap in ai_capabilities)
                        
                        # Check overlap with claimed capabilities
                        overlap = claimed_capabilities & ai_cap_set
                        if overlap:
                            evidence.append(f"{source.upper()} confirms: {', '.join(list(overlap)[:3])}")
                            confidence += 0.3
                        
                        # Check for required capabilities
                        req_overlap = required_capabilities & ai_cap_set
                        if req_overlap:
                            evidence.append(f"AI analysis identifies required capabilities: {', '.join(list(req_overlap)[:3])}")
                            confidence += 0.2
        
        # Check HubSpot internal data
        if "hubspot" in enrichment_data:
            hubspot_data = enrichment_data["hubspot"].data
            if hubspot_data and not enrichment_data["hubspot"].error:
                industry = hubspot_data.get("industry", "")
                if industry:
                    evidence.append(f"HubSpot industry: {industry}")
                    confidence += 0.2
        
        # Check Google search results for capability mentions
        if "google" in enrichment_data:
            google_data = enrichment_data["google"].data
            if google_data and not enrichment_data["google"].error:
                results = google_data.get("search_results", [])
                capability_mentions = 0
                for result in results:
                    snippet = result.get("snippet", "").lower()
                    for cap in claimed_capabilities:
                        if cap in snippet:
                            capability_mentions += 1
                
                if capability_mentions > 0:
                    evidence.append(f"Google search confirms {capability_mentions} capability mentions")
                    confidence += min(0.3, capability_mentions * 0.1)
        
        # Check for contradictions
        if claimed_capabilities and confidence < 0.2:
            contradictions.append("Claimed capabilities not strongly supported by external sources")
        
        # Determine status
        if confidence >= 0.7:
            status = ConfirmationStatus.CONFIRMED
        elif confidence >= 0.4:
            status = ConfirmationStatus.PARTIALLY_CONFIRMED
        elif contradictions:
            status = ConfirmationStatus.CONTRADICTED
        elif not evidence:
            status = ConfirmationStatus.INSUFFICIENT_DATA
        else:
            status = ConfirmationStatus.UNCONFIRMED
        
        return ConfirmationFactor(
            factor_name="capability_verification",
            status=status,
            confidence=min(1.0, confidence),
            evidence=evidence,
            contradictions=contradictions,
            weight=self.weights["capability_verification"]
        )
    
    async def _validate_certifications(
        self,
        company_data: Dict,
        solicitation_data: Dict,
        enrichment_data: Dict
    ) -> ConfirmationFactor:
        """Validate certifications and socioeconomic status"""
        
        evidence = []
        contradictions = []
        confidence = 0.5  # Neutral unless we find strong evidence
        
        claimed_status = company_data.get("socioeconomic_status", [])
        required_status = solicitation_data.get("set_asides", [])
        
        # Check SBIR data (indicates small business)
        if "sbir" in enrichment_data:
            sbir_data = enrichment_data["sbir"].data
            if sbir_data and not enrichment_data["sbir"].error:
                if sbir_data.get("total_awards", 0) > 0:
                    evidence.append("SBIR awards confirm small business status")
                    if "Small Business" in required_status or "SB" in required_status:
                        confidence += 0.3
        
        # Check USASpending for set-aside contracts
        if "usaspending" in enrichment_data:
            usa_data = enrichment_data["usaspending"].data
            if usa_data and not enrichment_data["usaspending"].error:
                # In real implementation, would check contract set-aside types
                if usa_data.get("total_contracts", 0) > 0:
                    evidence.append("Previous federal contracts found (status verification pending)")
                    confidence += 0.2
        
        # Check company size indicators
        employees = company_data.get("employees")
        revenue = company_data.get("annual_revenue")
        
        if employees or revenue:
            if employees and employees < 500:
                evidence.append(f"Employee count ({employees}) consistent with small business")
                confidence += 0.2
            elif revenue and revenue < 10000000:  # $10M
                evidence.append(f"Revenue consistent with small business")
                confidence += 0.2
        
        # Determine status
        if confidence >= 0.7:
            status = ConfirmationStatus.CONFIRMED
        elif confidence >= 0.4:
            status = ConfirmationStatus.PARTIALLY_CONFIRMED
        elif contradictions:
            status = ConfirmationStatus.CONTRADICTED
        else:
            status = ConfirmationStatus.INSUFFICIENT_DATA
        
        return ConfirmationFactor(
            factor_name="certification_validation",
            status=status,
            confidence=min(1.0, confidence),
            evidence=evidence,
            contradictions=contradictions,
            weight=self.weights["certification_validation"]
        )
    
    async def _confirm_size_and_clearance(
        self,
        company_data: Dict,
        solicitation_data: Dict,
        enrichment_data: Dict
    ) -> ConfirmationFactor:
        """Confirm company size and security clearance capabilities"""
        
        evidence = []
        contradictions = []
        confidence = 0.5
        
        # Size confirmation
        claimed_size = company_data.get("size", "").lower()
        employees = company_data.get("employees", 0)
        
        if employees:
            if claimed_size == "small" and employees < 500:
                evidence.append(f"Size claim consistent: {employees} employees")
                confidence += 0.2
            elif claimed_size == "large" and employees >= 500:
                evidence.append(f"Size claim consistent: {employees} employees")
                confidence += 0.2
        
        # Clearance verification
        claimed_clearances = company_data.get("security_clearances", [])
        required_clearance = solicitation_data.get("security_clearance")
        
        if claimed_clearances:
            # In real implementation, would verify through CAGE code or FSO verification
            evidence.append(f"Company claims clearances: {', '.join(claimed_clearances)}")
            
            if required_clearance and required_clearance in claimed_clearances:
                evidence.append(f"Required clearance ({required_clearance}) is claimed")
                confidence += 0.3
            else:
                evidence.append("Note: Clearance claims require independent verification")
        
        # Check for DoD/IC work in contracts
        if "usaspending" in enrichment_data:
            usa_data = enrichment_data["usaspending"].data
            if usa_data:
                agencies = usa_data.get("agencies", [])
                classified_agencies = ["DoD", "Defense", "Intelligence", "CIA", "NSA", "DIA"]
                
                for agency in agencies:
                    if any(ca.lower() in agency.lower() for ca in classified_agencies):
                        evidence.append(f"Past work with {agency} suggests clearance capability")
                        confidence += 0.2
                        break
        
        if confidence >= 0.7:
            status = ConfirmationStatus.CONFIRMED
        elif confidence >= 0.4:
            status = ConfirmationStatus.PARTIALLY_CONFIRMED
        else:
            status = ConfirmationStatus.INSUFFICIENT_DATA
        
        return ConfirmationFactor(
            factor_name="size_clearance_confirmation",
            status=status,
            confidence=min(1.0, confidence),
            evidence=evidence,
            contradictions=contradictions,
            weight=self.weights["size_clearance_confirmation"]
        )
    
    async def _assess_market_presence(
        self,
        company_data: Dict,
        enrichment_data: Dict
    ) -> ConfirmationFactor:
        """Assess overall market presence and reputation"""
        
        evidence = []
        contradictions = []
        confidence = 0.0
        
        # Check Google search results
        if "google" in enrichment_data:
            google_data = enrichment_data["google"].data
            if google_data:
                total_results = google_data.get("total_results", 0)
                if total_results > 1000:
                    evidence.append(f"Strong web presence: {total_results} search results")
                    confidence += 0.3
                elif total_results > 100:
                    evidence.append(f"Moderate web presence: {total_results} search results")
                    confidence += 0.2
        
        # Check website
        website = company_data.get("website")
        if website:
            evidence.append(f"Company website: {website}")
            confidence += 0.1
        
        # Check HubSpot engagement
        if "hubspot" in enrichment_data:
            hubspot_data = enrichment_data["hubspot"].data
            if hubspot_data and not enrichment_data["hubspot"].error:
                evidence.append("Active in HubSpot CRM (internal relationship)")
                confidence += 0.3
        
        # Check patents (innovation indicator)
        if "uspto" in enrichment_data:
            uspto_data = enrichment_data["uspto"].data
            if uspto_data and not enrichment_data["uspto"].error:
                patent_count = uspto_data.get("total_patents", 0)
                if patent_count > 0:
                    evidence.append(f"Patent portfolio: {patent_count} patents")
                    confidence += 0.3
        
        # Check funding/startup data
        if "pitchbook" in enrichment_data or "angellist" in enrichment_data:
            evidence.append("Funding data available (indicates investor confidence)")
            confidence += 0.2
        
        if confidence >= 0.6:
            status = ConfirmationStatus.CONFIRMED
        elif confidence >= 0.3:
            status = ConfirmationStatus.PARTIALLY_CONFIRMED
        elif not evidence:
            status = ConfirmationStatus.INSUFFICIENT_DATA
        else:
            status = ConfirmationStatus.UNCONFIRMED
        
        return ConfirmationFactor(
            factor_name="market_presence",
            status=status,
            confidence=min(1.0, confidence),
            evidence=evidence,
            contradictions=contradictions,
            weight=self.weights["market_presence"]
        )
    
    async def _verify_technical_expertise(
        self,
        company_data: Dict,
        solicitation_data: Dict,
        enrichment_data: Dict
    ) -> ConfirmationFactor:
        """Verify technical expertise through patents, publications, and project history"""
        
        evidence = []
        contradictions = []
        confidence = 0.0
        
        required_keywords = set(kw.lower() for kw in solicitation_data.get("keywords", []))
        
        # Check patents for technical keywords
        if "uspto" in enrichment_data:
            uspto_data = enrichment_data["uspto"].data
            if uspto_data and not enrichment_data["uspto"].error:
                patents = uspto_data.get("patents", [])
                if patents:
                    patent_titles = [p.get("patent_title", "").lower() for p in patents]
                    keyword_matches = 0
                    for keyword in required_keywords:
                        if any(keyword in title for title in patent_titles):
                            keyword_matches += 1
                    
                    if keyword_matches > 0:
                        evidence.append(f"Patents align with {keyword_matches} required keywords")
                        confidence += min(0.4, keyword_matches * 0.15)
        
        # Check NIH grants (research expertise)
        if "nih_reporter" in enrichment_data:
            nih_data = enrichment_data["nih_reporter"].data
            if nih_data and not enrichment_data["nih_reporter"].error:
                grants = nih_data.get("recent_grants", [])
                if grants:
                    evidence.append(f"Research expertise: {len(grants)} NIH grants")
                    confidence += 0.3
        
        # Check SBIR projects (innovation track record)
        if "sbir" in enrichment_data:
            sbir_data = enrichment_data["sbir"].data
            if sbir_data and not enrichment_data["sbir"].error:
                phases = sbir_data.get("phases", [])
                if "Phase II" in phases:
                    evidence.append("Proven innovation: SBIR Phase II awards")
                    confidence += 0.3
        
        # Check AI analysis for technical depth
        for ai_source in ["claude", "chatgpt"]:
            if ai_source in enrichment_data:
                ai_data = enrichment_data[ai_source].data
                if ai_data:
                    differentiators = ai_data.get("key_differentiators", [])
                    if differentiators:
                        evidence.append(f"{ai_source.upper()} identifies technical differentiators")
                        confidence += 0.2
                        break
        
        if confidence >= 0.7:
            status = ConfirmationStatus.CONFIRMED
        elif confidence >= 0.4:
            status = ConfirmationStatus.PARTIALLY_CONFIRMED
        elif not evidence:
            status = ConfirmationStatus.INSUFFICIENT_DATA
        else:
            status = ConfirmationStatus.UNCONFIRMED
        
        return ConfirmationFactor(
            factor_name="technical_expertise",
            status=status,
            confidence=min(1.0, confidence),
            evidence=evidence,
            contradictions=contradictions,
            weight=self.weights["technical_expertise"]
        )
    
    def _calculate_overall_confirmation(
        self,
        factors: List[ConfirmationFactor]
    ) -> Tuple[ConfirmationStatus, float]:
        """Calculate overall confirmation status and confidence"""
        
        # Weighted average of confidences
        total_weight = sum(f.weight for f in factors)
        weighted_confidence = sum(f.confidence * f.weight for f in factors) / total_weight if total_weight > 0 else 0.0
        
        # Count statuses
        status_counts = {
            ConfirmationStatus.CONFIRMED: 0,
            ConfirmationStatus.PARTIALLY_CONFIRMED: 0,
            ConfirmationStatus.UNCONFIRMED: 0,
            ConfirmationStatus.CONTRADICTED: 0,
            ConfirmationStatus.INSUFFICIENT_DATA: 0
        }
        
        for factor in factors:
            status_counts[factor.status] += 1
        
        # Determine overall status
        if status_counts[ConfirmationStatus.CONTRADICTED] > 0:
            overall_status = ConfirmationStatus.CONTRADICTED
        elif status_counts[ConfirmationStatus.CONFIRMED] >= len(factors) * 0.6:
            overall_status = ConfirmationStatus.CONFIRMED
        elif status_counts[ConfirmationStatus.CONFIRMED] + status_counts[ConfirmationStatus.PARTIALLY_CONFIRMED] >= len(factors) * 0.5:
            overall_status = ConfirmationStatus.PARTIALLY_CONFIRMED
        elif status_counts[ConfirmationStatus.INSUFFICIENT_DATA] >= len(factors) * 0.5:
            overall_status = ConfirmationStatus.INSUFFICIENT_DATA
        else:
            overall_status = ConfirmationStatus.UNCONFIRMED
        
        return overall_status, weighted_confidence
    
    def _generate_summary(
        self,
        factors: List[ConfirmationFactor],
        overall_status: ConfirmationStatus,
        overall_confidence: float
    ) -> str:
        """Generate human-readable summary"""
        
        confirmed_factors = [f for f in factors if f.status == ConfirmationStatus.CONFIRMED]
        partial_factors = [f for f in factors if f.status == ConfirmationStatus.PARTIALLY_CONFIRMED]
        contradicted_factors = [f for f in factors if f.status == ConfirmationStatus.CONTRADICTED]
        
        summary_parts = []
        
        if overall_status == ConfirmationStatus.CONFIRMED:
            summary_parts.append(f"✓ CONFIRMED MATCH (Confidence: {overall_confidence:.1%})")
        elif overall_status == ConfirmationStatus.PARTIALLY_CONFIRMED:
            summary_parts.append(f"⚠ PARTIALLY CONFIRMED (Confidence: {overall_confidence:.1%})")
        elif overall_status == ConfirmationStatus.CONTRADICTED:
            summary_parts.append(f"✗ CONTRADICTIONS FOUND (Confidence: {overall_confidence:.1%})")
        else:
            summary_parts.append(f"? INSUFFICIENT DATA (Confidence: {overall_confidence:.1%})")
        
        if confirmed_factors:
            summary_parts.append(f"\nConfirmed: {', '.join(f.factor_name for f in confirmed_factors)}")
        
        if partial_factors:
            summary_parts.append(f"\nPartially Confirmed: {', '.join(f.factor_name for f in partial_factors)}")
        
        if contradicted_factors:
            summary_parts.append(f"\nContradictions: {', '.join(f.factor_name for f in contradicted_factors)}")
        
        return "\n".join(summary_parts)
    
    def _assess_enrichment_quality(self, enrichment_data: Dict) -> Dict[str, Any]:
        """Assess quality of enrichment data"""
        
        total_sources = len(enrichment_data)
        successful_sources = sum(
            1 for data in enrichment_data.values()
            if not data.error and data.data
        )
        
        avg_confidence = sum(
            data.confidence for data in enrichment_data.values()
        ) / total_sources if total_sources > 0 else 0.0
        
        return {
            "total_sources": total_sources,
            "successful_sources": successful_sources,
            "success_rate": successful_sources / total_sources if total_sources > 0 else 0.0,
            "average_confidence": avg_confidence
        }
    
    def _assess_data_completeness(
        self,
        company_data: Dict,
        enrichment_data: Dict
    ) -> Dict[str, Any]:
        """Assess completeness of available data"""
        
        # Check key company fields
        key_fields = ["name", "naics_codes", "capabilities", "size", "description"]
        filled_fields = sum(1 for field in key_fields if company_data.get(field))
        
        # Check enrichment coverage
        priority_sources = ["usaspending", "hubspot", "claude", "chatgpt"]
        covered_sources = sum(
            1 for source in priority_sources
            if source in enrichment_data and not enrichment_data[source].error
        )
        
        return {
            "company_data_completeness": filled_fields / len(key_fields),
            "enrichment_coverage": covered_sources / len(priority_sources),
            "overall_completeness": (filled_fields / len(key_fields) + covered_sources / len(priority_sources)) / 2
        }



