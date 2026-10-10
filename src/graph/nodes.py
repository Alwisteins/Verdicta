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
RETRIEVAL_SCORE_THRESHOLD = 0.40
DEFAULT_CATEGORY: CategoryType = "general_inquiry"
NO_RELEVANT_DOCUMENTS_RESPONSE = (
    "Maaf, dokumen tidak tersedia di database dan informasi spesifik terkait "
    "hal tersebut tidak ditemukan."
)


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


def _document_score(doc: Any) -> Optional[float]:
    metadata = getattr(doc, "metadata", {}) or {}
    score = (
        getattr(doc, "score", None)
        or metadata.get("score")
        or metadata.get("_score")
        or metadata.get("relevance_score")
    )
    try:
        return float(score)
    except (TypeError, ValueError):
        return None


def _filter_relevant_documents(documents: list[Any]) -> list[Any]:
    relevant_documents = [
        doc
        for doc in documents
        if (_document_score(doc) or 0.0) >= RETRIEVAL_SCORE_THRESHOLD
    ]
    logger.info(
        "[Retrieve] Keeping %d/%d documents with score >= %.2f",
        len(relevant_documents),
        len(documents),
        RETRIEVAL_SCORE_THRESHOLD,
    )
    return relevant_documents


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
        # print(f"[Router] Prompt Messages: {prompt_messages}")
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

    # print(f"[Retrieve] Question: {query_text} | Category: {question_category} | Filters: {filters_obj}")

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
            # print(f"[Retrieve] Executing Filtered Search with filters: {filters_dict}")
            logger.info("[Retrieve] Executing Filtered Search with filters: %s", filters_dict)
            documents = vector_manager.search_with_filter(
                query_text,
                filters=filters_dict,
                top_k=top_k
            )
            if not documents:
                fallback_filters = _relaxed_filters(filters_dict)
                if fallback_filters:
                    # print(f"[Retrieve] Retrying with relaxed filters: {fallback_filters}")
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

    documents = _filter_relevant_documents(documents)

    logger.info("Ditemukan %d dokumen relevan.", len(documents))
    return {"documents": documents}

GENERATION_SYSTEM_PROMPT = """
Anda adalah Verdicta, asisten AI spesialis hukum Indonesia yang presisi, objektif, dan terpercaya. Tugas Anda adalah menjawab pertanyaan hukum pengguna berdasarkan HANYA pada konteks dokumen perundang-undangan yang disediakan dari hasil pencarian (Retrieval Context).

### ATURAN UTAMA & BATASAN KETAT (CRITICAL):

1. STRICT GROUNDEDNESS & ZERO HALLUCINATION (HUKUM MUTLAK)
- Jawaban Anda WAJIB 100% didasarkan pada dokumen hukum yang ada dalam [DOKUMEN RETRIEVAL].
- DILARANG KERAS mengarang, mengasumsi, mengestrapolasi, atau menggunakan pengetahuan di luar [DOKUMEN RETRIEVAL].
- Jika [DOKUMEN RETRIEVAL] kosong atau tidak memuat informasi yang cukup untuk menjawab pertanyaan pengguna, Anda WAJIB menjawab secara jujur:
  "Maaf, berdasarkan dokumen perundang-undangan yang tersedia dalam basis data saat ini, informasi spesifik mengenai hal tersebut tidak ditemukan."
- DILARANG memberikan argumen hukum atau kesimpulan pribadi yang tidak didukung secara eksplisit oleh teks pasal.

2. VERBATIM CITATION (KUTIPAN OTENTIK & PRESISI)
- Dalam mengutip pasal, ayat, atau ketentuan hukum, Anda WAJIB menggunakan teks ASLI kata-demi-kata (VERBATIM) sebagaimana tertulis dalam [DOKUMEN RETRIEVAL].
- DILARANG memparafasekan, mengubah susunan kata, menyingkat, atau merangkum isi teks pasal pada bagian kutipan.
- WAJIB menyertakan identitas lengkap dokumen pada kutipan (contoh: Nama UU/Peraturan, Nomor, Tahun, Bab, Pasal, dan Ayat).

3. KESEDERHANAAN BHS & AKSESIBILITAS (UNTUK AWAM)
- Struktur jawaban harus mudah dipahami oleh orang awam yang tidak memiliki latar belakang hukum.
- Gunakan bahasa Indonesia sehari-hari yang lugas, komunikatif, dan bebas dari jargon hukum yang membingungkan. Jika ada istilah hukum khusus (misal: "extradition", "delik aduan"), jelaskan maknanya secara sederhana.
- Pisahkan dengan tegas antara "Penjelasan Ringkas (Bahasa Awam)" dan "Dasar Hukum Resmi (Verbatim)".

---

### STRUKTUR FORMAT JAWABAN (WAJIB DIIKUTI):

Gunakan format Markdown berikut untuk menyusun jawaban:

### 💡 Penjelasan Ringkas
[Tuliskan penjelasan atau jawaban langsung atas pertanyaan pengguna menggunakan bahasa yang sederhana, mudah dimengerti, dan langsung ke intinya.]

---

### 📜 Dasar Hukum Resmi
[Sebutkan kutipan VERBATIM dari pasal/ayat yang relevan dari [DOKUMEN RETRIEVAL].]

* **[Nama Dokumen Hukum, Nomor & Tahun]**
  * **[Pasal X Ayat Y]:**
    > "[Tuliskan isi pasal/ayat secara persis/verbatim tanpa mengubah satu kata pun dari dokumen retrieval]"

---

### ⚠️ Catatan Tambahan (Opsional)
[Berikan catatan jika ada syarat, pengecualian, atau batas keberlakuan yang secara eksplisit tertulis di dalam dokumen.]
"""

def generation_node(state: GraphState) -> Dict[str, Any]:
    """
    Node LangGraph untuk menghasilkan jawaban akhir dari LLM
    berdasarkan pertanyaan, dokumen yang diambil, dan filter metadata.
    """
    question = state.get("question", "")
    documents = state.get("documents", [])
    filters_obj = state.get("filters", None)

    # Konversi ExtractedFilters ke Dict jika valid
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
        question_text = _question_to_text(question)

        if not documents:
            logger.info(
                "[Generation] Tidak ada dokumen dengan score >= %.2f. Mengembalikan fallback.",
                RETRIEVAL_SCORE_THRESHOLD,
            )
            return {"generation": NO_RELEVANT_DOCUMENTS_RESPONSE}

        user_prompt = [f"[PERTANYAAN PENGGUNA]\n{question_text}"]

        doc_contents = "\n\n".join(
            f"Dokumen #{idx + 1}:\n{getattr(doc, 'page_content', str(doc))}"
            for idx, doc in enumerate(documents)
        )
        user_prompt.append(f"[DOKUMEN RETRIEVAL]\n{doc_contents}")

        if filters_dict:
            user_prompt.append(f"[FILTER METADATA]\n{filters_dict}")

        # Gemini tidak mendukung model prefilling: turn terakhir harus user/function response.
        prompt_messages = [
            {"role": "system", "content": GENERATION_SYSTEM_PROMPT},
            {"role": "user", "content": "\n\n".join(user_prompt)},
        ]

        generation_result = llm.invoke(prompt_messages)
        generation_text = getattr(generation_result, "content", str(generation_result))
        return {"generation": generation_text}

    except Exception as exc:
        error_message = f"{type(exc).__name__}: {exc}"
        print(f"[Generation][Error] Gagal menghasilkan jawaban di generation_node: {error_message}")
        logger.error("Gagal menghasilkan jawaban di generation_node. Error: %s", error_message)
        return {"generation": "Maaf, terjadi kesalahan saat menghasilkan jawaban."}
