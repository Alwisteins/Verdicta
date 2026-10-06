import json
import os
import re
from typing import List
from langchain_core.documents import Document

from src.ingestion.chunker import resolve_document_category


def _extract_nomor_uu(judul_dokumen: str) -> str:
    nomor_match = re.search(
        r"\bnomor\s+(\d+[A-Za-z]?)\s+tahun\s+(\d{4})\b",
        judul_dokumen,
        flags=re.IGNORECASE,
    )
    if nomor_match:
        return f"Nomor {nomor_match.group(1)} Tahun {nomor_match.group(2)}"
    return judul_dokumen

def load_and_transform_json(json_path: str) -> List[Document]:
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"File tidak ditemukan: {json_path}")
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
      
    # 1. Mengambil metadata  
    source_file = data.get("source_file", "")
    root_metadata = data.get("metadata", {})
    resolved_category = resolve_document_category(source_file)
    category = (resolved_category.get("category") or root_metadata.get("category") or "").strip()
    category_code = resolved_category.get("category_code") or root_metadata.get("category_code", "")
    
    # 2. Ektrak judul & nomor uu
    filename = os.path.basename(source_file)
    judul_dokumen = os.path.splitext(filename)[0].replace("_", " ").strip()
    nomor_uu = _extract_nomor_uu(judul_dokumen)
        
    documents = []
    
    # 3. Iterasi pasal dan buat object document
    for item in data.get("pasal_list", []):
        isi_pasal = item.get("isi_pasal", "").strip()
        if not isi_pasal:
            continue
        
        pasal_num = str(item.get("pasal", "")).strip()
        bab = (item.get("bab") or "").strip()
        bab_judul = (item.get("bab_judul") or "").strip()
        bagian = (item.get("bagian") or "").strip()
        bagian_judul = (item.get("bagian_judul") or "").strip()
        
        # susun header injection untuk page_content
        header_parts = [f"[{judul_dokumen}]"]
        if bab:
            header_parts.append(f"[Bab {bab}: {bab_judul}]" if bab_judul else f"[Bab {bab}]")
        if bagian:
            header_parts.append(f"[Bagian {bagian}: {bagian_judul}]" if bagian_judul else f"[Bagian {bagian}]")
        header_parts.append(f"[Pasal {pasal_num}]")
        
        header_prefix = " ".join(header_parts)
        formatted_page_content = f"{header_prefix}\n{isi_pasal}"
        
        # Susun metadata
        doc_metadata = {
            "judul_dokumen": judul_dokumen,
            "nomor_uu": nomor_uu,
            "category": category,
            "category_code": category_code,
            "pasal": pasal_num,
            "bab": bab or "",
            "bab_judul": bab_judul or "",
            "bagian": bagian or "",
            "bagian_judul": bagian_judul or "",
            "source_file": source_file
        }
        
        documents.append(
            Document(
                page_content=formatted_page_content,
                metadata=doc_metadata
            )
        )
        
    return documents

def run_ingestion(json_filepath: str):
    from src.retrieval.vector import VectorStoreManager

    print(f"Membaca file: {json_filepath}...")
    documents = load_and_transform_json(json_filepath)
    print(f"Berhasil memproses {len(documents)} pasal.")

    print("Mengirim dokumen ke Qdrant...")
    vector_manager = VectorStoreManager()
    vector_manager.add_documents(documents)
    print("Ingestion selesai!")

if __name__ == "__main__":
    # Jalankan tes ingestion untuk 1 file JSON contoh
    sample_json = "data/parsing-output/Peraturan_Pemerintah_Nomor_31_Tahun_2026_parsed.json"
    run_ingestion(sample_json)
