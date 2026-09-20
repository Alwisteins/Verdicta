import argparse
import logging
import json
import re
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

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
    """Extract the JS string payload from self.__next_f.push([1,"..."]).

    The payload is a JS string literal with escaped quotes. We decode it as JSON
    after locating the quoted substring.
    """
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
    """Extract a JSON object substring starting at the opening '{' character."""
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


def extract_doc_cards(response: requests.Response) -> list[dict]:
    initial_data = extract_initial_data(response)
    cards = []
    if not initial_data:
        return cards

    results = initial_data.get("results", {})
    items = results.get("items", [])
    if not isinstance(items, list):
        return cards

    for item in items:
        doc_id = str(item.get("id", "")).strip()
        if not doc_id:
            continue
        cards.append(
            {
                "title": item.get("title", ""),
                "subtitle": item.get("subtitle", ""),
                "links": [
                    {
                        "doc_id": doc_id,
                        "href": f"/doc/{doc_id}",
                        "text": item.get("title", ""),
                    }
                ],
            }
        )

    return cards


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


def build_search_url(url: str, *, page: int | None = None, jenis_peraturan: int | None = None) -> str:
    parts = urlsplit(url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))

    if page is not None:
        query["page"] = str(page)
    elif "page" in query:
        query.pop("page", None)

    if jenis_peraturan is not None:
        query["jenis_peraturan"] = str(jenis_peraturan)

    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))

def _safe_filename(text: str, fallback: str) -> str:
    value = text.strip() if text else ""
    value = re.sub(r"[^A-Za-z0-9._-]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("._-")
    return value or fallback

def download_binary_file(url: str, destination: Path) -> bool:
    try:
        with SESSION.get(url, headers=HEADERS, timeout=60, stream=True) as response:
            response.raise_for_status()
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open("wb") as file_handle:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        file_handle.write(chunk)
        return True
    except requests.exceptions.RequestException:
        logger.warning("Gagal download file: %s", url)
        return False


def scrape_and_download_documents(
    url: str,
    *,
    limit_docs: int | None = None,
    jenis_peraturan: int | None = None,
    output_dir: str = "data/jdihn",
) -> list[dict]:
    seen_doc_ids: set[str] = set()
    downloaded_docs: list[dict] = []
    target_count = limit_docs if limit_docs and limit_docs > 0 else None
    page = 1
    base_output = Path(output_dir)

    while target_count is None or len(downloaded_docs) < target_count:
        page_url = build_search_url(url, page=page, jenis_peraturan=jenis_peraturan)
        response = fetch_html(page_url)
        if response is None:
            break

        summary = summarize_initial_data(response)
        logger.info("Page %d summary: %s", page, summary)

        items = extract_search_items(response)
        page_doc_ids = [str(item.get("id", "")).strip() for item in items if str(item.get("id", "")).strip()]
        overlap = [doc_id for doc_id in page_doc_ids if doc_id in seen_doc_ids]
        new_count = 0

        for item in items:
            doc_id = str(item.get("id", "")).strip()
            if not doc_id or doc_id in seen_doc_ids:
                continue

            seen_doc_ids.add(doc_id)
            new_count += 1
            
            download_url = f"https://jdihn.go.id/api/doc/{doc_id}/file?action=download";

            title = str(item.get("title", "")).strip() or f"doc-{doc_id}"
            safe_title = _safe_filename(title, f"doc_{doc_id}")
            destination_dir = base_output / f"jenis_{jenis_peraturan}" if jenis_peraturan is not None else base_output
            destination = destination_dir / f"{safe_title}.pdf"

            if download_binary_file(download_url, destination):
                downloaded_docs.append(
                    {
                        "doc_id": doc_id,
                        "title": title,
                        "download_url": download_url,
                        "file_path": str(destination),
                    }
                )
                logger.info("Downloaded doc_id=%s to %s", doc_id, destination)
            else:
                logger.warning("Download gagal untuk doc_id=%s", doc_id)

            if target_count is not None and len(downloaded_docs) >= target_count:
                break

        logger.info(
            "Page %d detail: first_id=%s last_id=%s overlap=%d new=%d downloaded=%d",
            page,
            page_doc_ids[0] if page_doc_ids else None,
            page_doc_ids[-1] if page_doc_ids else None,
            len(overlap),
            new_count,
            len(downloaded_docs),
        )

        if new_count == 0:
            break

        page += 1

    return downloaded_docs


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--limit-docs",
        type=int,
        default=None,
        help="Batas jumlah dokumen yang berhasil didownload",
    )
    parser.add_argument(
        "--jenis-peraturan",
        type=int,
        default=None,
        help="Filter jenis peraturan untuk URL JDIHN",
    )
    args = parser.parse_args()

    cards = scrape_and_download_documents(
        "https://jdihn.go.id/search?c=peraturan",
        limit_docs=args.limit_docs,
        jenis_peraturan=args.jenis_peraturan,
    )
    print("\n=== DOWNLOADED DOCS ===")
    if not cards:
        print("<none>")
        return

    for idx, card in enumerate(cards, start=1):
        print(f"{idx}. doc_id={card['doc_id']}")
        print(f"   title={card['title']}")
        print(f"   download_url={card['download_url']}")
        print(f"   file_path={card['file_path']}")


if __name__ == "__main__":
    main()
