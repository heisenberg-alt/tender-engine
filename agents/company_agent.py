import logging
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

from vectorstore.cosmos_vector_store import CosmosDBVectorStore

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CompanyAgent:
    """Agent for managing company profiles in Azure Cosmos DB"""
    
    def __init__(self, vector_store: CosmosDBVectorStore):
        """
        Initialize the company agent
        
        Args:
            vector_store: Cosmos DB vector store for company data
        """
        self.vector_store = vector_store
    
    def add_company_profile(self, 
                          name: str, 
                          description: str, 
                          expertise: List[str], 
                          **kwargs) -> Dict[str, Any]:
        """
        Add a new company profile to the vector store
        
        Args:
            name: Company name
            description: Company description
            expertise: List of expertise areas
            **kwargs: Additional company metadata
            
        Returns:
            Created company profile data
        """
        try:
            company_profile = {
                "name": name,
                "description": description,
                "expertise": expertise,
                "created_at": datetime.now().isoformat(),
                **kwargs
            }
            
            # Add to vector store
            success = self.vector_store.add_company(company_profile)
            
            if success:
                logger.info(f"Successfully added company profile: {name}")
                return company_profile
            else:
                logger.error(f"Failed to add company profile: {name}")
                return None
                
        except Exception as e:
            logger.error(f"Error adding company profile: {str(e)}")
            return None
    
    def search_companies(self, 
                        query: str, 
                        max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Search for companies based on query
        
        Args:
            query: Search query
            max_results: Maximum number of results
            
        Returns:
            List of matching company profiles
        """
        try:
            results = self.vector_store.search_similar_companies(
                query, max_results=max_results
            )
            return results
            
        except Exception as e:
            logger.error(f"Error searching companies: {str(e)}")
            return []
    
    def get_company_profile(self, company_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific company profile by name
        
        Args:
            company_name: Name of the company
            
        Returns:
            Company profile data or None if not found
        """
        try:
            results = self.search_companies(company_name, max_results=1)
            if results and results[0].get("name", "").lower() == company_name.lower():
                return results[0]
            return None
            
        except Exception as e:
            logger.error(f"Error getting company profile: {str(e)}")
            return None
    
    def create_company_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a company profile from structured data
        
        Args:
            profile_data: Dictionary containing company information
            
        Returns:
            Created company profile
        """
        name = profile_data.get("name", "Unknown Company")
        description = profile_data.get("description", "")
        expertise = profile_data.get("expertise", [])
        
        return self.add_company_profile(
            name=name,
            description=description,
            expertise=expertise,
            **{k: v for k, v in profile_data.items() if k not in ["name", "description", "expertise"]}
        )
