import unittest
from src.ingestion.parser import split_zones

class TestSplitZones(unittest.TestCase):
    def test_poin_7_preamble_removal_and_line_wrap(self):
        # Case where "Pasal 1" is line-wrapped in preamble vs. real "Pasal 1"
        raw_text = (
            "UNDANG-UNDANG TENTANG SEMENTARA\n"
            "Menimbang:\n"
            "  a. bahwa sebagaimana dimaksud dalam\n"
            "  Pasal 1 Undang-Undang Dasar...\n"
            "MEMUTUSKAN:\n"
            "Menetapkan:\n"
            "  UNDANG-UNDANG TENTANG SEMENTARA\n"
            "BAB I\n"
            "KETENTUAN UMUM\n"
            "Pasal 1\n"
            "Isi pasal 1 disini.\n"
        )
        zones = split_zones(raw_text)
        self.assertTrue(zones["batang_tubuh"].startswith("BAB I"))
        self.assertNotIn("Menimbang", zones["batang_tubuh"])
        self.assertNotIn("sebagaimana dimaksud", zones["batang_tubuh"])

    def test_poin_6_explanation_detection_and_ocr(self):
        # Test PENJELASAN ATAS, I. UMUM, II. PASAL DEMI PASAL with different OCRs
        raw_text_1 = (
            "MEMUTUSKAN:\n"
            "Pasal 1\n"
            "Isi pasal 1.\n"
            "PENJELASAN ATAS PERATURAN\n"
            "I. UMUM\n"
            "Isi penjelasan umum.\n"
        )
        zones_1 = split_zones(raw_text_1)
        self.assertTrue(zones_1["has_explanation"])
        self.assertEqual(zones_1["batang_tubuh"], "Pasal 1\nIsi pasal 1.")
        self.assertTrue(zones_1["penjelasan"].startswith("PENJELASAN ATAS"))

        # Test II. PASAL DEMI PASAL with OCR error ll.
        raw_text_2 = (
            "MEMUTUSKAN:\n"
            "Pasal 1\n"
            "Isi pasal 1.\n"
            "ll. PASAL DEMI PASAL\n"
            "Isi penjelasan pasal demi pasal.\n"
        )
        zones_2 = split_zones(raw_text_2)
        self.assertTrue(zones_2["has_explanation"])
        self.assertEqual(zones_2["batang_tubuh"], "Pasal 1\nIsi pasal 1.")
        self.assertTrue(zones_2["penjelasan"].startswith("ll. PASAL DEMI PASAL"))

    def test_poin_18_lampiran_detection(self):
        raw_text = (
            "MEMUTUSKAN:\n"
            "Pasal 1\n"
            "Isi pasal 1.\n"
            "LAMP1RAN I\n"
            "Ini adalah isi lampiran 1.\n"
        )
        zones = split_zones(raw_text)
        self.assertTrue(zones["has_lampiran"])
        self.assertEqual(zones["batang_tubuh"], "Pasal 1\nIsi pasal 1.")
        self.assertTrue(zones["lampiran"].startswith("LAMP1RAN I"))

    def test_all_zones_together_and_order(self):
        raw_text = (
            "MEMUTUSKAN:\n"
            "Pasal 1\n"
            "Isi pasal 1.\n"
            "PENJELASAN ATAS\n"
            "Penjelasan...\n"
            "LAMPIRAN II\n"
            "Lampiran...\n"
        )
        zones = split_zones(raw_text)
        self.assertTrue(zones["has_explanation"])
        self.assertTrue(zones["has_lampiran"])
        self.assertEqual(zones["batang_tubuh"], "Pasal 1\nIsi pasal 1.")
        self.assertEqual(zones["penjelasan"], "PENJELASAN ATAS\nPenjelasan...")
        self.assertEqual(zones["lampiran"], "LAMPIRAN II\nLampiran...")

if __name__ == "__main__":
    unittest.main()
