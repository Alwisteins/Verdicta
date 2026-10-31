import argparse
import logging
import json
import re
from pathlib import Path
from typing import List, Optional, Union

from src.ingestion.scrapper import scrape_and_download_documents
from src.ingestion.chunker import (
    iter_pdf_paths,
    extract_raw_text,
    split_zones,
    parse_batang_tubuh,
    clean_pasal_final,
    validate_parsing,
    get_debug_metadata,
)
from src.ingestion.ingest import load_and_transform_json
from src.retrieval.vector import VectorStoreManager, COLLECTION_NAME, EMBEDDING_DIMENSION, qdrant_models

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

def scrape_documents(categories: Union[str, List[str]], limit_per_category: int, output_dir: str) -> List[Path]:
    logger.info("==================================================")
    logger.info("=== STEP 1: SCRAPER EXECUTION ===")
    logger.info("==================================================")
    
    downloaded_docs = scrape_and_download_documents(
        categories=categories,
        limit_per_category=limit_per_category,
        output_dir=output_dir,
        )
    logger.info("[Scraper] Total downloaded documents: %d", len(downloaded_docs))
    return downloaded_docs

def parse_and_chunk_documents(jdihn_dir: str, parsing_output_dir: str, auto_cleanup_pdf: bool) -> None:
    logger.info("==================================================")
    logger.info("=== STEP 2 & 3: PARSING, CHUNKING & PDF CLEANUP ===")
    logger.info("==================================================")

    pdf_paths = iter_pdf_paths(root_path=str(jdihn_dir))
    total_pdfs = len(pdf_paths)
    if total_pdfs == 0:
        logger.warning("[Pipeline] Tidak ada file PDF ditemukan di %s untuk diparsing.", jdihn_dir)
    else:
        for idx, pdf_path in enumerate(pdf_paths, start=1):
            logger.info("[%d/%d] [Parsing] Converting %s -> JSON", idx, total_pdfs, pdf_path.name)
            try:
                raw_text = extract_raw_text(str(pdf_path))
                zones = split_zones(raw_text)
                pasal_list = parse_batang_tubuh(zones["batang_tubuh"])
                pasal_list = clean_pasal_final(pasal_list)
                warnings = validate_parsing(pasal_list, zones)
                category_code: Optional[int] = None
                m = re.search(r"jenis_(\d+)", str(pdf_path))
                if m:
                    try:
                        category_code = int(m.group(1))
                    except ValueError:
                        category_code = None
                metadata = get_debug_metadata(pasal_list, zones, warnings, pdf_path=pdf_path, category_code=category_code)

                result_data = {
                    "source_file": str(pdf_path),
                    "metadata": metadata,
                    "pasal_list": pasal_list,
                }

                out_file = parsing_path / f"{pdf_path.stem}_parsed.json"
                out_file.write_text(json.dumps(result_data, ensure_ascii=False, indent=2), encoding="utf-8")
                logger.info("[%d/%d] [Parsing] Success parsed & saved to %s", idx, total_pdfs, out_file.name)

            except Exception as exc:
                logger.error("[%d/%d] [Parsing Error] Gagal memparsing file %s: %s", idx, total_pdfs, pdf_path.name, exc, exc_info=True)
            finally:
                if auto_cleanup_pdf:
                    # Step 3: Immediate PDF Cleanup (Ephemeral Storage)
                    try:
                        if pdf_path.exists():
                            pdf_path.unlink()
                            logger.info("[%d/%d] [Cleanup] Deleted temp PDF: %s", idx, total_pdfs, pdf_path.name)
                    except Exception as cleanup_exc:
                        logger.warning("[%d/%d] [Cleanup Warning] Gagal menghapus PDF %s: %s", idx, total_pdfs, pdf_path.name, cleanup_exc)

def reset_qdrant_collection():
    logger.info("==================================================")
    logger.info("=== STEP 4: QDRANT COLLECTION RESET ===")
    logger.info("==================================================")
    logger.info("[Qdrant] Resetting collection '%s'...", COLLECTION_NAME)
    vector_manager = VectorStoreManager()
    client = vector_manager.client
    
    if client.collection_exists(COLLECTION_NAME):
        client.delete_collection(collection_name=COLLECTION_NAME)
        logger.info("[Qdrant] Existing collection '%s' deleted successfully.", COLLECTION_NAME)
    
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=qdrant_models.VectorParams(
            size=EMBEDDING_DIMENSION,
            distance=qdrant_models.Distance.COSINE
        )
    )
    logger.info("[Qdrant] Collection '%s' recreated fresh.", COLLECTION_NAME)

def ingest_documents_to_qdrant(parsing_path: Path) -> int:
    logger.info("==================================================")
    logger.info("=== STEP 5: BATCH INGESTION TO QDRANT ===")
    logger.info("==================================================")

    json_files = sorted(parsing_path.glob("*_parsed.json"))
    total_json = len(json_files)
    if total_json == 0:
        logger.warning("[Ingest] Tidak ada file JSON di %s untuk di-ingest.", parsing_path)
        return

    vector_manager = VectorStoreManager()
    total_documents_pushed = 0

    for idx, json_file in enumerate(json_files, start=1):
        logger.info("[%d/%d] [Ingest] Memproses file JSON: %s", idx, total_json, json_file.name)
        try:
            documents = load_and_transform_json(str(json_file))
            if documents:
                vector_manager.add_documents(documents)
                total_documents_pushed += len(documents)
                logger.info("[%d/%d] [Ingest] Pushed %d documents from %s to Qdrant", idx, total_json, len(documents), json_file.name)
            else:
                logger.warning("[%d/%d] [Ingest] Tidak ada dokumen valid ditemukan di %s", idx, total_json, json_file.name)
        except Exception as exc:
            logger.error("[%d/%d] [Ingest Error] Gagal meng-ingest file %s: %s", idx, total_json, json_file.name, exc, exc_info=True)
    
    return total_documents_pushed

def run_pipeline(
    categories: Union[str, List[str]] = ["9", "10", "11", "12", "27", "36", "57", "58", "59"],
    limit_per_category: int = 5,
    jdihn_dir: str = "data/jdihn",
    parsing_output_dir: str = "data/parsing-output",
):
    """Menjalankan alur kerja ingestion pipeline secara end-to-end secara sekuensial dan terisolasi."""
    jdihn_path = Path(jdihn_dir)
    parsing_path = Path(parsing_output_dir)
    parsing_path.mkdir(parents=True, exist_ok=True)

    # --- Step 1: Scraper Execution ---
    # scrape_documents(categories=categories, limit_per_category=limit_per_category, output_dir=str(jdihn_path))

    # --- Step 2 & 3: Parsing/Chunking & Immediate PDF Cleanup ---
    # parse_and_chunk_documents(jdihn_dir=str(jdihn_path), parsing_output_dir=str(parsing_path), auto_cleanup_pdf=True)

    # --- Step 4: Qdrant Collection Reset ---
    reset_qdrant_collection()

    # --- Step 5: Batch Ingestion ---
    total_documents_pushed = ingest_documents_to_qdrant(parsing_path=parsing_path)

    logger.info("==================================================")
    logger.info("=== PIPELINE SELESAI. Total dokumen di-ingest: %d ===", total_documents_pushed)
    logger.info("==================================================")


def main():
    parser = argparse.ArgumentParser(description="Orchestrator pipeline ingestion data JDIHN ke Qdrant")
    parser.add_argument(
        "--categories",
        type=str,
        default="9,10,11,12,27,36,57,58,59",
        help="Kategori peraturan (pisahkan dengan koma atau 'all')",
    )
    parser.add_argument(
        "--limit-per-category",
        type=int,
        default=2,
        help="Batas jumlah dokumen per kategori untuk didownload",
    )
    parser.add_argument(
        "--jdihn-dir",
        type=str,
        default="data/jdihn",
        help="Direktori penyimpanan sementara file PDF",
    )
    parser.add_argument(
        "--parsing-output-dir",
        type=str,
        default="data/parsing-output",
        help="Direktori penyimpanan file JSON hasil parsing",
    )
    args = parser.parse_args()

    if args.categories.lower() != "all":
        if "," in args.categories:
            categories = [c.strip() for c in args.categories.split(",") if c.strip()]
        else:
            categories = [args.categories.strip()]
    else:
        categories = "all"

    run_pipeline(
        categories=categories,
        limit_per_category=args.limit_per_category,
        jdihn_dir=args.jdihn_dir,
        parsing_output_dir=args.parsing_output_dir,
    )


if __name__ == "__main__":
    main()
