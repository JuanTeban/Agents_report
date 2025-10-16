import logging
from typing import List, Dict, Any, Optional
import chromadb
from app.config.settings_etl import VECTOR_STORE_DIR, CHROMA_COLLECTIONS
from app.utils.embedding_manager import get_embedder

logger = logging.getLogger(__name__)

class BaseRetriever:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=str(VECTOR_STORE_DIR))
        self.embedder = get_embedder()
        self.collections: Dict[str, chromadb.Collection] = {}
        self._init_collections()

    def _init_collections(self):
        for key, name in CHROMA_COLLECTIONS.items():
            try:
                self.collections[key] = self.client.get_collection(name=name)
                logger.info(f"Colección '{name}' cargada para {self.__class__.__name__}")
            except Exception as e:
                logger.warning(f"No se pudo cargar colección '{name}': {e}")

    async def query_collection(
        self,
        collection_key: str,
        query: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        collection = self.collections.get(collection_key)
        if not collection:
            logger.warning(f"Intento de query en colección no disponible: {collection_key}")
            return []

        try:
            query_embedding = await self.embedder.embed_content(
                [query],
                task_type="RETRIEVAL_QUERY"
            )
            if not query_embedding:
                return []

            results = collection.query(
                query_embeddings=query_embedding,
                n_results=top_k,
                include=["documents", "metadatas", "distances"]
            )

            docs = []
            for i in range(len(results["documents"][0])):
                docs.append({
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i]
                })
            docs.sort(key=lambda x: x["distance"])
            return docs

        except Exception as e:
            logger.error(f"Error en query de colección '{collection_key}': {e}")
            return []

    async def filter_collection(
        self,
        collection_key: str,
        where_filter: Dict[str, Any],
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        collection = self.collections.get(collection_key)
        if not collection:
            logger.warning(f"Intento de filtro en colección no disponible: {collection_key}")
            return []

        try:
            results = collection.get(
                where=where_filter,
                limit=limit,
                include=["documents", "metadatas"]
            )
            
            docs = []
            for i in range(len(results["documents"])):
                docs.append({
                    "content": results["documents"][i],
                    "metadata": results["metadatas"][i]
                })
            
            return docs
        except Exception as e:
            logger.error(f"Error en filtro de colección '{collection_key}': {e}")
            return []

    def _normalize_text(self, text: str) -> str:
        import unicodedata
        import re

        text = re.sub(r'\s*\(\d+\)\s*$', '', text).strip()
        text = unicodedata.normalize('NFD', text.lower())
        text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
        text = re.sub(r'[^a-z0-9]+', '_', text)
        text = text.strip('_')
        return text