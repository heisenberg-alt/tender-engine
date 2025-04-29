import os
import json
import uuid
import logging
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

from utils.firecrawl_wrapper import FirecrawlWrapper
from utils.config import TENDER_EXTRACTION_PROMPT
from vectorstore.chromadb_store import ChromaDBStore

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TenderAgent:
    """Agent for scraping, processing, and indexing tenders"""
    
    def __init__(self, vector_store: ChromaDBStore, config: Dict[str, Any]):
        """
        Initialize the tender agent
        
        Args:
            vector_store: Vector store for tender embeddings
            config: Configuration dictionary
        """
        self.vector_store = vector_store
        self.config = config
        self.firecrawl = FirecrawlWrapper(config["FIRECRAWL_API_KEY"])
        self.ollama_host = config["OLLAMA_HOST"]
        self.ollama_model = config["OLLAMA_MODEL"]
        self.embedding_model = config["OLLAMA_EMBEDDING_MODEL"]
        self.raw_tenders_dir = config["RAW_TENDERS_DIR"]
        
        # Create raw tenders directory if it doesn't exist
        os.makedirs(self.raw_tenders_dir, exist_ok=True)
    
    def search_and_index_tenders(self, 
                                query: str, 
                                max_results: int = 10, 
                                source_type: str = "Government Tenders", 
                                days_back: int = 30) -> List[Dict[str, Any]]:
        """
        Search for government tenders and index them in the vector store
        
        Args:
            query: Search query for tenders
            max_results: Maximum number of tenders to retrieve
            source_type: Type of source to search (e.g., Government Tenders)
            days_back: Number of days to look back for tenders
            
        Returns:
            List of indexed tenders with similarity scores
        """
        # Search for tenders
        logger.info(f"Searching for tenders with query: '{query}'")
        search_results = self.firecrawl.search_tenders(query, max_results, source_type, days_back)
        
        if not search_results:
            logger.warning("No tenders found in search")
            return []
        
        logger.info(f"Found {len(search_results)} tender search results")
        
        # Process and index tenders
        indexed_tenders = []
        for result in search_results:
            url = result.get("url")
            if not url:
                continue
                
            # Extract tender details
            tender_data = self._extract_tender_details(result)
            if not tender_data:
                continue
                
            # Generate a unique ID for the tender
            tender_id = f"tender_{uuid.uuid4().hex}"
            
            # Save raw tender data
            raw_path = os.path.join(self.raw_tenders_dir, f"{tender_id}.json")
            with open(raw_path, 'w') as f:
                json.dump(tender_data, f, indent=2)
            
            # Index tender in vector store
            logger.info(f"Indexing tender: {tender_data.get('title', 'Untitled')}")
            success = self.vector_store.add_tender(
                tender_id=tender_id,
                tender_data=tender_data,
                ollama_host=self.ollama_host,
                embedding_model=self.embedding_model
            )
            
            if success:
                # Add similarity score for display
                tender_data["id"] = tender_id
                tender_data["similarity_score"] = 1.0  # Perfect match for newly indexed tenders
                indexed_tenders.append(tender_data)
        
        logger.info(f"Successfully indexed {len(indexed_tenders)} tenders")
        return indexed_tenders
    
    def _extract_tender_details(self, search_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract detailed tender information from search result
        
        Args:
            search_result: Search result from Firecrawl
            
        Returns:
            Extracted tender details or None if extraction failed
        """
        url = search_result.get("url")
        if not url:
            return None
        
        # Scrape full content from URL
        scraped_content = self.firecrawl.scrape_tender_details(url)
        if not scraped_content:
            # Use search snippet if we can't scrape details
            return self._create_basic_tender(search_result)
        
        # Get the full text content
        full_text = scraped_content.get("text", "")
        if not full_text:
            return self._create_basic_tender(search_result)
        
        # Use LLM to extract tender information
        extracted_data = self._extract_with_llm(full_text)
        if not extracted_data:
            return self._create_basic_tender(search_result)
        
        # Combine extracted data with search result data
        tender_details = {
            "title": extracted_data.get("title") or search_result.get("title", "Untitled Tender"),
            "description": extracted_data.get("description") or search_result.get("snippet", ""),
            "source": search_result.get("domain", "Unknown Source"),
            "source_url": url,
            "deadline": extracted_data.get("deadline", ""),
            "publication_date": search_result.get("date", ""),
            "value": extracted_data.get("value", ""),
            "category": extracted_data.get("category", ""),
            "eligibility": extracted_data.get("eligibility", ""),
            "contact_details": extracted_data.get("contact_details", ""),
            "raw_text": full_text[:5000]  # Store the first 5000 chars of raw text
        }
        
        # Download linked documents if available
        documents = []
        for link in scraped_content.get("links", []):
            link_url = link.get("url")
            link_text = link.get("text", "").lower()
            
            # Check if it's likely a tender document
            if link_url and any(doc_type in link_text for doc_type in ["pdf", "doc", "tender", "application"]):
                doc_id = f"doc_{uuid.uuid4().hex}"
                doc_path = os.path.join(self.raw_tenders_dir, f"{doc_id}.pdf")
                
                if self.firecrawl.download_tender_documents(link_url, doc_path):
                    documents.append({
                        "id": doc_id,
                        "name": link_text,
                        "url": link_url,
                        "local_path": doc_path
                    })
        
        if documents:
            tender_details["documents"] = documents
            
        return tender_details
    
    def _create_basic_tender(self, search_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create basic tender data from search result when detailed extraction fails
        
        Args:
            search_result: Search result from Firecrawl
            
        Returns:
            Basic tender data
        """
        return {
            "title": search_result.get("title", "Untitled Tender"),
            "description": search_result.get("snippet", ""),
            "source": search_result.get("domain", "Unknown Source"),
            "source_url": search_result.get("url", ""),
            "publication_date": search_result.get("date", ""),
            "deadline": "",  # Unknown from search results
            "value": "",     # Unknown from search results
            "category": ""   # Unknown from search results
        }
    
    def _extract_with_llm(self, text: str) -> Dict[str, Any]:
        """
        Extract structured tender information using Ollama LLM
        
        Args:
            text: Raw text to extract information from
            
        Returns:
            Extracted tender data
        """
        try:
            # Prepare prompt with text
            prompt = TENDER_EXTRACTION_PROMPT.format(tender_text=text[:10000])  # Limit text size
            
            # Call Ollama API
            response = requests.post(
                f"{self.ollama_host}/api/generate",
                json={
                    "model": self.ollama_model,
                    "prompt": prompt,
                    "stream": False
                }
            )
            response.raise_for_status()
            
            # Parse response
            llm_response = response.json().get("response", "")
            
            # Extract fields from response
            data = {}
            for line in llm_response.splitlines():
                line = line.strip()
                if not line or line.startswith("-"):
                    continue
                    
                parts = line.split(":", 1)
                if len(parts) == 2:
                    key = parts[0].strip().lower().replace(" ", "_")
                    value = parts[1].strip()
                    data[key] = value
            
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling Ollama API: {str(e)}")
            return {}
        except Exception as e:
            logger.error(f"Error extracting tender data with LLM: {str(e)}")
            return {}
    
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
        # Prepare text for embedding
        text_to_embed = f"{company_profile.get('name', '')} {company_profile.get('description', '')} " \
                       f"{' '.join(company_profile.get('expertise', []))}"
        
        # Get embeddings
        embeddings = self.vector_store.get_embeddings(text_to_embed, self.embedding_model)
        
        # Find the most similar tenders
        recommendations = self.vector_store.search_similar_tenders(
            embeddings, min_score, max_results, filter_expired)
        
        return recommendations

