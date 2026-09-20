import json
import re
from pathlib import Path
from typing import Optional


PAGE_BREAK = "__PAGE_BREAK__"

# ---------------------------------------------------------------------------
# Regex constants
# ---------------------------------------------------------------------------

HEADER_FOOTER_PATTERNS = [
    re.compile(r"^\s*SALINAN\s*$", re.IGNORECASE),
    re.compile(r"^\s*PRESIDEN\s*$", re.IGNORECASE),
    re.compile(r"^\s*REP[UJI]BLIK\s+INDONESI[A]?\.*\s*$", re.IGNORECASE),
    re.compile(r"^\s*-\s*\d+\s*-\s*$"),
    re.compile(r"^\s*SK\s+No\.?\s*\w+\s*$", re.IGNORECASE),
    re.compile(r"^\s*[A-Z]\s*$"),
    re.compile(r"^\s*ttn\s*$", re.IGNORECASE),
]

CONTINUATION_MARKER_PATTERN = re.compile(
    r"^\s*.+(?:\.{3,}|(?:\.\s*){3,})\s*$",
    re.IGNORECASE,
)

LANDMARK_PATTERN = re.compile(r"\b(MEMUTUSKAN|MENETAPKAN)\b", re.IGNORECASE)

BODY_START_PATTERN = re.compile(
    r"^(\s*BAB\s+I\b|\s*Pasal\s*1\b)", re.MULTILINE | re.IGNORECASE
)

EXPLANATION_PATTERN = re.compile(
    r"^(\s*(?:PENJELASAN\s+ATAS\b|PENJELASAN\s*$|(?:I|1|l)\.\s*UMUM\s*$|"
    r"(?:II|ll|I\s*I|l\s*I|11)\.\s*PASAL\s+DEMI\s+PASAL\s*$))",
    re.MULTILINE | re.IGNORECASE,
)

LAMPIRAN_PATTERN = re.compile(
    r"^(\s*LAMP[I1]RAN(?:\s+(?:[IVXLCDM\d]+|[A-Z\s\-_.:()]+))?\s*$)",
    re.MULTILINE | re.IGNORECASE,
)

BAB_PATTERN = re.compile(
    r"^\s*BAB\s+([IVXLCDM\d]+|[A-Z0-9]+)\.?\s*$",
    re.IGNORECASE,
)

BAGIAN_PATTERN = re.compile(
    r"^\s*Bagian\s+([A-Za-z0-9\s-]+?)\.?\s*$",
    re.IGNORECASE,
)

PARAGRAF_PATTERN = re.compile(
    r"^\s*Paragraf\s+([A-Za-z0-9\s-]+?)\.?\s*$",
    re.IGNORECASE,
)

PASAL_PATTERN = re.compile(
    r"^\s*Pasal\s*([0-9OIl]+[A-Z]?)\.?\s*$",
    re.IGNORECASE,
)

CLOSING_PATTERN = re.compile(
    r"^\s*(Ditetapkan\s+di|Diundangkan\s+di|Disahkan\s+di|Agar\s+setiap\s+orang\s+mengetahuinya)\b",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# 1. Mapper — ambil semua PDF JDIH
# ---------------------------------------------------------------------------

def iter_pdf_paths(root_path: str = "data/jdihn") -> list[Path]:
    """Ambil semua PDF JDIH secara rekursif (Poin 1)."""
    return sorted(Path(root_path).rglob("*.pdf"))


# ---------------------------------------------------------------------------
# 2. Extractor & Cleaner
# ---------------------------------------------------------------------------

def _normalize_line_endings(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _is_noise_line(line: str) -> bool:
    if any(pattern.match(line) for pattern in HEADER_FOOTER_PATTERNS):
        return True
    return bool(CONTINUATION_MARKER_PATTERN.match(line))


def _normalize_pasal_number(value: str) -> str:
    return value.translate(str.maketrans({"O": "0", "o": "0", "I": "1", "l": "1"}))


def _normalize_bab_roman(value: str) -> str:
    normalized = re.sub(r"\s+", "", value.upper())
    # OCR umum pada angka Romawi: IV kadang terbaca TV.
    if normalized == "TV":
        return "IV"
    return normalized


def _normalize_structural_heading(line: str) -> str:
    bab_match = re.match(r"^(\s*)BAB\s*([IVXLCDMTV]+)\s*$", line, re.IGNORECASE)
    if bab_match:
        return f"{bab_match.group(1)}BAB {_normalize_bab_roman(bab_match.group(2))}"

    pasal_match = re.match(r"^(\s*)Pasal\s*([0-9OIl]+(?:\s+[0-9OIl]+)*[A-Z]?)\s*$", line, re.IGNORECASE)
    if pasal_match:
        raw_num = pasal_match.group(2).replace(" ", "")
        return f"{pasal_match.group(1)}Pasal {_normalize_pasal_number(raw_num)}"

    return line


def _pre_merge_split_pasal_lines(text: str) -> str:
    """Menggabungkan baris 'Pasal' dan nomor pasal yang terpisah baris atau terpisah spasi antar angka akibat OCR/layout."""
    lines = text.split("\n")
    merged = []
    i = 0
    n = len(lines)
    while i < n:
        line_s = lines[i].strip()
        if re.match(r"^Pasal\.?$", line_s, re.IGNORECASE) and i + 1 < n:
            next_s = lines[i + 1].strip()
            if re.match(r"^([0-9OIl]+(?: [0-9OIl]+)*[A-Z]?)\.?$", next_s):
                raw_num = re.match(r"^([0-9OIl]+(?: [0-9OIl]+)*[A-Z]?)\.?$", next_s).group(1).replace(" ", "")
                num = _normalize_pasal_number(raw_num)
                indent = re.match(r"^(\s*)", lines[i]).group(1)
                merged.append(f"{indent}Pasal {num}")
                i += 2
                continue

        merged.append(lines[i])
        i += 1
    return "\n".join(merged)


def _clean_and_normalize_text(text: str) -> str:
    normalized = _normalize_line_endings(text)
    pre_merged = _pre_merge_split_pasal_lines(normalized)
    cleaned_lines = [
        _normalize_structural_heading(line.rstrip())
        for line in pre_merged.split("\n")
        if not _is_noise_line(line.rstrip())
    ]
    return "\n".join(cleaned_lines).strip()


def _extract_pages_with_pdfplumber(pdf_path: str) -> list[str]:
    import pdfplumber

    pages: list[str] = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_number, page in enumerate(pdf.pages, start=1):
                try:
                    text = page.extract_text(layout=True)
                except Exception as exc:  # noqa: BLE001 - log & lanjut, jangan crash
                    print(f"  [WARN] Gagal extract halaman {page_number} di {pdf_path}: {exc}")
                    continue
                if text:
                    pages.append(text)
    except Exception as exc:  # noqa: BLE001
        print(f"[ERROR] Gagal membuka {pdf_path}: {exc}")
        return []

    return pages


def extract_raw_text(pdf_path: str) -> str:
    """Ekstrak teks PDF, jaga layout, lalu lakukan normalisasi awal (Poin 2-5)."""
    pages = _extract_pages_with_pdfplumber(pdf_path)
    full_text = [_clean_and_normalize_text(page) for page in pages if page.strip()]
    return f"\n{PAGE_BREAK}\n".join(full_text)


# ---------------------------------------------------------------------------
# 3. Zone Splitter
# ---------------------------------------------------------------------------

def _find_body_start(text: str) -> int:
    """Cari titik awal Batang Tubuh, lewati mukadimah (Poin 7)."""
    landmark_match = LANDMARK_PATTERN.search(text)
    search_start = landmark_match.end() if landmark_match else 0

    start_match = BODY_START_PATTERN.search(text, search_start)
    if not start_match and search_start > 0:
        # Fallback: cari dari awal dokumen jika tidak ketemu setelah landmark.
        start_match = BODY_START_PATTERN.search(text)

    return start_match.start() if start_match else 0


def _find_zone_anchor(pattern: re.Pattern, text: str, start: int) -> Optional[int]:
    """Cari posisi awal kemunculan pertama sebuah anchor zona, atau None."""
    match = pattern.search(text, pos=start)
    return match.start() if match else None


def split_zones(raw_text: str) -> dict:
    """Memisahkan Batang Tubuh, Penjelasan, dan Lampiran (Poin 6, 7 & 18).

    Pendekatan: kumpulkan semua anchor zona yang ditemukan, urutkan
    berdasarkan posisi kemunculan di teks, lalu potong teks berurutan
    di antara anchor-anchor tersebut. Ini menghindari percabangan
    if/elif/else kombinatorial yang tumbuh seiring bertambahnya jenis zona.
    """
    body_start = _find_body_start(raw_text)

    explanation_start = _find_zone_anchor(EXPLANATION_PATTERN, raw_text, body_start)
    lampiran_start = _find_zone_anchor(LAMPIRAN_PATTERN, raw_text, body_start)

    anchors = sorted(
        (pos, label)
        for pos, label in (
            (explanation_start, "penjelasan"),
            (lampiran_start, "lampiran"),
        )
        if pos is not None
    )

    boundaries = [body_start] + [pos for pos, _ in anchors] + [len(raw_text)]
    labels = ["batang_tubuh"] + [label for _, label in anchors]

    zones = {"batang_tubuh": "", "penjelasan": "", "lampiran": ""}
    for label, start, end in zip(labels, boundaries, boundaries[1:]):
        zones[label] = raw_text[start:end].strip()

    return {
        **zones,
        "has_explanation": explanation_start is not None,
        "has_lampiran": lampiran_start is not None,
    }

# ---------------------------------------------------------------------------
# 4. State Machine Parser
# ---------------------------------------------------------------------------

def _clean_isi_pasal(isi_lines: list[str]) -> str:
    text = "\n".join(isi_lines).strip()
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def _is_any_heading(line: str) -> bool:
    line_s = line.strip()
    if not line_s or line_s == PAGE_BREAK:
        return True
    if CONTINUATION_MARKER_PATTERN.match(line_s):
        return True
    if BAB_PATTERN.match(line_s):
        return True
    if BAGIAN_PATTERN.match(line_s):
        return True
    if PARAGRAF_PATTERN.match(line_s):
        return True
    if PASAL_PATTERN.match(line_s):
        return True
    if LAMPIRAN_PATTERN.match(line_s):
        return True
    if CLOSING_PATTERN.match(line_s):
        return True
    return False


def _collect_title(lines: list[str], start_idx: int) -> tuple[Optional[str], int]:
    title_parts = []
    curr = start_idx
    while curr < len(lines):
        line = lines[curr].strip()
        if not line or line == PAGE_BREAK or _is_any_heading(lines[curr]):
            break
        title_parts.append(line)
        curr += 1

    title = " ".join(title_parts).strip() if title_parts else None
    return title, curr


def parse_batang_tubuh(batang_tubuh_text: str) -> list[dict]:
    """Scan teks batang tubuh baris demi baris dan kumpulkan pasal (Poin 8-17)."""
    lines = batang_tubuh_text.splitlines()

    current_bab: Optional[str] = None
    current_bab_judul: Optional[str] = None
    current_bagian: Optional[str] = None
    current_bagian_judul: Optional[str] = None
    current_paragraf: Optional[str] = None
    current_paragraf_judul: Optional[str] = None
    current_pasal: Optional[str] = None
    current_isi: list[str] = []

    pasal_list: list[dict] = []

    def _flush_current_pasal():
        nonlocal current_pasal, current_isi
        if current_pasal is not None:
            isi_str = _clean_isi_pasal(current_isi)
            pasal_list.append({
                "bab": current_bab,
                "bab_judul": current_bab_judul,
                "bagian": current_bagian,
                "bagian_judul": current_bagian_judul,
                "paragraf": current_paragraf,
                "paragraf_judul": current_paragraf_judul,
                "pasal": current_pasal,
                "isi_pasal": isi_str,
            })
            current_pasal = None
            current_isi = []

    i = 0
    n = len(lines)
    while i < n:
        raw_line = lines[i]
        line = raw_line.strip()

        if not line or line == PAGE_BREAK:
            if current_pasal is not None and line != PAGE_BREAK:
                current_isi.append(raw_line)
            i += 1
            continue

        if LAMPIRAN_PATTERN.match(line) or CLOSING_PATTERN.match(line):
            _flush_current_pasal()
            break

        bab_match = BAB_PATTERN.match(line)
        if bab_match:
            _flush_current_pasal()
            current_bab = _normalize_bab_roman(bab_match.group(1))
            current_bagian = None
            current_bagian_judul = None
            current_paragraf = None
            current_paragraf_judul = None
            title, i = _collect_title(lines, i + 1)
            current_bab_judul = title
            continue

        bagian_match = BAGIAN_PATTERN.match(line)
        if bagian_match:
            _flush_current_pasal()
            current_bagian = bagian_match.group(1).strip()
            current_paragraf = None
            current_paragraf_judul = None
            title, i = _collect_title(lines, i + 1)
            current_bagian_judul = title
            continue

        paragraf_match = PARAGRAF_PATTERN.match(line)
        if paragraf_match:
            _flush_current_pasal()
            current_paragraf = paragraf_match.group(1).strip()
            title, i = _collect_title(lines, i + 1)
            current_paragraf_judul = title
            continue

        pasal_match = PASAL_PATTERN.match(line)
        if pasal_match:
            _flush_current_pasal()
            current_pasal = _normalize_pasal_number(pasal_match.group(1))
            current_isi = []
            i += 1
            continue

        if current_pasal is not None:
            current_isi.append(raw_line)

        i += 1

    _flush_current_pasal()

    return pasal_list

# ---------------------------------------------------------------------------
# 5. Validator & Debug Logger
# ---------------------------------------------------------------------------

def _normalize_whitespace_and_newlines(text: str) -> str:
    """Membersihkan spasi berlebih dan merapikan newline agar optimal untuk embedding/RAG,
    tetap mempertahankan struktur ayat ((1), a., dll.).
    """
    lines = text.splitlines()
    processed_lines = []
    
    structural_prefix_pattern = re.compile(r"^(\s*\(?\d+\)|\s*[a-z]\.|\s*\d+\.)")

    for line in lines:
        rline = line.rstrip()
        if not rline:
            processed_lines.append("")
            continue
            
        collapsed = re.sub(r"[ \t]+", " ", rline).strip()
        
        if structural_prefix_pattern.match(collapsed):
            processed_lines.append(collapsed)
        else:
            if processed_lines and processed_lines[-1] and not structural_prefix_pattern.match(processed_lines[-1]):
                processed_lines[-1] = f"{processed_lines[-1]} {collapsed}"
            else:
                processed_lines.append(collapsed)

    joined = "\n".join(processed_lines)
    joined = re.sub(r"\n{3,}", "\n\n", joined)
    return joined.strip()


def clean_pasal_final(pasal_list: list[dict]) -> list[dict]:
    cleaned_list = []
    for item in pasal_list:
        isi = item.get("isi_pasal", "")
        lines = []
        for line in isi.splitlines():
            rline = line.rstrip()
            if any(p.match(rline) for p in HEADER_FOOTER_PATTERNS):
                continue
            if CONTINUATION_MARKER_PATTERN.match(rline):
                continue
            lines.append(rline)
        cleaned_isi = "\n".join(lines).strip()
        cleaned_isi = _normalize_whitespace_and_newlines(cleaned_isi)

        new_item = dict(item)
        new_item["isi_pasal"] = cleaned_isi
        cleaned_list.append(new_item)

    # Tangani duplikat: jika ada nomor pasal yang sama, utamakan yang memiliki isi (tidak kosong).
    # Jika keduanya ada atau keduanya kosong, pertahankan salah satu atau yang terakhir.
    pasal_map: dict[str, dict] = {}
    for item in cleaned_list:
        p_num = item.get("pasal")
        if not p_num:
            continue
        if p_num not in pasal_map:
            pasal_map[p_num] = item
        else:
            # Jika pasal yang sudah tersimpan kosong, tapi item baru punya isi, ganti dengan item baru
            existing_isi = pasal_map[p_num].get("isi_pasal", "").strip()
            new_isi = item.get("isi_pasal", "").strip()
            if not existing_isi and new_isi:
                pasal_map[p_num] = item

    return list(pasal_map.values())


def validate_parsing(pasal_list: list[dict], zones: dict) -> list[str]:
    warnings = []
    if not pasal_list:
        warnings.append("Tidak ada pasal yang terdeteksi dalam batang tubuh.")
        return warnings

    seen_pasal = set()
    prev_num = None

    for item in pasal_list:
        p_num = item.get("pasal")
        if not item.get("isi_pasal"):
            warnings.append(f"Pasal {p_num} memiliki isi kosong.")

        if p_num in seen_pasal:
            warnings.append(f"Nomor pasal duplikat: Pasal {p_num}.")
        seen_pasal.add(p_num)

        m = re.match(r"^(\d+)", str(p_num or ""))
        if m:
            curr_num = int(m.group(1))
            if prev_num is not None and curr_num - prev_num > 5:
                warnings.append(f"Lompatan nomor pasal jauh: Pasal {prev_num} ke Pasal {curr_num}.")
            prev_num = curr_num

    batang_tubuh_text = zones.get("batang_tubuh", "")
    if EXPLANATION_PATTERN.search(batang_tubuh_text):
        warnings.append("Teks penjelasan terdeteksi di dalam zona batang tubuh.")

    return warnings


_CATEGORY_MAP_PATH = Path(__file__).resolve().parents[2] / "data" / "document_category_map.json"


def _load_category_map() -> dict[int, str]:
    try:
        data = json.loads(_CATEGORY_MAP_PATH.read_text(encoding="utf-8"))
        return {int(k): v for k, v in data.items()}
    except Exception:
        return {}


DOCUMENT_CATEGORY_MAP: dict[int, str] = _load_category_map()


def resolve_document_category(pdf_path: str | Path | None = None, category_code: Optional[int] = None) -> dict:
    if category_code is not None:
        return {"category_code": category_code, "category": DOCUMENT_CATEGORY_MAP.get(category_code)}

    if pdf_path is None:
        return {"category_code": None, "category": None}

    filename = Path(pdf_path).stem.lower().replace("_", " ")
    
    # Sortir kategori berdasarkan panjang karakter (descending) 
    # agar mencocokkan yang paling spesifik terlebih dahulu (e.g. 'peraturan pemerintah' sebelum 'peraturan').
    sorted_categories = sorted(DOCUMENT_CATEGORY_MAP.items(), key=lambda x: len(x[1]), reverse=True)
    
    for code, name in sorted_categories:
        if name.lower() in filename:
            return {"category_code": code, "category": name}

    return {"category_code": None, "category": None}


def get_debug_metadata(pasal_list: list[dict], zones: dict, warnings: list[str], pdf_path: str | Path | None = None, category_code: Optional[int] = None) -> dict:
    cat = resolve_document_category(pdf_path, category_code)
    return {
        "category": cat["category"],
        "category_code": cat["category_code"],
        "has_explanation": zones.get("has_explanation", False),
        "has_lampiran": zones.get("has_lampiran", False),
        "start_heading_found": len(pasal_list) > 0,
        "pasal_count": len(pasal_list),
        "warnings": warnings,
    }


if __name__ == "__main__":
    import json

    output_dir = Path("data/parsing-output")
    output_dir.mkdir(parents=True, exist_ok=True)

    for path in iter_pdf_paths():
        print("Current extract:", path)
        try:
            raw = extract_raw_text(str(path))
        except Exception as exc:  # noqa: BLE001 - jangan sampai 1 file matiin batch
            print(f"  [ERROR] Skip {path}: {exc}")
            continue

        print("  Panjang teks mentah:", len(raw))

        zones = split_zones(raw)
        print(
            "  Batang Tubuh:", len(zones["batang_tubuh"]),
            "| Penjelasan:", len(zones["penjelasan"]),
            "| Lampiran:", len(zones["lampiran"]),
        )
        pasal_list = parse_batang_tubuh(zones["batang_tubuh"])
        pasal_list = clean_pasal_final(pasal_list)
        warnings = validate_parsing(pasal_list, zones)
        metadata = get_debug_metadata(pasal_list, zones, warnings, pdf_path=path)
        
        result_data = {
            "source_file": str(path),
            "metadata": metadata,
            "pasal_list": pasal_list
        }

        out_file = output_dir / f"{path.stem}_parsed.json"
        out_file.write_text(json.dumps(result_data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  [SAVED] {out_file}")