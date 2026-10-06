from typing import Annotated, List, Optional, TypedDict, Literal, Dict, Any
from langchain_core.documents import Document
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field

CategoryType = Literal["specific_article", "general_inquiry", "comparative_analysis", "list_discovery", "legal_status", "definition_term", "penalty_sanction"]

class ExtractedFilters(BaseModel):
    """
    Filter metadata yang TERVALIDASI, menggantikan `Optional[dict]` bebas.
    Field ditulis eksplisit supaya LLM tidak bisa menyisipkan key sembarangan
    yang nantinya diteruskan mentah-mentah ke query Qdrant.
    """
    nomor_uu: Optional[str] = None
    category: Optional[str] = None
    category_code: Optional[int] = None
    pasal: Optional[str] = None
    bab: Optional[str] = None
    bagian: Optional[str] = None

    def to_query_dict(self) -> Dict[str, Any]:
        return {
            key: value.strip() if isinstance(value, str) else value
            for key, value in self.model_dump(exclude_none=True).items()
            if not (isinstance(value, str) and not value.strip())
        }

class GraphState(TypedDict):
    question         : Annotated[list, add_messages]    # user input
    question_category: CategoryType                     # kategori pertanyaan
    filters          : Optional[ExtractedFilters]       # filter metadata
    documents        : List[Document]                   # hasil retrieval dari Qdrant
    generation       : str                              # output akhir dari LLM
