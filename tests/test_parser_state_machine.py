import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import unittest
from src.ingestion.chunker import parse_batang_tubuh, clean_pasal_final, validate_parsing, get_debug_metadata


class TestStateMachineParser(unittest.TestCase):
    def test_poin_8_to_17_full_structure(self):
        batang_tubuh = (
            "BAB I\n"
            "KETENTUAN UMUM\n"
            "\n"
            "Bagian Kesatu\n"
            "Pengertian\n"
            "\n"
            "Paragraf 1\n"
            "Definisi Umum\n"
            "\n"
            "Pasal 1\n"
            "Dalam Peraturan ini yang dimaksud dengan:\n"
            "1. Hukum adalah peraturan.\n"
            "2. Negara adalah Indonesia.\n"
            "\n"
            "Pasal 2\n"
            "Peraturan ini berlaku seluruh wilayah.\n"
            "\n"
            "BAB II\n"
            "ASAS DAN TUJUAN\n"
            "\n"
            "Bagian Kedua\n"
            "Tujuan\n"
            "\n"
            "Pasal 3\n"
            "Tujuan dari peraturan ini adalah untuk ketertiban.\n"
            "\n"
            "Ditetapkan di Jakarta\n"
            "pada tanggal 1 Januari 2024\n"
        )

        pasal_list = parse_batang_tubuh(batang_tubuh)
        self.assertEqual(len(pasal_list), 3)

        # Check Pasal 1
        p1 = pasal_list[0]
        self.assertEqual(p1["bab"], "I")
        self.assertEqual(p1["bab_judul"], "KETENTUAN UMUM")
        self.assertEqual(p1["bagian"], "Kesatu")
        self.assertEqual(p1["bagian_judul"], "Pengertian")
        self.assertEqual(p1["paragraf"], "1")
        self.assertEqual(p1["paragraf_judul"], "Definisi Umum")
        self.assertEqual(p1["pasal"], "1")
        self.assertIn("Dalam Peraturan ini yang dimaksud dengan:", p1["isi_pasal"])

        # Check Pasal 2
        p2 = pasal_list[1]
        self.assertEqual(p2["bab"], "I")
        self.assertEqual(p2["bab_judul"], "KETENTUAN UMUM")
        self.assertEqual(p2["bagian"], "Kesatu")
        self.assertEqual(p2["bagian_judul"], "Pengertian")
        self.assertEqual(p2["paragraf"], "1")
        self.assertEqual(p2["paragraf_judul"], "Definisi Umum")
        self.assertEqual(p2["pasal"], "2")
        self.assertEqual(p2["isi_pasal"], "Peraturan ini berlaku seluruh wilayah.")

        # Check Pasal 3 under BAB II
        p3 = pasal_list[2]
        self.assertEqual(p3["bab"], "II")
        self.assertEqual(p3["bab_judul"], "ASAS DAN TUJUAN")
        self.assertEqual(p3["bagian"], "Kedua")
        self.assertEqual(p3["bagian_judul"], "Tujuan")
        self.assertIsNone(p3["paragraf"])
        self.assertIsNone(p3["paragraf_judul"])
        self.assertEqual(p3["pasal"], "3")
        self.assertEqual(p3["isi_pasal"], "Tujuan dari peraturan ini adalah untuk ketertiban.")

    def test_poin_15_pasal_tanpa_bab(self):
        batang_tubuh = (
            "Pasal 1\n"
            "Isi pasal 1 tanpa BAB.\n"
            "\n"
            "Pasal 2\n"
            "Isi pasal 2 tanpa BAB.\n"
        )
        pasal_list = parse_batang_tubuh(batang_tubuh)
        self.assertEqual(len(pasal_list), 2)
        self.assertIsNone(pasal_list[0]["bab"])
        self.assertIsNone(pasal_list[0]["bab_judul"])
        self.assertEqual(pasal_list[0]["pasal"], "1")

    def test_poin_16_pasal_sisipan_dan_ocr(self):
        batang_tubuh = (
            "Pasal 1O\n"
            "Isi pasal 10 OCR O.\n"
            "\n"
            "Pasal 10A\n"
            "Isi pasal sisipan 10A.\n"
        )
        pasal_list = parse_batang_tubuh(batang_tubuh)
        self.assertEqual(len(pasal_list), 2)
        self.assertEqual(pasal_list[0]["pasal"], "10")
        self.assertEqual(pasal_list[1]["pasal"], "10A")

    def test_poin_19_to_22_validator_and_debug(self):
        pasal_raw = [
            {"pasal": "1", "isi_pasal": "   SALINAN\n\nIsi pasal 1...\n\n\n"},
            {"pasal": "1", "isi_pasal": ""},
        ]
        cleaned = clean_pasal_final(pasal_raw)
        self.assertNotIn("SALINAN", cleaned[0]["isi_pasal"])
        
        zones = {"batang_tubuh": "Pasal 1\nIsi", "has_explanation": False, "has_lampiran": False}
        warnings = validate_parsing(pasal_raw, zones)
        self.assertTrue(any("kosong" in w for w in warnings))
        self.assertTrue(any("duplikat" in w for w in warnings))

        metadata = get_debug_metadata(cleaned, zones, warnings)
        self.assertEqual(metadata["pasal_count"], 1)
        self.assertFalse(metadata["has_explanation"])
        self.assertIn("warnings", metadata)



if __name__ == "__main__":
    unittest.main()
