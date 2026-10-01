from typing import List, Optional, TypedDict, Literal, Dict, Any
from langchain_core.documents import Document
from pydantic import BaseModel, Field

CategoryType = Literal["specific_article", "general_inquiry", "comparative_analysis", "list_discovery", "legal_status", "definition_term", "penalty_sanction"]

class ExtractedFilters(BaseModel):
    """
    Filter metadata yang TERVALIDASI, menggantikan `Optional[dict]` bebas.
    Field ditulis eksplisit supaya LLM tidak bisa menyisipkan key sembarangan
    yang nantinya diteruskan mentah-mentah ke query Qdrant.
    """
    nomor_uu: Optional[str] = None
    tahun: Optional[str] = None
    jenis_dokumen: Optional[str] = None

    def to_query_dict(self) -> Dict[str, Any]:
        return self.model_dump(exclude_none=True)

class GraphState(TypedDict):
    question         : str                          # user input
    question_category: CategoryType                 # kategori pertanyaan
    filters          : Optional[ExtractedFilters]   # filter metadata
    documents        : List[Document]               # hasil retrieval dari Qdrant
    generation       : str                          # output akhir dari LLM