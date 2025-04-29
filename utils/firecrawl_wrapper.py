import requests
import json
import time
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FirecrawlWrapper:
    """Wrapper for the Firecrawl API for web scraping tender information"""
    
    def __init__(self, api_key: str):
        """Initialize the Firecrawl wrapper with API key"""
        self.api_key = api_key
        self.base_url = "https://api.firecrawl.dev"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
    
    def search_tenders(self, 
                       query: str, 
                       max_results: int = 10, 
                       source_type: str = "All", 
                       days_back: int = 30) -> List[Dict[str, Any]]:
        """
        Search for tenders using Firecrawl API
        
        Args:
            query: Search keywords
            max_results: Maximum number of results to return
            source_type: Type of source ("Government Portals", "TenderInfo", "All Sources")
            days_back: Number of days to look back for tenders
            
        Returns:
            List of tender search results
        """
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        # Map source type to Firecrawl filter
        source_filter = None
        if source_type == "Government Portals":
            source_filter = ["government"]
        elif source_type == "TenderInfo":
            source_filter = ["tenderinfo", "tendersinfo"]
            
        # Prepare search payload
        payload = {
            "query": f"tender {query}",
            "max_results": max_results,
            "date_range": {
                "start": start_date.strftime("%Y-%m-%d"),
                "end": end_date.strftime("%Y-%m-%d")
            }
        }
        
        if source_filter:
            payload["filters"] = {"domains": source_filter}
            
        try:
            # Make search request to Firecrawl
            response = requests.post(
                f"{self.base_url}/search",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            
            search_id = response.json().get("search_id")
            if not search_id:
                logger.error("No search ID returned from Firecrawl")
                return []
                
            # Poll for search results
            results = self._poll_search_results(search_id)
            
            # Filter for relevant tender results
            filtered_results = [
                result for result in results
                if any(keyword in (result.get("title", "") + result.get("snippet", "")).lower() 
                       for keyword in ["tender", "bid", "procurement", "rfp", "rfq"])
            ]
            
            return filtered_results[:max_results]
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error searching tenders: {str(e)}")
            return []
    
    def _poll_search_results(self, search_id: str, max_attempts: int = 10, backoff_factor: int = 2) -> List[Dict[str, Any]]:
        """
        Poll for search results using the search ID
        
        Args:
            search_id: Search ID returned from search request
            max_attempts: Maximum number of polling attempts
            backoff_factor: Exponential backoff factor
            
        Returns:
            Search results
        """
        for attempt in range(max_attempts):
            try:
                response = requests.get(
                    f"{self.base_url}/search/{search_id}/results",
                    headers=self.headers
                )
                response.raise_for_status()
                
                data = response.json()
                status = data.get("status")
                
                if status == "completed":
                    return data.get("results", [])
                elif status == "failed":
                    logger.error("Search failed on Firecrawl side")
                    return []
                    
                # Wait before retrying with exponential backoff
                time.sleep(backoff_factor ** attempt)
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Error polling search results: {str(e)}")
                return []
                
        logger.warning(f"Max polling attempts reached for search {search_id}")
        return []
    
    def scrape_tender_details(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Scrape detailed tender information from a URL
        
        Args:
            url: URL of the tender page
            
        Returns:
            Dictionary with tender details or None if scraping failed
        """
        try:
            # Initialize scraping job
            response = requests.post(
                f"{self.base_url}/scrape",
                headers=self.headers,
                json={"url": url, "render_js": True}
            )
            response.raise_for_status()
            
            scrape_id = response.json().get("scrape_id")
            if not scrape_id:
                logger.error("No scrape ID returned from Firecrawl")
                return None
                
            # Poll for scrape results
            content = self._poll_scrape_results(scrape_id)
            if content:
                return {
                    "html": content.get("html"),
                    "text": content.get("text"),
                    "links": content.get("links", []),
                    "metadata": content.get("metadata", {})
                }
            return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error scraping tender details: {str(e)}")
            return None

    def _poll_scrape_results(self, scrape_id: str, max_attempts: int = 10, backoff_factor: int = 2) -> Optional[Dict[str, Any]]:
        """
        Poll for scrape results using scrape ID
        
        Args:
            scrape_id: Scrape ID returned from scrape request
            max_attempts: Maximum number of polling attempts
            
        Returns:
            Scraped content or None if failed
        """
        for attempt in range(max_attempts):
            try:
                poll_response = requests.get(
                    f"{self.base_url}/scrape/{scrape_id}",
                    headers=self.headers
                )
                poll_response.raise_for_status()
                
                data = poll_response.json()
                status = data.get("status")
                
                if status == "completed":
                    return data.get("content", {})
                elif status == "failed":
                    logger.error("Scrape failed on Firecrawl side")
                    return None
                    
                time.sleep(backoff_factor ** attempt)
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Error polling scrape results: {str(e)}")
                return None
                
        logger.warning(f"Max polling attempts reached for scrape {scrape_id}")
        return None

    def download_tender_documents(self, url: str, save_path: str, timeout: int = 30) -> bool:
        """
        Download tender documents from URL
        
        Args:
            url: URL of the document
            save_path: Path to save the downloaded document
            timeout: Timeout for downloading the document (default 30s)
            
        Returns:
            True if download successful, False otherwise
        """
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            
            with open(save_path, 'wb') as f:
                f.write(response.content)
                
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error downloading tender document: {str(e)}")
            return False
        except IOError as e:
            logger.error(f"Error saving tender document: {str(e)}")
            return False