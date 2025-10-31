"""
Unit tests for FastAPI endpoints
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app import app

client = TestClient(app)


class TestHealthEndpoints:
    """Test suite for health check endpoints"""
    
    def test_root_health_endpoint(self):
        """Test root health check"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
        assert "version" in data
    
    def test_health_endpoint(self):
        """Test /health endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "data_sources_available" in data


class TestSolicitationEndpoints:
    """Test suite for solicitation-related endpoints"""
    
    @patch('app.analyze_solicitation_themes')
    @patch('app.parse_solicitation_text')
    def test_upload_solicitation_text(self, mock_parse, mock_analyze):
        """Test uploading solicitation via text"""
        mock_parse.return_value = {
            "naics_codes": ["541512"],
            "keywords": ["cybersecurity"]
        }
        mock_analyze.return_value = {
            "problem_areas": ["Security gaps"],
            "key_priorities": ["24/7 monitoring"]
        }
        
        response = client.post(
            "/api/solicitations/upload",
            json={
                "raw_text": "Test solicitation about cybersecurity",
                "title": "Test Solicitation"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "solicitation_id" in data
        assert "themes" in data
    
    def test_upload_solicitation_missing_text(self):
        """Test error handling for missing text"""
        response = client.post(
            "/api/solicitations/upload",
            json={}
        )
        
        # Should handle gracefully or return error
        assert response.status_code in [200, 400, 422]


class TestPipelineEndpoints:
    """Test suite for full pipeline endpoints"""
    
    @patch('app.theme_search')
    @patch('app.data_source_manager')
    def test_full_pipeline_no_companies(self, mock_dsm, mock_search):
        """Test full pipeline with no companies found"""
        mock_search.search_by_themes = MagicMock(return_value=[])
        
        response = client.post(
            "/api/full-pipeline",
            json={
                "solicitation_id": "test-123",
                "raw_text": "Test solicitation",
                "title": "Test",
                "company_id": None,
                "enrich": False,
                "top_k": 5,
                "company_type": "for-profit",
                "company_size": "small"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert len(data["results"]) == 0
        assert data["companies_evaluated"] == 0




