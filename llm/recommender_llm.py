import logging
import requests
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from openai import AzureOpenAI

from vectorstore.cosmos_vector_store import CosmosDBVectorStore
from agents.company_agent import CompanyAgent

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RecommenderLLM:
    """LLM-based tender recommendation engine"""
    
    def __init__(self, vector_store: ChromaDBStore, config: Dict[str, Any]):
        """
        Initialize the recommender
        
        Args:
            vector_store: Vector store for company and tender data
            config: Configuration dictionary
        """
        self.vector_store = vector_store
        self.config = config
        self.ollama_host = config["OLLAMA_HOST"]
        self.ollama_model = config["OLLAMA_MODEL"]
        self.embedding_model = config["OLLAMA_EMBEDDING_MODEL"]
    
    def get_recommendations(self, 
                      company_name: str, 
                      min_score: float = 0.6, 
                      max_results: int = 10,
                      sort_by: str = "Match Score",
                      filter_expired: bool = True) -> List[Dict[str, Any]]:
        """
        Get tender recommendations for a company
        
        Args:
            company_name: Name of the company
            min_score: Minimum match score
            max_results: Maximum number of recommendations
            sort_by: Sort criteria ("Match Score", "Deadline", "Value")
            filter_expired: Whether to filter out expired tenders
            
        Returns:
            List of tender recommendations
        """
        # Get company profile
        companies = self.vector_store.query_collection("companies", company_name, top_k=1)
        
        if not companies or len(companies) == 0:
            logger.error(f"Company {company_name} not found in database")
            return []
        
        company_data = companies[0]
        logger.info(f"Found company profile for {company_name}")
        
        # Create company agent to analyze the profile
        company_agent = CompanyAgent(company_data)
        company_profile = company_agent.get_profile_summary()
        
        # Retrieve relevant tenders
        tenders = self.vector_store.query_collection("tenders", company_profile, top_k=50)
        
        if not tenders or len(tenders) == 0:
            logger.info(f"No relevant tenders found for {company_name}")
            return []
        
        # Filter expired tenders if requested
        if filter_expired:
            current_date = datetime.now()
            tenders = [
                tender for tender in tenders 
                if tender.get("deadline") and datetime.fromisoformat(tender["deadline"]) > current_date
            ]
        
        # Prepare recommendations using LLM
        recommendations = self._generate_recommendations(company_profile, tenders)
        
        # Filter by minimum score
        recommendations = [rec for rec in recommendations if rec["match_score"] >= min_score]
        
        # Sort recommendations
        if sort_by == "Match Score":
            recommendations.sort(key=lambda x: x["match_score"], reverse=True)
        elif sort_by == "Deadline":
            recommendations.sort(key=lambda x: datetime.fromisoformat(x["deadline"]))
        elif sort_by == "Value":
            recommendations.sort(key=lambda x: x.get("estimated_value", 0), reverse=True)
        
        # Limit results
        return recommendations[:max_results]

    def _generate_recommendations(self, company_profile: Dict[str, Any], tenders: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate tender recommendations using LLM
        
        Args:
            company_profile: Company profile information
            tenders: List of tender data
            
        Returns:
            List of recommendations with match scores
        """
        recommendations = []
        
        # Process each tender
        for tender in tenders:
            try:
                # Create prompt for the LLM
                prompt = TENDER_RECOMMENDATION_PROMPT.format(
                    company_profile=json.dumps(company_profile, indent=2),
                    tender_details=json.dumps(tender, indent=2)
                )
                
                # Call LLM for matching analysis
                response = self._call_llm(prompt)
                
                # Parse the LLM response to extract match score and reasoning
                analysis = self._parse_llm_response(response)
                
                if analysis:
                    # Add score and reasoning to the tender data
                    recommendation = {
                        **tender,
                        "match_score": analysis["match_score"],
                        "match_reasoning": analysis["reasoning"]
                    }
                    recommendations.append(recommendation)
                
            except Exception as e:
                logger.error(f"Error processing tender {tender.get('id', 'unknown')}: {str(e)}")
        
        return recommendations

    def _call_llm(self, prompt: str) -> str:
        """
        Call the LLM with the given prompt
        
        Args:
            prompt: The prompt to send to the LLM
            
        Returns:
            LLM response text
        """
        try:
            url = f"{self.ollama_host}/api/generate"
            payload = {
                "model": self.ollama_model,
                "prompt": prompt,
                "stream": False
            }
            
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "")
        
        except Exception as e:
            logger.error(f"Error calling LLM: {str(e)}")
            raise

    def _parse_llm_response(self, response: str) -> Optional[Dict[str, Any]]:
        """
        Parse the LLM response to extract match score and reasoning
        
        Args:
            response: The LLM response text
            
        Returns:
            Dictionary with match score and reasoning or None if parsing fails
        """
        try:
            # Look for JSON in the response
            if "{" in response and "}" in response:
                json_start = response.find("{")
                json_end = response.rfind("}") + 1
                json_str = response[json_start:json_end]
                
                data = json.loads(json_str)
                match_score = float(data.get("match_score", 0))
                reasoning = data.get("reasoning", "")
                
                return {
                    "match_score": match_score,
                    "reasoning": reasoning
                }
            else:
                # Try to extract match score using simple parsing
                match_score = 0.0
                for line in response.split("\n"):
                    if "match score:" in line.lower():
                        try:
                            score_text = line.split(":")[-1].strip()
                            match_score = float(score_text)
                            break
                        except ValueError:
                            pass
                
                return {
                    "match_score": match_score,
                    "reasoning": response
                }
        
        except Exception as e:
            logger.error(f"Error parsing LLM response: {str(e)}")
            return None

    def get_embedding(self, text: str) -> List[float]:
        """
        Get embedding vector for text using Ollama
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector as list of floats
        """
        try:
            url = f"{self.ollama_host}/api/embeddings"
            payload = {
                "model": self.embedding_model,
                "prompt": text
            }
            
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            return result.get("embedding", [])
        
        except Exception as e:
            logger.error(f"Error getting embedding: {str(e)}")
            raise