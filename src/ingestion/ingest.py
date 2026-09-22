import json
import os
from typing import List
from langchain_core.documents import Document

def load_and_transform_json(json_path: str) -> List[Document]:
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"File tidak ditemukan: {json_path}")
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
      
    # 1. Mengambil metadata  
    source_file = data.get("source_file", "")
    root_metadata = data.get("metadata", {})
    category = root_metadata.get("category", "").strip()
    category_code = root_metadata.get("category_code", "")
    
    # 2. Ektrak judul & nomor uu
    filename = os.path.basename(source_file)
    judul_dokumen = os.path.splitext(filename)[0].replace("_", " ").strip()
    nomor_uu = judul_dokumen
    if category and judul_dokumen.lower().startswith(category.lower()):
        nomor_uu = judul_dokumen[len(category):].strip()
        
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

from src.ingestion.vectorstore import VectorStoreManager

def run_ingestion(json_filepath: str):
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