import pytest
from unittest.mock import MagicMock

# Assuming 'workflow' is an object that processes questions and maintains memory.
# In a real scenario, this would be an instance of your Langchain/Langgraph application.

class TestFollowUpQuestions:

    @pytest.fixture
    def mock_app(self):
        mock_app = MagicMock()
        mock_app.invoke.side_effect = lambda input_data, config: {
            "messages": [
                MagicMock(content="Informasi tentang UU No. 1 Tahun 2026 adalah tentang Ketentuan Umum."),
                MagicMock(content="Pasal 1 UU tersebut mengatur tentang definisi operasional."),
                MagicMock(content="UU No. 2 Tahun 2026 mengatur tentang anggaran."),
                MagicMock(content="PP No. 24 Tahun 2026 membahas modal daerah.")
            ]
        }
        return mock_app

    def test_follow_up_uu_ketentuan_umum(self, mock_app):
        # Case 1: Follow up on UU No 1 2026
        config = {"configurable": {"thread_id": "1"}}
        res1 = mock_app.invoke({"messages": [("user", "Apa isi UU No. 1 Tahun 2026?")]}, config)
        assert "Ketentuan Umum" in res1["messages"][0].content
        
        res2 = mock_app.invoke({"messages": [("user", "Apa isi Pasal 1-nya?")]}, config)
        assert "definisi operasional" in res2["messages"][1].content

    def test_follow_up_anggaran(self, mock_app):
        # Case 2: Follow up on UU No 2 2026 (Anggaran)
        config = {"configurable": {"thread_id": "2"}}
        res1 = mock_app.invoke({"messages": [("user", "Apa topik UU No. 2 Tahun 2026?")]}, config)
        assert "anggaran" in res1["messages"][2].content
        
        res2 = mock_app.invoke({"messages": [("user", "Berapa nilainya?")]}, config)
        assert "anggaran" in res2["messages"][2].content

    def test_follow_up_pp_modal(self, mock_app):
        # Case 3: Follow up on PP No 24 2026
        config = {"configurable": {"thread_id": "3"}}
        res1 = mock_app.invoke({"messages": [("user", "Jelaskan PP No. 24 Tahun 2026")]}, config)
        assert "modal daerah" in res1["messages"][3].content
        
        res2 = mock_app.invoke({"messages": [("user", "Siapa sasarannya?")]}, config)
        assert "modal daerah" in res2["messages"][3].content

