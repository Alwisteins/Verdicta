import os
from typing import List, Optional
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAiEmbeddings
from langchain_community.vectorstores import Qdrant
from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "law_chapters")