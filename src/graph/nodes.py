import logging
import re
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
ROUTER_MODEL_NAME = "gemini-3.5-flash-lite"
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
            "(seperti nomor_uu, category, category_code, pasal, bab, dan bagian jika spesifik)."
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
- Ekstrak filter metadata HANYA memakai key yang benar-benar ada di metadata dokumen: `nomor_uu`, `category`, `category_code`, `pasal`, `bab`, dan `bagian`.
- Jangan pernah membuat filter `tahun` atau `jenis_dokumen`; kedua key itu tidak ada di metadata.
- Nilai `nomor_uu` harus berupa gabungan nomor dan tahun, misalnya `Nomor 1 Tahun 2022`, bukan hanya `1` dan bukan field tahun terpisah.
- Jika user menyebut jenis dokumen, isi `category` dengan nama metadata, misalnya `undang undang`, `peraturan pemerintah pengganti undang undang`, `peraturan pemerintah`, atau `peraturan presiden`.
- Jika user menyebutkan pasal/nomor dokumen secara spesifik pada kategori APAPUN, pastikan field `filters` terisi secara akurat.
- Jika tidak ada metadata spesifik yang disebutkan, kosongkan `filters` (set None)."""

router_prompt = ChatPromptTemplate.from_messages([
    ("system", ROUTER_SYSTEM_PROMPT),
    ("human", "{question}"),
])

# Instansiasi module-level
llm = ChatGoogleGenerativeAI(model=ROUTER_MODEL_NAME, temperature=ROUTER_TEMPERATURE)
vector_manager = VectorStoreManager()

_structured_llm = llm.with_structured_output(RouteQuery)


DOCUMENT_CATEGORY_ALIASES = {
    "perppu": "peraturan pemerintah pengganti undang undang",
    "perpu": "peraturan pemerintah pengganti undang undang",
    "peraturan pemerintah pengganti undang-undang": "peraturan pemerintah pengganti undang undang",
    "peraturan pemerintah pengganti undang undang": "peraturan pemerintah pengganti undang undang",
    "uu": "undang undang",
    "undang-undang": "undang undang",
    "undang undang": "undang undang",
    "pp": "peraturan pemerintah",
    "peraturan pemerintah": "peraturan pemerintah",
    "perpres": "peraturan presiden",
    "peraturan presiden": "peraturan presiden",
}


def _question_to_text(question: Any) -> str:
    if isinstance(question, str):
        return question
    if isinstance(question, list):
        return "\n".join(
            str(getattr(item, "content", item))
            for item in question
            if getattr(item, "content", item)
        )
    return str(question)


def _latest_question_text(question: Any) -> str:
    if isinstance(question, list) and question:
        return str(getattr(question[-1], "content", question[-1]))
    return _question_to_text(question)


def _normalize_filters(question: Any, filters: Optional[ExtractedFilters]) -> Optional[ExtractedFilters]:
    text = _question_to_text(question)
    current = filters.to_query_dict() if filters else {}

    nomor_match = re.search(
        r"(?:nomor|no\.?)\s*(\d+[A-Za-z]?)\s*(?:/|tahun|thn\.?)\s*(\d{4})",
        text,
        flags=re.IGNORECASE,
    )
    if nomor_match:
        current["nomor_uu"] = f"Nomor {nomor_match.group(1)} Tahun {nomor_match.group(2)}"

    pasal_match = re.search(r"\bpasal\s+([0-9]+[A-Za-z]?)\b", text, flags=re.IGNORECASE)
    if pasal_match:
        current["pasal"] = pasal_match.group(1).upper()

    if isinstance(current.get("category"), str):
        normalized_category = current["category"].strip().lower().replace("-", " ")
        current["category"] = DOCUMENT_CATEGORY_ALIASES.get(normalized_category, normalized_category)

    lowered = text.lower()
    for alias, category in DOCUMENT_CATEGORY_ALIASES.items():
        if re.search(rf"\b{re.escape(alias)}\b", lowered):
            current.setdefault("category", category)
            break

    if not current:
        return None
    return ExtractedFilters(**current)


def _relaxed_filters(filters: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    relaxed = {
        key: value
        for key, value in filters.items()
        if key in {"nomor_uu", "pasal", "bab", "bagian"}
    }
    if relaxed and relaxed != filters:
        return relaxed
    return None


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
        question_text = _question_to_text(question)
        prompt_messages = router_prompt.invoke({"question": question_text})
        print(f"[Router] Prompt Messages: {prompt_messages}")
        result = _structured_llm.invoke(prompt_messages)
        filters = _normalize_filters(question, result.filters if result.filters else None)

        # Konversi ke dict/query format untuk logging
        filters_dict = filters.to_query_dict() if hasattr(filters, "to_query_dict") and filters else filters
        # print(f"[Router] apakah resultnya bisa di print: {result}")
        # print(f"[Router] Structured Output: Category: {result.category}, Filters: {filters_dict}, Reasoning: {result.reasoning}")

        logger.info("[Router] Category: %s | Filters: %s | Reason: %s", result.category, filters_dict, result.reasoning)
        # print(f"[Router] Category: {result.category} | Filters: {filters_dict} | Reason: {result.reasoning}")
        return {"question_category": result.category, "filters": filters}

    except Exception as exc:
        error_message = f"{type(exc).__name__}: {exc}"
        logger.exception(
            "Gagal melakukan structured output di router_node, fallback ke default category. Error: %s",
            error_message,
        )
        print(f"[Router][Error] Gagal ekstrak kategori dari LLM: {error_message}")
        return {"question_category": DEFAULT_CATEGORY, "filters": None}


def retrieve_node(state: GraphState) -> Dict[str, Any]:
    """
    Node LangGraph untuk melakukan pencarian dokumen ke Qdrant
    berdasarkan strategi top_k dan filter metadata dari state.
    """
    question = state.get("question", "")
    question_category = state.get("question_category", DEFAULT_CATEGORY)
    filters_obj = state.get("filters", None)
    
    query_text = _latest_question_text(question)

    print(f"[Retrieve] Question: {query_text} | Category: {question_category} | Filters: {filters_obj}")

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
            print(f"[Retrieve] Executing Filtered Search with filters: {filters_dict}")
            logger.info("[Retrieve] Executing Filtered Search with filters: %s", filters_dict)
            documents = vector_manager.search_with_filter(
                query_text,
                filters=filters_dict,
                top_k=top_k
            )
            if not documents:
                fallback_filters = _relaxed_filters(filters_dict)
                if fallback_filters:
                    print(f"[Retrieve] Retrying with relaxed filters: {fallback_filters}")
                    logger.info("[Retrieve] Retrying with relaxed filters: %s", fallback_filters)
                    documents = vector_manager.search_with_filter(
                        query_text,
                        filters=fallback_filters,
                        top_k=top_k
                    )
        else:
            logger.info("[Retrieve] Executing Pure Semantic Search (Top-K: %d)", top_k)
            documents = vector_manager.search(
                query_text,
                top_k=top_k
            )

    except Exception:
        logger.exception("Gagal melakukan vector search di retrieve_node.")
        return {"documents": []}

    logger.info("Ditemukan %d dokumen relevan.", len(documents))
    return {"documents": documents}
