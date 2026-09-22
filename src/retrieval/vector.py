import os
from typing import List, Optional
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models
from dotenv import load_dotenv

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "law_chapters")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "models/gemini-embedding-2")
EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", "768"))

class VectorStoreManager:
    def __init__(self, collection_name: str = COLLECTION_NAME):
        self.collection_name = collection_name
        
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model=GEMINI_EMBEDDING_MODEL,
            google_api_key=GEMINI_API_KEY,
            output_dimensionality=EMBEDDING_DIMENSION
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
                if value is not None:
                    filter_conditions.append(
                        qdrant_models.FieldCondition(
                            key=f"metadata.{key}",
                            match=qdrant_models.MatchValue(value=value)
                        )
                    )
            if filter_conditions:
                qdrant_filter = qdrant_models.Filter(must=filter_conditions)    
            
        results = vectorstore.similarity_search(
            query=query,
            k=k,
            filter=qdrant_filter
        )
        
        return results
