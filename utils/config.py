import os
import dotenv
from dataclasses import dataclass
from typing import Dict, Any, List, Optional

@dataclass
class TenderSchema:
    """Schema for tender data"""
    id: str
    title: str
    description: str
    source: str
    source_url: str
    publication_date: str
    deadline: str
    category: List[str]
    organization: str
    location: str
    estimated_value: Optional[float] = None
    currency: Optional[str] = None
    cpv_codes: Optional[List[str]] = None
    contact_info: Optional[Dict[str, str]] = None
    attachments: Optional[List[Dict[str, str]]] = None

@dataclass
class CompanySchema:
    """Schema for company data"""
    id: str
    name: str
    description: str
    industry: List[str]
    services: List[str]
    location: str
    size: str  # Small, Medium, Large
    expertise: List[str]
    past_projects: Optional[List[Dict[str, Any]]] = None
    certifications: Optional[List[str]] = None
    founded_year: Optional[int] = None
    revenue_range: Optional[str] = None
    contact_info: Optional[Dict[str, str]] = None

# Load environment variables
def load_config() -> Dict[str, Any]:
    """Load configuration from .env file"""
    dotenv.load_dotenv()
    
    config = {
        "OLLAMA_HOST": os.getenv("OLLAMA_HOST", "http://localhost:11434"),
        "OLLAMA_MODEL": os.getenv("OLLAMA_MODEL", "llama3"),
        "OLLAMA_EMBEDDING_MODEL": os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text"),
        "VECTOR_DB_PATH": os.getenv("VECTOR_DB_PATH", "./data/vector_db"),
        "VECTOR_DIMENSION": int(os.getenv("VECTOR_DIMENSION", "384")),
        "FIRECRAWL_API_KEY": os.getenv("FIRECRAWL_API_KEY", "")
    }
    
    return config

# Prompt templates
TENDER_EXTRACTION_PROMPT = """
You are a tender analysis system that extracts and structures information from tender documents.
Please analyze the following tender data and enrich it with additional insights.

Tender Data:
{tender_details}

Please provide:
1. A categorization of this tender (e.g., Construction, IT Services, Healthcare)
2. Key requirements and qualifications needed
3. Estimated complexity level (Low, Medium, High)
4. Potential challenges for bidders
5. Any specific compliance requirements

Format your response as a JSON object with the following structure:
{{
  "category": ["category1", "category2"],
  "key_requirements": ["requirement1", "requirement2", ...],
  "complexity_level": "Medium",
  "potential_challenges": ["challenge1", "challenge2", ...],
  "compliance_requirements": ["requirement1", "requirement2", ...]
}}
"""

COMPANY_PROFILE_EXTRACTION_PROMPT = """
You are a company profile analysis system. Please extract structured information from the following company document.

Document Content:
{document_text}

Extract the following information:
1. Company name
2. Brief description of the company
3. Industry sectors they operate in
4. Services they offer
5. Key expertise areas
6. Company size/scale
7. Notable past projects or clients
8. Certifications or compliance standards
9. Location information
10. Any other relevant information for matching with tenders

Format your response as a JSON object with the following structure:
{{
  "name": "Company Name",
  "description": "Brief description of the company",
  "industry": ["Industry1", "Industry2", ...],
  "services": ["Service1", "Service2", ...],
  "expertise": ["Expertise1", "Expertise2", ...],
  "size": "Small/Medium/Large",
  "past_projects": [
    {{ "name": "Project Name", "description": "Brief description" }},
    ...
  ],
  "certifications": ["Certification1", "Certification2", ...],
  "location": "Company location",
  "founded_year": 2005,
  "additional_info": "Any other relevant information"
}}
"""

TENDER_RECOMMENDATION_PROMPT = """
You are a tender recommendation system that matches companies with suitable tenders.
Please analyze the following company profile and tender details to determine how well they match.

Company Profile:
{company_profile}

Tender Details:
{tender_details}

Please evaluate how well this tender matches the company's profile based on:
1. Industry alignment
2. Required expertise match
3. Scale/size appropriateness
4. Location compatibility
5. Past experience relevance
6. Certification/compliance match

Provide a match score between 0.0 (no match) and 1.0 (perfect match), along with your reasoning.

Format your response as a JSON object with the following structure:
{{
  "match_score": 0.85,
  "reasoning": "Detailed explanation of the match analysis including strengths and potential gaps"
}}
"""