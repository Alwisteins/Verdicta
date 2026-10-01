import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.graph.nodes import retrieve_node

# Test Case 1: Query dengan Filter Metadata
test_state_1 = {
    "question": "Siapa saja Aparatur Negara yang berhak mendapat tunjangan Hari Raya?",
    "filters": {
        "nomor_uu": "Nomor 9 Tahun 2026",
        "pasal": "3"
    }
}

print("=== TES 1: WITH METADATA FILTER ===")
result_1 = retrieve_node(test_state_1)
for doc in result_1["documents"]:
    print(f"-> [{doc.metadata['judul_dokumen']}] Pasal {doc.metadata['pasal']}")

# Test Case 2: Query Tanpa Filter (Pure Semantic Search)
test_state_2 = {
    "question": "PNS dapat tunjangan hari raya tidak?",
    "filters": None
}

print("\n=== TES 2: PURE SEMANTIC SEARCH ===")
result_2 = retrieve_node(test_state_2)
for doc in result_2["documents"]:
    print(f"-> [{doc.metadata['judul_dokumen']}] Pasal {doc.metadata['pasal']}")