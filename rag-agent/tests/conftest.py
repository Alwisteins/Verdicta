import logging
import pytest

@pytest.fixture(autouse=True, scope="session")
def silence_third_party_loggers():
    # Daftar library yang berisik di terminal
    noisy_loggers = [
        "httpx",
        "httpcore",
        "grpc",
        "qdrant_client",
        "google",
        "google.genai",
        "google_genai",
        "langchain",
        "langchain_core",
        "langgraph",
        "urllib3",
    ]
    
    for logger_name in noisy_loggers:
        logging.getLogger(logger_name).setLevel(logging.WARNING)