"""Local BGE-M3 document embedding and Qdrant writes for ingestion."""

import os
import uuid
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from langchain_core.documents import Document
from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer

load_dotenv(Path(__file__).resolve().parent / ".env")

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")
EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", "1024"))
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "law_chapters")


class VectorStoreManager:
    """Embeds documents locally and upserts them into Qdrant."""

    def __init__(self, collection_name: str = COLLECTION_NAME):
        self.collection_name = collection_name
        self.model = SentenceTransformer(EMBEDDING_MODEL)
        dimension = self.model.get_sentence_embedding_dimension()
        if dimension != EMBEDDING_DIMENSION:
            raise ValueError(
                f"Model {EMBEDDING_MODEL!r} returns {dimension} dimensions, "
                f"but EMBEDDING_DIMENSION is {EMBEDDING_DIMENSION}."
            )
        self.client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
        self._ensure_collection_exists()

    def _ensure_collection_exists(self) -> None:
        if not self.client.collection_exists(self.collection_name):
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=EMBEDDING_DIMENSION,
                    distance=models.Distance.COSINE,
                ),
            )

    def add_documents(self, documents: List[Document]) -> None:
        if not documents:
            return
        vectors = self.model.encode(
            [doc.page_content for doc in documents],
            normalize_embeddings=True,
            show_progress_bar=len(documents) > 32,
        )
        self.client.upload_points(
            collection_name=self.collection_name,
            points=[
                models.PointStruct(
                id=str(uuid.uuid4()),
                    vector=vector.tolist(),
                    payload={"page_content": doc.page_content, "metadata": doc.metadata},
                )
                for doc, vector in zip(documents, vectors)
            ],
        )

    def close(self) -> None:
        self.client.close()
