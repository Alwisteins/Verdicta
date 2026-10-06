import os
import sys
from typing import List, Optional
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
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

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
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

class VectorStoreManager:
    def __init__(self, collection_name: str = COLLECTION_NAME):
        self.collection_name = collection_name
        
        self.embeddings = HuggingFaceEmbeddings(
            model_name="BAAI/bge-m3",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True}
        )
        
        self.client = QdrantClient(url=QDRANT_URL)
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
        
    def get_vectorstore(self) -> QdrantVectorStore:
        """Mengembalikan instance LangChain Qdrant vectorstore"""
        return QdrantVectorStore(
            client=self.client,
            collection_name=self.collection_name,
            embedding=self.embeddings
        )
        
    def add_documents(self, documents: List[Document]) -> None:
        """
        Menyimpan daftar dokumen ke Qdrant vector store.
        Otomatis menghitung embedding dari `page_content` dan menyimpan seluruh dict `metadata`
        """
        if not documents:
            print("⚠️ Tidak ada dokumen untuk ditambahkan.")
            return
        
        print(f"📦 Menyimpan {len(documents)} dokumen ke Qdrant collection '{self.collection_name}'")
        
        vectorstore = self.get_vectorstore()
        vectorstore.add_documents(documents)
        
        print(f"✅ Selesai menyimpan {len(documents)} dokumen ke Qdrant collection '{self.collection_name}'!")
        
    def search_documents(
        self,
        query: str,
        k: int = 4,
        filter_dict: Optional[dict] = None
    ) -> List[Document]:
        """
        Mencari dokumen paling relevan berdasarkan query semantik.
        Mendukung filter berdasarkan metadata (nomor_uu / pasal).
        """
        vectorstore = self.get_vectorstore()
        
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
            print(f"[VectorStoreManager] Filter conditions: {filter_conditions}")
            if filter_conditions:
                qdrant_filter = qdrant_models.Filter(must=filter_conditions)    
           
        results = vectorstore.similarity_search(
            query=query,
            k=k,
            filter=qdrant_filter
        )
        
        print(f"[VectorStoreManager] Found {len(results)} documents for query: '{query}' with filter: {filter_dict}")
        
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
