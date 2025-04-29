import chromadb
import json
import logging
import requests
from typing import Dict, List, Any, Optional
import os
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ChromaDBStore")

class ChromaDBStore:
    """Vector store wrapper using ChromaDB for storing tenders and company profiles."""

    def __init__(self, db_path: str, embedding_dimension: int):
        self.embedding_dimension = embedding_dimension
        db_path = os.path.abspath(db_path)
        os.makedirs(db_path, exist_ok=True)
        logger.info(f"Database path set at: {db_path}")

        # Generate a unique client ID to avoid conflicts
        client_id = f"client_{int(time.time())}"
        
        try:
            # First, try using PersistentClient with just the path
            try:
                logger.info("Attempting to initialize with PersistentClient using basic path")
                self.client = chromadb.PersistentClient(path=db_path)
                logger.info("Successfully initialized ChromaDB with PersistentClient (basic)")
            except Exception as e1:
                logger.warning(f"Basic PersistentClient failed: {e1}")
                
                # If that fails, try with more explicit settings but no tenant/db
                try:
                    logger.info("Attempting to initialize with PersistentClient and no tenant/db")
                    persist_directory = os.path.join(db_path, client_id)
                    os.makedirs(persist_directory, exist_ok=True)
                    self.client = chromadb.PersistentClient(path=persist_directory)
                    logger.info(f"Successfully initialized ChromaDB with unique path: {persist_directory}")
                except Exception as e2:
                    logger.warning(f"Unique path PersistentClient failed: {e2}")
                    
                    # As a last resort, use in-memory client
                    logger.info("Falling back to EphemeralClient (in-memory)")
                    self.client = chromadb.EphemeralClient()
                    logger.warning("Using in-memory database - data will not persist between runs")
            
            # Get or create collections
            self.tender_collection = self._get_or_create_collection("tenders")
            self.company_collection = self._get_or_create_collection("companies")
            
            logger.info("Successfully initialized ChromaDB collections")
        except Exception as e:
            logger.exception(f"Failed to initialize ChromaDB client: {e}")
            raise

    def _get_or_create_collection(self, name: str) -> Any:
        """Returns existing or newly created ChromaDB collection with retry logic."""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # Try to get the collection first
                try:
                    collection = self.client.get_collection(name=name)
                    logger.info(f"Retrieved existing collection '{name}'")
                    return collection
                except Exception:
                    # Collection doesn't exist, create it
                    logger.info(f"Creating new collection '{name}'")
                    return self.client.create_collection(
                        name=name,
                        metadata={"dimension": self.embedding_dimension}
                    )
            except Exception as e:
                retry_count += 1
                if retry_count >= max_retries:
                    logger.error(f"Failed to get/create collection '{name}' after {max_retries} attempts: {e}")
                    raise
                logger.warning(f"Attempt {retry_count} failed for collection '{name}': {e}. Retrying...")
                time.sleep(0.5)  # Short delay before retry

    def _get_embeddings(self, texts: List[str], ollama_host: str, model: str) -> List[List[float]]:
        """Fetch embeddings from Ollama host for each text."""
        embeddings = []
        for text in texts:
            try:
                response = requests.post(
                    f"{ollama_host}/api/embeddings",
                    json={"model": model, "prompt": text}
                )
                response.raise_for_status()
                embedding = response.json().get("embedding", [])
                if embedding:
                    embeddings.append(embedding)
                else:
                    embeddings.append([0.0] * self.embedding_dimension)
            except Exception as e:
                logger.error(f"Embedding fetch failed: {str(e)}")
                embeddings.append([0.0] * self.embedding_dimension)
        return embeddings

    def _get_embedding_safe(self, text: str, ollama_host: str, model: str) -> List[float]:
        return self._get_embeddings([text], ollama_host, model)[0]

    def add_tender(self, tender_id: str, tender_data: Dict[str, Any],
                   embeddings: Optional[List[float]] = None,
                   ollama_host: Optional[str] = None, embedding_model: Optional[str] = None) -> bool:
        """Adds a tender record with embeddings."""
        try:
            text = f"{tender_data.get('title', '')} {tender_data.get('description', '')}"
            if embeddings is None:
                if not ollama_host or not embedding_model:
                    raise ValueError("Missing embedding source details")
                embeddings = self._get_embedding_safe(text, ollama_host, embedding_model)

            self.tender_collection.add(
                ids=[tender_id],
                embeddings=[embeddings],
                metadatas=[{
                    "title": tender_data.get("title", ""),
                    "source": tender_data.get("source", ""),
                    "deadline": tender_data.get("deadline", ""),
                    "value": tender_data.get("value", ""),
                    "category": tender_data.get("category", "")
                }],
                documents=[json.dumps(tender_data)]
            )
            return True
        except Exception as e:
            logger.error(f"Failed to add tender: {str(e)}")
            return False

    def add_company_profile(self, company_id: str, company_data: Dict[str, Any],
                            embeddings: Optional[List[float]] = None,
                            ollama_host: Optional[str] = None, embedding_model: Optional[str] = None) -> bool:
        """Adds a company profile with embeddings."""
        try:
            text = f"{company_data.get('name', '')} {company_data.get('description', '')} {' '.join(company_data.get('expertise', []))}"
            if embeddings is None:
                if not ollama_host or not embedding_model:
                    raise ValueError("Missing embedding source details")
                embeddings = self._get_embedding_safe(text, ollama_host, embedding_model)

            self.company_collection.add(
                ids=[company_id],
                embeddings=[embeddings],
                metadatas=[{
                    "name": company_data.get("name", ""),
                    "size": company_data.get("size", ""),
                    "expertise": ",".join(company_data.get("expertise", [])),
                    "years_active": str(company_data.get("years_active", 0))
                }],
                documents=[json.dumps(company_data)]
            )
            return True
        except Exception as e:
            logger.error(f"Failed to add company: {str(e)}")
            return False

    def _search_similar(self, collection, query_embedding: List[float], limit: int) -> List[Dict[str, Any]]:
        try:
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                include=["metadatas", "documents", "distances"]
            )
            output = []
            for i in range(len(results.get("ids", [[]])[0])):
                doc_id = results["ids"][0][i]
                distance = results["distances"][0][i]
                document = json.loads(results["documents"][0][i])
                output.append({
                    "id": doc_id,
                    "similarity_score": 1.0 - min(distance, 1.0),
                    **document
                })
            return output
        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            return []

    def search_similar_tenders(self, query_embedding: List[float], limit: int = 10) -> List[Dict[str, Any]]:
        return self._search_similar(self.tender_collection, query_embedding, limit)

    def search_similar_companies(self, query_embedding: List[float], limit: int = 10) -> List[Dict[str, Any]]:
        return self._search_similar(self.company_collection, query_embedding, limit)

    def _fetch_all_records(self, collection) -> List[Dict[str, Any]]:
        try:
            results = collection.get(include=["metadatas", "documents"])
            return [{
                "id": results["ids"][i],
                **json.loads(results["documents"][i])
            } for i in range(len(results.get("ids", [])))]
        except Exception as e:
            logger.error(f"Failed to fetch records: {str(e)}")
            return []

    def get_all_tenders(self) -> List[Dict[str, Any]]:
        return self._fetch_all_records(self.tender_collection)

    def get_all_companies(self) -> List[Dict[str, Any]]:
        return self._fetch_all_records(self.company_collection)

    def _get_by_id(self, collection, item_id: str) -> Optional[Dict[str, Any]]:
        try:
            result = collection.get(ids=[item_id], include=["metadatas", "documents"])
            if result.get("ids"):
                return json.loads(result["documents"][0])
            return None
        except Exception as e:
            logger.error(f"Get by ID failed ({item_id}): {str(e)}")
            return None

    def get_tender_by_id(self, tender_id: str) -> Optional[Dict[str, Any]]:
        return self._get_by_id(self.tender_collection, tender_id)

    def get_company_by_id(self, company_id: str) -> Optional[Dict[str, Any]]:
        return self._get_by_id(self.company_collection, company_id)