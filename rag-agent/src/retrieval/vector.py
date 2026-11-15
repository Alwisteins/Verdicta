import os
import sys
import time
import requests
from typing import List, Optional
from langchain_core.documents import Document
from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models
from dotenv import load_dotenv

load_dotenv()

_orig_qdrant_del = QdrantClient.__del__

def _safe_qdrant_del(self):
    if sys.meta_path is None:
        return
    try:
        _orig_qdrant_del(self)
    except Exception:
        pass

QdrantClient.__del__ = _safe_qdrant_del

ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID")
AUTH_TOKEN = os.getenv("CLOUDFLARE_API_KEY")
CF_URL = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/ai/run/@cf/baai/bge-m3"
HEADERS = {"Authorization": f"Bearer {AUTH_TOKEN}"}

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "law_chapters")
EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", "1024"))
ALLOWED_METADATA_FILTERS = {
    "judul_dokumen",
    "nomor_uu",
    "category",
    "category_code",
    "pasal",
    "bab",
    "bab_judul",
    "bagian",
    "bagian_judul",
    "source_file",
}


def get_cloudflare_query_embedding(text: str) -> List[float]:
    """Menghasilkan embedding query menggunakan Cloudflare Workers AI BGE-M3 dengan retry (total ~25s, timeout per panggilan)."""
    start_time = time.time()
    max_total_time = 25.0
    per_call_timeout = 8.0

    while True:
        elapsed = time.time() - start_time
        if elapsed >= max_total_time:
            raise TimeoutError("Cloudflare embedding request exceeded total retry time limit (25s).")

        current_timeout = min(per_call_timeout, max_total_time - elapsed)
        if current_timeout <= 0:
            raise TimeoutError("Cloudflare embedding request timed out.")

        try:
            response = requests.post(
                CF_URL,
                headers=HEADERS,
                json={"text": text},
                timeout=current_timeout
            )
            response.raise_for_status()
            result = response.json()["result"]
            return result["data"][0] if "data" in result else result["embeddings"][0]
        except (requests.RequestException, TimeoutError) as e:
            if time.time() - start_time >= max_total_time:
                raise e
            time.sleep(1.0)


class VectorStoreManager:
    def __init__(self, collection_name: str = COLLECTION_NAME):
        self.collection_name = collection_name
        self.client = QdrantClient(
            url=QDRANT_URL,
            api_key=QDRANT_API_KEY
        )
        self._ensure_collection_exists()
        
    def _ensure_collection_exists(self):
        """Membuat collection di Qdrant jika belum ada."""
        if not self.client.collection_exists(self.collection_name):
            print(f"Collection '{self.collection_name}' tidak ditemukan. Membuat collection baru...")
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=qdrant_models.VectorParams(
                    size=EMBEDDING_DIMENSION,
                    distance=qdrant_models.Distance.COSINE
                )
            )
            print(f"Collection '{self.collection_name}' berhasil dibuat!")
        
    def search_documents(
        self,
        query: str,
        k: int = 4,
        filter_dict: Optional[dict] = None
    ) -> List[Document]:
        """
        Mencari dokumen paling relevan berdasarkan query semantik menggunakan Cloudflare Workers AI BGE-M3.
        Mendukung filter metadata.
        """
        # 1. Generate query embedding via Cloudflare Workers AI BGE-M3
        query_vector = get_cloudflare_query_embedding(query)
        
        # 2. Build Qdrant filter
        qdrant_filter = None
        if filter_dict:
            filter_conditions = []
            for key, value in filter_dict.items():
                if key not in ALLOWED_METADATA_FILTERS:
                    print(f"[VectorStoreManager] Ignoring unsupported metadata filter: {key}")
                    continue
                if value is not None:
                    filter_conditions.append(
                        qdrant_models.FieldCondition(
                            key=f"metadata.{key}",
                            match=qdrant_models.MatchValue(value=value)
                        )
                    )
            if filter_conditions:
                qdrant_filter = qdrant_models.Filter(must=filter_conditions)    
           
        # 3. Query Qdrant directly using Cloudflare embedding vector
        search_result = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=k,
            query_filter=qdrant_filter,
            with_payload=True
        ).points

        results = []
        for point in search_result:
            payload = point.payload or {}
            page_content = payload.get("page_content", "")
            metadata = payload.get("metadata", {})
            metadata["score"] = point.score
            metadata["_id"] = point.id
            metadata["_collection_name"] = self.collection_name
            
            doc = Document(page_content=page_content, metadata=metadata)
            results.append(doc)
        
        return results

    def search_with_filter(
        self,
        query: str,
        filters: Optional[dict] = None,
        top_k: int = 4
    ) -> List[Document]:
        """
        Mencari dokumen berdasarkan query semantik dengan filter metadata spesifik dan top_k.
        """
        return self.search_documents(query=query, k=top_k, filter_dict=filters)

    def search(
        self,
        query: str,
        top_k: int = 4
    ) -> List[Document]:
        """
        Mencari dokumen standar berdasarkan query semantik dan top_k tanpa filter.
        """
        return self.search_documents(query=query, k=top_k, filter_dict=None)

    def close(self):
        try:
            self.client.close()
        except Exception:
            pass

    def __del__(self):
        if sys.meta_path is None:
            return
        try:
            self.close()
        except Exception:
            pass
