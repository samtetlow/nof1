"""
Pytest configuration and shared fixtures
"""
import pytest
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

@pytest.fixture
def mock_config():
    """Mock configuration for tests"""
    return {
        "chatgpt": {
            "api_key": "test-key-123",
            "model": "gpt-3.5-turbo"
        }
    }

@pytest.fixture
def sample_solicitation_text():
    """Sample solicitation text for testing"""
    return """
    SOLICITATION TITLE: Advanced Cybersecurity Solutions
    NAICS: 541512
    
    The Department requires innovative cybersecurity solutions to address
    critical infrastructure protection. Must have experience with threat
    detection, incident response, and security operations.
    
    Key requirements:
    - 24/7 monitoring capabilities
    - SOC 2 Type II certification
    - Minimum 5 years experience
    - Secret clearance required
    """

@pytest.fixture
def sample_themes():
    """Sample extracted themes for testing"""
    return {
        "overview": "Cybersecurity solutions for critical infrastructure",
        "problem_statement": "Need for advanced threat detection and response",
        "problem_areas": [
            "Critical infrastructure vulnerabilities",
            "Threat detection gaps",
            "Incident response delays"
        ],
        "key_priorities": [
            "24/7 monitoring",
            "SOC 2 compliance",
            "Experienced team"
        ],
        "technical_capabilities": [
            {"area": "Cybersecurity", "terms": ["threat detection", "SOC", "monitoring"]},
            {"area": "Cloud Security", "terms": ["AWS", "Azure", "infrastructure"]}
        ],
        "evaluation_factors": ["Technical approach", "Past performance"],
        "search_keywords": ["cybersecurity", "threat", "detection", "monitoring", "SOC"]
    }

@pytest.fixture
def sample_company():
    """Sample company data for testing"""
    return {
        "name": "CyberSecure Solutions",
        "description": "Leading cybersecurity firm specializing in threat detection",
        "website": "https://cybersecure.example.com",
        "capabilities": ["Threat Detection", "SOC Operations", "Incident Response"],
        "source": "chatgpt",
        "relevance_score": 0.85
    }




