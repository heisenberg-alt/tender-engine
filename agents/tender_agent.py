import os
import json
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple

from utils.tender_crawler import TenderAPIWrapper, EUTenderCrawler
from vectorstore.cosmos_vector_store import CosmosDBVectorStore
from llm.azure_recommender_llm import AzureRecommenderLLM

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TenderAgent:
    """Agent for scraping, processing, and indexing tenders"""
    
    def __init__(self, vector_store: CosmosDBVectorStore, llm_service: AzureRecommenderLLM, config: Dict[str, Any]):
        """
        Initialize the tender agent
        
        Args:
            vector_store: Vector store for tender embeddings
            llm_service: Azure OpenAI LLM service
            config: Configuration dictionary
        """
        self.vector_store = vector_store
        self.llm_service = llm_service
        self.config = config
        
        # Initialize tender crawler with EU TED API
        eu_api_key = config.get("EU_TED_API_KEY", "")
        self.tender_crawler = TenderAPIWrapper(eu_api_key=eu_api_key)
        
        # Data directories
        self.raw_tenders_dir = config.get("RAW_TENDERS_DIR", "data/raw_tenders")
        
        # Create raw tenders directory if it doesn't exist
        os.makedirs(self.raw_tenders_dir, exist_ok=True)
    
    def search_and_index_tenders(self, 
                                query: str, 
                                max_results: int = 10, 
                                country_codes: List[str] = None,
                                cpv_codes: List[str] = None,
                                days_back: int = 30) -> List[Dict[str, Any]]:
        """
        Search for EU tenders and index them in the vector store
        
        Args:
            query: Search query for tenders
            max_results: Maximum number of tenders to retrieve
            country_codes: List of EU country codes (e.g., ['DE', 'FR', 'IT'])
            cpv_codes: List of CPV (Common Procurement Vocabulary) codes
            days_back: Number of days to look back for tenders
            
        Returns:
            List of indexed tenders with similarity scores
        """
        # Search for tenders using EU TED API
        logger.info(f"Searching EU TED for tenders with query: '{query}'")
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        search_results = self.tender_crawler.search_tenders(
            query=query,
            max_results=max_results,
            sources=["eu_ted"],
            country_codes=country_codes,
            cpv_codes=cpv_codes,
            publication_date_from=start_date.strftime("%Y-%m-%d"),
            publication_date_to=end_date.strftime("%Y-%m-%d")
        )
        
        if not search_results:
            logger.warning("No tenders found in EU TED search")
            return []
        
        logger.info(f"Found {len(search_results)} tender search results from EU TED")
        
        # Process and index tenders
        indexed_tenders = []
        for tender_data in search_results:
            try:
                # Enhance tender data with AI analysis if needed
                enhanced_tender = self._enhance_tender_data(tender_data)
                
                # Generate a unique ID for the tender if not present
                tender_id = enhanced_tender.get("id") or f"tender_{uuid.uuid4().hex}"
                enhanced_tender["id"] = tender_id
                
                # Save raw tender data
                raw_path = os.path.join(self.raw_tenders_dir, f"{tender_id}.json")
                with open(raw_path, 'w') as f:
                    json.dump(enhanced_tender, f, indent=2)
                
                # Index tender in vector store
                logger.info(f"Indexing tender: {enhanced_tender.get('title', 'Untitled')}")
                success = self.vector_store.add_tender(tender_data=enhanced_tender)
                
                if success:
                    # Add similarity score for display
                    enhanced_tender["similarity_score"] = 1.0  # Perfect match for newly indexed tenders
                    indexed_tenders.append(enhanced_tender)
                    
            except Exception as e:
                logger.error(f"Error processing tender: {str(e)}")
                continue
        
        logger.info(f"Successfully indexed {len(indexed_tenders)} tenders")
        return indexed_tenders
    
    def _enhance_tender_data(self, tender_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance tender data with additional AI analysis
        
        Args:
            tender_data: Raw tender data from crawler
            
        Returns:
            Enhanced tender data with AI insights
        """
        enhanced = tender_data.copy()
        
        # Add timestamp
        enhanced["indexed_at"] = datetime.now().isoformat()
        
        # Extract and categorize key information
        description = tender_data.get("description", "")
        title = tender_data.get("title", "")
        
        # Add derived fields
        enhanced["keywords"] = self._extract_keywords(f"{title} {description}")
        enhanced["sector"] = self._determine_sector(tender_data)
        enhanced["complexity_score"] = self._calculate_complexity(tender_data)
        
        return enhanced
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from tender text"""
        # Simple keyword extraction - can be enhanced with NLP
        common_words = {"the", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
        words = text.lower().split()
        keywords = [word.strip(".,!?;:()[]{}\"'") for word in words 
                   if len(word) > 3 and word not in common_words]
        return list(set(keywords))[:20]  # Return top 20 unique keywords
    
    def _determine_sector(self, tender_data: Dict[str, Any]) -> str:
        """Determine the sector based on CPV codes and description"""
        cpv_codes = tender_data.get("cpv_codes", [])
        description = tender_data.get("description", "").lower()
        
        # Map CPV codes to sectors
        if any(code.startswith("45") for code in cpv_codes):
            return "Construction"
        elif any(code.startswith("48") for code in cpv_codes):
            return "IT/Software"
        elif any(code.startswith("33") for code in cpv_codes):
            return "Healthcare"
        elif any(code.startswith("31") for code in cpv_codes):
            return "Energy"
        elif "energy" in description or "renewable" in description:
            return "Energy"
        elif "construction" in description or "building" in description:
            return "Construction"
        elif "software" in description or "digital" in description:
            return "IT/Software"
        else:
            return "General"
    
    def _calculate_complexity(self, tender_data: Dict[str, Any]) -> float:
        """Calculate complexity score based on various factors"""
        score = 0.0
        
        # Based on estimated value
        value = tender_data.get("estimated_value", 0)
        if value > 10000000:  # >10M
            score += 0.4
        elif value > 1000000:  # >1M
            score += 0.2
        
        # Based on description length
        desc_length = len(tender_data.get("description", ""))
        if desc_length > 1000:
            score += 0.3
        elif desc_length > 500:
            score += 0.2
        
        # Based on number of CPV codes
        cpv_count = len(tender_data.get("cpv_codes", []))
        if cpv_count > 3:
            score += 0.3
        elif cpv_count > 1:
            score += 0.1
        
        return min(score, 1.0)  # Cap at 1.0
    
    def get_tender_recommendations(self, 
                                 company_profile: Dict[str, Any], 
                                 min_score: float = 0.6,
                                 max_results: int = 10,
                                 filter_expired: bool = True) -> List[Dict[str, Any]]:
        """
        Get tender recommendations for a company
        
        Args:
            company_profile: Company profile data
            min_score: Minimum similarity score
            max_results: Maximum number of recommendations
            filter_expired: Whether to filter out expired tenders
            
        Returns:
            List of recommended tenders with similarity scores
        """
        try:
            # Prepare text for embedding using Azure OpenAI
            company_text = f"{company_profile.get('name', '')} {company_profile.get('description', '')} " \
                          f"{' '.join(company_profile.get('expertise', []))}"
            
            # Get embeddings using Azure OpenAI
            embeddings = self.llm_service.get_embeddings(company_text)
            
            # Search for similar tenders in Cosmos DB
            similar_tenders = self.vector_store.search_similar_tenders(
                embeddings, min_score, max_results, filter_expired
            )
            
            return similar_tenders
            
        except Exception as e:
            logger.error(f"Error getting tender recommendations: {str(e)}")
            return []

