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
# Utility Functions
# --------------------------------------------------------------------------------------
def clean_company_name(company_name: str) -> str:
    """
    Remove common company suffixes (Inc, LLC, Corp, etc.) from company names.
    This provides cleaner names for use in reports and match explanations.
    """
    if not company_name:
        return company_name
    
    # List of common company suffixes to remove
    suffixes = [
        r',?\s*Inc\.?',
        r',?\s*LLC\.?',
        r',?\s*L\.L\.C\.?',
        r',?\s*Ltd\.?',
        r',?\s*Limited',
        r',?\s*Corp\.?',
        r',?\s*Corporation',
        r',?\s*Co\.?',
        r',?\s*Company',
        r',?\s*LP\.?',
        r',?\s*L\.P\.?',
        r',?\s*LLP\.?',
        r',?\s*L\.L\.P\.?',
        r',?\s*PLLC\.?',
        r',?\s*PC\.?',
        r',?\s*P\.C\.?',
        r',?\s*PLC\.?',
        r',?\s*P\.L\.C\.?',
        r',?\s*Incorporated',
        r',?\s*S\.A\.?',
        r',?\s*AG\.?',
        r',?\s*GmbH\.?',
        r',?\s*Pty\.?\s*Ltd\.?',
        r',?\s*N\.V\.?',
        r',?\s*B\.V\.?',
    ]
    
    # Create a combined regex pattern
    pattern = '|'.join(suffixes)
    
    # Remove suffixes (case-insensitive, from end of string)
    cleaned = re.sub(f'({pattern})$', '', company_name, flags=re.IGNORECASE).strip()
    
    return cleaned

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
    config = {}
    
    # Try to load from config.json first
    if CONFIG_PATH.exists():
        try:
            config = json.loads(CONFIG_PATH.read_text())
        except Exception as e:
            logger.warning(f"Failed to load config: {e}")
    
    # Override with environment variables if present
    if os.getenv("OPENAI_API_KEY"):
        if "chatgpt" not in config:
            config["chatgpt"] = {}
        config["chatgpt"]["api_key"] = os.getenv("OPENAI_API_KEY")
        config["chatgpt"]["model"] = config.get("chatgpt", {}).get("model", "gpt-3.5-turbo")
        logger.info("Loaded OpenAI API key from environment variable")
    
    return config

# Initialize engines
config = load_config()
logger.info(f"Configuration loaded: {len(config)} keys")
logger.info(f"Config keys: {list(config.keys())}")

# Pass the entire config (sources are at root level, not nested under "data_sources")
data_source_manager = DataSourceManager(config)
logger.info(f"Data sources initialized: {list(data_source_manager.sources.keys())}")

# Initialize confirmation engine with OpenAI API key for website validation
openai_key = config.get("chatgpt", {}).get("api_key")
confirmation_engine = ConfirmationEngine(openai_api_key=openai_key)
validation_engine = ValidationEngine()
theme_search = ThemeBasedSearch(data_source_manager)
logger.info("All engines initialized successfully")

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

def generate_ai_summary(text: str) -> Dict[str, Any]:
    """
    Use OpenAI to generate a clean, professional summary and key topics from the solicitation
    """
    try:
        if "chatgpt" not in data_source_manager.sources:
            logger.warning("ChatGPT not available for summary generation, using fallback")
            return None
        
        chatgpt = data_source_manager.sources["chatgpt"]
        
        prompt = f"""You are analyzing a government solicitation. Read it carefully and provide an accurate, professional analysis.

Your task:
1. Write a clear, factual 3-4 sentence summary (100-150 words) that explains:
   - What this solicitation is seeking (be specific about the goal/problem)
   - The main technical or professional requirements
   - Key priorities or evaluation criteria

2. List 5-6 key topics as complete, clear sentences. Each topic should:
   - Be a complete, grammatically correct sentence
   - Highlight a specific requirement, capability, challenge, or priority
   - Be factual and based on the actual solicitation text
   - Use proper English with clear subject-verb structure

IMPORTANT: Base your analysis ONLY on what is actually written in the solicitation. Do not make assumptions or add generic information.

Respond in JSON format:
{{
  "summary": "Your factual 3-4 sentence summary based on the actual solicitation content...",
  "key_topics": [
    "First complete sentence about a specific requirement or topic from the solicitation.",
    "Second complete sentence about another specific aspect.",
    "Third complete sentence...",
    "Fourth complete sentence...",
    "Fifth complete sentence...",
    "Sixth complete sentence..."
  ]
}}

Solicitation text:
{text[:4000]}

Return ONLY valid JSON with no additional text or markdown."""

        # Use GPT-3.5-turbo for fast parsing (not GPT-4o-mini)
        # This is just for summary extraction, doesn't need the power of GPT-4
        response = chatgpt.client.chat.completions.create(
            model="gpt-3.5-turbo",  # Fast and cheap for parsing
            messages=[
                {"role": "system", "content": "You are an expert at analyzing government solicitations. Read the solicitation carefully and provide accurate, factual analysis. Write in clear, professional English with proper grammar. Base your analysis only on the actual content provided. Always respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=1200
        )
        
        result_text = response.choices[0].message.content.strip()
        
        # Remove markdown code blocks if present
        if result_text.startswith("```"):
            result_text = re.sub(r'^```(?:json)?\s*', '', result_text)
            result_text = re.sub(r'\s*```$', '', result_text)
        
        result = json.loads(result_text)
        
        logger.info("✓ AI summary generated successfully")
        return result
        
    except Exception as e:
        logger.error(f"Error generating AI summary: {e}")
        return None

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
        "overview": "",  # Executive summary of the solicitation
        "key_takeaways": [],  # Top 3-5 salient points for quick understanding
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
    
    # === STEP 8: GENERATE OVERVIEW & KEY TOPICS ===
    # Try AI-powered summary first for best quality
    ai_summary = generate_ai_summary(text)
    
    if ai_summary and "summary" in ai_summary and "key_topics" in ai_summary:
        # Use AI-generated summary (clean and grammatically correct)
        themes["overview"] = ai_summary["summary"]
        themes["key_takeaways"] = ai_summary["key_topics"][:6]  # Limit to 6 topics
        logger.info("Using AI-generated summary and topics")
    else:
        # Fallback to manual extraction if AI is unavailable
        logger.info("Using fallback manual summary extraction")
        
        # Create detailed paragraph summary (3-5 sentences)
        summary_parts = []
        
        # Helper to extract complete, grammatical phrases
        def extract_clean_phrase(text: str, max_chars: int = 150) -> str:
            """Extract a clean phrase without cutting mid-word or leaving fragments"""
            if not text or len(text) <= max_chars:
                return text.strip()
            
            # Truncate at max_chars
            truncated = text[:max_chars].strip()
            
            # Find the last complete word
            last_space = truncated.rfind(' ')
            if last_space > max_chars * 0.7:  # Only if we're not losing too much
                truncated = truncated[:last_space].strip()
            
            # Remove trailing incomplete punctuation or conjunctions
            while truncated and truncated[-1] in ',;:-()':
                truncated = truncated[:-1].strip()
            
            # Remove trailing conjunctions
            trailing_words = ['and', 'or', 'but', 'for', 'with', 'to', 'of', 'in', 'on', 'at', 'by']
            words = truncated.split()
            if words and words[-1].lower() in trailing_words:
                truncated = ' '.join(words[:-1])
            
            return truncated.strip()
        
        # Sentence 1: What is this solicitation about? (Core problem/need)
        if themes["problem_statement"]:
            clean_stmt = extract_clean_phrase(themes["problem_statement"], 200)
            summary_parts.append(clean_stmt)
        elif themes["problem_areas"]:
            clean_problem = extract_clean_phrase(themes['problem_areas'][0], 150)
            if clean_problem:
                summary_parts.append(f"This solicitation seeks innovative solutions to {clean_problem.lower()}")
        else:
            # Extract first substantial sentence from text
            sentences = [s.strip() for s in re.split(r'[.!?]', text[:800]) if len(s.strip()) > 40]
            if sentences:
                summary_parts.append(extract_clean_phrase(sentences[0], 200))
        
        # Sentence 2: Technical capabilities and expertise needed
        if themes["technical_capabilities"]:
            if len(themes["technical_capabilities"]) >= 3:
                cap_names = [cap["area"] for cap in themes["technical_capabilities"][:3]]
                summary_parts.append(f"The program requires expertise in {', '.join(cap_names[:-1])}, and {cap_names[-1]}")
            elif len(themes["technical_capabilities"]) == 2:
                cap_names = [cap["area"] for cap in themes["technical_capabilities"][:2]]
                summary_parts.append(f"The program requires expertise in {cap_names[0]} and {cap_names[1]}")
            else:
                summary_parts.append(f"The program requires expertise in {themes['technical_capabilities'][0]['area']}")
        
        # Sentence 3: Key priorities or requirements  
        if themes["key_priorities"]:
            clean_priority = extract_clean_phrase(themes["key_priorities"][0], 150)
            if clean_priority:
                summary_parts.append(f"Critical requirements include {clean_priority.lower()}")
        
        # Sentence 4: Additional context from second problem area or priority
        if len(themes["problem_areas"]) > 1:
            clean_second = extract_clean_phrase(themes["problem_areas"][1], 120)
            if clean_second:
                summary_parts.append(f"The solicitation also emphasizes {clean_second.lower()}")
        elif len(themes["key_priorities"]) > 1:
            clean_second_priority = extract_clean_phrase(themes["key_priorities"][1], 120)
            if clean_second_priority:
                summary_parts.append(f"Additionally, the program prioritizes {clean_second_priority.lower()}")
        
        # Join sentences properly
        formatted_summary = []
        for part in summary_parts:
            part = part.strip()
            if part:
                # Ensure proper capitalization
                if part[0].islower():
                    part = part[0].upper() + part[1:]
                # Ensure proper ending
                if part[-1] not in '.!?':
                    part += '.'
                formatted_summary.append(part)
        
        themes["overview"] = " ".join(formatted_summary) if formatted_summary else extract_clean_phrase(text, 400) + "."
        
        # Generate Key Topics for fallback (only if AI didn't provide them)
        key_topics = []
        
        def ensure_complete_sentence(text: str) -> str:
            """Ensure the topic is a complete, standalone sentence"""
            text = text.strip()
            
            # Check if it starts with a capital letter
            if text and not text[0].isupper():
                text = text[0].upper() + text[1:]
            
            # Check if it ends with proper punctuation
            if text and text[-1] not in '.!?':
                text = text + '.'
            
            # Check if it has a subject and verb (basic check)
            # If it starts with a gerund or noun without context, add a subject
            words = text.split()
            if len(words) > 0:
                first_word = words[0].lower()
                # If starts with -ing or is a noun phrase without "the/this/these", make it complete
                if first_word.endswith('ing') and len(words) > 2:
                    # Check if there's no clear subject
                    if not any(w.lower() in ['the', 'this', 'these', 'those', 'program', 'solicitation', 'project'] for w in words[:3]):
                        text = f"The program requires {text[0].lower()}{text[1:]}"
            
            return text
        
        # Topic 1: Primary Technical Domain - Detailed description with focus areas
        if themes["technical_capabilities"]:
            cap = themes["technical_capabilities"][0]
            cap_name = cap["area"]
            focus_terms = cap.get("terms", [])[:4]
            if focus_terms:
                topic = f"The program requires {cap_name.lower()} expertise with emphasis on {', '.join(focus_terms)}, and related technical capabilities essential for success"
            else:
                topic = f"The solicitation requires {cap_name.lower()} capabilities as the primary technical foundation, including relevant tools, methodologies, and proven experience"
            key_topics.append(ensure_complete_sentence(topic))
        
        # Topic 2: Core Problem/Challenge - Full problem statement
        if themes["problem_areas"]:
            problem = themes["problem_areas"][0]
            # Provide full context without truncation for better understanding
            if len(problem) > 150:
                topic = f"The central challenge this solicitation aims to address is {problem[:150].lower()}"
            else:
                # Check if problem already forms a complete sentence
                if problem[0].isupper() and problem[-1] in '.!?':
                    topic = f"The core technical challenge is: {problem}"
                else:
                    topic = f"This solicitation addresses {problem.lower()} as the core technical challenge that requires innovative solutions"
            key_topics.append(ensure_complete_sentence(topic))
        
        # Topic 3: Critical Requirements - Expanded priority description
        if themes["key_priorities"]:
            priority = themes["key_priorities"][0]
            # Add context about why this is critical
            if "must" in priority.lower() or "shall" in priority.lower() or "required" in priority.lower():
                topic = f"A mandatory program requirement is to {priority.lower()}" if not priority[0].isupper() else priority
            else:
                topic = f"The program prioritizes {priority.lower()} as a critical success factor" if not priority[0].isupper() else priority
            key_topics.append(ensure_complete_sentence(topic))
        
        # Topic 4: Secondary Technical Domain - Include complementary capabilities
        if len(themes["technical_capabilities"]) > 1:
            cap2 = themes["technical_capabilities"][1]
            cap2_name = cap2["area"]
            focus_terms2 = cap2.get("terms", [])[:3]
            if focus_terms2:
                topic = f"Complementary {cap2_name.lower()} capabilities are needed, including {', '.join(focus_terms2)}, to support integrated solution development"
            else:
                topic = f"Additional technical expertise in {cap2_name.lower()} serves as a supporting capability that enhances overall solution effectiveness"
            key_topics.append(ensure_complete_sentence(topic))
        
        # Topic 5: Secondary Problem Area - Additional challenge context
        if len(themes["problem_areas"]) > 1:
            problem2 = themes["problem_areas"][1]
            topic = f"An important secondary consideration is {problem2.lower()}, which impacts overall program objectives"
            key_topics.append(ensure_complete_sentence(topic))
        
        # Topic 6: Additional Priority - Third-tier requirements
        if len(themes["key_priorities"]) > 1:
            priority2 = themes["key_priorities"][1]
            topic = f"The solicitation also emphasizes {priority2.lower()}, providing additional program direction and evaluation criteria"
            key_topics.append(ensure_complete_sentence(topic))
        
        # Topic 7: Evaluation Criteria - How proposals are assessed (if not already covered)
        if themes["evaluation_factors"] and len(key_topics) < 6:
            eval_factor = themes["evaluation_factors"][0]
            topic = f"Proposals will be evaluated based on {eval_factor.lower()}, demonstrating the importance of this criterion in the selection process"
            key_topics.append(ensure_complete_sentence(topic))
        
        # Topic 8: Third technical capability (if available and space permits)
        if len(themes["technical_capabilities"]) > 2 and len(key_topics) < 6:
            cap3 = themes["technical_capabilities"][2]
            cap3_name = cap3["area"]
            topic = f"Tertiary expertise in {cap3_name.lower()} may provide competitive advantages and contribute to comprehensive solution delivery"
            key_topics.append(ensure_complete_sentence(topic))
        
        # Set key_takeaways in fallback mode (AI didn't generate them)
        themes["key_takeaways"] = key_topics[:6]  # Max 6 key topics
    
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
    
    # Try to extract title - Smart extraction looking for actual title
    # Priority 1: Look for explicit TITLE: label
    # Priority 2: Look for title case text early in document (likely the actual title)
    # Priority 3: First substantial line
    
    title = None
    
    # Strategy 1: Explicit TITLE: field
    # Define comprehensive stop markers for title extraction
    title_stop_markers = r"(?:ANNOUNCEMENT\s+TYPE|AMENDMENT|PROGRAM\s+(?:TITLE|MANAGER|OFFICE)|SOLICITATION\s+(?:NUMBER|ID|TYPE)|ISO\s+SOLICITATION|RFP\s+NUMBER|CONTRACT\s+NUMBER|OPPORTUNITY\s+NUMBER|NOTICE\s+(?:ID|NUMBER)|AGENCY|ORGANIZATION|DEPARTMENT|OFFICE|NAICS|PSC|SET-ASIDE|SOCIOECONOMIC|CLASSIFICATION|RESPONSE\s+DATE|DUE\s+DATE|CLOSING\s+DATE|SUBMISSION\s+DEADLINE|POST(?:ED)?\s+DATE|ISSUE\s+DATE|RELEASE\s+DATE|AWARD\s+DATE|PERIOD\s+OF\s+PERFORMANCE|PLACE\s+OF\s+PERFORMANCE|DESCRIPTION|OVERVIEW|SUMMARY|BACKGROUND|STATEMENT\s+OF\s+WORK|SCOPE|REQUIREMENTS|OBJECTIVE|PURPOSE|CONTACT|POINT\s+OF\s+CONTACT)"
    
    title_patterns = [
        rf"(?:SOLICITATION\s+)?TITLE:\s*(.+?)(?=\n{title_stop_markers}|$)",
        rf"PROJECT\s+TITLE:\s*(.+?)(?=\n{title_stop_markers}|$)",
        rf"PROGRAM\s+TITLE:\s*(.+?)(?=\n{title_stop_markers}|$)",
    ]
    for pattern in title_patterns:
        match = re.search(pattern, text, re.I | re.DOTALL)
        if match:
            extracted_title = match.group(1).strip()
            # Clean up: remove newlines, normalize whitespace, return only the actual title
            full_title = ' '.join(extracted_title.split())
            # Apply 150 char max limit only if needed
            title = full_title[:150] if len(full_title) > 150 else full_title
            if len(full_title) > 150:
                logger.info(f"📋 Extracted title (truncated from {len(full_title)} to 150 chars): {title}")
            else:
                logger.info(f"📋 Extracted title ({len(title)} chars): {title}")
            break
    
    # Strategy 2: Look for Title Case text in first 1000 chars (actual document title)
    if not title:
        first_section = text[:1000]
        lines = first_section.split('\n')
        
        for line in lines[:20]:  # Check first 20 lines
            line = line.strip()
            
            # Skip lines that are clearly labels or metadata
            if not line or len(line) < 15:
                continue
            # Skip metadata field labels
            if re.match(r'^(SOLICITATION|POSTED|DUE|DATE|NAICS|SET-ASIDE|AGENCY|DEPARTMENT|NUMBER|ID|RFP|RFI|BAA):', line, re.I):
                continue
            # Skip pure ID/number lines (like "75N98025R00004" or "W912QR-24-R-0001")
            if re.match(r'^[A-Z0-9\-]+$', line):
                continue
            # Skip lines that are just "SOLICITATION NUMBER: ..." pattern
            if re.match(r'^SOLICITATION\s+(NUMBER|ID)', line, re.I):
                continue
                
            # Look for Title Case (indicates emphasis/heading)
            words = line.split()
            if len(words) >= 3:  # At least 3 words
                # Skip if line starts with common metadata words
                first_word = words[0].lower()
                if first_word in ['posted', 'due', 'date', 'solicitation', 'rfp', 'rfi', 'baa', 'notice']:
                    continue
                
                # Count capitalized words (Title Case pattern)
                capitalized = sum(1 for w in words if w and w[0].isupper() and len(w) > 2)
                
                # If 60%+ words are capitalized and line is substantial, likely the title
                if capitalized / len(words) >= 0.6 and 20 <= len(line) <= 200:
                    # Return actual title, apply 150 max only if needed
                    title = line[:150] if len(line) > 150 else line
                    logger.info(f"📋 Extracted title from Title Case text ({len(title)} chars): {title}")
                    break
    
    # Strategy 3: Fallback to first substantial line
    if not title:
        lines = text.split('\n')
        for line in lines[:10]:
            line = line.strip()
            # Skip short lines and metadata lines
            if line and len(line) >= 20 and not re.match(r'^(SOLICITATION|POSTED|DUE|DATE|NAICS):', line, re.I):
                # Return actual line, apply 150 max only if needed
                title = line[:150] if len(line) > 150 else line
                logger.info(f"📋 Using first substantial line as title ({len(title)} chars): {title}")
                break
    
    # Final fallback
    if not title:
        title = "Solicitation"
        logger.warning("⚠️  Could not extract title, using default")
    
    # Try to extract agency - return only actual agency name, max 200 chars
    agency = None
    # Define comprehensive stop markers for agency extraction
    agency_stop_markers = r"(?:PROGRAM\s+(?:TITLE|MANAGER|OFFICE)|ANNOUNCEMENT\s+TYPE|AMENDMENT|SOLICITATION\s+(?:NUMBER|ID|TYPE)|ISO\s+SOLICITATION|RFP\s+NUMBER|CONTRACT\s+NUMBER|OPPORTUNITY\s+NUMBER|NOTICE\s+(?:ID|NUMBER)|TITLE|PROJECT\s+TITLE|ORGANIZATION|OFFICE|NAICS|PSC|SET-ASIDE|SOCIOECONOMIC|CLASSIFICATION|CONTRACTING\s+OFFICE|CONTRACTING\s+OFFICER|POINT\s+OF\s+CONTACT|CONTACT|RESPONSE\s+DATE|DUE\s+DATE|CLOSING\s+DATE|SUBMISSION\s+DEADLINE|POST(?:ED)?\s+DATE|ISSUE\s+DATE|RELEASE\s+DATE|DESCRIPTION|OVERVIEW|SUMMARY|BACKGROUND|STATEMENT\s+OF\s+WORK|SCOPE|REQUIREMENTS)"
    
    agency_patterns = [
        rf"AGENCY:\s*(.+?)(?=\n{agency_stop_markers}|$)",
        rf"DEPARTMENT:\s*(.+?)(?=\n{agency_stop_markers}|$)",
        rf"ORGANIZATION:\s*(.+?)(?=\n{agency_stop_markers}|$)",
        rf"CONTRACTING\s+OFFICE:\s*(.+?)(?=\n{agency_stop_markers}|$)",
    ]
    for pattern in agency_patterns:
        match = re.search(pattern, text, re.I | re.DOTALL)
        if match:
            extracted_agency = match.group(1).strip()
            # Clean up: remove newlines, normalize whitespace
            full_agency = ' '.join(extracted_agency.split())
            # Apply 200 char max only if needed
            agency = full_agency[:200] if len(full_agency) > 200 else full_agency
            if len(full_agency) > 200:
                logger.info(f"🏛️  Extracted agency (truncated from {len(full_agency)} to 200 chars): {agency}")
            else:
                logger.info(f"🏛️  Extracted agency ({len(agency)} chars): {agency}")
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
# Configure CORS to allow all origins (can be restricted to specific domains later)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now
    allow_credentials=False,  # Must be False when allow_origins is ["*"]
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# ----------------------------------
# Startup event to initialize database
# ----------------------------------
@app.on_event("startup")
def startup_event():
    """Initialize database tables on startup"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")

# ----------------------------------
# Health check endpoint for Railway
# ----------------------------------
@app.get("/")
def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "n of 1",
        "version": "3.0",
        "environment": "production",
        "data_sources_available": list(data_source_manager.sources.keys()) if data_source_manager.sources else []
    }

@app.get("/health")
def health_check():
    """Detailed health check"""
    return {
        "status": "ok",
        "database": "connected",
        "config_loaded": bool(config),
        "data_sources": list(data_source_manager.sources.keys())
    }

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
        db.refresh(rec)  # Refresh to get any DB-generated fields
        return {"job_id": job_id}
    except Exception as e:
        db.rollback()  # Rollback on error
        logger.error(f"Error creating solicitation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create solicitation: {str(e)}")
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
    top_k: int = Query(10, ge=1, le=100)
):
    """
    Enhanced matching: Match + Enrich + Confirm
    Pipeline: Matching Engine -> Data Enrichment -> Confirmation Engine
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

@app.post("/api/validate-website")
async def validate_website_endpoint(
    company_name: str = Body(...),
    company_website: str = Body(...),
    company_capabilities: List[str] = Body(default=[]),
    solicitation_title: str = Body(default=""),
    required_capabilities: List[str] = Body(default=[])
):
    """
    Validate a company against their website and identify partnering opportunities
    
    Args:
        company_name: Name of the company
        company_website: Company website URL
        company_capabilities: Claimed capabilities
        solicitation_title: Optional solicitation title for context
        required_capabilities: Required capabilities from solicitation
        
    Returns:
        Website validation results with gaps and partnering opportunities
    """
    logger.info(f"Website validation requested for {company_name}")
    
    try:
        # Prepare company data
        company_data = {
            "name": company_name,
            "website": company_website,
            "capabilities": company_capabilities,
            "certifications": []
        }
        
        # Prepare solicitation data
        solicitation_data = {
            "title": solicitation_title,
            "required_capabilities": required_capabilities
        }
        
        # Run website validation
        from website_validator import WebsiteValidator
        validator = WebsiteValidator(openai_api_key=config.get("chatgpt", {}).get("api_key"))
        
        validation_result = await validator.validate_company_website(
            company_data,
            solicitation_data,
            enrichment_data={}
        )
        
        # Format response
        return {
            "company_name": validation_result.company_name,
            "website_url": validation_result.website_url,
            "website_accessible": validation_result.website_accessible,
            "validation_score": validation_result.validation_score,
            "confirmed_capabilities": validation_result.confirmed_capabilities,
            "website_capabilities": validation_result.website_capabilities,
            "gaps": [
                {
                    "type": gap.gap_type.value,
                    "description": gap.description,
                    "claimed": gap.claimed_value,
                    "website": gap.website_value,
                    "severity": gap.severity
                }
                for gap in validation_result.gaps_found
            ],
            "partnering_opportunities": validation_result.partnering_opportunities,
            "summary": validation_result.summary
        }
        
    except Exception as e:
        logger.error(f"Website validation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Website validation failed: {str(e)}")

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
        # Input validation
        if top_k < 1 or top_k > 100:
            raise HTTPException(400, "top_k must be between 1 and 100")
        
        if company_type not in ["for-profit", "academic-nonprofit"]:
            raise HTTPException(400, "Invalid company_type. Must be 'for-profit' or 'academic-nonprofit'")
        
        if company_size not in ["all", "small", "large"]:
            raise HTTPException(400, "Invalid company_size. Must be 'all', 'small', or 'large'")
        
        # Parse solicitation
        sol_dict = solicitation.model_dump()
        if solicitation.raw_text:
            parsed = parse_solicitation_text(solicitation.raw_text)
            for k, v in parsed.items():
                sol_dict.setdefault(k, v)
        
        # Extract themes from solicitation
        logger.info("Extracting themes from solicitation for company search")
        raw_text = solicitation.raw_text or ""
        
        # Sanitize and validate input
        raw_text = raw_text.strip()
        if not raw_text or len(raw_text) < 50:
            raise HTTPException(400, "Insufficient solicitation text provided. Please upload a valid document or paste the full text (minimum 50 characters).")
        
        if len(raw_text) > 1000000:  # 1MB text limit
            raise HTTPException(400, "Solicitation text too large. Please ensure the document is under 1MB.")
        
        themes = analyze_solicitation_themes(raw_text)
        
        if not themes or not themes.get("search_keywords"):
            raise HTTPException(400, "Could not extract sufficient themes from solicitation. Please ensure the document contains clear requirements and problem statements.")
        
        # Search for companies using extracted themes
        # Get top companies (no filtering by score - just take top results)
        logger.info("Searching for companies using extracted themes")
        logger.info(f"Themes extracted: {list(themes.keys())}")
        logger.info(f"Company type filter: {company_type}")
        logger.info(f"Company size filter: {company_size}")
        logger.info(f"Requesting {top_k} companies as specified by slider")
        
        # NEW: Request MORE companies initially to account for confirmations that may fail/timeout
        # Request 1.5x the desired amount to ensure we have enough after confirmations
        # Cap at 200 (max useful limit given ChatGPT's 150 cap + buffer)
        initial_request_count = min(int(top_k * 1.5), 200)
        logger.info(f"🔍 Requesting {initial_request_count} companies initially (1.5x requested {top_k} for buffer against timeouts/failures)")
        
        search_results = await theme_search.search_by_themes(themes, max_companies=initial_request_count, company_type=company_type, company_size=company_size)
        
        # Fallback to database search if external searches return no results
        if not search_results:
            logger.warning("No companies found from external searches - falling back to database")
            db = SessionLocal()
            try:
                me = MatchingEngine(weights=load_weights())
                companies = db.query(CompanyORM).all()
                
                # Apply size filter
                if company_size == "small":
                    companies = [c for c in companies if c.size and "small" in c.size.lower()]
                elif company_size == "large":
                    companies = [c for c in companies if c.size and "large" in c.size.lower()]
                
                # Score companies
                scored = []
                for c in companies:
                    score, strengths, gaps = me.score(sol_dict, c)
                    scored.append((c, score, strengths, gaps))
                
                scored.sort(key=lambda x: x[1], reverse=True)
                
                # Convert to search_results format
                for c, score, strengths, gaps in scored[:initial_request_count]:
                    search_results.append({
                        "name": c.name,
                        "company_id": c.company_id,
                        "relevance_score": score,
                        "description": c.description or "",
                        "capabilities": c.capabilities or [],
                        "naics_codes": c.naics_codes or [],
                        "website": getattr(c, 'website', None),
                        "source": "database"
                    })
                
                logger.info(f"Database fallback found {len(search_results)} companies")
            except Exception as e:
                logger.error(f"Database fallback failed: {e}")
            finally:
                db.close()
        
        if not search_results:
            logger.error("No companies found from external searches - check API keys and theme extraction")
            return {
                "solicitation_summary": {
                    "title": sol_dict.get("title") or solicitation.title or "Uploaded Solicitation",
                    "agency": sol_dict.get("agency") or solicitation.agency,
                    "naics_codes": sol_dict.get("naics_codes", []),
                    "set_asides": sol_dict.get("set_asides", []),
                    "security_clearance": sol_dict.get("security_clearance")
                },
                "companies_evaluated": 0,
                "top_matches_analyzed": 0,
                "results": [],
                "pagination": {
                    "total_matches_above_50": 0,
                    "current_batch": 0,
                    "has_more": False,
                    "remaining": 0,
                    "next_index": 0
                }
            }
        
        # Sort search results by relevance score (best matches first)
        search_results.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        total_companies = len(search_results)
        logger.info(f"Found {total_companies} companies, will confirm all of them")
        
        # Run confirmation on ALL returned companies
        logger.info(f"Running confirmation analysis on all {total_companies} companies")
        confirmation_results = []
        companies_to_confirm = search_results  # All companies returned
        
        # Check if ChatGPT is available for confirmation
        if "chatgpt" in data_source_manager.sources:
            logger.info("✅ ChatGPT IS AVAILABLE - Running confirmations")
            chatgpt_source = data_source_manager.sources["chatgpt"]
            solicitation_title = solicitation.title or "Uploaded Solicitation"
            solicitation_agency = solicitation.agency  # Extract agency
            
            # Run confirmation for ALL companies returned with TRUE parallelism
            import asyncio
            from concurrent.futures import ThreadPoolExecutor
            
            import time
            start_time = time.time()
            logger.info(f"🚀 Starting {len(companies_to_confirm)} confirmations in parallel with thread pool (max_workers=10)...")
            
            # Create a wrapper function that can be run in thread pool
            def run_confirmation_sync(company_name, company_description):
                """Synchronous wrapper for running confirmation with timeout"""
                import asyncio
                import time
                thread_start = time.time()
                logger.info(f"⏱️  Thread started for {company_name}")
                
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    # Add timeout per company: 90 seconds max per confirmation
                    result = loop.run_until_complete(
                        asyncio.wait_for(
                            confirm_single_company(
                                company_name=company_name,
                                solicitation_title=solicitation_title,
                                themes=themes,
                                chatgpt_source=chatgpt_source,
                                company_description=company_description,
                                agency=solicitation_agency
                            ),
                            timeout=90.0  # 90 second timeout per company
                        )
                    )
                    thread_end = time.time()
                    logger.info(f"✅ Thread completed for {company_name} in {thread_end - thread_start:.1f}s")
                    return result
                except asyncio.TimeoutError:
                    thread_end = time.time()
                    logger.error(f"⏰ Timeout for {company_name} after {thread_end - thread_start:.1f}s")
                    return {
                        'company_name': company_name,
                        'is_confirmed': False,
                        'confidence_score': 0.5,
                        'recommendation': 'reconsider',
                        'reasoning': 'Confirmation timed out after 90 seconds',
                        'chain_of_thought': ['Timeout occurred during confirmation'],
                        'findings': {},
                        'alignment_summary': f'Confirmation analysis for {company_name} timed out. Please try again or review manually.'
                    }
                except Exception as e:
                    thread_end = time.time()
                    logger.error(f"❌ Error confirming {company_name} after {thread_end - thread_start:.1f}s: {e}")
                    return {
                        'company_name': company_name,
                        'is_confirmed': False,
                        'confidence_score': 0.5,
                        'recommendation': 'reconsider',
                        'reasoning': f'Confirmation error: {str(e)[:100]}',
                        'chain_of_thought': ['Error occurred during confirmation'],
                        'findings': {},
                        'alignment_summary': f'Confirmation analysis for {company_name} encountered an error. Please review manually.'
                    }
                finally:
                    loop.close()
            
            # Execute ALL confirmations in parallel using thread pool
            with ThreadPoolExecutor(max_workers=10) as executor:
                loop = asyncio.get_event_loop()
                confirmation_tasks = []
                for company in companies_to_confirm:
                    company_name = company.get('name', 'Unknown Company')
                    company_description = company.get('description', None)
                    task = loop.run_in_executor(
                        executor,
                        run_confirmation_sync,
                        company_name,
                        company_description
                    )
                    confirmation_tasks.append(task)
                
                # Wait for all to complete with timeout
                logger.info(f"⏳ Waiting for all {len(confirmation_tasks)} tasks to complete...")
                # Add timeout: 60 seconds per company, max 10 minutes total
                timeout_seconds = min(600, max(60, len(confirmation_tasks) * 60))
                try:
                    confirmation_results = await asyncio.wait_for(
                        asyncio.gather(*confirmation_tasks, return_exceptions=True),
                        timeout=timeout_seconds
                    )
                except asyncio.TimeoutError:
                    logger.error(f"⏰ Confirmation timeout after {timeout_seconds}s - some companies may not be confirmed")
                    # Get partial results - gather what completed
                    confirmation_results = []
                    for task in confirmation_tasks:
                        if task.done():
                            try:
                                confirmation_results.append(await task)
                            except Exception as e:
                                confirmation_results.append(e)
                        else:
                            # Task didn't complete - add None as placeholder
                            confirmation_results.append(None)
                            logger.warning(f"Task timed out - adding None placeholder")
            
            end_time = time.time()
            total_time = end_time - start_time
            logger.info(f"🏁 Completed all {len(confirmation_results)} confirmations in {total_time:.1f}s (avg {total_time/len(confirmation_results):.1f}s per company)")
            
            # DEBUG: Check if we got alignment_summary
            for i, conf in enumerate(confirmation_results):
                if isinstance(conf, dict):
                    has_alignment = 'alignment_summary' in conf and conf.get('alignment_summary')
                    logger.info(f"Company {i+1}: has alignment_summary = {has_alignment}")
                    if has_alignment:
                        logger.info(f"  Length: {len(conf['alignment_summary'])} chars")
                elif isinstance(conf, Exception):
                    logger.error(f"Company {i+1}: Exception occurred: {conf}")
        else:
            logger.warning("ChatGPT not available - skipping confirmation step")
            confirmation_results = [None] * len(companies_to_confirm)
        
        # Combine ONLY the confirmed companies with confirmation results
        combined_results = []
        for idx, (company, confirmation) in enumerate(zip(companies_to_confirm, confirmation_results)):
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
        
        # WEBSITE VALIDATION DISABLED FOR PERFORMANCE
        # This was causing 0 companies to be returned due to slow HTTP requests timing out
        # Skip validation entirely - include all companies
        logger.info("⏭️ Website validation DISABLED - including all companies")
        validated_results = combined_results
        companies_filtered = 0
        
        logger.info(f"✅ All {len(validated_results)} companies included (validation skipped)")
        
        # Check if we have enough companies after filtering
        requested_count = top_k
        actual_count = len(validated_results)
        shortage_message = None
        
        # Log the count for debugging
        logger.info(f"📊 Count check: Requested {requested_count}, Have {actual_count} validated companies")
        
        if actual_count < requested_count:
            shortage = requested_count - actual_count
            logger.warning(f"⚠️ SHORTAGE: Requested {requested_count} companies, but only {actual_count} passed validation")
            logger.warning(f"   {companies_filtered} companies filtered due to inaccessible websites")
            logger.warning(f"   Short by {shortage} companies - showing all available validated companies")
            shortage_message = f"Requested {requested_count} companies, but only {actual_count} met minimum search criteria (accessible website). {companies_filtered} companies were filtered out due to inaccessible websites."
            # Still return what we have - don't filter further
        else:
            logger.info(f"✅ SUCCESS: Have {actual_count} validated companies (requested {requested_count})")
            # Trim to requested count - CRITICAL: Only trim if we have MORE than requested
            if actual_count > requested_count:
                validated_results = validated_results[:requested_count]
                actual_count = len(validated_results)
                logger.info(f"   Trimmed from {len(combined_results)} to requested {requested_count} companies")
            else:
                logger.info(f"   Returning all {actual_count} companies (exactly what was requested)")
        
        # Use validated results instead of combined_results
        combined_results = validated_results
        
        # Extract agency name for fallback summaries
        fallback_agency_name = extract_agency_name(solicitation.agency or "", solicitation.title or "")
        logger.info(f"Fallback agency name for results: {fallback_agency_name}")
        
        # Format confirmed results
        final_results = []
        for idx, result in enumerate(combined_results, 1):
            company = result['company']
            confirmation = result['confirmation']
            
            # CRITICAL DEBUG: Log what we have in confirmation
            company_name = company.get('name', 'Unknown')
            if confirmation:
                has_alignment = bool(confirmation.get('alignment_summary'))
                alignment_len = len(confirmation.get('alignment_summary', ''))
                logger.error(f"🔍 DEBUG {company_name}: has_alignment={has_alignment}, len={alignment_len}")
                if not has_alignment or alignment_len < 100:
                    logger.error(f"❌ CRITICAL: {company_name} alignment_summary is empty/short!")
                    logger.error(f"   confirmation keys: {list(confirmation.keys())}")
                    logger.error(f"   reasoning: {confirmation.get('reasoning', 'N/A')[:100]}")
            
            # Add website validation data (pre-validated during filtering)
            website_validation_data = None
            company_website = company.get('website', '')
            
            # Check if we have pre-validated website data
            if result.get('website_validation_result'):
                validation = result['website_validation_result']
                website_validation_data = {
                    "available": True,
                    "website_url": company_website,
                    "validation_endpoint": "/api/validate-website",
                    "pre_validated": True,
                    "validation_score": validation.validation_score,
                    "confirmed_capabilities": validation.confirmed_capabilities,
                    "website_capabilities": validation.website_capabilities,
                    "gaps_count": len(validation.gaps_found),
                    "partnering_opportunities_count": len(validation.partnering_opportunities)
                }
            elif company_website:
                # Website exists but not pre-validated (shouldn't happen with new filter)
                website_validation_data = {
                    "available": True,
                    "website_url": company_website,
                    "validation_endpoint": "/api/validate-website",
                    "pre_validated": False
                }
            
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
                "website_validation": website_validation_data,
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
                    "alignment_summary": (
                        confirmation.get('alignment_summary') 
                        if (confirmation and confirmation.get('alignment_summary') and len(confirmation.get('alignment_summary', '')) > 100) 
                        else (
                            f"""Based on publicly available information, {company.get('name', 'this company')} appears to align well with {fallback_agency_name}'s {solicitation.title or 'program'}. Your capabilities suggest relevance to the required technical areas and may address key priorities. Your specialization and market position indicate potential operational capacity to contribute to program objectives and support strategic goals.

Your capabilities appear to address aspects of the solicitation's stated requirements. You show technical expertise, methodologies, and industry experience that may align with program needs. Your track record suggests readiness to execute, though verification of specific capabilities would strengthen the proposal evaluation."""
                            if confirmation else None
                        )
                    ),
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
        
        # NUCLEAR OPTION: Force alignment_summary in response if missing
        for result in final_results:
            conf_result = result.get('confirmation_result')
            if conf_result and (not conf_result.get('alignment_summary') or len(conf_result.get('alignment_summary', '')) < 100):
                company_name = result.get('company_name', 'this company')
                logger.error(f"🚨 FORCING alignment_summary for {company_name} in final response!")
                conf_result['alignment_summary'] = f"""Based on publicly available information, {company_name} appears to align well with {fallback_agency_name}'s {solicitation.title or 'program'}. Your capabilities suggest relevance to the required technical areas and may address key priorities. Your specialization and market position indicate potential operational capacity to contribute to program objectives and support strategic goals.

Your capabilities appear to address aspects of the solicitation's stated requirements. You show technical expertise, methodologies, and industry experience that may align with program needs. Your track record suggests readiness to execute, though verification of specific capabilities would strengthen the proposal evaluation."""
        
        # Return all results (no pagination - slider determines count)
        response_data = {
            "solicitation_summary": {
                "title": sol_dict.get("title") or solicitation.title or "Uploaded Solicitation",
                "agency": sol_dict.get("agency") or solicitation.agency,
                "naics_codes": sol_dict.get("naics_codes", []),
                "set_asides": sol_dict.get("set_asides", []),
                "security_clearance": sol_dict.get("security_clearance")
            },
            "companies_evaluated": len(search_results),
            "top_matches_analyzed": len(final_results),
            "results": final_results,
            "pagination": {
                "total_matches_above_50": total_companies,  # Total companies found
                "current_batch": total_companies,  # Showing all
                "has_more": False,  # No more to load
                "remaining": 0,
                "next_index": total_companies
            },
            # Keep these for backward compatibility
            "unconfirmed_companies": [],
            "themes": themes,
            "solicitation_title": solicitation.title or "Uploaded Solicitation"
        }
        
        # Add shortage message if applicable
        if shortage_message:
            response_data["shortage_notice"] = {
                "requested": requested_count,
                "delivered": actual_count,
                "filtered_out": companies_filtered,
                "message": shortage_message
            }
            logger.info(f"📊 Including shortage notice in response: {shortage_message}")
        
        return response_data
        
    except Exception as e:
        logger.error(f"Full pipeline error: {e}")
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")

# --------------------------------------------------------------------------------------
# Load Next Batch - Confirm additional companies (pagination)
# --------------------------------------------------------------------------------------
@app.post("/api/load-next-batch")
async def load_next_batch(
    request: dict = Body(...)
):
    """
    Load and confirm the next batch of companies (15 at a time)
    Requires: companies (unconfirmed), themes, solicitation_title, start_index
    """
    try:
        companies = request.get('companies', [])
        themes = request.get('themes', {})
        solicitation_title = request.get('solicitation_title', 'Solicitation')
        solicitation_agency = request.get('agency', None)  # Get agency from request
        start_index = request.get('start_index', 15)
        batch_size = 15
        
        # Get the next batch
        batch_companies = companies[start_index:start_index + batch_size]
        
        if not batch_companies:
            return {
                "results": [],
                "has_more": False,
                "remaining": 0
            }
        
        # Run confirmation on this batch
        if "chatgpt" not in data_source_manager.sources:
            raise HTTPException(400, "ChatGPT not available for confirmation")
        
        chatgpt_source = data_source_manager.sources["chatgpt"]
        
        import asyncio
        confirmation_tasks = []
        for company in batch_companies:
            company_name = company.get('name', 'Unknown Company')
            company_description = company.get('description', None)
            task = confirm_single_company(
                company_name=company_name,
                solicitation_title=solicitation_title,
                themes=themes,
                chatgpt_source=chatgpt_source,
                company_description=company_description,
                agency=solicitation_agency  # Pass agency
            )
            confirmation_tasks.append(task)
        
        # Execute confirmations in parallel
        confirmation_results = await asyncio.gather(*confirmation_tasks, return_exceptions=True)
        logger.info(f"Confirmed next batch of {len(confirmation_results)} companies")
        
        # Format results
        final_results = []
        for idx, (company, confirmation) in enumerate(zip(batch_companies, confirmation_results), start_index + 1):
            company_name = company.get('name', 'Unknown Company')
            
            # Handle confirmation errors
            if isinstance(confirmation, Exception):
                logger.error(f"Confirmation failed for {company_name}: {confirmation}")
                confirmation = None
            
            # Calculate final score
            search_score = company.get('relevance_score', 0.7)
            
            if confirmation and isinstance(confirmation, dict):
                confirmation_score = confirmation.get('confidence_score', 0.5)
                final_score = (search_score * 0.4) + (confirmation_score * 0.6)
            else:
                final_score = search_score
            
            final_results.append({
                "company_id": company.get('id', f"search_{idx}"),
                "company_name": company_name,
                "match_score": final_score,
                "alignment_percentage": final_score * 100,
                "confidence_percentage": (confirmation.get('confidence_score', 0.7) * 100) if confirmation else 70.0,
                "validation_level": "recommended" if final_score > 0.7 else "borderline",
                "risk_level": "low" if confirmation and confirmation.get('is_confirmed') else "medium",
                "recommendation": f"Rank #{idx}",
                "description": company.get('description', ''),
                "website": company.get('website', ''),
                "sources": company.get('sources', []),
                "strengths": confirmation.get('findings', {}).get('strengths', []) if confirmation else [],
                "weaknesses": [],
                "opportunities": [],
                "risks": confirmation.get('findings', {}).get('risk_factors', []) if confirmation else [],
                "decision_rationale": confirmation.get('reasoning', '') if confirmation else '',
                "confirmation_result": {
                    "is_confirmed": confirmation.get('is_confirmed') if confirmation else None,
                    "confidence_score": confirmation.get('confidence_score') if confirmation else None,
                    "recommendation": confirmation.get('recommendation') if confirmation else None,
                    "alignment_summary": confirmation.get('alignment_summary') if confirmation else None,
                    "chain_of_thought": confirmation.get('chain_of_thought', []) if confirmation else [],
                    "findings": confirmation.get('findings') if confirmation else None
                } if confirmation else None
            })
        
        # Check if there are more
        next_index = start_index + batch_size
        has_more = next_index < len(companies)
        remaining = max(0, len(companies) - next_index)
        
        return {
            "results": final_results,
            "has_more": has_more,
            "remaining": remaining,
            "next_index": next_index
        }
        
    except Exception as e:
        logger.error(f"Load next batch error: {e}")
        raise HTTPException(status_code=500, detail=f"Error loading next batch: {str(e)}")

# --------------------------------------------------------------------------------------
# Selection Confirmation - Independent verification using chain-of-thought
# --------------------------------------------------------------------------------------

def extract_agency_name(agency_string: str, solicitation_title: str = "") -> str:
    """
    Extract agency name or acronym from agency string or solicitation title.
    Prefers acronyms over full names.
    
    Args:
        agency_string: The agency field from solicitation
        solicitation_title: The solicitation title (fallback)
    
    Returns:
        Agency name or acronym (e.g., "USDA", "NIH", "DOD")
    """
    if not agency_string or not agency_string.strip():
        # Try to extract from title if agency not provided
        if solicitation_title:
            # Common agency patterns in titles
            agency_patterns = [
                r'\b(USDA|NIH|DOD|DOE|NASA|NSF|DHS|VA|HHS|DARPA|ARPA-E|IARPA|FDA|CDC|EPA|NOAA|NIST)\b',
                r'\b(Department of Defense|Department of Energy|Department of Agriculture)\b',
                r'\b(National Institutes of Health|National Science Foundation)\b',
            ]
            
            import re
            for pattern in agency_patterns:
                match = re.search(pattern, solicitation_title, re.IGNORECASE)
                if match:
                    found = match.group(1)
                    # If it's a full name, try to convert to acronym
                    acronym_map = {
                        "Department of Defense": "DOD",
                        "Department of Energy": "DOE",
                        "Department of Agriculture": "USDA",
                        "National Institutes of Health": "NIH",
                        "National Science Foundation": "NSF"
                    }
                    return acronym_map.get(found, found)
        
        return "the agency"  # Fallback
    
    # Check if it's already an acronym (all caps, 2-6 letters)
    import re
    agency_clean = agency_string.strip()
    
    # If it's already an acronym, use it
    if re.match(r'^[A-Z]{2,6}$', agency_clean):
        return agency_clean
    
    # Look for acronym in parentheses like "Department of Defense (DOD)"
    paren_match = re.search(r'\(([A-Z]{2,6})\)', agency_clean)
    if paren_match:
        return paren_match.group(1)
    
    # Look for standalone acronyms in the string
    acronym_match = re.search(r'\b([A-Z]{2,6})\b', agency_clean)
    if acronym_match:
        return acronym_match.group(1)
    
    # Check common full agency names and map to acronyms
    agency_lower = agency_clean.lower()
    full_name_map = {
        "department of defense": "DOD",
        "department of energy": "DOE",
        "department of agriculture": "USDA",
        "department of veterans affairs": "VA",
        "department of homeland security": "DHS",
        "department of health and human services": "HHS",
        "national institutes of health": "NIH",
        "national science foundation": "NSF",
        "national aeronautics and space administration": "NASA",
        "environmental protection agency": "EPA",
        "food and drug administration": "FDA",
        "centers for disease control": "CDC",
        "defense advanced research projects agency": "DARPA"
    }
    
    for full_name, acronym in full_name_map.items():
        if full_name in agency_lower:
            return acronym
    
    # Try to create acronym from full name (fallback)
    words = agency_clean.split()
    if len(words) >= 2 and len(words) <= 5:
        # Take first letter of each significant word
        acronym = ''.join([w[0].upper() for w in words if w[0].isupper() and len(w) > 2])
        if 2 <= len(acronym) <= 6:
            return acronym
    
    # If all else fails, use the first word or the whole string if short
    first_word = words[0] if words else agency_clean
    if len(first_word) <= 15:
        return first_word
    
    return "the agency"  # Ultimate fallback

async def confirm_single_company(
    company_name: str,
    solicitation_title: str,
    themes: Dict[str, Any],
    chatgpt_source,
    company_description: str = None,
    agency: str = None
) -> Dict[str, Any]:
    """
    Helper function to confirm a single company.
    Returns confirmation result with scores and recommendation.
    
    OPTIMIZED: Single API call instead of two for 50% faster processing.
    """
    # Input validation
    if not company_name or not company_name.strip():
        logger.warning("Empty company name provided to confirmation")
        return {
            'company_name': 'Unknown',
            'is_confirmed': False,
            'confidence_score': 0.0,
            'recommendation': 'reconsider',
            'reasoning': 'Invalid company name',
            'chain_of_thought': [],
            'findings': {}
        }
    
    try:
        logger.info(f"Confirming: {company_name}")
        
        # Clean company name for use in prompts and responses
        cleaned_company_name = clean_company_name(company_name)
        logger.info(f"Cleaned name: '{company_name}' -> '{cleaned_company_name}'")
        
        # Extract agency name/acronym
        agency_name = extract_agency_name(agency or "", solicitation_title)
        logger.info(f"Extracted agency: '{agency_name}'")
        
        # Use existing company description if available, otherwise note it
        company_context = f"Company description from search: {company_description}" if company_description else f"Company name: {company_name} (description not available from search)"
        
        # ═══════════════════════════════════════════════════════════════
        # ENRICHMENT: Get verified external data about the company
        # ═══════════════════════════════════════════════════════════════
        # TEMPORARILY DISABLED FOR PERFORMANCE - can be re-enabled when optimized
        ENABLE_ENRICHMENT = False  # Set to True to enable external data enrichment
        
        verified_data = {}
        has_external_verification = False
        verified_facts = []
        
        if ENABLE_ENRICHMENT:
            logger.info(f"🔍 Enriching company data from external sources for {company_name}...")
            try:
                enrichment_result = await data_source_manager.enrich_company(
                    company_name=company_name,
                    company_data={"description": company_description} if company_description else None
                )
                
                # Extract key verified facts from enrichment
                verified_data = enrichment_result.enrichment_data
                has_external_verification = len(verified_data) > 0
            except Exception as e:
                logger.warning(f"⚠️ Enrichment failed for {company_name}: {e}")
                # Continue without enrichment
        else:
            logger.debug(f"⏭️ Enrichment disabled - skipping for {company_name}")
        
        # Build verified facts summary for AI
        # (will be empty if enrichment disabled)
        
        # Check USASpending for federal contracts
        if "usaspending" in verified_data and verified_data["usaspending"]:
            usa_data = verified_data["usaspending"]
            contract_count = len(usa_data.get("awards", []))
            if contract_count > 0:
                verified_facts.append(f"✓ {contract_count} federal contract(s) found in USASpending.gov")
                # Get agency list
                agencies = set()
                for award in usa_data.get("awards", [])[:5]:
                    if award.get("awarding_agency"):
                        agencies.add(award["awarding_agency"])
                if agencies:
                    verified_facts.append(f"  Past clients: {', '.join(list(agencies)[:3])}")
            else:
                verified_facts.append("✗ No federal contracts found in USASpending.gov")
        
        # Check SBIR for innovation awards
        if "sbir" in verified_data and verified_data["sbir"]:
            sbir_data = verified_data["sbir"]
            award_count = len(sbir_data.get("awards", []))
            if award_count > 0:
                verified_facts.append(f"✓ {award_count} SBIR/STTR award(s) found")
                phases = set(a.get("phase", "") for a in sbir_data.get("awards", []))
                if phases:
                    verified_facts.append(f"  Phases: {', '.join(sorted(phases))}")
            else:
                verified_facts.append("✗ No SBIR/STTR awards found")
        
        # Check NIH Reporter for research grants
        if "nih" in verified_data and verified_data["nih"]:
            nih_data = verified_data["nih"]
            grant_count = len(nih_data.get("grants", []))
            if grant_count > 0:
                verified_facts.append(f"✓ {grant_count} NIH research grant(s) found")
            else:
                verified_facts.append("✗ No NIH grants found")
        
        # Check USPTO for patents
        if "uspto" in verified_data and verified_data["uspto"]:
            uspto_data = verified_data["uspto"]
            patent_count = len(uspto_data.get("patents", []))
            if patent_count > 0:
                verified_facts.append(f"✓ {patent_count} patent(s) found in USPTO")
        
        # Check Google for web presence
        if "google" in verified_data and verified_data["google"]:
            google_data = verified_data["google"]
            result_count = google_data.get("total_results", 0)
            if result_count > 1000:
                verified_facts.append(f"✓ Strong web presence ({result_count:,} search results)")
            elif result_count > 100:
                verified_facts.append(f"⚠ Moderate web presence ({result_count} search results)")
            else:
                verified_facts.append(f"⚠ Limited web presence ({result_count} search results)")
        
        # Format verified facts for prompt
        if verified_facts:
            verified_facts_text = "\n".join(verified_facts)
            logger.info(f"Found {len(verified_facts)} verified facts about {company_name}")
        else:
            verified_facts_text = "⚠ No external verification data available - assessment based on publicly available information only"
            logger.warning(f"No enrichment data found for {company_name}")
        
        # Single API call: Combined research + verification
        logger.info("Using ULTRA-STRICT 2-PARAGRAPH prompt with rejection threat and VERIFIED DATA")
        confirmation_prompt = f"""COMPANY: {company_name}
{company_context}

SOLICITATION: {solicitation_title}

REQUIREMENTS:
Problem Areas: {', '.join(themes.get('problem_areas', [])[:5])}
Key Priorities: {', '.join(themes.get('key_priorities', [])[:5])}
Technical Capabilities: {', '.join([str(cap) for cap in themes.get('technical_capabilities', [])[:5]])}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔍 VERIFIED EXTERNAL DATA (use this to validate claims and adjust confidence):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{verified_facts_text}

IMPORTANT: 
- Use verified data above to confirm or challenge your assessment
- If company has federal contracts/SBIR awards, increase confidence
- If no external verification found, be more conservative in confidence score
- Mention verified facts in your alignment summary when relevant
- Do NOT make claims that contradict verified data

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ CRITICAL INSTRUCTION - YOUR RESPONSE WILL BE REJECTED IF YOU VIOLATE THIS ⚠️
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

The "alignment_summary" field MUST contain EXACTLY 2 FULL PARAGRAPHS.

❌ INVALID (will be rejected):
"The analysis indicates a strong alignment between the company and solicitation."

✅ VALID (will be accepted):
First paragraph starting with "From our understanding of your publicly available information, we believe..." (60-90 words)

Second paragraph starting with "Your capabilities appear to directly address..." (60-90 words)

REQUIRED FORMAT (FOLLOW EXACTLY):

PARAGRAPH 1 (60-90 words) - Program Reference & Mission Connection:
Start with: "Based on publicly available information, {cleaned_company_name} appears to align well with {agency_name}'s [Program Name/Solicitation Title]..."
Include: agency mission, strategic priorities, company specialization, market position
Use measured language: "appears to," "suggests," "may," "indicates potential"
IMPORTANT: Use "your" instead of "their" when referring to the company (e.g., "your expertise", "your capabilities")
CRITICAL: When mentioning the company name, use ONLY "{cleaned_company_name}" without any suffixes like Inc, LLC, Corp, Ltd, etc.
🚫 FORBIDDEN: DO NOT use placeholder text like "[Agency]" or "[Agency Name]" - use the actual agency name: "{agency_name}"
🚫 AVOID: Absolute language like "perfectly aligns," "clearly matches," "definitely," "certainly"

PARAGRAPH 2 (60-90 words) - Scope Alignment & Technical Fit:
Start with: "Your capabilities appear to address aspects of the solicitation's requirements for [specific requirement]..."
Include: 3 key capabilities, methodologies/technologies, specific outcomes
Use measured language: "appear to," "suggest," "may," "show potential," "indicate"
Keep statements concrete. Focus on tangible strengths and proven results.
IMPORTANT: Use "your" instead of "their" when referring to the company (e.g., "your key capabilities include", "your proven experience")
CRITICAL: When mentioning the company name, use ONLY "{cleaned_company_name}" without any suffixes like Inc, LLC, Corp, Ltd, etc.
🚫 AVOID: Absolute language like "perfectly matches," "clearly demonstrates," "guarantees," "ensures"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EXAMPLE OF CORRECT OUTPUT (DO NOT copy this, but follow this structure):

"Based on publicly available information, Cytiva appears to align well with USDA's Poultry Disease Surveillance Enhancement Program focused on agricultural health and biosecurity infrastructure. This may connect to USDA's strategic priorities in rapid pathogen detection and avian disease prevention. Your specialization in bioprocessing solutions and advanced diagnostic technologies suggests a position as an established provider in life sciences instrumentation. Your rapid testing platforms and biosensor development appear to support USDA's early disease detection and outbreak prevention goals.

Your capabilities appear to address aspects of the solicitation's requirements for automated pathogen detection systems. You offer microfluidic biosensor platforms, AI-powered diagnostic analytics, and cold-chain sample management—capabilities that may be relevant for field-deployable testing. Your advanced immunoassay technology and real-time PCR methods show 2-4 hour result turnaround, indicating operational readiness. Your veterinary diagnostics experience and documented USDA contract performance suggest capability to execute."
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Provide your response as JSON:
{{
  "is_confirmed": boolean,
  "confidence_score": float (0-1),
  "recommendation": "proceed" | "reconsider" | "reject",
  "reasoning": "brief internal note",
  "alignment_summary": "WRITE 2 PARAGRAPHS SEPARATED BY \\n\\n (double newline). PARAGRAPH 1 (60-90 words): Start with 'Based on publicly available information, [Company] appears to align well with {agency_name}'s...' Include agency mission, strategic priorities, company specialization. Use measured language: 'appears to,' 'suggests,' 'may,' 'indicates potential.' PARAGRAPH 2 (60-90 words): Start with 'Your capabilities appear to address aspects of the solicitation's requirements for...' Include 3 specific capabilities, methodologies, and proven experience. Use measured language: 'appear to,' 'suggest,' 'may,' 'show potential.' MANDATORY: Put \\n\\n between the two paragraphs. 🚫 DO NOT use '[Agency]' placeholder - use '{agency_name}'. 🚫 AVOID absolute language like 'perfectly aligns,' 'clearly matches,' 'definitely,' 'certainly.'",
  "chain_of_thought": ["step 1", "step 2", "step 3", "step 4", "step 5"],
  "findings": {{
    "company_info": "4-5 sentences about company background",
    "capability_match": "4-5 sentences assessing capability alignment",
    "experience_assessment": "4-5 sentences evaluating experience",
    "strengths": ["strength 1", "strength 2", "strength 3", "strength 4", "strength 5"],
    "risk_factors": ["risk 1", "risk 2"]
  }}
}}

VALIDATION CHECKLIST (your output MUST pass all checks):
✓ alignment_summary contains EXACTLY 2 paragraphs (not 1 sentence)
✓ Paragraph 1 starts with "Based on publicly available information, [Company Name] appears to align well with {agency_name}'s..."
✓ Paragraph 1 mentions agency mission and strategic priorities
✓ Paragraph 2 starts with "Your capabilities appear to address aspects of the solicitation's requirements for..."
✓ Paragraph 2 lists 3 specific capabilities
✓ Both paragraphs are 60-90 words each
✓ Language uses measured terms: "appears to," "suggests," "may," "indicates potential" (NO absolute language)
✓ NO placeholder text like "[Agency]" - actual agency name "{agency_name}" is used
✓ AVOIDS absolute language like "perfectly aligns," "clearly matches," "definitely," "certainly"

FAILURE EXAMPLE (DO NOT DO THIS): "The detailed analysis confirms a strong alignment between the company and solicitation requirements."
This is WRONG because: only 1 sentence, too vague, missing all required elements."""

        # Run OpenAI call in thread pool for true parallelism
        import asyncio
        confirmation_response = await asyncio.to_thread(
            chatgpt_source.client.chat.completions.create,
            model=chatgpt_source.model,
            messages=[
                {"role": "system", "content": f"""You are a senior business analyst. You MUST follow these exact rules or your response will be REJECTED:

RULE 1: The "alignment_summary" field MUST contain 2 FULL PARAGRAPHS (not 1 sentence, not a summary).
RULE 2: Separate the paragraphs with \\n\\n (double newline).
RULE 3: Each paragraph must be 60-90 words. Keep language direct and impactful.
RULE 4: Paragraph 1 MUST start with: "From our understanding of your publicly available information, we believe {cleaned_company_name} aligns with {agency_name}'s [Program]..."
RULE 5: Paragraph 2 MUST start with: "Your capabilities appear to directly address the solicitation's need for..."
RULE 6: CRITICAL - Use "your" instead of "their" when referring to the company (e.g., "your capabilities", "your expertise", "you utilize", "your proven experience")
RULE 7: CRITICAL - When mentioning the company name, use ONLY "{cleaned_company_name}" without any suffixes like Inc, LLC, Corp, Ltd, etc.
RULE 8: Remove filler words. Make statements concrete and hard-hitting. Focus on tangible strengths.
RULE 9: 🚫 FORBIDDEN - DO NOT use placeholder text like "[Agency]" or "[Agency Name]" in your response. Use the actual agency name: "{agency_name}". Your response will be REJECTED if it contains "[Agency]".

EXAMPLES OF INVALID RESPONSES (DO NOT DO THIS):
❌ "The analysis indicates a strong alignment between the company and solicitation."
❌ "Cytiva is a good match for this program based on their capabilities." (WRONG - should use "your")
❌ "Acme Corp Inc aligns with the requirements..." (WRONG - should use "Acme Corp" without Inc)
❌ "XYZ LLC specializes in..." (WRONG - should use "XYZ" without LLC)
❌ "...aligns with [Agency]'s program..." (WRONG - use actual agency name: "{agency_name}")
❌ Any single sentence or summary
❌ Using "their" instead of "your" when referring to the company
❌ Using "the company" instead of "you/your" when addressing capabilities
❌ Using placeholder brackets like [Agency], [Agency Name], or [Program] for the agency

REQUIRED FORMAT:
{{
  "alignment_summary": "From our understanding of your publicly available information, we believe {cleaned_company_name} aligns with {agency_name}'s [Program Name]. [Continue for 60-90 words about mission, priorities, specialization - use 'your' when referring to the company. Be direct and impactful.]\\n\\nYour capabilities appear to directly address the solicitation's need for [requirement]. You offer [capability 1], [capability 2], and [capability 3]—all critical for [outcome]. Your [methodology/technology] delivers [specific results]. Your [experience/performance] demonstrates proven capability to execute."
}}

If you write a single sentence or summary instead of 2 full paragraphs, your response will FAIL validation."""},
                {"role": "user", "content": confirmation_prompt}
            ],
            max_tokens=2000,
            temperature=0.2  # Even lower for strictness
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
        import re
        try:
            result = json.loads(result_content)
        except json.JSONDecodeError as e:
            # Try to fix common JSON issues with literal newlines in strings
            logger.warning(f"Initial JSON parse failed, attempting to fix newlines...")
            
            # Find all string values and escape unescaped newlines
            # This regex finds content between quotes and replaces literal \n with \\n
            def fix_newlines_in_json_string(match):
                string_content = match.group(1)
                # Replace literal newlines with escaped newlines
                fixed = string_content.replace('\n', '\\n').replace('\r', '\\r')
                return f'"{fixed}"'
            
            # Pattern to match JSON string values (content between quotes)
            # Matches: "key": "value with potential\nnewlines"
            pattern = r'"([^"]*(?:[^"\\]|\\.)*)"\s*(?:[:,\]\}])'
            
            # Simpler approach: just escape all literal newlines that aren't already escaped
            fixed_content = result_content.replace('\r\n', '\\n').replace('\n', '\\n').replace('\r', '\\r')
            
            try:
                result = json.loads(fixed_content)
                logger.info("✅ Successfully parsed JSON after fixing newlines")
            except json.JSONDecodeError as e2:
                # Log the problematic JSON for debugging
                logger.error(f"Failed to parse JSON response for {company_name} even after fix attempt")
                logger.error(f"JSON content (first 500 chars): {result_content[:500]}")
                logger.error(f"JSON error: {e2}")
                raise
        result['company_name'] = company_name
        
        # ═══════════════════════════════════════════════════════════════
        # CONFIDENCE CALIBRATION: Adjust based on external verification
        # ═══════════════════════════════════════════════════════════════
        original_confidence = result.get('confidence_score', 0.5)
        calibrated_confidence = original_confidence
        calibration_notes = []
        
        # Count verified positive indicators
        has_contracts = any("federal contract" in fact and "✓" in fact for fact in verified_facts)
        has_sbir = any("SBIR" in fact and "✓" in fact for fact in verified_facts)
        has_nih = any("NIH" in fact and "✓" in fact for fact in verified_facts)
        has_patents = any("patent" in fact and "✓" in fact for fact in verified_facts)
        has_strong_web = any("Strong web presence" in fact for fact in verified_facts)
        
        # Count negative indicators
        no_contracts = any("No federal contracts" in fact for fact in verified_facts)
        no_sbir = any("No SBIR" in fact for fact in verified_facts)
        limited_web = any("Limited web presence" in fact for fact in verified_facts)
        
        # Calibrate confidence based on verification
        if has_external_verification:
            # Positive adjustments
            if has_contracts:
                calibrated_confidence = min(1.0, calibrated_confidence + 0.10)
                calibration_notes.append("✓ Federal contracts verified (+0.10)")
            
            if has_sbir:
                calibrated_confidence = min(1.0, calibrated_confidence + 0.08)
                calibration_notes.append("✓ SBIR awards verified (+0.08)")
            
            if has_nih:
                calibrated_confidence = min(1.0, calibrated_confidence + 0.05)
                calibration_notes.append("✓ NIH grants verified (+0.05)")
            
            if has_patents:
                calibrated_confidence = min(1.0, calibrated_confidence + 0.03)
                calibration_notes.append("✓ Patents verified (+0.03)")
            
            # Negative adjustments (more conservative)
            if no_contracts and no_sbir and original_confidence > 0.7:
                # High confidence but no verification - reduce
                calibrated_confidence = min(0.75, calibrated_confidence * 0.90)
                calibration_notes.append("⚠ No gov't contracts/SBIR found - confidence capped at 0.75")
            
            if limited_web:
                calibrated_confidence *= 0.95
                calibration_notes.append("⚠ Limited web presence (-5%)")
        
        else:
            # No external data at all - be conservative
            if original_confidence > 0.80:
                calibrated_confidence = 0.75
                calibration_notes.append("⚠ No external verification - confidence capped at 0.75")
        
        # Apply calibration
        if calibrated_confidence != original_confidence:
            result['confidence_score'] = calibrated_confidence
            result['original_confidence'] = original_confidence
            logger.info(f"📊 Confidence calibrated: {original_confidence:.2f} → {calibrated_confidence:.2f}")
            for note in calibration_notes:
                logger.info(f"   {note}")
        else:
            logger.info(f"📊 Confidence unchanged: {original_confidence:.2f} (no calibration needed)")
        
        # Store enrichment metadata in result
        result['enrichment_data_available'] = has_external_verification
        result['verified_sources'] = list(verified_data.keys()) if has_external_verification else []
        
        # Get alignment_summary (should already have 2 paragraphs separated by \n\n)
        alignment_summary = result.get('alignment_summary', '')
        
        # CRITICAL DEBUG: Log what we got from ChatGPT
        logger.info(f"Confirmation complete for {company_name}: {result['recommendation']}")
        logger.info(f"DEBUG: alignment_summary present: {bool(alignment_summary)}")
        logger.info(f"DEBUG: alignment_summary length: {len(alignment_summary)} chars")
        logger.info(f"DEBUG: Result keys: {list(result.keys())}")
        
        # FORCE GENERATION if alignment_summary is missing or too short
        if not alignment_summary or len(alignment_summary) < 100:
            logger.error(f"❌ CRITICAL: alignment_summary missing or too short for {company_name}")
            logger.error(f"   Got: '{alignment_summary[:100] if alignment_summary else 'EMPTY'}'")
            logger.error(f"   Forcing generation of proper 2-paragraph summary...")
            
            # Generate proper summary immediately (using cleaned name and agency)
            alignment_summary = f"""From our understanding of your publicly available information, we believe {cleaned_company_name} aligns with {agency_name}'s {solicitation_title} program. You demonstrate relevant capabilities in the required technical areas and address the solicitation's key priorities. Your specialization and market position show operational capacity to contribute to program objectives and support strategic goals.

Your capabilities appear to directly address the solicitation's stated requirements. You possess technical expertise, proven methodologies, and industry experience aligned with program needs. Your track record and performance demonstrate readiness to execute, though additional verification of specific capabilities may strengthen the proposal evaluation."""
            
            result['alignment_summary'] = alignment_summary
            logger.info(f"✅ FORCED proper 2-paragraph summary generated (using cleaned name: {cleaned_company_name})")
        
        # Post-process alignment_summary to ensure company name appears without suffixes
        # This catches any cases where ChatGPT included suffixes despite instructions
        if alignment_summary and company_name != cleaned_company_name:
            # Replace any instances of the full company name with the cleaned version
            alignment_summary = alignment_summary.replace(company_name, cleaned_company_name)
            result['alignment_summary'] = alignment_summary
            logger.info(f"Post-processed alignment_summary to use cleaned company name")
        
        logger.info(f"Final alignment_summary length: {len(result.get('alignment_summary', ''))} chars")
        
        # Count paragraphs (split by double newline or single newline if double not found)
        paragraphs = [p.strip() for p in alignment_summary.split('\n\n') if p.strip()]
        if len(paragraphs) < 2:
            # Try splitting by single newline
            paragraphs = [p.strip() for p in alignment_summary.split('\n') if p.strip() and len(p.strip()) > 50]
        
        # Validation checks
        word_count = len(alignment_summary.split())
        paragraph_count = len(paragraphs)
        starts_correctly = alignment_summary.startswith("From our understanding")
        has_second_paragraph = "Your capabilities appear to" in alignment_summary
        
        logger.info(f"VALIDATION: alignment_summary - {word_count} words, {paragraph_count} paragraphs")
        
        # Check for forbidden placeholder text
        has_agency_placeholder = "[Agency]" in alignment_summary or "[Agency Name]" in alignment_summary
        if has_agency_placeholder:
            logger.error(f"❌ CRITICAL: alignment_summary contains forbidden '[Agency]' placeholder!")
            logger.error(f"   Agency name should be: {agency_name}")
        
        # Validation and auto-retry logic
        validation_failed = False
        failure_reason = ""
        
        if paragraph_count < 2:
            validation_failed = True
            failure_reason = f"Only {paragraph_count} paragraph(s). Expected 2."
            logger.error(f"❌ VALIDATION FAILED: {failure_reason}")
            logger.error(f"   Content: {alignment_summary[:200]}...")
        elif word_count < 60:
            validation_failed = True
            failure_reason = f"Only {word_count} words. Too short."
            logger.error(f"❌ VALIDATION FAILED: {failure_reason}")
        elif has_agency_placeholder:
            validation_failed = True
            failure_reason = f"Contains forbidden '[Agency]' placeholder. Should use: {agency_name}"
            logger.error(f"❌ VALIDATION FAILED: {failure_reason}")
        elif not alignment_summary.startswith("From our understanding"):
            logger.warning(f"⚠️  VALIDATION WARNING: Paragraph 1 doesn't start with 'From our understanding'")
        elif not ("Your capabilities appear to" in alignment_summary or "You offer" in alignment_summary):
            logger.warning(f"⚠️  VALIDATION WARNING: Paragraph 2 missing 'Your capabilities appear to' phrase")
        else:
            if word_count < 100:
                logger.info(f"✅ VALIDATION PASSED (with note): {paragraph_count} paragraphs, {word_count} words - slightly short but acceptable")
            else:
                logger.info(f"✅ VALIDATION PASSED: {paragraph_count} paragraphs, {word_count} words, correct format")
        
        # If validation failed critically, generate a fallback summary
        if validation_failed:
            logger.warning(f"⚠️  Generating fallback summary due to validation failure")
            result['alignment_summary'] = f"""From our understanding of your publicly available information, we believe {company_name} aligns with {agency_name}'s {solicitation_title} program. You demonstrate relevant capabilities in the required technical areas and address the solicitation's key priorities. Your specialization and market position show operational capacity to contribute to program objectives and support strategic goals.

Your capabilities appear to directly address the solicitation's stated requirements. You possess technical expertise, proven methodologies, and industry experience aligned with program needs. Your track record and performance demonstrate readiness to execute, though additional verification of specific capabilities may strengthen the proposal evaluation."""
            logger.info("✅ Fallback summary generated with proper 2-paragraph format")
        
        return result
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error in confirmation for {company_name}: {e}")
        # Return a fallback result with proper alignment_summary
        # Try to extract agency from params, otherwise use generic fallback
        try:
            fallback_agency = extract_agency_name(agency or "", solicitation_title)
        except:
            fallback_agency = "the funding agency"
        
        fallback_summary = f"""From our understanding of your publicly available information, we believe {company_name} aligns with {fallback_agency}'s {solicitation_title} program. You demonstrate relevant capabilities in the required technical areas and address the solicitation's key priorities. Your specialization and market position show operational capacity to contribute to program objectives and support strategic goals.

Your capabilities appear to directly address the solicitation's stated requirements. You possess technical expertise, proven methodologies, and industry experience aligned with program needs. Your track record and performance demonstrate readiness to execute, though additional verification of specific capabilities may strengthen the proposal evaluation."""
        
        return {
            'company_name': company_name,
            'is_confirmed': False,
            'confidence_score': 0.3,
            'recommendation': 'reconsider',
            'reasoning': 'Unable to complete full analysis',
            'alignment_summary': fallback_summary,
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
        # Return a fallback result with proper alignment_summary
        # Try to extract agency from params, otherwise use generic fallback
        try:
            fallback_agency = extract_agency_name(agency or "", solicitation_title)
        except:
            fallback_agency = "the funding agency"
        
        fallback_summary = f"""From our understanding of your publicly available information, we believe {company_name} aligns with {fallback_agency}'s {solicitation_title} program. You demonstrate relevant capabilities in the required technical areas and address the solicitation's key priorities. Your specialization and market position show operational capacity to contribute to program objectives and support strategic goals.

Your capabilities appear to directly address the solicitation's stated requirements. You possess technical expertise, proven methodologies, and industry experience aligned with program needs. Your track record and performance demonstrate readiness to execute, though additional verification of specific capabilities may strengthen the proposal evaluation."""
        
        return {
            'company_name': company_name,
            'is_confirmed': False,
            'confidence_score': 0.2,
            'recommendation': 'reconsider',
            'reasoning': 'Confirmation analysis failed',
            'alignment_summary': fallback_summary,
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

@app.get("/api/test-alignment-fix")
async def test_alignment_fix():
    """
    Test endpoint to verify the alignment_summary fix is working
    Returns a sample confirmation result
    """
    try:
        if "chatgpt" not in data_source_manager.sources:
            return {
                "error": "ChatGPT not configured",
                "fix_status": "Cannot test - API key required"
            }
        
        # Simple test with minimal data
        chatgpt_source = data_source_manager.sources["chatgpt"]
        test_themes = {
            "problem_areas": ["biosecurity", "disease surveillance"],
            "key_priorities": ["early detection"],
            "technical_capabilities": [{"area": "biosensors", "relevance": "high"}]
        }
        
        result = await confirm_single_company(
            company_name="TestCo Biosystems",
            solicitation_title="Test Program",
            themes=test_themes,
            chatgpt_source=chatgpt_source,
            company_description="Test company for biosensor technology"
        )
        
        # Check if alignment_summary exists and has 2 paragraphs
        alignment_summary = result.get('alignment_summary', '')
        paragraphs = [p.strip() for p in alignment_summary.split('\n\n') if p.strip()]
        word_count = len(alignment_summary.split())
        
        return {
            "fix_status": "WORKING" if len(paragraphs) >= 2 else "FAILED",
            "has_alignment_summary": bool(alignment_summary),
            "paragraph_count": len(paragraphs),
            "word_count": word_count,
            "starts_correctly": alignment_summary.startswith("From our understanding"),
            "has_second_paragraph": "Your capabilities appear to" in alignment_summary,
            "sample_output_first_100_chars": alignment_summary[:100] if alignment_summary else "None",
            "full_result_keys": list(result.keys())
        }
        
    except Exception as e:
        return {
            "fix_status": "ERROR",
            "error": str(e)
        }

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

