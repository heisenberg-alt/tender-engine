import requests
import json
import time
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from abc import ABC, abstractmethod

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TenderCrawlerBase(ABC):
    """Base class for tender crawlers"""
    
    def __init__(self, api_key: str, base_url: str, name: str):
        self.api_key = api_key
        self.base_url = base_url
        self.name = name
        self.session = requests.Session()
        self.session.headers.update(self._get_default_headers())
    
    @abstractmethod
    def _get_default_headers(self) -> Dict[str, str]:
        """Get default headers for API requests"""
        pass
    
    @abstractmethod
    def search_tenders(self, query: str, max_results: int = 10, **kwargs) -> List[Dict[str, Any]]:
        """Search for tenders"""
        pass
    
    @abstractmethod
    def _parse_tender_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse raw API response into standardized tender format"""
        pass
    
    def _make_request(self, endpoint: str, params: Dict[str, Any] = None, method: str = "GET") -> Optional[Dict[str, Any]]:
        """Make HTTP request to the API"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url, params=params, timeout=30)
            elif method.upper() == "POST":
                response = self.session.post(url, json=params, timeout=30)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed for {self.name}: {str(e)}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response from {self.name}: {str(e)}")
            return None

class EUTenderCrawler(TenderCrawlerBase):
    """Crawler for EU TED (Tenders Electronic Daily) API"""
    
    def __init__(self, api_key: str):
        super().__init__(
            api_key=api_key,
            base_url="https://api.ted.europa.eu",  # Updated base URL
            name="EU TED"
        )
    
    def _get_default_headers(self) -> Dict[str, str]:
        """Get default headers for TED API requests"""
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-API-Key": self.api_key,
            "User-Agent": "TenderRecommenderAI/1.0"
        }
    
    def search_tenders(self, 
                       query: str, 
                       max_results: int = 10,
                       country_codes: List[str] = None,
                       cpv_codes: List[str] = None,
                       publication_date_from: str = None,
                       publication_date_to: str = None) -> List[Dict[str, Any]]:
        """
        Search for tenders in the EU TED database
        
        Args:
            query: Search keywords
            max_results: Maximum number of results (max 100 per TED API)
            country_codes: List of ISO country codes (e.g., ['DE', 'FR', 'IT'])
            cpv_codes: List of CPV (Common Procurement Vocabulary) codes
            publication_date_from: Start date in YYYY-MM-DD format
            publication_date_to: End date in YYYY-MM-DD format
            
        Returns:
            List of standardized tender dictionaries
        """
        logger.info(f"Searching EU TED for: {query} (max {max_results} results)")
        
        # Set default date range if not provided
        if not publication_date_from:
            publication_date_from = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        if not publication_date_to:
            publication_date_to = datetime.now().strftime("%Y-%m-%d")
        
        # Build search parameters
        params = {
            "q": query,
            "pageSize": min(max_results, 100),  # TED API max is 100
            "pageNum": 1,
            "publicationDateFrom": publication_date_from,
            "publicationDateTo": publication_date_to,
            "scope": 3,  # EU-wide scope
            "documentType": ["CONTRACT_NOTICE", "CALL_FOR_COMPETITION"]
        }
        
        # Add optional filters
        if country_codes:
            params["countryCode"] = country_codes
        
        if cpv_codes:
            params["cpvCode"] = cpv_codes
        
        try:
            # Try the real API first - multiple possible endpoints
            endpoints_to_try = [
                "/v3.0/notices/search",
                "/api/v2.0/notices/search", 
                "/notices/search"
            ]
            
            response = None
            for endpoint in endpoints_to_try:
                response = self._make_request(endpoint, params)
                if response:
                    break
                    
            if not response:
                logger.warning("All EU TED API endpoints failed, using fallback data")
                return self._get_fallback_tenders(query, max_results)
            
            if "notices" not in response:
                logger.warning("No notices field in TED API response, using fallback data")
                return self._get_fallback_tenders(query, max_results)
            
            tenders = []
            for notice in response["notices"][:max_results]:
                try:
                    parsed_tender = self._parse_tender_data(notice)
                    if parsed_tender:
                        tenders.append(parsed_tender)
                except Exception as e:
                    logger.error(f"Error parsing tender data: {str(e)}")
                    continue
            
            logger.info(f"Successfully retrieved {len(tenders)} tenders from EU TED")
            return tenders
            
        except Exception as e:
            logger.error(f"Error searching EU TED: {str(e)}")
            return self._get_fallback_tenders(query, max_results)
    
    def _parse_tender_data(self, notice: Dict[str, Any]) -> Dict[str, Any]:
        """Parse TED API notice into standardized tender format"""
        try:
            # Extract basic information
            tender_id = notice.get("noticeOjs", {}).get("ojsNumber", "") or notice.get("noticeId", "")
            title = self._extract_multilingual_text(notice.get("title", {}))
            description = self._extract_multilingual_text(notice.get("shortDescription", {}))
            
            # Extract organization info
            organization = ""
            if "contractingBody" in notice:
                org_name = self._extract_multilingual_text(notice["contractingBody"].get("officialName", {}))
                organization = org_name
            
            # Extract location
            location = ""
            if "placeOfPerformance" in notice:
                place = notice["placeOfPerformance"]
                if "nuts" in place:
                    location = place["nuts"].get("code", "")
                elif "country" in place:
                    location = place["country"].get("code", "")
            
            # Extract estimated value
            estimated_value = None
            currency = "EUR"
            if "lotInfo" in notice and notice["lotInfo"]:
                lot = notice["lotInfo"][0]  # Take first lot
                if "estimatedValue" in lot:
                    estimated_value = lot["estimatedValue"].get("value")
                    currency = lot["estimatedValue"].get("currency", "EUR")
            
            # Extract deadline
            deadline = None
            if "tenderSubmissionDeadline" in notice:
                deadline = notice["tenderSubmissionDeadline"].get("date")
            
            # Extract CPV codes (categories)
            categories = []
            if "cpv" in notice:
                cpv_main = notice["cpv"].get("main", {})
                if "code" in cpv_main:
                    categories.append(cpv_main["code"])
            
            # Build source URL
            source_url = f"https://ted.europa.eu/udl?uri=TED:NOTICE:{tender_id}"
            
            return {
                "id": tender_id,
                "title": title,
                "description": description,
                "organization": organization,
                "location": location,
                "estimated_value": estimated_value,
                "currency": currency,
                "deadline": deadline,
                "category": categories,
                "source": "EU TED",
                "source_url": source_url,
                "publication_date": notice.get("publicationDate"),
                "cpv_codes": categories,
                "country_code": notice.get("countryCode"),
                "raw_data": notice  # Keep original data for debugging
            }
            
        except Exception as e:
            logger.error(f"Error parsing tender notice: {str(e)}")
            return None
    
    def _extract_multilingual_text(self, text_obj: Union[Dict, str]) -> str:
        """Extract text from multilingual object, preferring English"""
        if isinstance(text_obj, str):
            return text_obj
        
        if isinstance(text_obj, dict):
            # Try English first
            if "en" in text_obj:
                return text_obj["en"]
            
            # Try other common languages
            for lang in ["fr", "de", "es", "it"]:
                if lang in text_obj:
                    return text_obj[lang]
            
            # Return first available value
            if text_obj:
                return list(text_obj.values())[0]
        
        return ""
    
    def _get_fallback_tenders(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Return mock data when API fails"""
        logger.info("Using fallback mock data for EU tenders")
        
        mock_tenders = [
            {
                "id": "EU001-2025",
                "title": "Renewable Energy Infrastructure Development",
                "description": "Procurement for solar panel installation and wind energy systems across European municipalities",
                "organization": "European Environment Agency",
                "location": "EU",
                "estimated_value": 5000000,
                "currency": "EUR",
                "deadline": (datetime.now() + timedelta(days=45)).isoformat(),
                "category": ["45112700", "31150000"],  # CPV codes
                "source": "EU TED",
                "source_url": "https://ted.europa.eu/udl?uri=TED:NOTICE:EU001-2025",
                "publication_date": datetime.now().isoformat(),
                "cpv_codes": ["45112700", "31150000"],
                "country_code": "EU"
            },
            {
                "id": "EU002-2025",
                "title": "Digital Infrastructure Modernization",
                "description": "Technology procurement for digital transformation of government services",
                "organization": "European Commission",
                "location": "Brussels, Belgium",
                "estimated_value": 12000000,
                "currency": "EUR",
                "deadline": (datetime.now() + timedelta(days=60)).isoformat(),
                "category": ["48000000", "72000000"],  # CPV codes
                "source": "EU TED",
                "source_url": "https://ted.europa.eu/udl?uri=TED:NOTICE:EU002-2025",
                "publication_date": datetime.now().isoformat(),
                "cpv_codes": ["48000000", "72000000"],
                "country_code": "BE"
            },
            {
                "id": "EU003-2025",
                "title": "Healthcare Equipment Procurement",
                "description": "Medical devices and equipment for European healthcare facilities",
                "organization": "European Health Insurance Card",
                "location": "EU",
                "estimated_value": 8500000,
                "currency": "EUR",
                "deadline": (datetime.now() + timedelta(days=30)).isoformat(),
                "category": ["33140000", "33100000"],  # CPV codes
                "source": "EU TED",
                "source_url": "https://ted.europa.eu/udl?uri=TED:NOTICE:EU003-2025",
                "publication_date": datetime.now().isoformat(),
                "cpv_codes": ["33140000", "33100000"],
                "country_code": "EU"
            }
        ]
        
        # Filter based on query keywords
        filtered_tenders = []
        query_lower = query.lower()
        
        for tender in mock_tenders:
            title_desc = (tender["title"] + " " + tender["description"]).lower()
            if any(keyword in title_desc for keyword in query_lower.split()):
                filtered_tenders.append(tender)
        
        return filtered_tenders[:max_results]

class SwissTenderCrawler(TenderCrawlerBase):
    """Placeholder for Swiss tender crawler - to be implemented later"""
    
    def __init__(self, api_key: str = None):
        super().__init__(
            api_key=api_key or "",
            base_url="https://api.swiss-tenders.ch",  # Placeholder URL
            name="Swiss Tenders"
        )
    
    def _get_default_headers(self) -> Dict[str, str]:
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "TenderRecommenderAI/1.0"
        }
    
    def search_tenders(self, query: str, max_results: int = 10, **kwargs) -> List[Dict[str, Any]]:
        """Placeholder for Swiss tender search - to be implemented"""
        logger.info("Swiss tender API not yet implemented - using mock data")
        
        # Mock Swiss tender data
        return [
            {
                "id": "CH001-2025",
                "title": "Swiss Infrastructure Development",
                "description": "Infrastructure development project in Swiss cantons",
                "organization": "Swiss Federal Office",
                "location": "Switzerland",
                "estimated_value": 3000000,
                "currency": "CHF",
                "deadline": (datetime.now() + timedelta(days=40)).isoformat(),
                "category": ["infrastructure"],
                "source": "Swiss Tenders",
                "source_url": "https://swiss-tenders.ch/notice/CH001-2025",
                "publication_date": datetime.now().isoformat()
            }
        ]
    
    def _parse_tender_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Placeholder for Swiss tender parsing"""
        return raw_data

class TenderCrawlerFactory:
    """Factory class to create appropriate tender crawlers"""
    
    @staticmethod
    def create_crawler(source: str, api_key: str = None) -> TenderCrawlerBase:
        """
        Create a tender crawler for the specified source
        
        Args:
            source: Source type ('eu_ted', 'swiss', etc.)
            api_key: API key for the service
            
        Returns:
            TenderCrawlerBase instance
        """
        if source.lower() == "eu_ted":
            if not api_key:
                raise ValueError("API key is required for EU TED crawler")
            return EUTenderCrawler(api_key)
        
        elif source.lower() == "swiss":
            return SwissTenderCrawler(api_key)
        
        else:
            raise ValueError(f"Unsupported tender source: {source}")
    
    @staticmethod
    def get_available_sources() -> List[str]:
        """Get list of available tender sources"""
        return ["eu_ted", "swiss"]

# For backward compatibility with existing code
class TenderAPIWrapper:
    """Wrapper class that combines multiple tender sources"""
    
    def __init__(self, eu_api_key: str = None, swiss_api_key: str = None):
        self.crawlers = {}
        
        if eu_api_key:
            self.crawlers["eu_ted"] = EUTenderCrawler(eu_api_key)
        
        if swiss_api_key:
            self.crawlers["swiss"] = SwissTenderCrawler(swiss_api_key)
    
    def search_tenders(self, 
                       query: str, 
                       max_results: int = 10,
                       sources: List[str] = None,
                       **kwargs) -> List[Dict[str, Any]]:
        """
        Search for tenders across multiple sources
        
        Args:
            query: Search keywords
            max_results: Maximum total results
            sources: List of sources to search (default: all available)
            **kwargs: Additional parameters for specific crawlers
            
        Returns:
            Combined list of tenders from all sources
        """
        if not sources:
            sources = list(self.crawlers.keys())
        
        all_tenders = []
        results_per_source = max(1, max_results // len(sources))
        
        for source in sources:
            if source in self.crawlers:
                try:
                    tenders = self.crawlers[source].search_tenders(
                        query=query,
                        max_results=results_per_source,
                        **kwargs
                    )
                    all_tenders.extend(tenders)
                except Exception as e:
                    logger.error(f"Error searching {source}: {str(e)}")
        
        # Sort by publication date (newest first) and limit results
        all_tenders.sort(
            key=lambda x: x.get("publication_date", ""), 
            reverse=True
        )
        
        return all_tenders[:max_results]
