import argparse
import logging
import json
import re
import sys
from pathlib import Path
from typing import Union, List
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import requests
from bs4 import BeautifulSoup


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

SESSION = requests.Session()

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
    "Connection": "close",
}


def fetch_html(url: str) -> requests.Response | None:
    logger.info("Mengakses URL: %s", url)
    try:
        response = SESSION.get(url, headers=HEADERS, timeout=30)
    except requests.exceptions.RequestException:
        logger.warning("Request gagal untuk URL: %s", url)
        return None

    logger.info(
        "Response: status=%s final_url=%s content_type=%s content_length=%s",
        response.status_code,
        response.url,
        response.headers.get("Content-Type"),
        response.headers.get("Content-Length"),
    )
    return response


def extract_initial_data(response: requests.Response) -> dict | None:
    soup = BeautifulSoup(response.text or "", "html.parser")
    scripts = soup.find_all("script")

    for script in scripts:
        script_text = script.get_text(" ", strip=False) or ""
        if "initialData" not in script_text:
            continue

        payload = _extract_next_f_payload(script_text)
        if not payload:
            continue

        start = payload.find('{"initialData":')
        if start == -1:
            continue

        raw_object = _extract_json_object(payload, start)
        if not raw_object:
            continue

        try:
            parsed = json.loads(raw_object)
        except json.JSONDecodeError:
            logger.exception("Failed to json.loads extracted initialData object")
            continue

        return parsed.get("initialData")

    return None


def _extract_next_f_payload(script_text: str) -> str:
    marker = 'self.__next_f.push([1,'
    start = script_text.find(marker)
    if start == -1:
        return ""

    quote_start = script_text.find('"', start + len(marker))
    if quote_start == -1:
        return ""

    buf = []
    escape = False
    for idx in range(quote_start + 1, len(script_text)):
        ch = script_text[idx]
        if escape:
            buf.append(ch)
            escape = False
            continue
        if ch == "\\":
            buf.append(ch)
            escape = True
            continue
        if ch == '"':
            raw = '"' + "".join(buf) + '"'
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return ""
        buf.append(ch)

    return ""


def _extract_json_object(text: str, start_index: int) -> str:
    if start_index >= len(text) or text[start_index] != "{":
        return ""

    depth = 0
    in_string = False
    escape = False

    for idx in range(start_index, len(text)):
        ch = text[idx]

        if escape:
            escape = False
            continue

        if ch == "\\":
            escape = True
            continue

        if ch == '"':
            in_string = not in_string
            continue

        if in_string:
            continue

        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start_index : idx + 1]

    return ""


def summarize_initial_data(response: requests.Response) -> dict:
    initial_data = extract_initial_data(response) or {}
    results = initial_data.get("results", {}) if isinstance(initial_data, dict) else {}

    summary = {
        "mode": initial_data.get("mode"),
        "page": results.get("page"),
        "total": results.get("total"),
        "perPage": results.get("perPage"),
        "items": len(results.get("items", [])) if isinstance(results.get("items", []), list) else None,
        "keys": sorted(list(results.keys())) if isinstance(results, dict) else [],
    }
    return summary


def extract_search_items(response: requests.Response) -> list[dict]:
    initial_data = extract_initial_data(response)
    if not initial_data:
        return []

    results = initial_data.get("results", {})
    items = results.get("items", [])
    if not isinstance(items, list):
        return []

    return [item for item in items if isinstance(item, dict)]


def build_search_url(url: str, *, page: int | None = None, jenis_peraturan: int | str | None = None) -> str:
    parts = urlsplit(url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))

    if page is not None:
        query["page"] = str(page)
    elif "page" in query:
        query.pop("page", None)

    if jenis_peraturan is not None:
        query["jenis_peraturan"] = str(jenis_peraturan)

    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def _safe_filename(text: str, fallback: str, max_length: int = 240) -> str:
    value = text.strip() if text else ""
    value = re.sub(r"[^A-Za-z0-9._-]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("._-")
    if not value:
        value = fallback
    if len(value) > max_length:
        value = value[:max_length].rstrip("._-")
    return value


def download_binary_file(url: str, destination: Path) -> bool:
    try:
        abs_dest = destination.resolve()
        if sys.platform == "win32" and not str(abs_dest).startswith("\\\\?\\"):
            target_path = Path(f"\\\\?\\{abs_dest}")
        else:
            target_path = abs_dest

        with SESSION.get(url, headers=HEADERS, timeout=60, stream=True) as response:
            response.raise_for_status()
            target_path.parent.mkdir(parents=True, exist_ok=True)
            with target_path.open("wb") as file_handle:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        file_handle.write(chunk)
        return True
    except requests.exceptions.RequestException:
        logger.warning("Gagal download file: %s", url)
        return False
    except Exception:
        logger.exception("Gagal menyimpan file ke %s", destination)
        return False


def load_category_map() -> dict:
    map_path = Path("data/document_category_map.json")
    if not map_path.exists():
        logger.warning("Category map file not found at %s", map_path)
        return {}
    try:
        with map_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        logger.exception("Failed to load category map json")
        return {}


def scrape_and_download_documents(
    categories: Union[List[str], str] = "all",
    limit_per_category: int = 10,
    output_dir: str = "data/jdihn",
    base_url: str = "https://jdihn.go.id/search?c=peraturan",
) -> list[dict]:
    category_map = load_category_map()

    if isinstance(categories, str):
        if categories.lower() == "all":
            target_categories = list(category_map.keys())
        else:
            target_categories = [categories]
    elif isinstance(categories, list):
        target_categories = [str(c) for c in categories]
    else:
        target_categories = []

    all_downloaded_docs = []
    base_output = Path(output_dir)

    for cat_code in target_categories:
        if cat_code not in category_map:
            logger.warning("[Scraper] Category code '%s' not found in category map. Skipping.", cat_code)
            continue

        cat_name = category_map[cat_code]
        logger.info("[Scraper] Checking category %s (%s)...", cat_code, cat_name)

        seen_doc_ids: set[str] = set()
        category_downloaded: list[dict] = []
        page = 1

        while len(category_downloaded) < limit_per_category:
            page_url = build_search_url(base_url, page=page, jenis_peraturan=cat_code)
            response = fetch_html(page_url)
            if response is None:
                break

            items = extract_search_items(response)
            if not items:
                break

            page_doc_ids = [str(item.get("id", "")).strip() for item in items if str(item.get("id", "")).strip()]
            new_count = 0

            for item in items:
                if len(category_downloaded) >= limit_per_category:
                    break

                doc_id = str(item.get("id", "")).strip()
                if not doc_id or doc_id in seen_doc_ids:
                    continue

                seen_doc_ids.add(doc_id)
                new_count += 1

                download_url = f"https://jdihn.go.id/api/doc/{doc_id}/file?action=download"
                source_url = f"https://jdihn.go.id/doc/{doc_id}"

                title = str(item.get("title", "")).strip() or f"doc-{doc_id}"
                safe_title = _safe_filename(title, f"doc_{doc_id}")

                destination_dir = base_output / f"jenis_{cat_code}"
                destination = destination_dir / f"{safe_title}.pdf"

                if download_binary_file(download_url, destination):
                    doc_record = {
                        "category_code": cat_code,
                        "category_name": cat_name,
                        "doc_id": doc_id,
                        "title": title,
                        "filename": destination.name,
                        "file_path": str(destination),
                        "source_url": source_url,
                        "download_url": download_url,
                    }
                    category_downloaded.append(doc_record)
                    all_downloaded_docs.append(doc_record)
                    logger.info(
                        "[Scraper] Checking category %s... Progress: %d/%d items processed",
                        cat_code,
                        len(category_downloaded),
                        limit_per_category,
                    )
                else:
                    logger.warning("Download gagal untuk doc_id=%s", doc_id)

            if new_count == 0 or len(category_downloaded) >= limit_per_category:
                break

            page += 1

        logger.info("[Scraper] Finished category %s (%s). Total downloaded: %d", cat_code, cat_name, len(category_downloaded))

    return all_downloaded_docs


def main() -> None:
    parser = argparse.ArgumentParser(description="Scraper JDIHN dengan filter kategori dan limit")
    parser.add_argument(
        "--categories",
        type=str,
        default="all",
        help="Kategori peraturan (misal: '9' atau '9,11,12' atau 'all')",
    )
    parser.add_argument(
        "--limit-per-category",
        type=int,
        default=10,
        help="Batas jumlah dokumen per kategori",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/jdihn",
        help="Direktori output penyimpanan PDF",
    )
    args = parser.parse_args()

    if args.categories.lower() != "all":
        if "," in args.categories:
            categories = [c.strip() for c in args.categories.split(",") if c.strip()]
        else:
            categories = args.categories.strip()
    else:
        categories = "all"

    cards = scrape_and_download_documents(
        categories=categories,
        limit_per_category=args.limit_per_category,
        output_dir=args.output_dir,
    )
    print("\n=== DOWNLOADED DOCS ===")
    if not cards:
        print("<none>")
        return

    for idx, card in enumerate(cards, start=1):
        print(f"{idx}. [{card['category_code']} - {card['category_name']}] doc_id={card['doc_id']}")
        print(f"   title={card['title']}")
        print(f"   file_path={card['file_path']}")
        print(f"   source_url={card['source_url']}")


if __name__ == "__main__":
    main()
