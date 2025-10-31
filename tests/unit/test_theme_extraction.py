"""
Unit tests for theme extraction functionality
"""
import pytest
from app import analyze_solicitation_themes, parse_solicitation_text


class TestThemeExtraction:
    """Test suite for solicitation theme extraction"""
    
    def test_analyze_solicitation_themes_basic(self, sample_solicitation_text):
        """Test basic theme extraction from solicitation text"""
        themes = analyze_solicitation_themes(sample_solicitation_text)
        
        assert themes is not None
        assert isinstance(themes, dict)
        assert "problem_areas" in themes
        assert "key_priorities" in themes
        assert "technical_capabilities" in themes
        assert "search_keywords" in themes
    
    def test_analyze_solicitation_themes_problem_areas(self, sample_solicitation_text):
        """Test that problem areas are extracted"""
        themes = analyze_solicitation_themes(sample_solicitation_text)
        
        assert len(themes["problem_areas"]) > 0
        # Should detect security/infrastructure concerns
        problem_text = " ".join(themes["problem_areas"]).lower()
        assert any(term in problem_text for term in ["security", "threat", "infrastructure", "protection"])
    
    def test_analyze_solicitation_themes_technical_capabilities(self, sample_solicitation_text):
        """Test that technical capabilities are identified"""
        themes = analyze_solicitation_themes(sample_solicitation_text)
        
        assert len(themes["technical_capabilities"]) > 0
        assert all(isinstance(cap, dict) for cap in themes["technical_capabilities"])
        assert all("area" in cap for cap in themes["technical_capabilities"])
    
    def test_analyze_solicitation_themes_search_keywords(self, sample_solicitation_text):
        """Test that search keywords are generated"""
        themes = analyze_solicitation_themes(sample_solicitation_text)
        
        assert len(themes["search_keywords"]) > 0
        keywords_lower = [kw.lower() for kw in themes["search_keywords"]]
        # Should include relevant technical terms
        assert any(term in keywords_lower for term in ["cybersecurity", "security", "monitoring", "detection"])
    
    def test_analyze_solicitation_themes_empty_input(self):
        """Test handling of empty input"""
        themes = analyze_solicitation_themes("")
        
        assert themes is not None
        assert themes["problem_areas"] == []
        assert themes["key_priorities"] == []
    
    def test_analyze_solicitation_themes_short_input(self):
        """Test handling of very short input"""
        themes = analyze_solicitation_themes("Test")
        
        assert themes is not None
        # Should handle gracefully even with minimal input
    
    def test_parse_solicitation_text_naics(self, sample_solicitation_text):
        """Test NAICS code extraction"""
        parsed = parse_solicitation_text(sample_solicitation_text)
        
        assert "naics_codes" in parsed
        assert "541512" in parsed["naics_codes"]
    
    def test_parse_solicitation_text_clearance(self, sample_solicitation_text):
        """Test security clearance detection"""
        parsed = parse_solicitation_text(sample_solicitation_text)
        
        assert "security_clearance" in parsed
        assert parsed["security_clearance"] == "Secret"
    
    def test_parse_solicitation_text_keywords(self, sample_solicitation_text):
        """Test keyword extraction"""
        parsed = parse_solicitation_text(sample_solicitation_text)
        
        assert "keywords" in parsed
        assert len(parsed["keywords"]) > 0
        keywords_lower = [kw.lower() for kw in parsed["keywords"]]
        assert any(term in keywords_lower for term in ["cybersecurity", "security", "monitoring"])




