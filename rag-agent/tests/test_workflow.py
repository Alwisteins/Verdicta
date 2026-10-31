import pytest
import uuid
from langchain_core.messages import HumanMessage, AIMessage
from src.graph.workflow import app


@pytest.mark.parametrize(
    "history_messages, follow_up, expected_category",
    [
        (
            [
                HumanMessage(content="Jelaskan PERPPU Nomor 1 Tahun 2022 tentang pembentukan KPU Provinsi di Papua."),
                AIMessage(content="PERPPU Nomor 1 Tahun 2022 mengatur pembentukan KPU di provinsi baru Papua seperti Papua Selatan, Papua Tengah, Papua Pegunungan, dan Papua Barat Daya (Pasal 10A)."),
            ],
            "Kalau Pasal 10A yang tadi dibahas, bagaimana bunyi lengkapnya terkait pembentukan KPU Provinsi di Papua?",
            "specific_article",
        ),
        (
            [
                HumanMessage(content="Apa itu Komoditas SDA Strategis menurut peraturan pemerintah?"),
                AIMessage(content="Komoditas SDA Strategis adalah hasil alam yang menguasai hajat hidup orang banyak dan memiliki nilai ekonomi tinggi bagi negara."),
            ],
            "Lalu bagaimana tata kelola ekspornya diatur dalam peraturan yang tadi? Apakah ada kewajiban khusus?",
            "general_inquiry",
        ),
    ],
)
def test_workflow_routing_and_retrieval(history_messages: list, follow_up: str, expected_category: str):
    thread_id = f"test-memory-{expected_category}-{uuid.uuid4().hex[:6]}"
    config = {"configurable": {"thread_id": thread_id}}

    # Inject history percakapan ke memory checkpointer
    app.update_state(
        config,
        {
            "question": history_messages,
        }
    )

    # Eksekusi workflow untuk pertanyaan follow up
    result_state = app.invoke(
        {
            "question": HumanMessage(content=follow_up),
            "filters": None,
            "documents": [],
            "generation": "",
        },
        config,
    )

    # =========================================================================
    # LOGGING KUSTOM KHUSUS TEST WORKFLOW
    # =========================================================================
    print("\n" + "=" * 80)
    print(f"📌 TEST CASE: [{expected_category.upper()}] - Thread ID: {thread_id}")
    print("=" * 80)

    # 1. History Percakapan
    print("\n📜 [1] HISTORY PERCAKAPAN:")
    for idx, msg in enumerate(history_messages, start=1):
        role = "User" if isinstance(msg, HumanMessage) else "AI"
        print(f"   {idx}. {role}: {msg.content}")

    # 2. Pertanyaan Follow-up
    print(f"\n❓ [2] PERTANYAAN FOLLOW-UP USER:")
    print(f"   {follow_up}")

    # 3. Question Category
    category = result_state.get("question_category", "N/A")
    print(f"\n🏷️  [3] QUESTION CATEGORY: {category}")

    # 4. Documents beserta Isinya
    docs = result_state.get("documents", [])
    print(f"\n📚 [4] DOCUMENTS RETRIEVED ({len(docs)} dokumen):")
    if not docs:
        print("   (Tidak ada dokumen yang ditemukan)")
    else:
        for idx, doc in enumerate(docs, start=1):
            metadata = getattr(doc, "metadata", {})
            judul = metadata.get("judul_dokumen", "N/A")
            pasal = metadata.get("pasal", "N/A")
            score = (
                getattr(doc, "score", None)
                or metadata.get("score")
                or "N/A"
            )
            print(f"   --- Dokumen #{idx} ---")
            print(f"   Judul : {judul}")
            print(f"   Pasal : {pasal}")
            print(f"   Score : {score}\n")

    # 5. Jawaban LLM (Field Generation)
    generation = result_state.get("generation", "N/A")
    print(f"🤖 [5] JAWABAN LLM (GENERATION):")
    print(f"   {generation}")
    print("=" * 80 + "\n")

    # Assertions
    assert "question_category" in result_state
    assert "documents" in result_state
