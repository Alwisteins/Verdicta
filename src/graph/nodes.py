import logging
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from src.graph.state import GraphState, CategoryType, ExtractedFilters
from src.retrieval.vector import VectorStoreManager

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
ROUTER_MODEL_NAME = "gemini-flash-latest"
ROUTER_TEMPERATURE = 0
DEFAULT_TOP_K = 5
BROAD_TOP_K = 20
DEFAULT_CATEGORY: CategoryType = "general_inquiry"


class RouteQuery(BaseModel):
    category: CategoryType = Field(
        description="Kategori taksonomi hukum dari pertanyaan pengguna."
    )
    reasoning: str = Field(
        description="Alasan singkat pemilihan kategori."
    )
    filters: Optional[ExtractedFilters] = Field(
        default=None,
        description=(
            "Filter metadata yang relevan diekstrak dari pertanyaan "
            "(seperti nomor_uu, tahun, jenis_dokumen, dan pasal jika spesifik)."
        ),
    )


ROUTER_SYSTEM_PROMPT = """Anda adalah router AI spesialis hukum Indonesia. Tugas Anda adalah mengklasifikasikan pertanyaan hukum pengguna ke dalam salah satu dari 7 kategori taksonomi berikut serta mengekstrak filter metadata jika ada.

7 Kategori Taksonomi:
1. specific_article: Pencarian pasal/bab/nomor UU spesifik (misal: "Isi Pasal 10A PERPPU 1/2022").
2. general_inquiry: Pertanyaan kasus/topik hukum umum tanpa menyebut nomor pasal (misal: "Batas usia anggota Bawaslu").
3. comparative_analysis: Membandingkan dua atau lebih aturan hukum (misal: "Perbedaan syarat KPU di UU 7/2017 vs PERPPU 1/2022").
4. list_discovery: Meminta daftar pasal atau daftar dokumen perundang-undangan.
5. legal_status: Menanyakan status keberlakuan/amandemen aturan hukum.
6. definition_term: Menanyakan definisi resmi dari Pasal 1 / Ketentuan Umum.
7. penalty_sanction: Menanyakan sanksi pidana, denda, atau akibat hukum.

Instruksi Ekstraksi Filter:
- Ekstrak filter metadata yang relevan ke dalam struktur `filters` (termasuk `nomor_uu`, `tahun`, `jenis_dokumen`, dan `pasal` jika ada).
- Jika user menyebutkan pasal/nomor UU/tahun secara spesifik pada kategori APAPUN, pastikan field `filters` terisi secara akurat.
- Jika tidak ada metadata spesifik yang disebutkan, kosongkan `filters` (set None)."""

router_prompt = ChatPromptTemplate.from_messages([
    ("system", ROUTER_SYSTEM_PROMPT),
    ("human", "{question}"),
])

# Instansiasi module-level
llm = ChatGoogleGenerativeAI(model=ROUTER_MODEL_NAME, temperature=ROUTER_TEMPERATURE)
vector_manager = VectorStoreManager()

_structured_llm = llm.with_structured_output(RouteQuery)


def router_node(state: GraphState) -> Dict[str, Any]:
    """
    Node LangGraph untuk mengklasifikasikan pertanyaan pengguna ke dalam
    salah satu dari 7 kategori taksonomi hukum dan mengekstrak filter metadata.
    """
    question = state.get("question", "")

    if not question:
        logger.warning("router_node dipanggil tanpa 'question' di state.")
        return {"question_category": DEFAULT_CATEGORY, "filters": None}

    try:
        messages = router_prompt.invoke({"question": question})
        result = _structured_llm.invoke(messages)
        filters = result.filters if result.filters else None

        # Konversi ke dict/query format untuk logging
        filters_dict = filters.to_query_dict() if hasattr(filters, "to_query_dict") and filters else filters

        logger.info("[Router] Category: %s | Filters: %s | Reason: %s", result.category, filters_dict, result.reasoning)
        return {"question_category": result.category, "filters": filters}

    except Exception:
        logger.exception(
            "Gagal melakukan structured output di router_node, fallback ke default category."
        )
        return {"question_category": DEFAULT_CATEGORY, "filters": None}


def retrieve_node(state: GraphState) -> Dict[str, Any]:
    """
    Node LangGraph untuk melakukan pencarian dokumen ke Qdrant
    berdasarkan strategi top_k dan filter metadata dari state.
    """
    question = state.get("question", "")
    question_category = state.get("question_category", DEFAULT_CATEGORY)
    filters_obj = state.get("filters", None)

    if not question:
        logger.warning("retrieve_node dipanggil tanpa 'question' di state.")
        return {"documents": []}

    # 1. Tentukan Top-K berdasarkan Kategori
    top_k = BROAD_TOP_K if question_category == "list_discovery" else DEFAULT_TOP_K

    # 2. Konversi ExtractedFilters ke Dict jika valid
    filters_dict = None
    if filters_obj:
        if hasattr(filters_obj, "to_query_dict"):
            filters_dict = filters_obj.to_query_dict()
        elif isinstance(filters_obj, dict):
            filters_dict = filters_obj

    # Clean up empty dict
    if filters_dict == {}:
        filters_dict = None

    try:
        # 3. Eksekusi Pencarian: Jika ADA filter metadata (kategori apapun), jalankan search_with_filter!
        if filters_dict:
            logger.info("[Retrieve] Executing Filtered Search with filters: %s", filters_dict)
            documents = vector_manager.search_with_filter(
                question,
                filters=filters_dict,
                top_k=top_k
            )
        else:
            logger.info("[Retrieve] Executing Pure Semantic Search (Top-K: %d)", top_k)
            documents = vector_manager.search(
                question,
                top_k=top_k
            )

    except Exception:
        logger.exception("Gagal melakukan vector search di retrieve_node.")
        return {"documents": []}

    logger.info("Ditemukan %d dokumen relevan.", len(documents))
    return {"documents": documents}