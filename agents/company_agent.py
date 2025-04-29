import os
import json
import uuid
import logging
import requests
from typing import Dict, List, Any, Optional
import PyPDF2
import docx
from datetime import datetime
from utils.config import COMPANY_PROFILE_EXTRACTION_PROMPT
from vectorstore.chromadb_store import ChromaDBStore

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CompanyAgent:
    """Agent for processing and storing company profiles"""
    
    def __init__(self, 
                company_data: Optional[Dict[str, Any]] = None,
                vector_store: Optional[ChromaDBStore] = None,
                ollama_host: str = "http://localhost:11434",
                ollama_model: str = "llama3",
                ollama_embedding_model: str = "nomic-embed-text"):
        """
        Initialize the company agent
        
        Args:
            company_data: Optional company data
            vector_store: Optional vector store for company profiles
            ollama_host: Ollama API host
            ollama_model: Ollama model name
            ollama_embedding_model: Ollama embedding model name
        """
        self.company_data = company_data
        self.vector_store = vector_store
        self.ollama_host = ollama_host
        self.ollama_model = ollama_model
        self.ollama_embedding_model = ollama_embedding_model
    
    def extract_company_profile(self, file_path: str) -> Dict[str, Any]:
        """
        Extract company profile from a document file
        
        Args:
            file_path: Path to the document file (PDF, DOCX)
            
        Returns:
            Extracted company profile
        """
        # Extract text from the file
        file_text = self._extract_text_from_file(file_path)
        
        if not file_text:
            logger.error(f"Failed to extract text from file: {file_path}")
            return {}
        
        # Use LLM to extract structured company profile
        company_profile = self._extract_profile_with_llm(file_text)
        
        # Add a unique ID if not present
        if "id" not in company_profile:
            company_profile["id"] = str(uuid.uuid4())
        
        # Store the company data
        self.company_data = company_profile
        
        # Store in vector database if provided
        if self.vector_store:
            company_text = f"{company_profile.get('name', '')} {company_profile.get('description', '')}"
            embedding = self._get_embedding(company_text)
            
            self.vector_store.add_company(company_profile["id"], company_profile, embedding)
        
        return company_profile
    
    def create_company_profile(self, 
                              name: str,
                              description: str,
                              industry: List[str],
                              services: List[str],
                              location: str,
                              size: str,
                              expertise: List[str],
                              **kwargs) -> Dict[str, Any]:
        """
        Create a company profile from structured data
        
        Args:
            name: Company name
            description: Company description
            industry: List of industries
            services: List of services offered
            location: Company location
            size: Company size (e.g., "Small", "Medium", "Large")
            expertise: List of expertise areas
            **kwargs: Additional company profile fields
            
        Returns:
            Created company profile
        """
        # Create company profile dictionary
        company_profile = {
            "id": str(uuid.uuid4()),
            "name": name,
            "description": description,
            "industry": industry,
            "services": services,
            "location": location,
            "size": size,
            "expertise": expertise,
            "created_at": datetime.now().isoformat(),
            **kwargs
        }
        
        # Store the company data
        self.company_data = company_profile
        
        # Store in vector database if provided
        if self.vector_store:
            company_text = f"{name} {description}"
            embedding = self._get_embedding(company_text)
            
            self.vector_store.add_company(company_profile["id"], company_profile, embedding)
        
        logger.info(f"Created company profile for: {name}")
        return company_profile
    
    def update_company_profile(self, company_id: str, updated_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing company profile
        
        Args:
            company_id: ID of the company to update
            updated_data: Updated company data
            
        Returns:
            Updated company profile
        """
        if not self.vector_store:
            logger.error("Vector store is required for updating company profiles")
            return {}
        
        # Get existing company profile
        existing_profile = self.vector_store.get_company(company_id)
        
        if not existing_profile:
            logger.error(f"Company profile not found: {company_id}")
            return {}
        
        # Update the profile
        updated_profile = {**existing_profile, **updated_data, "updated_at": datetime.now().isoformat()}
        
        # Update in vector database
        company_text = f"{updated_profile.get('name', '')} {updated_profile.get('description', '')}"
        embedding = self._get_embedding(company_text)
        
        self.vector_store.update_company(company_id, updated_profile, embedding)
        
        # Update local copy
        self.company_data = updated_profile
        
        logger.info(f"Updated company profile: {company_id}")
        return updated_profile
    
    def get_company_profile(self, company_id: str) -> Dict[str, Any]:
        """
        Get a company profile by ID
        
        Args:
            company_id: ID of the company
            
        Returns:
            Company profile
        """
        if not self.vector_store:
            logger.error("Vector store is required for retrieving company profiles")
            return {}
        
        company_profile = self.vector_store.get_company(company_id)
        
        if not company_profile:
            logger.error(f"Company profile not found: {company_id}")
            return {}
        
        return company_profile
    
    def search_companies(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search for companies by query
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching company profiles
        """
        if not self.vector_store:
            logger.error("Vector store is required for searching companies")
            return []
        
        # Get embedding for query
        query_embedding = self._get_embedding(query)
        
        # Search in vector database
        results = self.vector_store.search_companies(query_embedding, limit)
        
        return results
    
    def _extract_text_from_file(self, file_path: str) -> str:
        """
        Extract text from a document file
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Extracted text
        """
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return ""
        
        file_extension = os.path.splitext(file_path)[1].lower()
        
        try:
            if file_extension == ".pdf":
                return self._extract_text_from_pdf(file_path)
            elif file_extension in [".docx", ".doc"]:
                return self._extract_text_from_docx(file_path)
            else:
                logger.error(f"Unsupported file format: {file_extension}")
                return ""
        except Exception as e:
            logger.error(f"Error extracting text from file {file_path}: {str(e)}")
            return ""
    
    def _extract_text_from_pdf(self, file_path: str) -> str:
        """
        Extract text from a PDF file
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Extracted text
        """
        text = ""
        
        with open(file_path, "rb") as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text() + "\n"
        
        return text
    
    def _extract_text_from_docx(self, file_path: str) -> str:
        """
        Extract text from a DOCX file
        
        Args:
            file_path: Path to the DOCX file
            
        Returns:
            Extracted text
        """
        doc = docx.Document(file_path)
        text = ""
        
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        
        return text
    
    def _extract_profile_with_llm(self, text: str) -> Dict[str, Any]:
        """
        Extract structured company profile from text using LLM
        
        Args:
            text: Text to extract profile from
            
        Returns:
            Structured company profile
        """
        try:
            # Prepare the prompt with the text
            prompt = COMPANY_PROFILE_EXTRACTION_PROMPT.replace("{{TEXT}}", text)
            
            # Call Ollama API
            response = requests.post(
                f"{self.ollama_host}/api/generate",
                json={
                    "model": self.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1
                    }
                }
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Parse the JSON response from the LLM
            try:
                # Try to find JSON in the response
                response_text = result.get("response", "")
                
                # Find JSON block in the response
                start_idx = response_text.find("{")
                end_idx = response_text.rfind("}")
                
                if start_idx != -1 and end_idx != -1:
                    json_str = response_text[start_idx:end_idx+1]
                    profile = json.loads(json_str)
                    return profile
                else:
                    logger.error("No valid JSON found in LLM response")
                    return {}
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from LLM response: {str(e)}")
                return {}
        except requests.exceptions.RequestException as e:
            logger.error(f"Error contacting Ollama API: {str(e)}")
            return {}

    def _get_embedding(self, text: str) -> List[float]:
        """
        Generate text embeddings using Ollama
        
        Args:
            text: Text to generate embeddings for
            
        Returns:
            Embedding list
        """
        try:
            response = requests.post(
                f"{self.ollama_host}/api/embedding",
                json={
                    "model": self.ollama_embedding_model,
                    "text": text
                }
            )
            response.raise_for_status()
            result = response.json()
            return result.get("embedding", [])
        except requests.exceptions.RequestException as e:
            logger.error(f"Error generating embedding: {str(e)}")
            return []