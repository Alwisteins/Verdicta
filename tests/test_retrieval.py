import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.retrieval.vector import VectorStoreManager
from src.graph.nodes import retrieve_node

def test_retrieval_with_metadata_filter():
    vector_manager = VectorStoreManager()
    query = "Siapa saja Aparatur Negara yang berhak mendapat tunjangan Hari Raya?"
    filters = {
        "nomor_uu": "Nomor 9 Tahun 2026",
        "pasal": "3"
    }

    print("=" * 60)
    print(f"QUERY  : {query}")
    print(f"FILTER : {filters}")
    print("=" * 60)

    # 1. Test Direct Vector Store Search
    print("\n--- [1] MENGAMBIL HASIL DARI VectorStoreManager ---")
    results = vector_manager.search_documents(query=query, k=2, filter_dict=filters)
    assert len(results) >= 0

    print(f"Jumlah dokumen ditemukan: {len(results)}")
    for i, doc in enumerate(results, 1):
        print(f"\n[Dokumen {i}]")
        # Menampilkan isi teks dan metadata jika ada
        content = getattr(doc, 'page_content', doc)
        metadata = getattr(doc, 'metadata', None)
        print(f"Isi Dokumen : {content}")
        if metadata:
            print(f"Metadata    : {metadata}")

    # 2. Test retrieve_node from graph nodes
    print("\n--- [2] MENGAMBIL HASIL DARI retrieve_node (Graph) ---")
    state = {
        "query": query,
        "filter_dict": filters,
        "k": 2
    }
    node_result = retrieve_node(state)
    assert "documents" in node_result

    node_docs = node_result.get("documents", [])
    print(f"Jumlah dokumen dari Node State: {len(node_docs)}")
    for i, doc in enumerate(node_docs, 1):
        print(f"\n[Dokumen Node {i}]")
        content = getattr(doc, 'page_content', doc)
        metadata = getattr(doc, 'metadata', None)
        print(f"Isi Dokumen : {content}")
        if metadata:
            print(f"Metadata    : {metadata}")

    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_retrieval_with_metadata_filter()
    print("Retrieval and metadata filter tests passed successfully.")