import os
import json
import uuid
import logging
from typing import Dict, List, Any, Optional
from azure.cosmos import CosmosClient, PartitionKey
from azure.cosmos.exceptions import CosmosResourceNotFoundError
from openai import AzureOpenAI
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CosmosDBVectorStore:
    """Vector store implementation using Azure Cosmos DB with vector search capabilities"""
    
    def __init__(self, 
                 cosmos_endpoint: str,
                 cosmos_key: str,
                 database_name: str,
                 openai_client: AzureOpenAI,
                 embedding_deployment: str):
        """
        Initialize the Cosmos DB vector store
        
        Args:
            cosmos_endpoint: Cosmos DB endpoint URL
            cosmos_key: Cosmos DB primary key
            database_name: Name of the database
            openai_client: Azure OpenAI client for embeddings
            embedding_deployment: Name of the embedding deployment
        """
        self.cosmos_client = CosmosClient(cosmos_endpoint, cosmos_key)
        self.database_name = database_name
        self.openai_client = openai_client
        self.embedding_deployment = embedding_deployment
        
        # Initialize database and containers
        self.database = self.cosmos_client.create_database_if_not_exists(id=database_name)
        
        # Create containers with vector indexing
        self.tenders_container = self.database.create_container_if_not_exists(
            id="tenders",
            partition_key=PartitionKey(path="/id"),
            offer_throughput=400
        )
        
        self.companies_container = self.database.create_container_if_not_exists(
            id="companies", 
            partition_key=PartitionKey(path="/id"),
            offer_throughput=400
        )
        
        logger.info(f"Successfully initialized Cosmos DB vector store with database: {database_name}")
    
    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embeddings using Azure OpenAI"""
        try:
            response = self.openai_client.embeddings.create(
                input=text,
                model=self.embedding_deployment
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            # Return a zero vector as fallback
            return [0.0] * 1536  # text-embedding-3-small dimension
    
    def add_tender(self, 
                   tender_data: Dict[str, Any], 
                   metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Add a tender document to the vector store
        
        Args:
            tender_data: Tender document data
            metadata: Additional metadata
            
        Returns:
            Document ID
        """
        try:
            # Generate unique ID if not provided
            document_id = tender_data.get('id', str(uuid.uuid4()))
            
            # Create text for embedding
            embedding_text = self._create_tender_embedding_text(tender_data)
            
            # Generate embedding
            embedding = self._generate_embedding(embedding_text)
            
            # Prepare document
            document = {
                'id': document_id,
                'type': 'tender',
                'data': tender_data,
                'metadata': metadata or {},
                'embedding_text': embedding_text,
                'embedding': embedding,
                'created_at': tender_data.get('publication_date', ''),
                'title': tender_data.get('title', ''),
                'category': tender_data.get('category', []),
                'location': tender_data.get('location', ''),
                'estimated_value': tender_data.get('estimated_value', 0)
            }
            
            # Insert into container
            self.tenders_container.create_item(body=document)
            logger.info(f"Added tender document with ID: {document_id}")
            
            return document_id
            
        except Exception as e:
            logger.error(f"Error adding tender document: {str(e)}")
            raise
    
    def add_company(self, 
                    company_data: Dict[str, Any], 
                    metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Add a company document to the vector store
        
        Args:
            company_data: Company document data
            metadata: Additional metadata
            
        Returns:
            Document ID
        """
        try:
            # Generate unique ID if not provided
            document_id = company_data.get('id', str(uuid.uuid4()))
            
            # Create text for embedding
            embedding_text = self._create_company_embedding_text(company_data)
            
            # Generate embedding
            embedding = self._generate_embedding(embedding_text)
            
            # Prepare document
            document = {
                'id': document_id,
                'type': 'company',
                'data': company_data,
                'metadata': metadata or {},
                'embedding_text': embedding_text,
                'embedding': embedding,
                'name': company_data.get('name', ''),
                'industry': company_data.get('industry', []),
                'services': company_data.get('services', []),
                'location': company_data.get('location', ''),
                'size': company_data.get('size', '')
            }
            
            # Insert into container
            self.companies_container.create_item(body=document)
            logger.info(f"Added company document with ID: {document_id}")
            
            return document_id
            
        except Exception as e:
            logger.error(f"Error adding company document: {str(e)}")
            raise
    
    def search_tenders(self, 
                       query: str, 
                       limit: int = 10,
                       filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Search for similar tenders using vector similarity
        
        Args:
            query: Search query
            limit: Maximum number of results
            filters: Additional filters
            
        Returns:
            List of similar tender documents with similarity scores
        """
        try:
            # Generate embedding for query
            query_embedding = self._generate_embedding(query)
            
            # Build SQL query with vector search
            sql_query = """
            SELECT 
                c.id,
                c.data,
                c.metadata,
                c.title,
                c.category,
                c.location,
                c.estimated_value,
                VectorDistance(c.embedding, @queryVector) AS similarity_score
            FROM c 
            WHERE c.type = 'tender'
            ORDER BY VectorDistance(c.embedding, @queryVector)
            OFFSET 0 LIMIT @limit
            """
            
            parameters = [
                {"name": "@queryVector", "value": query_embedding},
                {"name": "@limit", "value": limit}
            ]
            
            # Execute query
            items = list(self.tenders_container.query_items(
                query=sql_query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            logger.info(f"Found {len(items)} similar tenders for query: {query}")
            return items
            
        except Exception as e:
            logger.error(f"Error searching tenders: {str(e)}")
            return []
    
    def search_companies(self, 
                         query: str, 
                         limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for similar companies using vector similarity
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of similar company documents with similarity scores
        """
        try:
            # Generate embedding for query
            query_embedding = self._generate_embedding(query)
            
            # Build SQL query with vector search
            sql_query = """
            SELECT 
                c.id,
                c.data,
                c.metadata,
                c.name,
                c.industry,
                c.services,
                c.location,
                c.size,
                VectorDistance(c.embedding, @queryVector) AS similarity_score
            FROM c 
            WHERE c.type = 'company'
            ORDER BY VectorDistance(c.embedding, @queryVector)
            OFFSET 0 LIMIT @limit
            """
            
            parameters = [
                {"name": "@queryVector", "value": query_embedding},
                {"name": "@limit", "value": limit}
            ]
            
            # Execute query
            items = list(self.companies_container.query_items(
                query=sql_query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            logger.info(f"Found {len(items)} similar companies for query: {query}")
            return items
            
        except Exception as e:
            logger.error(f"Error searching companies: {str(e)}")
            return []
    
    def get_tender_by_id(self, tender_id: str) -> Optional[Dict[str, Any]]:
        """Get a tender by ID"""
        try:
            item = self.tenders_container.read_item(item=tender_id, partition_key=tender_id)
            return item
        except CosmosResourceNotFoundError:
            return None
        except Exception as e:
            logger.error(f"Error getting tender by ID {tender_id}: {str(e)}")
            return None
    
    def get_company_by_id(self, company_id: str) -> Optional[Dict[str, Any]]:
        """Get a company by ID"""
        try:
            item = self.companies_container.read_item(item=company_id, partition_key=company_id)
            return item
        except CosmosResourceNotFoundError:
            return None
        except Exception as e:
            logger.error(f"Error getting company by ID {company_id}: {str(e)}")
            return None
    
    def get_all_tenders(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all tenders with optional limit"""
        try:
            sql_query = "SELECT * FROM c WHERE c.type = 'tender' ORDER BY c._ts DESC OFFSET 0 LIMIT @limit"
            parameters = [{"name": "@limit", "value": limit}]
            
            items = list(self.tenders_container.query_items(
                query=sql_query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            return items
        except Exception as e:
            logger.error(f"Error getting all tenders: {str(e)}")
            return []
    
    def get_all_companies(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all companies with optional limit"""
        try:
            sql_query = "SELECT * FROM c WHERE c.type = 'company' ORDER BY c._ts DESC OFFSET 0 LIMIT @limit"
            parameters = [{"name": "@limit", "value": limit}]
            
            items = list(self.companies_container.query_items(
                query=sql_query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            return items
        except Exception as e:
            logger.error(f"Error getting all companies: {str(e)}")
            return []
    
    def _create_tender_embedding_text(self, tender_data: Dict[str, Any]) -> str:
        """Create text representation for tender embedding"""
        parts = []
        
        if 'title' in tender_data:
            parts.append(f"Title: {tender_data['title']}")
        
        if 'description' in tender_data:
            parts.append(f"Description: {tender_data['description']}")
        
        if 'category' in tender_data and tender_data['category']:
            categories = tender_data['category'] if isinstance(tender_data['category'], list) else [tender_data['category']]
            parts.append(f"Categories: {', '.join(categories)}")
        
        if 'organization' in tender_data:
            parts.append(f"Organization: {tender_data['organization']}")
        
        if 'location' in tender_data:
            parts.append(f"Location: {tender_data['location']}")
        
        if 'estimated_value' in tender_data and tender_data['estimated_value']:
            parts.append(f"Estimated Value: {tender_data['estimated_value']}")
        
        return " | ".join(parts)
    
    def _create_company_embedding_text(self, company_data: Dict[str, Any]) -> str:
        """Create text representation for company embedding"""
        parts = []
        
        if 'name' in company_data:
            parts.append(f"Company: {company_data['name']}")
        
        if 'description' in company_data:
            parts.append(f"Description: {company_data['description']}")
        
        if 'industry' in company_data and company_data['industry']:
            industries = company_data['industry'] if isinstance(company_data['industry'], list) else [company_data['industry']]
            parts.append(f"Industries: {', '.join(industries)}")
        
        if 'services' in company_data and company_data['services']:
            services = company_data['services'] if isinstance(company_data['services'], list) else [company_data['services']]
            parts.append(f"Services: {', '.join(services)}")
        
        if 'expertise' in company_data and company_data['expertise']:
            expertise = company_data['expertise'] if isinstance(company_data['expertise'], list) else [company_data['expertise']]
            parts.append(f"Expertise: {', '.join(expertise)}")
        
        if 'location' in company_data:
            parts.append(f"Location: {company_data['location']}")
        
        if 'size' in company_data:
            parts.append(f"Size: {company_data['size']}")
        
        return " | ".join(parts)
