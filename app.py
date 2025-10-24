# app.py
# n of 1 — Enhanced with Confirmation & Validation Engines + Data Source Integrations
# Run:  pip install fastapi uvicorn sqlalchemy pydantic typing-extensions python-multipart httpx anthropic openai
#       uvicorn app:app --reload
import os
import re
import json
import uuid
import math
import pathlib
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple

from fastapi import FastAPI, HTTPException, UploadFile, File, Body, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from sqlalchemy import (
    create_engine, Column, String, Integer, Float, JSON as SA_JSON,
    DateTime, Text
)
from sqlalchemy.orm import declarative_base, sessionmaker

# Import new engines
from data_sources import DataSourceManager, EnrichmentResult
from confirmation_engine import ConfirmationEngine, ConfirmationResult, ConfirmationStatus
from validation_engine import ValidationEngine, ValidationResult, ValidationLevel, RiskLevel
from theme_search import ThemeBasedSearch

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------------------
# Config / Storage
# --------------------------------------------------------------------------------------
DB_URL = os.getenv("DATABASE_URL", "sqlite:///./nof1.db")
WEIGHTS_PATH = pathlib.Path(os.getenv("WEIGHTS_PATH", "./weights.yaml"))  # optional external file
CONFIG_PATH = pathlib.Path(os.getenv("CONFIG_PATH", "./config.json"))

engine = create_engine(DB_URL, connect_args={"check_same_thread": False} if DB_URL.startswith("sqlite") else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Load configuration for data sources
def load_config() -> Dict[str, Any]:
    """Load configuration for API keys and data sources"""
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text())
        except Exception as e:
            logger.warning(f"Failed to load config: {e}")
            return {}
    return {}

# Initialize engines
config = load_config()
# Pass the entire config (sources are at root level, not nested under "data_sources")
data_source_manager = DataSourceManager(config)
confirmation_engine = ConfirmationEngine()
validation_engine = ValidationEngine()
theme_search = ThemeBasedSearch(data_source_manager)

DEFAULT_WEIGHTS = {
    "naics": 0.20,
    "capabilities": 0.25,
    "past_performance": 0.20,
    "size_status": 0.10,
    "clearance": 0.10,
    "location": 0.05,
    "keywords": 0.10,
}

def load_weights() -> Dict[str, float]:
    if WEIGHTS_PATH.exists():
        try:
            import yaml
            return yaml.safe_load(WEIGHTS_PATH.read_text()) or DEFAULT_WEIGHTS
        except Exception:
            return DEFAULT_WEIGHTS
    return DEFAULT_WEIGHTS

def save_weights(weights: Dict[str, float]) -> None:
    try:
        import yaml
        WEIGHTS_PATH.parent.mkdir(parents=True, exist_ok=True)
        WEIGHTS_PATH.write_text(yaml.dump(weights, sort_keys=True))
    except Exception:
        # Fallback: keep only in-memory without persisting
        pass

# --------------------------------------------------------------------------------------
# Models (SQLite friendly: use JSON columns for arrays)
# --------------------------------------------------------------------------------------
class CompanyORM(Base):
    __tablename__ = "companies"
    company_id = Column(String, primary_key=True)
    name = Column(String, index=True)
    duns = Column(String, nullable=True, index=True)
    cage_code = Column(String, nullable=True, index=True)
    naics_codes = Column(SA_JSON)              # list[str]
    size = Column(String)                      # Small/Medium/Large
    socioeconomic_status = Column(SA_JSON)     # list[str] e.g., ["8(a)","WOSB"]
    capabilities = Column(SA_JSON)             # list[str]
    certifications = Column(SA_JSON)           # list[str]
    security_clearances = Column(SA_JSON)      # list[str]
    locations = Column(SA_JSON)                # list[str]
    employees = Column(Integer)
    annual_revenue = Column(Float)
    description = Column(Text)
    keywords = Column(SA_JSON)                 # list[str]
    capability_statement = Column(Text)
    website = Column(String)

class PastContractORM(Base):
    __tablename__ = "past_contracts"
    id = Column(String, primary_key=True)
    company_id = Column(String)                # FK-ish; simplified for single file
    agency = Column(String)
    contract_number = Column(String)
    value = Column(String)                     # raw string
    value_usd = Column(Float)                  # normalized
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    description = Column(Text)

class SolicitationORM(Base):
    __tablename__ = "solicitations"
    job_id = Column(String, primary_key=True)
    solicitation_id = Column(String)
    title = Column(String)
    agency = Column(String, index=True)
    posting_date = Column(DateTime)
    due_date = Column(DateTime)
    contract_type = Column(String)
    set_asides = Column(SA_JSON)               # list[str]
    naics_codes = Column(SA_JSON)              # list[str]
    place_of_performance = Column(String)
    estimated_value = Column(String)
    technical_requirements = Column(SA_JSON)   # list[str]
    evaluation_criteria = Column(SA_JSON)      # dict
    keywords = Column(SA_JSON)                 # list[str]
    required_capabilities = Column(SA_JSON)    # list[str]
    past_performance_requirements = Column(SA_JSON)  # dict
    security_clearance = Column(String)
    raw_text = Column(Text)

Base.metadata.create_all(bind=engine)

# --------------------------------------------------------------------------------------
# Schemas
# --------------------------------------------------------------------------------------
class CompanyIn(BaseModel):
    name: str
    duns: Optional[str] = None
    cage_code: Optional[str] = None
    naics_codes: List[str] = Field(default_factory=list)
    size: Optional[str] = None
    socioeconomic_status: List[str] = Field(default_factory=list)
    capabilities: List[str] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    security_clearances: List[str] = Field(default_factory=list)
    locations: List[str] = Field(default_factory=list)
    employees: Optional[int] = None
    annual_revenue: Optional[float] = None
    description: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)
    capability_statement: Optional[str] = None
    website: Optional[str] = None

class CompanyOut(CompanyIn):
    company_id: str

class PastContractIn(BaseModel):
    company_id: str
    agency: Optional[str] = None
    contract_number: Optional[str] = None
    value: Optional[str] = None
    value_usd: Optional[float] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    description: Optional[str] = None

class PastContractOut(PastContractIn):
    id: str

class SolicitationIn(BaseModel):
    solicitation_id: Optional[str] = None
    title: Optional[str] = None
    agency: Optional[str] = None
    posting_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    contract_type: Optional[str] = None
    set_asides: List[str] = Field(default_factory=list)
    naics_codes: List[str] = Field(default_factory=list)
    place_of_performance: Optional[str] = None
    estimated_value: Optional[str] = None
    technical_requirements: List[str] = Field(default_factory=list)
    evaluation_criteria: Dict[str, Any] = Field(default_factory=dict)
    keywords: List[str] = Field(default_factory=list)
    required_capabilities: List[str] = Field(default_factory=list)
    past_performance_requirements: Dict[str, Any] = Field(default_factory=dict)
    security_clearance: Optional[str] = None
    raw_text: Optional[str] = None

class MatchResult(BaseModel):
    company_id: str
    name: str
    score: float
    strengths: List[str]
    gaps: List[str]
    recommendation: str

# --------------------------------------------------------------------------------------
# Lightweight Solicitation Parser (deterministic extractors)
# --------------------------------------------------------------------------------------
NAICS_RX = re.compile(r"\b(5415[1-9]\d?|54\d{3}|3364\d|334\d{2}|6114\d|6211\d|6221\d)\b")
SETASIDE_TERMS = ["8(a)", "WOSB", "EDWOSB", "SDVOSB", "HUBZone", "Small Business", "SB"]
CLEARANCE_TERMS = ["Public Trust", "Confidential", "Secret", "Top Secret", "TS", "TS/SCI"]

def analyze_solicitation_themes(text: str) -> Dict[str, Any]:
    """
    Analyze solicitation to extract key topics and priorities.
    Prioritizes PROBLEM AREAS as the primary driver, using semantic importance over mention counts.
    """
    if not text or len(text.strip()) < 100:
        logger.warning("Insufficient text for theme analysis")
        return {
            "problem_statement": "",
            "problem_areas": [],
            "key_priorities": [],
            "technical_capabilities": [],
            "evaluation_factors": [],
            "search_keywords": []
        }
    
    # Extract key themes and priorities
    themes = {
        "problem_statement": "",  # The core problem to solve
        "problem_areas": [],  # Specific pain points (HIGHEST PRIORITY)
        "key_priorities": [],  # Must-have requirements
        "technical_capabilities": [],  # Technical skills needed (derived from problems)
        "evaluation_factors": [],  # How proposals will be judged
        "search_keywords": []  # Keywords for company search
    }
    
    # === STEP 1: IDENTIFY THE CORE PROBLEM (Most Important) ===
    # Look for problem statements, needs, and challenges
    problem_statement_patterns = [
        r"(?:the\s+)?(?:challenge|problem|issue|need)\s+is\s+([^.]{30,200})",
        r"(?:seeking|looking for|need)\s+(?:a\s+)?(?:solution|approach|system|capability|contractor|vendor)\s+(?:to|that|for)\s+([^.]{30,200})",
        r"(?:currently|presently)\s+(?:faces|experiencing|dealing with)\s+([^.]{30,200})",
        r"in\s+order\s+to\s+address\s+([^.]{30,200})",
    ]
    
    problem_statement = ""
    for pattern in problem_statement_patterns:
        match = re.search(pattern, text, re.I)
        if match:
            problem_statement = re.sub(r'\s+', ' ', match.group(1)).strip()
            if len(problem_statement) > 30:
                themes["problem_statement"] = problem_statement
                break
    
    # === STEP 2: EXTRACT SPECIFIC PROBLEM AREAS (Critical for Search) ===
    # These drive what companies we look for
    problem_patterns = [
        # Explicit problems
        (r"(?:challenge|problem|issue|difficulty|barrier|obstacle)\s+(?:is|with|of|in|includes?|involves?)\s+([^.;]{25,150})", 1.0),
        # Gaps and deficiencies  
        (r"(?:lack(?:s|ing)?|insufficient|inadequate|limited|missing|absent|without)\s+([^.;]{15,120})", 0.95),
        # Needs and requirements
        (r"(?:need(?:s|ed)?|require(?:s|d|ment)?|must\s+have|essential|critical(?:ly)?)\s+(?:for|to|that)?\s*([^.;]{20,120})", 0.9),
        # Current state problems
        (r"(?:current|existing|legacy|outdated|aging)\s+(?:system|solution|infrastructure|approach|method|process)\s+(?:is|has|lacks?|cannot|fails?)\s+([^.;]{20,120})", 0.85),
        # Risk and vulnerability language
        (r"(?:risk|vulnerability|threat|concern|weakness|exposure)\s+(?:of|from|in|with|regarding)\s+([^.;]{20,120})", 0.8),
    ]
    
    problem_extractions = []
    for pattern, importance_score in problem_patterns:
        matches = re.findall(pattern, text, re.I)
        for match in matches[:5]:  # Top 5 per pattern
            cleaned = re.sub(r'\s+', ' ', match).strip()
            if len(cleaned) >= 20 and cleaned.lower() not in [p["text"].lower() for p in problem_extractions]:
                problem_extractions.append({
                    "text": cleaned,
                    "importance": importance_score,
                    "type": "problem"
                })
    
    # Sort by importance, not just frequency
    problem_extractions.sort(key=lambda x: x["importance"], reverse=True)
    themes["problem_areas"] = [p["text"] for p in problem_extractions[:8]]
    
    # FALLBACK: If no problem areas found, extract key noun phrases from first 1000 chars
    if len(themes["problem_areas"]) == 0:
        logger.warning("No problem areas extracted via patterns, using fallback extraction")
        # Extract sentences or phrases with technical or domain terms
        sentences = re.split(r'[.!?;\n]', text[:1200])
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 30 and len(sentence) < 250:
                # Look for sentences with technical indicators or domain-specific terms
                if re.search(r'\b(system|technology|solution|service|capability|development|monitoring|detection|management|platform|biosensor|vaccine|diagnostic|iot|automated|data|surveillance|pathogen|disease|security|cloud|software|hardware)\b', sentence, re.I):
                    themes["problem_areas"].append(sentence)
                    logger.info(f"Fallback extracted: {sentence[:80]}...")
                    if len(themes["problem_areas"]) >= 6:
                        break
    
    # === STEP 3: KEY PRIORITIES (Must-haves) ===
    priority_patterns = [
        (r"(?:must|shall|required?\s+to|mandatory|critical\s+to)\s+([^.;]{20,120})", 1.0),
        (r"(?:priority|essential|crucial|vital|necessary|imperative)\s+(?:is|that|to|for)\s+([^.;]{20,120})", 0.9),
        (r"(?:requirement|stipulation|condition)\s+(?:is|that|for)\s+([^.;]{20,120})", 0.85),
    ]
    
    priority_extractions = []
    for pattern, importance_score in priority_patterns:
        matches = re.findall(pattern, text, re.I)
        for match in matches[:4]:
            cleaned = re.sub(r'\s+', ' ', match).strip()
            if len(cleaned) >= 20 and cleaned.lower() not in [p["text"].lower() for p in priority_extractions]:
                priority_extractions.append({
                    "text": cleaned,
                    "importance": importance_score
                })
    
    priority_extractions.sort(key=lambda x: x["importance"], reverse=True)
    themes["key_priorities"] = [p["text"] for p in priority_extractions[:8]]
    
    # === STEP 5: TECHNICAL CAPABILITIES (Derived from problems and priorities) ===
    # Comprehensive patterns across multiple domains
    capability_patterns = {
        # Agriculture & Animal Health
        "agriculture & animal health": r"\b(agricultur|farm|livestock|poultry|animal health|veterinary|biosecurity|disease surveillance|avian|cattle|swine|aquaculture|crop)\b",
        "biosensors & diagnostics": r"\b(biosensor|diagnostic|pathogen detection|lab|testing|screening|assay|biomarker|detection system)\b",
        "vaccine & therapeutics": r"\b(vaccine|vaccination|immunization|therapeutic|drug|pharmaceutical|cold[- ]chain|biologics)\b",
        
        # Healthcare & Biotech
        "healthcare & medical": r"\b(healthcare|medical|hospital|clinical|patient|health system|telemedicine|ehr|medical device)\b",
        "biotechnology": r"\b(biotech|genetic|genomic|molecular|dna|rna|crispr|gene therapy|biomanufacturing)\b",
        
        # Manufacturing & Supply Chain
        "manufacturing & production": r"\b(manufactur|production|assembly|fabrication|quality control|supply chain|logistics|warehouse)\b",
        "automation & robotics": r"\b(automat|robot|industrial control|plc|scada|process control|iot|sensor)\b",
        
        # Energy & Environment
        "energy & utilities": r"\b(energy|power|electric|solar|wind|renewable|grid|utility|transmission)\b",
        "environmental": r"\b(environmental|sustainability|climate|emission|waste|water treatment|pollution)\b",
        
        # IT & Cybersecurity (keep but lower priority)
        "cloud & infrastructure": r"\b(cloud|aws|azure|gcp|kubernetes|docker|container|infrastructure|iaas|paas|saas)\b",
        "cybersecurity": r"\b(cybersecurity|security|encryption|authentication|zero trust|siem|soar|threat)\b",
        "data & analytics": r"\b(data analytics|business intelligence|machine learning|ai|predictive|big data)\b",
        "software development": r"\b(software development|application|custom software|agile|devops|programming)\b",
    }
    
    capability_matches = []
    for capability, pattern in capability_patterns.items():
        # Find matches and their context (nearby problem/priority language)
        matches = list(re.finditer(pattern, text, re.I))
        if matches:
            # Calculate contextual importance (is it near problem language?)
            problem_words = r"\b(problem|challenge|need|require|must|critical|essential|lack|insufficient)\b"
            
            context_score = 0
            for match in matches:
                start = max(0, match.start() - 200)
                end = min(len(text), match.end() + 200)
                context = text[start:end]
                context_matches = len(re.findall(problem_words, context, re.I))
                context_score += context_matches
            
            # Importance = (number of matches) * (context score) * (early position bonus)
            first_match_pos = matches[0].start() / len(text)  # 0-1, earlier is better
            position_bonus = 1.2 if first_match_pos < 0.3 else 1.0  # First 30% of document
            
            importance = len(matches) * (1 + context_score * 0.5) * position_bonus
            
            capability_matches.append({
                "capability": capability,
                "importance": importance,
                "mentions": len(matches)
            })
    
    capability_matches.sort(key=lambda x: x["importance"], reverse=True)
    themes["technical_capabilities"] = [
        {"area": c["capability"], "relevance": "high" if c["importance"] > 10 else "medium"}
        for c in capability_matches[:6]
    ]
    
    # === STEP 6: EVALUATION FACTORS ===
    eval_patterns = [
        r"(?:evaluat|assess|judg|score|rate)\s+(?:based on|on|using|by)\s+([^.;]{20,120})",
        r"(?:factor|criterion|criteria)\s+(?:include|are|is)\s+([^.;]{20,120})",
        r"(?:past performance|experience|technical approach|management plan|key personnel)\s+(?:in|with|on|will be)\s+([^.;]{20,100})",
    ]
    
    for pattern in eval_patterns:
        matches = re.findall(pattern, text, re.I)
        for match in matches[:3]:
            cleaned = re.sub(r'\s+', ' ', match).strip()
            if len(cleaned) >= 20 and cleaned not in themes["evaluation_factors"]:
                themes["evaluation_factors"].append(cleaned)
    
    themes["evaluation_factors"] = themes["evaluation_factors"][:6]
    
    # === STEP 7: GENERATE SEARCH KEYWORDS ===
    # Derive keywords from problems + capabilities (not just frequency)
    search_keywords = []
    
    # Extract nouns and technical terms from problem areas
    for problem in themes["problem_areas"][:4]:
        words = re.findall(r'\b[a-zA-Z][a-zA-Z0-9\-]{3,}\b', problem.lower())
        search_keywords.extend(words[:5])
    
    # Add capability keywords
    for cap in themes["technical_capabilities"]:
        search_keywords.append(cap["area"].replace(" & ", " ").replace(" ", "_"))
    
    # Add domain-specific terms from priorities
    for priority in themes["key_priorities"][:3]:
        words = re.findall(r'\b[a-zA-Z][a-zA-Z0-9\-]{4,}\b', priority.lower())
        search_keywords.extend(words[:3])
    
    # Deduplicate and filter stop words
    stop_words = {
        "the", "and", "for", "with", "that", "this", "from", "shall", "will",
        "must", "have", "are", "was", "were", "has", "had", "system", "solution"
    }
    search_keywords = list(set([kw for kw in search_keywords if kw not in stop_words]))[:20]
    themes["search_keywords"] = search_keywords
    
    return themes

def parse_solicitation_text(text: str) -> Dict[str, Any]:
    """Enhanced solicitation parser - extracts all key information"""
    if not text:
        return {}
    
    # Extract NAICS codes
    naics = list(sorted(set(NAICS_RX.findall(text))))
    
    # Extract set-asides
    set_asides = [t for t in SETASIDE_TERMS if re.search(rf"\b{re.escape(t)}\b", text, re.I)]
    
    # Extract security clearance
    clearance = None
    for c in CLEARANCE_TERMS:
        if re.search(rf"\b{re.escape(c)}\b", text, re.I):
            clearance = c
            break
    
    # Try to extract title (look for common patterns)
    title = None
    title_patterns = [
        r"TITLE:\s*(.+?)(?:\n|$)",
        r"SOLICITATION\s+TITLE:\s*(.+?)(?:\n|$)",
        r"PROJECT\s+TITLE:\s*(.+?)(?:\n|$)",
        r"^(.+?)(?:\n|SOLICITATION)",  # First line
    ]
    for pattern in title_patterns:
        match = re.search(pattern, text, re.I | re.M)
        if match:
            title = match.group(1).strip()[:200]  # Limit to 200 chars
            break
    
    # Try to extract agency
    agency = None
    agency_patterns = [
        r"AGENCY:\s*(.+?)(?:\n|$)",
        r"DEPARTMENT:\s*(.+?)(?:\n|$)",
        r"CONTRACTING\s+OFFICE:\s*(.+?)(?:\n|$)",
    ]
    for pattern in agency_patterns:
        match = re.search(pattern, text, re.I | re.M)
        if match:
            agency = match.group(1).strip()[:200]
            break
    
    # Try to extract solicitation number
    solicitation_id = None
    sol_patterns = [
        r"SOLICITATION\s+(?:NUMBER|NO|#):\s*([A-Z0-9\-]+)",
        r"SOL(?:ICITATION)?\s+(?:NUMBER|NO|#):\s*([A-Z0-9\-]+)",
        r"RFP\s+(?:NUMBER|NO|#):\s*([A-Z0-9\-]+)",
    ]
    for pattern in sol_patterns:
        match = re.search(pattern, text, re.I)
        if match:
            solicitation_id = match.group(1).strip()
            break
    
    # Extract technical requirements and capabilities
    tech_keywords = [
        "cloud", "cybersecurity", "software", "hardware", "network", "system",
        "data", "analytics", "ai", "machine learning", "development", "infrastructure",
        "security", "encryption", "database", "api", "integration", "migration",
        "devops", "kubernetes", "docker", "aws", "azure", "gcp"
    ]
    
    required_capabilities = []
    for keyword in tech_keywords:
        if re.search(rf"\b{keyword}\b", text, re.I):
            required_capabilities.append(keyword)
    
    # Enhanced keyword extraction
    words = [w.lower() for w in re.findall(r"[a-zA-Z][a-zA-Z0-9\-]{2,}", text)]
    freq: Dict[str, int] = {}
    for w in words:
        freq[w] = freq.get(w, 0) + 1
    
    # Filter out common stop words
    stop_words = {
        "the", "and", "for", "with", "that", "this", "from", "shall", "will",
        "must", "have", "are", "was", "were", "has", "had", "but", "not", "any",
        "all", "may", "can", "could", "would", "should", "its", "their", "them",
        "than", "then", "these", "those", "only", "such", "into", "through",
        "during", "before", "after", "above", "below", "between", "under"
    }
    
    common = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:50]
    keywords = [w for w, count in common if w not in stop_words and count >= 2][:25]

    return {
        "solicitation_id": solicitation_id,
        "title": title,
        "agency": agency,
        "naics_codes": naics,
        "set_asides": set_asides,
        "security_clearance": clearance,
        "required_capabilities": required_capabilities[:15],  # Top 15
        "keywords": keywords,
        "raw_text": text,  # Keep original text
    }

# --------------------------------------------------------------------------------------
# Matching Engine
# --------------------------------------------------------------------------------------
class MatchingEngine:
    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.weights = weights or load_weights()
        # Fail-fast caps for hard requirements
        self.hard_caps = {"set_aside": 0.49, "clearance": 0.49}

    @staticmethod
    def _norm(s: Optional[str]) -> str:
        return (s or "").strip().lower()

    @staticmethod
    def _list_norm(lst: Optional[List[str]]) -> List[str]:
        return [MatchingEngine._norm(x) for x in (lst or []) if x]

    def _score_naics(self, sol: Dict[str, Any], comp: CompanyORM) -> float:
        s = set(self._list_norm(sol.get("naics_codes")))
        c = set(self._list_norm(comp.naics_codes))
        return 1.0 if s and (s & c) else 0.0

    def _score_capabilities(self, sol: Dict[str, Any], comp: CompanyORM) -> float:
        required = set(self._list_norm(sol.get("required_capabilities")))
        if not required:
            # fallback to keywords vs company capabilities
            required = set(self._list_norm(sol.get("keywords")))
        caps = set(self._list_norm(comp.capabilities))
        if not required:
            return 0.5 if caps else 0.0
        inter = len(required & caps)
        return min(1.0, inter / max(1, len(required)))

    def _score_past_perf(self, sol: Dict[str, Any], comp: CompanyORM) -> float:
        # very simple proxy: if keywords overlap with company keywords/description
        kws = set(self._list_norm(sol.get("keywords")))
        comp_kws = set(self._list_norm(comp.keywords))
        desc = set(self._list_norm(re.findall(r"[a-zA-Z][a-zA-Z0-9\-]{2,}", comp.description or "")))
        inter = len(kws & (comp_kws | desc))
        return min(1.0, inter / max(1, len(kws))) if kws else (0.3 if comp_kws or desc else 0.0)

    def _score_size_status(self, sol: Dict[str, Any], comp: CompanyORM) -> float:
        # If solicitation mentions Small Business set-aside, prefer Small
        req_ss = set(self._list_norm(sol.get("set_asides")))
        comp_size = self._norm(comp.size)
        if not req_ss:
            return 0.5 if comp_size else 0.0
        if "small business" in req_ss or "sb" in req_ss:
            return 1.0 if comp_size in {"small", "micro"} else 0.0
        return 0.5

    def _score_clearance(self, sol: Dict[str, Any], comp: CompanyORM) -> float:
        req = self._norm(sol.get("security_clearance"))
        if not req:
            return 0.5
        clrs = set(self._list_norm(comp.security_clearances))
        return 1.0 if req in clrs else 0.0

    def _score_location(self, sol: Dict[str, Any], comp: CompanyORM) -> float:
        # crude: match any location word overlap
        sol_loc = set(self._list_norm([sol.get("place_of_performance")]))
        comp_loc = set(self._list_norm(comp.locations))
        return 1.0 if sol_loc and (sol_loc & comp_loc) else (0.4 if comp_loc else 0.0)

    def _score_keywords(self, sol: Dict[str, Any], comp: CompanyORM) -> float:
        kws = set(self._list_norm(sol.get("keywords")))
        caps = set(self._list_norm(comp.capabilities))
        comp_kws = set(self._list_norm(comp.keywords))
        inter = len(kws & (caps | comp_kws))
        return min(1.0, inter / max(1, len(kws))) if kws else (0.3 if caps or comp_kws else 0.0)

    def _meets_set_aside(self, comp: CompanyORM, required: List[str]) -> bool:
        comp_ss = set(self._list_norm(comp.socioeconomic_status))
        req = set(self._list_norm(required))
        return bool(comp_ss & req) or not req

    def _meets_clearance(self, comp: CompanyORM, required: Optional[str]) -> bool:
        if not required:
            return True
        clrs = set(self._list_norm(comp.security_clearances))
        return self._norm(required) in clrs

    def score(self, sol: Dict[str, Any], comp: CompanyORM) -> Tuple[float, List[str], List[str]]:
        s_naics = self._score_naics(sol, comp)
        s_caps = self._score_capabilities(sol, comp)
        s_pp = self._score_past_perf(sol, comp)
        s_size = self._score_size_status(sol, comp)
        s_clear = self._score_clearance(sol, comp)
        s_loc = self._score_location(sol, comp)
        s_kw = self._score_keywords(sol, comp)

        total = (
            self.weights["naics"] * s_naics +
            self.weights["capabilities"] * s_caps +
            self.weights["past_performance"] * s_pp +
            self.weights["size_status"] * s_size +
            self.weights["clearance"] * s_clear +
            self.weights["location"] * s_loc +
            self.weights["keywords"] * s_kw
        )

        # Fail-fast caps for hard requirements
        if not self._meets_set_aside(comp, sol.get("set_asides", [])):
            total = min(total, self.hard_caps["set_aside"])
        if not self._meets_clearance(comp, sol.get("security_clearance")):
            total = min(total, self.hard_caps["clearance"])

        strengths, gaps = [], []
        if s_naics >= 1: strengths.append("NAICS match")
        else: gaps.append("NAICS mismatch")
        if s_caps >= 0.7: strengths.append("Capabilities aligned")
        else: gaps.append("Capabilities gap")
        if s_pp >= 0.6: strengths.append("Relevant past performance")
        else: gaps.append("Limited past performance alignment")
        if s_size >= 0.8: strengths.append("Meets size status")
        if s_clear >= 1.0: strengths.append("Required clearance available")
        elif sol.get("security_clearance"): gaps.append("Missing required clearance")
        if s_loc >= 1.0: strengths.append("Location alignment")
        if s_kw >= 0.6: strengths.append("Keyword alignment")
        return max(0.0, min(1.0, total)), strengths, gaps

    @staticmethod
    def label(score: float) -> str:
        if score >= 0.75: return "Recommended"
        if score >= 0.5:  return "Borderline"
        return "Not Recommended"

# --------------------------------------------------------------------------------------
# FastAPI app
# --------------------------------------------------------------------------------------
app = FastAPI(title="n of 1 — Reverse Search Platform (single-file MVP)")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------------
# Weights endpoints
# ----------------------------------
@app.get("/api/weights")
def get_weights():
    return load_weights()

@app.put("/api/weights")
def put_weights(new_weights: Dict[str, float]):
    expected = set(DEFAULT_WEIGHTS.keys())
    unknown = set(new_weights) - expected
    if unknown:
        raise HTTPException(400, f"Unknown keys: {', '.join(sorted(unknown))}")
    for k, v in new_weights.items():
        if not isinstance(v, (int, float)):
            raise HTTPException(400, f"Weight for {k} must be numeric")
    save_weights(new_weights)
    return {"ok": True, "weights": load_weights()}

# ----------------------------------
# Company CRUD + search
# ----------------------------------
@app.post("/api/companies", response_model=CompanyOut)
def create_company(data: CompanyIn):
    db = SessionLocal()
    try:
        c = CompanyORM(
            company_id=str(uuid.uuid4()),
            **data.model_dump()
        )
        db.add(c)
        db.commit()
        return CompanyOut(company_id=c.company_id, **data.model_dump())
    finally:
        db.close()

@app.get("/api/companies/{company_id}", response_model=CompanyOut)
def get_company(company_id: str):
    db = SessionLocal()
    try:
        c = db.query(CompanyORM).get(company_id)
        if not c:
            raise HTTPException(404, "Not found")
        return CompanyOut(
            company_id=c.company_id,
            name=c.name,
            duns=c.duns,
            cage_code=c.cage_code,
            naics_codes=c.naics_codes or [],
            size=c.size,
            socioeconomic_status=c.socioeconomic_status or [],
            capabilities=c.capabilities or [],
            certifications=c.certifications or [],
            security_clearances=c.security_clearances or [],
            locations=c.locations or [],
            employees=c.employees,
            annual_revenue=c.annual_revenue,
            description=c.description,
            keywords=c.keywords or [],
            capability_statement=c.capability_statement,
            website=c.website
        )
    finally:
        db.close()

@app.get("/api/companies/search")
def search_companies(
    q: Optional[str] = Query(default=None),
    naics: Optional[str] = Query(default=None),
    set_aside: Optional[str] = Query(default=None),
    clearance: Optional[str] = Query(default=None),
    location: Optional[str] = Query(default=None),
    limit: int = 25
):
    db = SessionLocal()
    try:
        rows = db.query(CompanyORM).all()
        # Basic filtering in Python (SQLite JSON filtering is clunky without custom functions)
        def norm(s): return (s or "").strip().lower()
        out = []
        for c in rows:
            if q:
                if q.lower() not in (c.name or "").lower() and (q.lower() not in (c.description or "").lower()):
                    continue
            if naics:
                if naics not in (c.naics_codes or []):
                    continue
            if set_aside:
                if not any(norm(set_aside) == norm(x) for x in (c.socioeconomic_status or [])):
                    continue
            if clearance:
                if not any(norm(clearance) == norm(x) for x in (c.security_clearances or [])):
                    continue
            if location:
                if not any(norm(location) == norm(x) for x in (c.locations or [])):
                    continue
            out.append({
                "company_id": c.company_id,
                "name": c.name,
                "naics_codes": c.naics_codes or [],
                "capabilities": c.capabilities or [],
                "locations": c.locations or [],
                "socioeconomic_status": c.socioeconomic_status or [],
                "security_clearances": c.security_clearances or []
            })
            if len(out) >= limit:
                break
        return JSONResponse(out)
    finally:
        db.close()

# ----------------------------------
# Past contracts (minimal)
# ----------------------------------
@app.post("/api/past-contracts", response_model=PastContractOut)
def add_past_contract(data: PastContractIn):
    db = SessionLocal()
    try:
        if not db.query(CompanyORM).get(data.company_id):
            raise HTTPException(400, "company_id does not exist")
        pc = PastContractORM(id=str(uuid.uuid4()), **data.model_dump())
        db.add(pc)
        db.commit()
        return PastContractOut(id=pc.id, **data.model_dump())
    finally:
        db.close()

# ----------------------------------
# Solicitations: parse + store + match
# ----------------------------------
@app.post("/api/solicitations/parse")
def parse_solicitation(raw_text: str = Body(..., embed=True)):
    parsed = parse_solicitation_text(raw_text)
    return parsed

@app.post("/api/solicitations/upload")
async def upload_and_parse_file(file: UploadFile = File(...)):
    """Upload and parse a solicitation file (PDF, DOC, DOCX, TXT)"""
    import tempfile
    
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=file.filename) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        # Extract text based on file type
        text = ""
        filename_lower = file.filename.lower() if file.filename else ""
        
        if filename_lower.endswith('.pdf'):
            # Extract text from PDF
            try:
                import PyPDF2
                with open(tmp_path, 'rb') as pdf_file:
                    pdf_reader = PyPDF2.PdfReader(pdf_file)
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"
            except Exception as e:
                logger.error(f"Error extracting PDF: {e}")
                raise HTTPException(status_code=400, detail="Could not extract text from PDF. Please try a text-based PDF or copy the text manually.")
        
        elif filename_lower.endswith('.docx'):
            # Extract text from DOCX
            try:
                import docx
                doc = docx.Document(tmp_path)
                text = "\n".join([para.text for para in doc.paragraphs])
            except Exception as e:
                logger.error(f"Error extracting DOCX: {e}")
                raise HTTPException(status_code=400, detail="Could not extract text from DOCX file.")
        
        elif filename_lower.endswith('.doc'):
            # For old .doc files, suggest conversion
            raise HTTPException(status_code=400, detail="Legacy .doc format not supported. Please save as .docx or copy the text manually.")
        
        else:
            # Assume text file
            text = content.decode('utf-8', errors='ignore')
        
        # Clean up temp file
        import os
        try:
            os.unlink(tmp_path)
        except:
            pass
        
        if not text or len(text.strip()) < 50:
            raise HTTPException(status_code=400, detail="Could not extract sufficient text from file.")
        
        # Parse the extracted text
        parsed = parse_solicitation_text(text)
        
        # Analyze themes and priorities
        themes = analyze_solicitation_themes(text)
        parsed["themes"] = themes
        
        return {
            "success": True,
            "text": text,
            "content": text,
            "parsed": parsed,
            "themes": themes,
            "filename": file.filename
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing file upload: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@app.post("/api/solicitations/fetch-url")
async def fetch_solicitation_from_url(url: str = Body(..., embed=True)):
    """Fetch and parse a solicitation from a URL (e.g., SAM.gov)"""
    import httpx
    from bs4 import BeautifulSoup
    
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()
            
            # Try to extract text from HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text and clean it
            text = soup.get_text(separator='\n')
            lines = [line.strip() for line in text.splitlines()]
            text = '\n'.join([line for line in lines if line])
            
            if not text or len(text) < 100:
                return {
                    "error": "Could not extract sufficient text from URL",
                    "text": text,
                    "suggestion": "Try uploading the file directly or copying the content"
                }
            
            # Parse the extracted text
            parsed = parse_solicitation_text(text)
            parsed["source_url"] = url
            
            return {
                "success": True,
                "text": text,
                "parsed": parsed
            }
            
    except httpx.RequestError as e:
        logger.error(f"Error fetching URL {url}: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to fetch URL: {str(e)}")
    except Exception as e:
        logger.error(f"Error processing URL {url}: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing URL: {str(e)}")

@app.post("/api/solicitations")
def create_solicitation(sol: SolicitationIn):
    db = SessionLocal()
    try:
        job_id = str(uuid.uuid4())
        payload = sol.model_dump()
        # if no structured fields provided but raw_text present, parse it
        if sol.raw_text and not (sol.naics_codes or sol.set_asides or sol.security_clearance or sol.keywords):
            parsed = parse_solicitation_text(sol.raw_text)
            for k, v in parsed.items():
                payload.setdefault(k, v)
        rec = SolicitationORM(job_id=job_id, **payload)
        db.add(rec)
        db.commit()
        return {"job_id": job_id}
    finally:
        db.close()

@app.get("/api/solicitations/{job_id}")
def get_solicitation(job_id: str):
    db = SessionLocal()
    try:
        s = db.query(SolicitationORM).get(job_id)
        if not s:
            raise HTTPException(404, "Not found")
        return {
            "job_id": s.job_id,
            "solicitation_id": s.solicitation_id,
            "title": s.title,
            "agency": s.agency,
            "posting_date": s.posting_date,
            "due_date": s.due_date,
            "contract_type": s.contract_type,
            "set_asides": s.set_asides or [],
            "naics_codes": s.naics_codes or [],
            "place_of_performance": s.place_of_performance,
            "estimated_value": s.estimated_value,
            "technical_requirements": s.technical_requirements or [],
            "evaluation_criteria": s.evaluation_criteria or {},
            "keywords": s.keywords or [],
            "required_capabilities": s.required_capabilities or [],
            "past_performance_requirements": s.past_performance_requirements or {},
            "security_clearance": s.security_clearance,
            "raw_text": s.raw_text,
        }
    finally:
        db.close()

@app.post("/api/match", response_model=List[MatchResult])
def match_companies(
    solicitation: SolicitationIn = Body(...),
    top_k: int = Query(25, ge=1, le=200)
):
    # Compose a dict for scoring (may include parsed fields)
    sol_dict = solicitation.model_dump()
    if solicitation.raw_text:
        parsed = parse_solicitation_text(solicitation.raw_text)
        for k, v in parsed.items():
            sol_dict.setdefault(k, v)

    me = MatchingEngine(weights=load_weights())
    db = SessionLocal()
    try:
        companies = db.query(CompanyORM).all()
        scored: List[Tuple[CompanyORM, float, List[str], List[str]]] = []
        for c in companies:
            score, strengths, gaps = me.score(sol_dict, c)
            scored.append((c, score, strengths, gaps))
        scored.sort(key=lambda x: x[1], reverse=True)
        results: List[MatchResult] = []
        for c, score, strengths, gaps in scored[:top_k]:
            results.append(MatchResult(
                company_id=c.company_id,
                name=c.name,
                score=round(score, 4),
                strengths=strengths,
                gaps=gaps,
                recommendation=MatchingEngine.label(score)
            ))
        return results
    finally:
        db.close()

# ----------------------------------
# Enhanced Pipeline: Enrichment + Confirmation + Validation
# ----------------------------------
@app.post("/api/enrich-company")
async def enrich_company_endpoint(
    company_id: str = Body(..., embed=True),
    sources: Optional[List[str]] = Body(default=None, embed=True)
):
    """Enrich company data from external sources"""
    db = SessionLocal()
    try:
        company = db.query(CompanyORM).get(company_id)
        if not company:
            raise HTTPException(404, "Company not found")
        
        # Prepare context
        context = {
            "naics_codes": company.naics_codes,
            "capabilities": company.capabilities,
            "description": company.description
        }
        
        # Enrich from data sources
        enrichment_results = await data_source_manager.enrich_company_all_sources(
            company.name,
            context=context,
            sources=sources
        )
        
        # Format results
        formatted_results = {}
        for source_name, result in enrichment_results.items():
            formatted_results[source_name] = {
                "success": not result.error,
                "confidence": result.confidence,
                "data": result.data,
                "error": result.error,
                "timestamp": result.timestamp.isoformat()
            }
        
        return formatted_results
        
    finally:
        db.close()

@app.post("/api/match-with-confirmation")
async def match_with_confirmation(
    solicitation: SolicitationIn = Body(...),
    company_id: Optional[str] = Body(default=None),
    enrich: bool = Body(default=True),
    top_k: int = Query(10, ge=1, le=50)
):
    """
    Enhanced matching: Match + Enrich + Confirm
    Pipeline: Matching Engine → Data Enrichment → Confirmation Engine
    """
    db = SessionLocal()
    try:
        # Parse solicitation
        sol_dict = solicitation.model_dump()
        if solicitation.raw_text:
            parsed = parse_solicitation_text(solicitation.raw_text)
            for k, v in parsed.items():
                sol_dict.setdefault(k, v)
        
        # Get companies to evaluate
        if company_id:
            company = db.query(CompanyORM).get(company_id)
            if not company:
                raise HTTPException(404, "Company not found")
            companies = [company]
        else:
            companies = db.query(CompanyORM).all()
        
        # Step 1: Match
        me = MatchingEngine(weights=load_weights())
        matched_companies = []
        
        for company in companies:
            score, strengths, gaps = me.score(sol_dict, company)
            matched_companies.append({
                "company": company,
                "match_result": {
                    "score": score,
                    "strengths": strengths,
                    "gaps": gaps,
                    "recommendation": MatchingEngine.label(score)
                }
            })
        
        # Sort by score
        matched_companies.sort(key=lambda x: x["match_result"]["score"], reverse=True)
        matched_companies = matched_companies[:top_k]
        
        # Step 2 & 3: Enrich and Confirm
        results = []
        for item in matched_companies:
            company = item["company"]
            match_result = item["match_result"]
            
            # Convert company to dict
            company_data = {
                "company_id": company.company_id,
                "name": company.name,
                "naics_codes": company.naics_codes or [],
                "size": company.size,
                "socioeconomic_status": company.socioeconomic_status or [],
                "capabilities": company.capabilities or [],
                "security_clearances": company.security_clearances or [],
                "locations": company.locations or [],
                "employees": company.employees,
                "annual_revenue": company.annual_revenue,
                "description": company.description,
                "keywords": company.keywords or []
            }
            
            # Enrich if requested
            enrichment_data = {}
            if enrich:
                context = {
                    "naics_codes": company.naics_codes,
                    "capabilities": company.capabilities,
                    "description": company.description
                }
                enrichment_data = await data_source_manager.enrich_company_all_sources(
                    company.name,
                    context=context
                )
            
            # Confirm
            confirmation_result = await confirmation_engine.confirm_match(
                company_data=company_data,
                solicitation_data=sol_dict,
                match_result=match_result,
                enrichment_data=enrichment_data
            )
            
            results.append({
                "company_id": company.company_id,
                "company_name": company.name,
                "match_score": match_result["score"],
                "match_strengths": match_result["strengths"],
                "match_gaps": match_result["gaps"],
                "confirmation_status": confirmation_result.overall_status.value,
                "confirmation_confidence": confirmation_result.overall_confidence,
                "confirmation_summary": confirmation_result.summary,
                "enrichment_sources": confirmation_result.enrichment_sources_used
            })
        
        return results
        
    finally:
        db.close()

@app.post("/api/search-companies-by-themes")
async def search_companies_by_themes(themes: Dict[str, Any] = Body(...), max_results: int = 20):
    """
    Search for companies across multiple data sources based on solicitation themes
    
    Args:
        themes: Extracted themes from solicitation analysis
        max_results: Maximum number of companies to return
        
    Returns:
        List of discovered companies with relevance scores
    """
    logger.info(f"Theme-based search requested for {max_results} companies")
    
    try:
        # Search across all available data sources
        companies = await theme_search.search_by_themes(themes, max_companies=max_results)
        
        return {
            "success": True,
            "total_found": len(companies),
            "companies": companies,
            "sources_used": list(set([
                source for company in companies 
                for source in company.get('sources', [])
            ])),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Theme search error: {e}")
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

@app.post("/api/full-pipeline")
async def full_pipeline(
    solicitation: SolicitationIn = Body(...),
    company_id: Optional[str] = Body(default=None),
    enrich: bool = Body(default=True),
    top_k: int = Body(default=5),
    company_type: str = Body(default="for-profit"),
    company_size: str = Body(default="all")
):
    """
    Search for companies matching solicitation themes and return top matches
    """
    try:
        # Parse solicitation
        sol_dict = solicitation.model_dump()
        if solicitation.raw_text:
            parsed = parse_solicitation_text(solicitation.raw_text)
            for k, v in parsed.items():
                sol_dict.setdefault(k, v)
        
        # Extract themes from solicitation
        logger.info("Extracting themes from solicitation for company search")
        raw_text = solicitation.raw_text or ""
        
        if not raw_text or len(raw_text.strip()) < 50:
            raise HTTPException(400, "Insufficient solicitation text provided. Please upload a valid document or paste the full text.")
        
        themes = analyze_solicitation_themes(raw_text)
        
        if not themes or not themes.get("search_keywords"):
            raise HTTPException(400, "Could not extract sufficient themes from solicitation. Please ensure the document contains clear requirements and problem statements.")
        
        # Search for companies using extracted themes
        logger.info("Searching for companies using extracted themes")
        logger.info(f"Themes extracted: {list(themes.keys())}")
        logger.info(f"Company type filter: {company_type}")
        logger.info(f"Company size filter: {company_size}")
        search_results = await theme_search.search_by_themes(themes, max_companies=top_k, company_type=company_type, company_size=company_size)
        
        if not search_results:
            logger.warning("No companies found - API keys may not be configured")
            return {
                "solicitation_summary": {
                    "title": solicitation.title or "Uploaded Solicitation",
                    "agency": solicitation.agency,
                    "naics_codes": sol_dict.get("naics_codes", []),
                    "set_asides": sol_dict.get("set_asides", []),
                    "security_clearance": sol_dict.get("security_clearance")
                },
                "companies_evaluated": 0,
                "top_matches_analyzed": 0,
                "results": []
            }
        
        # Run confirmation on all search results
        logger.info(f"Running confirmation analysis on {len(search_results)} companies")
        confirmation_results = []
        
        # Check if ChatGPT is available for confirmation
        if "chatgpt" in data_source_manager.sources:
            chatgpt_source = data_source_manager.sources["chatgpt"]
            solicitation_title = solicitation.title or "Uploaded Solicitation"
            
            # Run confirmation for each company in parallel
            import asyncio
            confirmation_tasks = []
            for company in search_results[:top_k]:
                company_name = company.get('name', 'Unknown Company')
                task = confirm_single_company(
                    company_name=company_name,
                    solicitation_title=solicitation_title,
                    themes=themes,
                    chatgpt_source=chatgpt_source
                )
                confirmation_tasks.append(task)
            
            # Execute all confirmations in parallel
            confirmation_results = await asyncio.gather(*confirmation_tasks, return_exceptions=True)
            logger.info(f"Completed {len(confirmation_results)} confirmation analyses")
        else:
            logger.warning("ChatGPT not available - skipping confirmation step")
            confirmation_results = [None] * len(search_results[:top_k])
        
        # Combine search results with confirmation results
        combined_results = []
        for idx, (company, confirmation) in enumerate(zip(search_results[:top_k], confirmation_results)):
            company_name = company.get('name', 'Unknown Company')
            
            # Handle confirmation errors
            if isinstance(confirmation, Exception):
                logger.error(f"Confirmation failed for {company_name}: {confirmation}")
                confirmation = None
            
            # Calculate final score (blend search relevance + confirmation)
            search_score = company.get('relevance_score', 0.0)
            
            if confirmation and isinstance(confirmation, dict):
                # Blend scores: 40% search relevance, 60% confirmation
                confirmation_score = confirmation.get('confidence_score', 0.5)
                final_score = (search_score * 0.4) + (confirmation_score * 0.6)
                is_confirmed = confirmation.get('is_confirmed', False)
                recommendation = confirmation.get('recommendation', 'review')
            else:
                # No confirmation available - use search score only
                final_score = search_score
                is_confirmed = None
                recommendation = 'review'
            
            combined_results.append({
                'company': company,
                'confirmation': confirmation,
                'final_score': final_score,
                'search_score': search_score,
                'is_confirmed': is_confirmed,
                'recommendation': recommendation
            })
        
        # Re-order by final score (after confirmation)
        combined_results.sort(key=lambda x: x['final_score'], reverse=True)
        logger.info("Re-ordered companies based on confirmation scores")
        
        # Format results for frontend
        final_results = []
        for idx, result in enumerate(combined_results, 1):
            company = result['company']
            confirmation = result['confirmation']
            
            final_results.append({
                "company_id": company.get('id', f"search_{idx}"),
                "company_name": company.get('name', 'Unknown Company'),
                "match_score": result['final_score'],
                "alignment_percentage": result['final_score'] * 100,
                "confidence_percentage": (confirmation.get('confidence_score', 0.7) * 100) if confirmation else 70.0,
                "validation_level": "recommended" if result['final_score'] > 0.7 else "borderline",
                "risk_level": "low" if result.get('is_confirmed') else "medium",
                "recommendation": f"Rank #{idx}: {confirmation.get('reasoning', company.get('match_reason', 'Matches search criteria'))}" if confirmation else f"Rank #{idx}: {company.get('match_reason', 'Matches search criteria')}",
                
                # Company details
                "description": company.get('description', ''),
                "website": company.get('website', ''),
                "locations": company.get('locations', []),
                "capabilities": company.get('capabilities', []),
                "sources": company.get('sources', []),
                
                # Analysis (from confirmation or search)
                "strengths": confirmation.get('findings', {}).get('strengths', [
                    f"Found via {', '.join(company.get('sources', ['search']))}",
                    company.get('match_reason', 'Matches solicitation themes')
                ]) if confirmation else [
                    f"Found via {', '.join(company.get('sources', ['search']))}",
                    company.get('match_reason', 'Matches solicitation themes')
                ],
                "weaknesses": [],
                "opportunities": ["Further research recommended"],
                "risks": confirmation.get('findings', {}).get('risk_factors', []) if confirmation else [],
                "recommended_actions": [
                    "Review company website and capabilities",
                    "Verify certifications and past performance"
                ],
                "decision_rationale": confirmation.get('reasoning', company.get('match_reason', 'Identified through theme-based search')) if confirmation else company.get('match_reason', 'Identified through theme-based search'),
                
                # Confirmation data
                "confirmation_status": "confirmed" if result.get('is_confirmed') else "discovered",
                "confirmation_result": {
                    "is_confirmed": result.get('is_confirmed'),
                    "confidence_score": confirmation.get('confidence_score') if confirmation else None,
                    "recommendation": confirmation.get('recommendation') if confirmation else None,
                    "chain_of_thought": confirmation.get('chain_of_thought', []) if confirmation else [],
                    "company_info": confirmation.get('findings', {}).get('company_info') if confirmation else None
                } if confirmation else None,
                
                # Metadata
                "enrichment_sources": company.get('sources', []),
                "data_quality_score": 0.9 if confirmation else 0.7,
                
                # Score components
                "score_components": [
                    {
                        "component": "search_relevance",
                        "score": result['search_score'],
                        "weight": 0.4,
                        "rationale": "Based on theme matching"
                    },
                    {
                        "component": "confirmation_score",
                        "score": confirmation.get('confidence_score', 0.0) if confirmation else 0.0,
                        "weight": 0.6,
                        "rationale": "Independent verification via confirmation engine"
                    }
                ]
            })
        
        return {
            "solicitation_summary": {
                "title": solicitation.title or "Uploaded Solicitation",
                "agency": solicitation.agency,
                "naics_codes": sol_dict.get("naics_codes", []),
                "set_asides": sol_dict.get("set_asides", []),
                "security_clearance": sol_dict.get("security_clearance")
            },
            "companies_evaluated": len(search_results),
            "top_matches_analyzed": len(final_results),
            "results": final_results
        }
        
    except Exception as e:
        logger.error(f"Full pipeline error: {e}")
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")

# --------------------------------------------------------------------------------------
# Selection Confirmation - Independent verification using chain-of-thought
# --------------------------------------------------------------------------------------

async def confirm_single_company(
    company_name: str,
    solicitation_title: str,
    themes: Dict[str, Any],
    chatgpt_source
) -> Dict[str, Any]:
    """
    Helper function to confirm a single company.
    Returns confirmation result with scores and recommendation.
    """
    try:
        logger.info(f"Confirming: {company_name}")
        
        # Step 1: Gather company information using ChatGPT
        company_info_prompt = f"""Research and provide comprehensive information about the company: {company_name}

Please provide:
1. Company overview (what they do, their main business focus)
2. Core capabilities and services
3. Industry expertise and specializations
4. Notable projects or clients (if known)
5. Company size and maturity indicators

Be factual and concise. If information is limited, indicate that."""
        
        # Get company information
        company_info_response = chatgpt_source.client.chat.completions.create(
            model=chatgpt_source.model,
            messages=[
                {"role": "system", "content": "You are a business intelligence analyst providing factual company information."},
                {"role": "user", "content": company_info_prompt}
            ],
            max_tokens=500
        )
        company_info = company_info_response.choices[0].message.content
        
        # Step 2: Perform chain-of-thought analysis
        
        confirmation_prompt = f"""You are an independent verification analyst. Perform a thorough chain-of-thought analysis to confirm if this company is truly a good fit for the solicitation.

COMPANY: {company_name}

COMPANY INFORMATION:
{company_info}

SOLICITATION: {solicitation_title}

SOLICITATION REQUIREMENTS:
Problem Areas: {', '.join(themes.get('problem_areas', [])[:5])}
Key Priorities: {', '.join(themes.get('key_priorities', [])[:5])}
Technical Capabilities Needed: {', '.join([str(cap) for cap in themes.get('technical_capabilities', [])[:5]])}

TASK: Perform a step-by-step analysis:
1. What specific capabilities does this company have?
2. How well do these capabilities match the solicitation requirements?
3. What relevant experience might they have?
4. What are the strengths of this match?
5. What are potential risk factors or gaps?
6. Final recommendation: proceed, reconsider, or reject?

Provide your response as JSON with this structure:
{{
  "is_confirmed": boolean,
  "confidence_score": float (0-1),
  "recommendation": "proceed" | "reconsider" | "reject",
  "reasoning": "brief summary",
  "chain_of_thought": ["step 1 analysis", "step 2 analysis", ...],
  "findings": {{
    "company_info": "summary",
    "capability_match": "assessment",
    "experience_assessment": "evaluation",
    "strengths": ["strength 1", "strength 2", ...],
    "risk_factors": ["risk 1", "risk 2", ...]
  }}
}}

Be honest and objective. If there are concerns, state them clearly."""

        confirmation_response = chatgpt_source.client.chat.completions.create(
            model=chatgpt_source.model,
            messages=[
                {"role": "system", "content": "You are an independent verification analyst performing objective assessments. Always return valid JSON."},
                {"role": "user", "content": confirmation_prompt}
            ],
            max_tokens=1500,
            temperature=0.3
        )
        
        result_content = confirmation_response.choices[0].message.content.strip()
        
        # Parse JSON response
        if result_content.startswith("```json"):
            result_content = result_content[7:]
        if result_content.startswith("```"):
            result_content = result_content[3:]
        if result_content.endswith("```"):
            result_content = result_content[:-3]
        result_content = result_content.strip()
        
        import json
        result = json.loads(result_content)
        result['company_name'] = company_name
        
        logger.info(f"Confirmation complete for {company_name}: {result['recommendation']}")
        return result
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error in confirmation for {company_name}: {e}")
        # Return a fallback result if JSON parsing fails
        return {
            'company_name': company_name,
            'is_confirmed': False,
            'confidence_score': 0.3,
            'recommendation': 'reconsider',
            'reasoning': 'Unable to complete full analysis',
            'chain_of_thought': ['Analysis incomplete due to parsing error'],
            'findings': {
                'company_info': 'Limited information available',
                'capability_match': 'Unable to assess',
                'experience_assessment': 'Unable to assess',
                'strengths': [],
                'risk_factors': ['Analysis incomplete']
            }
        }
    except Exception as e:
        logger.error(f"Selection confirmation error for {company_name}: {e}")
        # Return a fallback result if confirmation fails
        return {
            'company_name': company_name,
            'is_confirmed': False,
            'confidence_score': 0.2,
            'recommendation': 'reconsider',
            'reasoning': 'Confirmation analysis failed',
            'chain_of_thought': ['Unable to complete analysis'],
            'findings': {
                'company_info': 'Analysis failed',
                'capability_match': 'Unable to assess',
                'experience_assessment': 'Unable to assess',
                'strengths': [],
                'risk_factors': ['Analysis failed']
            }
        }


@app.post("/api/confirm-selection")
async def confirm_selection(
    company_name: str = Body(...),
    company_id: str = Body(...),
    solicitation_text: str = Body(...),
    solicitation_title: str = Body(...)
):
    """
    Single company confirmation endpoint (for manual confirmation).
    Independent verification of company alignment using chain-of-thought reasoning.
    """
    try:
        if "chatgpt" not in data_source_manager.sources:
            raise HTTPException(400, "ChatGPT API key required for selection confirmation")
        
        chatgpt_source = data_source_manager.sources["chatgpt"]
        themes = analyze_solicitation_themes(solicitation_text)
        
        result = await confirm_single_company(
            company_name,
            solicitation_title,
            themes,
            chatgpt_source
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Confirmation endpoint error: {e}")
        raise HTTPException(500, f"Confirmation error: {str(e)}")

# --------------------------------------------------------------------------------------
# Seed data helper (optional): call /seed to get a few companies to play with
# --------------------------------------------------------------------------------------
# Seed data removed - companies are now discovered via theme-based search
# from external APIs (Google, Pitchbook, USASpending, etc.)

@app.post("/seed")
def seed_companies():
    """
    Seed endpoint disabled - companies are now dynamically discovered
    through theme-based search across external data sources
    """
    return {
        "message": "Seed data disabled. Companies are now discovered via theme-based search.",
        "use_instead": "/api/search-companies-by-themes",
        "created": []
    }

# --------------------------------------------------------------------------------------
# Root
# --------------------------------------------------------------------------------------
@app.get("/")
def root():
    return {
        "service": "n of 1 — Enhanced Reverse Search Platform with Confirmation & Validation",
        "version": "2.0",
        "pipeline_modules": {
            "1-3": "Data Source Integrations (Google, Claude, ChatGPT, USASpending, NIH, SBIR, USPTO, etc.)",
            "4": "Matching Engine",
            "5": "Confirmation Engine",
            "6": "Validation Engine"
        },
        "endpoints": {
            "basic": {
                "weights_get": "/api/weights",
                "weights_put": "/api/weights",
                "company_create": "/api/companies",
                "company_get": "/api/companies/{company_id}",
                "company_search": "/api/companies/search",
                "past_contract_create": "/api/past-contracts",
                "solicitation_parse": "/api/solicitations/parse",
                "solicitation_create": "/api/solicitations",
                "solicitation_get": "/api/solicitations/{job_id}",
                "match": "/api/match",
                "seed": "/seed"
            },
            "enhanced": {
                "enrich_company": "/api/enrich-company (POST)",
                "match_with_confirmation": "/api/match-with-confirmation (POST)",
                "full_pipeline": "/api/full-pipeline (POST) - RECOMMENDED"
            }
        },
        "data_sources": {
            "search": ["Google Custom Search"],
            "ai_analysis": ["Claude (Anthropic)", "ChatGPT (OpenAI)"],
            "contracts": ["USASpending.gov", "NIH Reporter", "SBIR.gov"],
            "company_data": ["HubSpot CRM", "Pitchbook (manual)", "AngelList (manual)"],
            "innovation": ["USPTO Patents"]
        },
        "configuration": "Set API keys in config.json file"
    }

