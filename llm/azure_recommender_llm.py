import os
import json
import logging
from typing import Dict, List, Any, Optional
from openai import AzureOpenAI
from vectorstore.cosmos_vector_store import CosmosDBVectorStore

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AzureRecommenderLLM:
    """Azure OpenAI-based LLM for tender recommendations using Cosmos DB vector search"""
    
    def __init__(self, 
                 vector_store: CosmosDBVectorStore,
                 azure_openai_client: AzureOpenAI,
                 deployment_name: str):
        """
        Initialize the Azure recommender LLM
        
        Args:
            vector_store: Cosmos DB vector store
            azure_openai_client: Azure OpenAI client
            deployment_name: Name of the GPT deployment
        """
        self.vector_store = vector_store
        self.openai_client = azure_openai_client
        self.deployment_name = deployment_name
        
        logger.info("Successfully initialized Azure Recommender LLM")
    
    def recommend_tenders_for_company(self, 
                                      company_profile: Dict[str, Any], 
                                      max_recommendations: int = 5) -> List[Dict[str, Any]]:
        """
        Recommend tenders for a given company profile
        
        Args:
            company_profile: Company profile data
            max_recommendations: Maximum number of recommendations
            
        Returns:
            List of recommended tenders with match scores and reasoning
        """
        try:
            # Create search query from company profile
            search_query = self._create_company_search_query(company_profile)
            
            # Search for relevant tenders
            candidate_tenders = self.vector_store.search_tenders(
                query=search_query,
                limit=max_recommendations * 2  # Get more candidates for better filtering
            )
            
            if not candidate_tenders:
                logger.warning("No candidate tenders found")
                return []
            
            # Analyze and rank tenders using LLM
            recommendations = []
            for tender in candidate_tenders[:max_recommendations]:
                try:
                    analysis = self._analyze_tender_match(company_profile, tender)
                    if analysis and analysis.get('match_score', 0) > 0.3:  # Threshold for relevance
                        recommendations.append({
                            'tender': tender,
                            'analysis': analysis,
                            'vector_similarity': tender.get('similarity_score', 0)
                        })
                except Exception as e:
                    logger.error(f"Error analyzing tender match: {str(e)}")
                    continue
            
            # Sort by match score
            recommendations.sort(key=lambda x: x['analysis']['match_score'], reverse=True)
            
            logger.info(f"Generated {len(recommendations)} tender recommendations")
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating tender recommendations: {str(e)}")
            return []
    
    def recommend_companies_for_tender(self, 
                                       tender_data: Dict[str, Any], 
                                       max_recommendations: int = 5) -> List[Dict[str, Any]]:
        """
        Recommend companies for a given tender
        
        Args:
            tender_data: Tender data
            max_recommendations: Maximum number of recommendations
            
        Returns:
            List of recommended companies with match scores and reasoning
        """
        try:
            # Create search query from tender data
            search_query = self._create_tender_search_query(tender_data)
            
            # Search for relevant companies
            candidate_companies = self.vector_store.search_companies(
                query=search_query,
                limit=max_recommendations * 2
            )
            
            if not candidate_companies:
                logger.warning("No candidate companies found")
                return []
            
            # Analyze and rank companies using LLM
            recommendations = []
            for company in candidate_companies[:max_recommendations]:
                try:
                    analysis = self._analyze_company_match(tender_data, company)
                    if analysis and analysis.get('match_score', 0) > 0.3:
                        recommendations.append({
                            'company': company,
                            'analysis': analysis,
                            'vector_similarity': company.get('similarity_score', 0)
                        })
                except Exception as e:
                    logger.error(f"Error analyzing company match: {str(e)}")
                    continue
            
            # Sort by match score
            recommendations.sort(key=lambda x: x['analysis']['match_score'], reverse=True)
            
            logger.info(f"Generated {len(recommendations)} company recommendations")
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating company recommendations: {str(e)}")
            return []
    
    def _analyze_tender_match(self, 
                              company_profile: Dict[str, Any], 
                              tender: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze how well a tender matches a company profile using LLM"""
        try:
            prompt = self._create_tender_analysis_prompt(company_profile, tender)
            
            response = self.openai_client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": "You are an expert tender matching analyst. Analyze how well a tender matches a company's capabilities and provide a detailed assessment."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            analysis_text = response.choices[0].message.content
            
            # Parse the structured response
            return self._parse_analysis_response(analysis_text)
            
        except Exception as e:
            logger.error(f"Error in LLM tender analysis: {str(e)}")
            return None
    
    def _analyze_company_match(self, 
                               tender_data: Dict[str, Any], 
                               company: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze how well a company matches a tender using LLM"""
        try:
            prompt = self._create_company_analysis_prompt(tender_data, company)
            
            response = self.openai_client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": "You are an expert procurement analyst. Analyze how well a company fits the requirements of a tender and provide a detailed assessment."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            analysis_text = response.choices[0].message.content
            
            # Parse the structured response
            return self._parse_analysis_response(analysis_text)
            
        except Exception as e:
            logger.error(f"Error in LLM company analysis: {str(e)}")
            return None
    
    def _create_company_search_query(self, company_profile: Dict[str, Any]) -> str:
        """Create search query from company profile"""
        query_parts = []
        
        # Add industry and services
        if 'industry' in company_profile:
            industries = company_profile['industry'] if isinstance(company_profile['industry'], list) else [company_profile['industry']]
            query_parts.extend(industries)
        
        if 'services' in company_profile:
            services = company_profile['services'] if isinstance(company_profile['services'], list) else [company_profile['services']]
            query_parts.extend(services)
        
        if 'expertise' in company_profile:
            expertise = company_profile['expertise'] if isinstance(company_profile['expertise'], list) else [company_profile['expertise']]
            query_parts.extend(expertise)
        
        # Add location if available
        if 'location' in company_profile:
            query_parts.append(company_profile['location'])
        
        return " ".join(query_parts)
    
    def _create_tender_search_query(self, tender_data: Dict[str, Any]) -> str:
        """Create search query from tender data"""
        query_parts = []
        
        # Add categories
        if 'category' in tender_data:
            categories = tender_data['category'] if isinstance(tender_data['category'], list) else [tender_data['category']]
            query_parts.extend(categories)
        
        # Add title keywords
        if 'title' in tender_data:
            query_parts.append(tender_data['title'])
        
        # Add description keywords (first 100 chars)
        if 'description' in tender_data:
            desc_words = tender_data['description'][:100].split()
            query_parts.extend(desc_words)
        
        return " ".join(query_parts)
    
    def _create_tender_analysis_prompt(self, 
                                       company_profile: Dict[str, Any], 
                                       tender: Dict[str, Any]) -> str:
        """Create prompt for tender analysis"""
        company_data = company_profile.get('data', company_profile)
        tender_data = tender.get('data', tender)
        
        return f"""
        Analyze how well this tender matches the company's profile:

        COMPANY PROFILE:
        Name: {company_data.get('name', 'N/A')}
        Industry: {company_data.get('industry', [])}
        Services: {company_data.get('services', [])}
        Expertise: {company_data.get('expertise', [])}
        Location: {company_data.get('location', 'N/A')}
        Size: {company_data.get('size', 'N/A')}
        
        TENDER DETAILS:
        Title: {tender_data.get('title', 'N/A')}
        Description: {tender_data.get('description', 'N/A')[:500]}...
        Category: {tender_data.get('category', [])}
        Organization: {tender_data.get('organization', 'N/A')}
        Location: {tender_data.get('location', 'N/A')}
        Estimated Value: {tender_data.get('estimated_value', 'N/A')}
        Deadline: {tender_data.get('deadline', 'N/A')}

        Provide your analysis in the following JSON format:
        {{
            "match_score": 0.85,
            "reasoning": "Detailed explanation of the match including strengths and potential gaps",
            "key_strengths": ["strength1", "strength2"],
            "potential_challenges": ["challenge1", "challenge2"],
            "recommendation": "Strong match - company should definitely consider bidding"
        }}
        """
    
    def _create_company_analysis_prompt(self, 
                                        tender_data: Dict[str, Any], 
                                        company: Dict[str, Any]) -> str:
        """Create prompt for company analysis"""
        tender_info = tender_data.get('data', tender_data)
        company_data = company.get('data', company)
        
        return f"""
        Analyze how well this company fits the tender requirements:

        TENDER REQUIREMENTS:
        Title: {tender_info.get('title', 'N/A')}
        Description: {tender_info.get('description', 'N/A')[:500]}...
        Category: {tender_info.get('category', [])}
        Organization: {tender_info.get('organization', 'N/A')}
        Location: {tender_info.get('location', 'N/A')}
        Estimated Value: {tender_info.get('estimated_value', 'N/A')}
        
        COMPANY PROFILE:
        Name: {company_data.get('name', 'N/A')}
        Industry: {company_data.get('industry', [])}
        Services: {company_data.get('services', [])}
        Expertise: {company_data.get('expertise', [])}
        Location: {company_data.get('location', 'N/A')}
        Size: {company_data.get('size', 'N/A')}

        Provide your analysis in the following JSON format:
        {{
            "match_score": 0.85,
            "reasoning": "Detailed explanation of why this company is suitable for the tender",
            "key_strengths": ["strength1", "strength2"],
            "potential_challenges": ["challenge1", "challenge2"],
            "recommendation": "Highly suitable candidate for this tender"
        }}
        """
    
    def _parse_analysis_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Parse the LLM analysis response"""
        try:
            # Try to extract JSON from the response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx]
                analysis = json.loads(json_str)
                
                # Validate required fields
                if 'match_score' in analysis and 'reasoning' in analysis:
                    return analysis
            
            # Fallback: create basic analysis from text
            return {
                'match_score': 0.5,
                'reasoning': response_text,
                'key_strengths': [],
                'potential_challenges': [],
                'recommendation': 'Analysis available in reasoning field'
            }
            
        except json.JSONDecodeError:
            logger.warning("Failed to parse LLM response as JSON")
            return {
                'match_score': 0.5,
                'reasoning': response_text,
                'key_strengths': [],
                'potential_challenges': [],
                'recommendation': 'Analysis available in reasoning field'
            }
        except Exception as e:
            logger.error(f"Error parsing analysis response: {str(e)}")
            return None
