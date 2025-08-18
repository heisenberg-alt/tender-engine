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
        # Azure Cosmos DB Configuration
        "COSMOS_DB_ENDPOINT": os.getenv("COSMOS_DB_ENDPOINT", ""),
        "COSMOS_DB_KEY": os.getenv("COSMOS_DB_KEY", ""),
        "COSMOS_DB_DATABASE_NAME": os.getenv("COSMOS_DB_DATABASE_NAME", "tender-recommender"),
        
        # Azure OpenAI Configuration
        "AZURE_OPENAI_ENDPOINT": os.getenv("AZURE_OPENAI_ENDPOINT", ""),
        "AZURE_OPENAI_API_KEY": os.getenv("AZURE_OPENAI_API_KEY", ""),
        "AZURE_OPENAI_DEPLOYMENT_NAME": os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o"),
        "AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME": os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME", "text-embedding-3-small"),
        "AZURE_OPENAI_API_VERSION": os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview"),
        
        # Tender API Configuration
        "EU_TED_API_KEY": os.getenv("EU_TED_API_KEY", ""),
        "SWISS_TENDER_API_KEY": os.getenv("SWISS_TENDER_API_KEY", ""),
        
        # Application Insights
        "APPLICATIONINSIGHTS_CONNECTION_STRING": os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING", ""),
        
        # Application Configuration
        "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
        "RAW_TENDERS_DIR": os.getenv("RAW_TENDERS_DIR", "./data/raw_tenders")
    }
    
    return config

# Prompt templates
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