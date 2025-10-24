"""
validation_engine.py
Validation Engine - Final scoring and validation of confirmed matches
Provides comprehensive alignment score and recommendation
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class ValidationLevel(Enum):
    """Validation level classification"""
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    MARGINAL = "marginal"
    POOR = "poor"
    REJECTED = "rejected"


class RiskLevel(Enum):
    """Risk assessment levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ValidationScore:
    """Individual validation score component"""
    component_name: str
    score: float  # 0.0 to 1.0
    weight: float
    rationale: str
    risk_factors: List[str] = field(default_factory=list)


@dataclass
class ValidationResult:
    """Final validation result with comprehensive scoring"""
    company_id: str
    company_name: str
    solicitation_id: str
    
    # Core scores
    match_score: float  # From matching engine
    confirmation_score: float  # From confirmation engine
    validation_score: float  # Final composite score
    
    # Classification
    validation_level: ValidationLevel
    risk_level: RiskLevel
    recommendation: str
    
    # Detailed analysis
    score_components: List[ValidationScore]
    strengths: List[str]
    weaknesses: List[str]
    risks: List[str]
    opportunities: List[str]
    
    # Metrics
    alignment_percentage: float
    confidence_percentage: float
    data_quality_score: float
    
    # Actions
    recommended_actions: List[str]
    decision_rationale: str
    
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


class ValidationEngine:
    """
    Validation Engine - Module 6 (Final module in pipeline)
    
    Takes results from matching and confirmation engines to provide:
    1. Comprehensive validation score
    2. Risk assessment
    3. Detailed strengths/weaknesses analysis
    4. Final go/no-go recommendation
    5. Action items for improving fit
    """
    
    def __init__(self, config: Optional[Dict[str, float]] = None):
        # Validation component weights
        self.weights = config or {
            "match_quality": 0.30,
            "confirmation_quality": 0.25,
            "data_reliability": 0.15,
            "risk_assessment": 0.15,
            "strategic_fit": 0.15
        }
        
        # Scoring thresholds
        self.thresholds = {
            ValidationLevel.EXCELLENT: 0.85,
            ValidationLevel.GOOD: 0.70,
            ValidationLevel.ACCEPTABLE: 0.55,
            ValidationLevel.MARGINAL: 0.40,
            ValidationLevel.POOR: 0.25,
            ValidationLevel.REJECTED: 0.0
        }
    
    async def validate(
        self,
        company_data: Dict[str, Any],
        solicitation_data: Dict[str, Any],
        match_result: Dict[str, Any],
        confirmation_result: Any,  # ConfirmationResult from confirmation_engine
        enrichment_data: Dict[str, Any]
    ) -> ValidationResult:
        """
        Main validation method - produces final scoring and recommendation
        
        Args:
            company_data: Company profile
            solicitation_data: Solicitation requirements
            match_result: Results from matching engine
            confirmation_result: Results from confirmation engine
            enrichment_data: Enriched data from external sources
        
        Returns:
            ValidationResult with comprehensive scoring and recommendations
        """
        
        score_components = []
        
        # 1. Evaluate match quality
        match_component = self._evaluate_match_quality(match_result)
        score_components.append(match_component)
        
        # 2. Evaluate confirmation quality
        confirmation_component = self._evaluate_confirmation_quality(confirmation_result)
        score_components.append(confirmation_component)
        
        # 3. Assess data reliability
        data_component = self._assess_data_reliability(
            company_data, enrichment_data, confirmation_result
        )
        score_components.append(data_component)
        
        # 4. Perform risk assessment
        risk_component = self._assess_risks(
            company_data, solicitation_data, match_result, confirmation_result
        )
        score_components.append(risk_component)
        
        # 5. Evaluate strategic fit
        strategic_component = self._evaluate_strategic_fit(
            company_data, solicitation_data, enrichment_data
        )
        score_components.append(strategic_component)
        
        # Calculate composite validation score
        validation_score = self._calculate_validation_score(score_components)
        
        # Determine validation level and risk
        validation_level = self._determine_validation_level(validation_score)
        risk_level = self._determine_risk_level(risk_component, confirmation_result)
        
        # Generate SWOT analysis
        strengths, weaknesses, opportunities = self._generate_swot(
            match_result, confirmation_result, score_components
        )
        risks = self._extract_all_risks(score_components)
        
        # Generate recommendation and actions
        recommendation = self._generate_recommendation(
            validation_level, risk_level, validation_score
        )
        recommended_actions = self._generate_action_items(
            validation_level, weaknesses, risks, score_components
        )
        decision_rationale = self._generate_decision_rationale(
            validation_score, validation_level, score_components, confirmation_result
        )
        
        # Calculate metrics
        alignment_percentage = validation_score * 100
        confidence_percentage = confirmation_result.overall_confidence * 100 if hasattr(confirmation_result, 'overall_confidence') else 0.0
        data_quality_score = data_component.score
        
        return ValidationResult(
            company_id=company_data.get("company_id", ""),
            company_name=company_data.get("name", ""),
            solicitation_id=solicitation_data.get("job_id", ""),
            match_score=match_result.get("score", 0.0),
            confirmation_score=confirmation_result.overall_confidence if hasattr(confirmation_result, 'overall_confidence') else 0.0,
            validation_score=validation_score,
            validation_level=validation_level,
            risk_level=risk_level,
            recommendation=recommendation,
            score_components=score_components,
            strengths=strengths,
            weaknesses=weaknesses,
            risks=risks,
            opportunities=opportunities,
            recommended_actions=recommended_actions,
            decision_rationale=decision_rationale,
            alignment_percentage=alignment_percentage,
            confidence_percentage=confidence_percentage,
            data_quality_score=data_quality_score,
            timestamp=datetime.now(),
            metadata={
                "match_recommendation": match_result.get("recommendation", ""),
                "confirmation_status": confirmation_result.overall_status.value if hasattr(confirmation_result, 'overall_status') else "",
                "enrichment_sources": len(enrichment_data)
            }
        )
    
    def _evaluate_match_quality(self, match_result: Dict[str, Any]) -> ValidationScore:
        """Evaluate the quality of the initial match"""
        
        match_score = match_result.get("score", 0.0)
        strengths = match_result.get("strengths", [])
        gaps = match_result.get("gaps", [])
        
        # Adjust score based on strengths/gaps ratio
        strength_count = len(strengths)
        gap_count = len(gaps)
        
        adjusted_score = match_score
        if strength_count > 0 and gap_count > 0:
            ratio = strength_count / (strength_count + gap_count)
            adjusted_score = match_score * (0.7 + 0.3 * ratio)
        
        risk_factors = []
        if gap_count > strength_count:
            risk_factors.append("More gaps than strengths in initial match")
        if match_score < 0.5:
            risk_factors.append("Low initial match score")
        
        rationale = f"Match score: {match_score:.2f} with {strength_count} strengths and {gap_count} gaps"
        
        return ValidationScore(
            component_name="match_quality",
            score=adjusted_score,
            weight=self.weights["match_quality"],
            rationale=rationale,
            risk_factors=risk_factors
        )
    
    def _evaluate_confirmation_quality(self, confirmation_result: Any) -> ValidationScore:
        """Evaluate the quality of the confirmation"""
        
        if not hasattr(confirmation_result, 'overall_confidence'):
            return ValidationScore(
                component_name="confirmation_quality",
                score=0.0,
                weight=self.weights["confirmation_quality"],
                rationale="No confirmation data available",
                risk_factors=["Missing confirmation analysis"]
            )
        
        confirmation_score = confirmation_result.overall_confidence
        status = confirmation_result.overall_status.value
        
        # Adjust score based on status
        status_multipliers = {
            "confirmed": 1.0,
            "partially_confirmed": 0.75,
            "unconfirmed": 0.5,
            "contradicted": 0.2,
            "insufficient_data": 0.6
        }
        
        multiplier = status_multipliers.get(status, 0.5)
        adjusted_score = confirmation_score * multiplier
        
        risk_factors = []
        if status == "contradicted":
            risk_factors.append("Contradictions found in confirmation analysis")
        if status == "insufficient_data":
            risk_factors.append("Insufficient data for thorough confirmation")
        if confirmation_score < 0.5:
            risk_factors.append("Low confirmation confidence")
        
        # Count confirmed factors
        confirmed_count = sum(
            1 for factor in confirmation_result.factors
            if factor.status.value == "confirmed"
        )
        
        rationale = f"Confirmation: {status} with {confirmation_score:.2f} confidence ({confirmed_count} factors confirmed)"
        
        return ValidationScore(
            component_name="confirmation_quality",
            score=adjusted_score,
            weight=self.weights["confirmation_quality"],
            rationale=rationale,
            risk_factors=risk_factors
        )
    
    def _assess_data_reliability(
        self,
        company_data: Dict,
        enrichment_data: Dict,
        confirmation_result: Any
    ) -> ValidationScore:
        """Assess reliability and quality of data used"""
        
        reliability_score = 0.0
        risk_factors = []
        
        # Check company data completeness
        key_fields = ["name", "naics_codes", "capabilities", "size", "description"]
        filled_fields = sum(1 for field in key_fields if company_data.get(field))
        completeness = filled_fields / len(key_fields)
        reliability_score += completeness * 0.3
        
        if completeness < 0.6:
            risk_factors.append("Incomplete company profile data")
        
        # Check enrichment data quality
        enrichment_quality = 0.0  # Initialize outside if block
        if enrichment_data:
            successful_enrichments = sum(
                1 for data in enrichment_data.values()
                if hasattr(data, 'error') and not data.error and hasattr(data, 'data') and data.data
            )
            total_enrichments = len(enrichment_data)
            enrichment_quality = successful_enrichments / total_enrichments if total_enrichments > 0 else 0.0
            reliability_score += enrichment_quality * 0.4
            
            if enrichment_quality < 0.5:
                risk_factors.append("Low enrichment data success rate")
            
            # Check for high-confidence sources
            high_confidence_sources = sum(
                1 for data in enrichment_data.values()
                if hasattr(data, 'confidence') and data.confidence >= 0.8
            )
            if high_confidence_sources > 0:
                reliability_score += min(0.3, high_confidence_sources * 0.1)
        else:
            risk_factors.append("No external data enrichment")
        
        # Check data consistency (via confirmation)
        if hasattr(confirmation_result, 'detailed_analysis'):
            data_completeness = confirmation_result.detailed_analysis.get('data_completeness', {})
            overall_completeness = data_completeness.get('overall_completeness', 0.0)
            reliability_score = (reliability_score + overall_completeness) / 2
        
        rationale = f"Data reliability: {reliability_score:.2f} (company: {completeness:.1%}, enrichment: {enrichment_quality:.1%})"
        
        return ValidationScore(
            component_name="data_reliability",
            score=min(1.0, reliability_score),
            weight=self.weights["data_reliability"],
            rationale=rationale,
            risk_factors=risk_factors
        )
    
    def _assess_risks(
        self,
        company_data: Dict,
        solicitation_data: Dict,
        match_result: Dict,
        confirmation_result: Any
    ) -> ValidationScore:
        """Comprehensive risk assessment"""
        
        risk_score = 1.0  # Start high, reduce for each risk
        risk_factors = []
        
        # 1. Past performance risk
        if hasattr(confirmation_result, 'factors'):
            past_perf_factor = next(
                (f for f in confirmation_result.factors if f.factor_name == "past_performance_confirmation"),
                None
            )
            if past_perf_factor:
                if past_perf_factor.status.value in ["unconfirmed", "contradicted"]:
                    risk_factors.append("Unverified or contradicted past performance claims")
                    risk_score -= 0.3
                if past_perf_factor.contradictions:
                    risk_factors.extend(past_perf_factor.contradictions)
                    risk_score -= 0.2
        
        # 2. Capability gap risk
        gaps = match_result.get("gaps", [])
        if "Capabilities gap" in gaps or "NAICS mismatch" in gaps:
            risk_factors.append("Critical capability or NAICS gaps identified")
            risk_score -= 0.25
        
        # 3. Clearance risk
        required_clearance = solicitation_data.get("security_clearance")
        claimed_clearances = company_data.get("security_clearances", [])
        if required_clearance and required_clearance not in claimed_clearances:
            risk_factors.append(f"Required clearance ({required_clearance}) not confirmed")
            risk_score -= 0.3
        
        # 4. Set-aside compliance risk
        required_setasides = solicitation_data.get("set_asides", [])
        company_status = company_data.get("socioeconomic_status", [])
        if required_setasides:
            if not any(sa.lower() in [cs.lower() for cs in company_status] for sa in required_setasides):
                risk_factors.append("Set-aside requirement may not be met")
                risk_score -= 0.35
        
        # 5. Data quality risk
        if hasattr(confirmation_result, 'overall_status'):
            if confirmation_result.overall_status.value == "insufficient_data":
                risk_factors.append("Insufficient data for thorough evaluation")
                risk_score -= 0.2
        
        # 6. Size/scale risk
        employees = company_data.get("employees")
        if employees is not None and employees < 10:
            risk_factors.append("Very small team size may limit capacity")
            risk_score -= 0.15
        
        # 7. Experience risk (new to gov contracting)
        if hasattr(confirmation_result, 'factors'):
            past_perf = next(
                (f for f in confirmation_result.factors if f.factor_name == "past_performance_confirmation"),
                None
            )
            if past_perf and not past_perf.evidence:
                risk_factors.append("No documented government contracting experience")
                risk_score -= 0.2
        
        risk_score = max(0.0, risk_score)
        
        rationale = f"Risk assessment: {len(risk_factors)} risk factors identified, risk score: {risk_score:.2f}"
        
        return ValidationScore(
            component_name="risk_assessment",
            score=risk_score,
            weight=self.weights["risk_assessment"],
            rationale=rationale,
            risk_factors=risk_factors
        )
    
    def _evaluate_strategic_fit(
        self,
        company_data: Dict,
        solicitation_data: Dict,
        enrichment_data: Dict
    ) -> ValidationScore:
        """Evaluate strategic fit and long-term potential"""
        
        strategic_score = 0.5  # Start neutral
        risk_factors = []
        
        # 1. Agency alignment
        sol_agency = solicitation_data.get("agency", "").lower()
        if "usaspending" in enrichment_data:
            usa_data = enrichment_data["usaspending"]
            if hasattr(usa_data, 'data') and usa_data.data:
                agencies = [a.lower() for a in usa_data.data.get("agencies", [])]
                if any(sol_agency in agency for agency in agencies):
                    strategic_score += 0.2
        
        # 2. Innovation indicators
        has_patents = "uspto" in enrichment_data and enrichment_data["uspto"].data
        has_sbir = "sbir" in enrichment_data and enrichment_data["sbir"].data
        has_nih = "nih_reporter" in enrichment_data and enrichment_data["nih_reporter"].data
        
        if has_patents or has_sbir or has_nih:
            strategic_score += 0.2
        
        # 3. Market presence
        if hasattr(enrichment_data.get("google", {}), 'data'):
            google_data = enrichment_data["google"].data
            if google_data and google_data.get("total_results", 0) > 1000:
                strategic_score += 0.15
        
        # 4. Internal relationship
        if "hubspot" in enrichment_data:
            hubspot_data = enrichment_data["hubspot"]
            if hasattr(hubspot_data, 'data') and hubspot_data.data and not hubspot_data.error:
                strategic_score += 0.15
        
        # 5. Growth trajectory
        annual_revenue = company_data.get("annual_revenue")
        if annual_revenue is not None and annual_revenue > 5000000:  # $5M+
            strategic_score += 0.15
        elif annual_revenue is not None and annual_revenue < 500000:  # < $500K
            risk_factors.append("Limited revenue may indicate capacity constraints")
        
        # 6. Technical depth
        capabilities = company_data.get("capabilities", [])
        required_capabilities = solicitation_data.get("required_capabilities", [])
        if len(capabilities) >= len(required_capabilities) * 1.5:
            strategic_score += 0.15
        
        rationale = f"Strategic fit: {strategic_score:.2f} - evaluating long-term alignment and potential"
        
        return ValidationScore(
            component_name="strategic_fit",
            score=min(1.0, strategic_score),
            weight=self.weights["strategic_fit"],
            rationale=rationale,
            risk_factors=risk_factors
        )
    
    def _calculate_validation_score(self, components: List[ValidationScore]) -> float:
        """Calculate weighted composite validation score"""
        
        total_weight = sum(c.weight for c in components)
        if total_weight == 0:
            return 0.0
        
        weighted_score = sum(c.score * c.weight for c in components) / total_weight
        return max(0.0, min(1.0, weighted_score))
    
    def _determine_validation_level(self, score: float) -> ValidationLevel:
        """Determine validation level from score"""
        
        if score >= self.thresholds[ValidationLevel.EXCELLENT]:
            return ValidationLevel.EXCELLENT
        elif score >= self.thresholds[ValidationLevel.GOOD]:
            return ValidationLevel.GOOD
        elif score >= self.thresholds[ValidationLevel.ACCEPTABLE]:
            return ValidationLevel.ACCEPTABLE
        elif score >= self.thresholds[ValidationLevel.MARGINAL]:
            return ValidationLevel.MARGINAL
        elif score >= self.thresholds[ValidationLevel.POOR]:
            return ValidationLevel.POOR
        else:
            return ValidationLevel.REJECTED
    
    def _determine_risk_level(self, risk_component: ValidationScore, confirmation_result: Any) -> RiskLevel:
        """Determine overall risk level"""
        
        risk_count = len(risk_component.risk_factors)
        risk_score = risk_component.score
        
        # Check for critical risks
        critical_keywords = ["clearance", "set-aside", "contradicted"]
        has_critical = any(
            any(keyword in risk.lower() for keyword in critical_keywords)
            for risk in risk_component.risk_factors
        )
        
        if has_critical or risk_score < 0.3:
            return RiskLevel.CRITICAL
        elif risk_score < 0.5 or risk_count >= 5:
            return RiskLevel.HIGH
        elif risk_score < 0.7 or risk_count >= 3:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def _generate_swot(
        self,
        match_result: Dict,
        confirmation_result: Any,
        components: List[ValidationScore]
    ) -> Tuple[List[str], List[str], List[str]]:
        """Generate SWOT analysis (Strengths, Weaknesses, Opportunities)"""
        
        strengths = list(match_result.get("strengths", []))
        weaknesses = list(match_result.get("gaps", []))
        opportunities = []
        
        # Add confirmation-based strengths
        if hasattr(confirmation_result, 'factors'):
            for factor in confirmation_result.factors:
                if factor.status.value == "confirmed" and factor.evidence:
                    strengths.extend(factor.evidence[:2])  # Top 2 evidence items
        
        # Add component-based insights
        for component in components:
            if component.score >= 0.8:
                strengths.append(f"Strong {component.component_name.replace('_', ' ')}")
            elif component.score < 0.5:
                weaknesses.append(f"Weak {component.component_name.replace('_', ' ')}")
        
        # Identify opportunities
        if any(c.component_name == "strategic_fit" and c.score >= 0.7 for c in components):
            opportunities.append("Strong strategic alignment for long-term partnership")
        
        if hasattr(confirmation_result, 'factors'):
            market_factor = next(
                (f for f in confirmation_result.factors if f.factor_name == "market_presence"),
                None
            )
            if market_factor and market_factor.status.value == "confirmed":
                opportunities.append("Established market presence supports credibility")
        
        # Remove duplicates
        strengths = list(set(strengths))[:10]
        weaknesses = list(set(weaknesses))[:10]
        opportunities = list(set(opportunities))[:5]
        
        return strengths, weaknesses, opportunities
    
    def _extract_all_risks(self, components: List[ValidationScore]) -> List[str]:
        """Extract all risk factors from components"""
        
        all_risks = []
        for component in components:
            all_risks.extend(component.risk_factors)
        
        return list(set(all_risks))[:15]  # Top 15 unique risks
    
    def _generate_recommendation(
        self,
        validation_level: ValidationLevel,
        risk_level: RiskLevel,
        score: float
    ) -> str:
        """Generate final recommendation"""
        
        if validation_level == ValidationLevel.EXCELLENT and risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM]:
            return "✓ STRONGLY RECOMMEND - Proceed with proposal"
        elif validation_level == ValidationLevel.GOOD and risk_level != RiskLevel.CRITICAL:
            return "✓ RECOMMEND - Good fit, proceed with confidence"
        elif validation_level == ValidationLevel.ACCEPTABLE and risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM]:
            return "⚠ CONDITIONAL RECOMMEND - Proceed with risk mitigation"
        elif validation_level == ValidationLevel.MARGINAL:
            return "⚠ MARGINAL - Consider only if strategic value justifies risks"
        elif risk_level == RiskLevel.CRITICAL:
            return "✗ DO NOT RECOMMEND - Critical risks identified"
        else:
            return "✗ DO NOT RECOMMEND - Insufficient alignment"
    
    def _generate_action_items(
        self,
        validation_level: ValidationLevel,
        weaknesses: List[str],
        risks: List[str],
        components: List[ValidationScore]
    ) -> List[str]:
        """Generate recommended actions"""
        
        actions = []
        
        # Priority actions based on validation level
        if validation_level in [ValidationLevel.EXCELLENT, ValidationLevel.GOOD]:
            actions.append("Prepare proposal highlighting confirmed strengths")
            actions.append("Gather supporting documentation for past performance")
        elif validation_level == ValidationLevel.ACCEPTABLE:
            actions.append("Address identified gaps before proposal submission")
            actions.append("Develop risk mitigation strategies")
        else:
            actions.append("Evaluate whether opportunity aligns with company strategy")
            actions.append("Consider partnerships to address capability gaps")
        
        # Specific actions based on weaknesses
        if any("capability" in w.lower() or "gap" in w.lower() for w in weaknesses):
            actions.append("Document existing capabilities that address requirements")
            actions.append("Consider teaming arrangements for missing capabilities")
        
        if any("past performance" in w.lower() for w in weaknesses):
            actions.append("Compile detailed past performance narratives")
            actions.append("Obtain customer references and testimonials")
        
        # Risk-based actions
        if any("clearance" in r.lower() for r in risks):
            actions.append("Verify FSO and facility clearance status")
            actions.append("Plan for employee clearance processing timelines")
        
        if any("set-aside" in r.lower() for r in risks):
            actions.append("Verify small business certifications and registrations")
            actions.append("Ensure SAM.gov profile is current")
        
        # Data quality actions
        data_component = next((c for c in components if c.component_name == "data_reliability"), None)
        if data_component and data_component.score < 0.6:
            actions.append("Update company profile with missing information")
            actions.append("Enhance capability statement documentation")
        
        return actions[:10]  # Top 10 actions
    
    def _generate_decision_rationale(
        self,
        score: float,
        level: ValidationLevel,
        components: List[ValidationScore],
        confirmation_result: Any
    ) -> str:
        """Generate detailed decision rationale"""
        
        rationale_parts = []
        
        rationale_parts.append(f"Validation Score: {score:.1%} ({level.value.upper()})")
        rationale_parts.append("")
        
        # Component breakdown
        rationale_parts.append("Score Breakdown:")
        for component in components:
            weighted_contribution = component.score * component.weight
            rationale_parts.append(
                f"  • {component.component_name.replace('_', ' ').title()}: "
                f"{component.score:.1%} (weighted: {weighted_contribution:.1%})"
            )
        
        rationale_parts.append("")
        rationale_parts.append("Key Findings:")
        
        # Highlight top performing components
        top_components = sorted(components, key=lambda x: x.score, reverse=True)[:2]
        for comp in top_components:
            if comp.score >= 0.7:
                rationale_parts.append(f"  + {comp.rationale}")
        
        # Highlight concerns
        low_components = [c for c in components if c.score < 0.5]
        if low_components:
            rationale_parts.append("")
            rationale_parts.append("  Concerns:")
            for comp in low_components:
                rationale_parts.append(f"  - {comp.rationale}")
        
        # Confirmation summary
        if hasattr(confirmation_result, 'summary'):
            rationale_parts.append("")
            rationale_parts.append("Confirmation Summary:")
            rationale_parts.append(f"  {confirmation_result.summary}")
        
        return "\n".join(rationale_parts)



