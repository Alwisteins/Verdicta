from typing import List, Optional
import logging
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.graph.workflow import app as langgraph_app

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("verdicta-api")

app = FastAPI(
    title="Verdicta Legal RAG API",
    version="1.0.0",
    description="REST API wrapper for Verdicta LangGraph Legal RAG workflow"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    question: str = Field(..., description="Pertanyaan dari pengguna")
    thread_id: str = Field(..., description="Identifier unik sesi percakapan untuk LangGraph MemorySaver")

class DocumentMetadata(BaseModel):
    title: Optional[str] = None
    nomor_uu: Optional[str] = None
    pasal: Optional[str] = None
    jenis_dokumen: Optional[str] = None

class ChatResponse(BaseModel):
    answer: str = Field(..., description="Teks balasan akhir dari AI")
    category: Optional[str] = Field(None, description="Kategori hasil klasifikasi router_node")
    cited_documents: List[DocumentMetadata] = Field(default_factory=list, description="Daftar metadata dokumen/pasal yang dikutip")
    is_fallback: bool = Field(..., description="True jika cited_documents kosong atau AI memberikan jawaban fallback")

@app.get("/", tags=["Health Check"])
async def root():
    return {"status": "ok", "message": "Verdicta Legal RAG API is running"}

@app.post("/api/v1/chat", response_model=ChatResponse, tags=["Chat"])
async def chat_endpoint(payload: ChatRequest):
    try:
        config = {"configurable": {"thread_id": payload.thread_id}}
        input_data = {
            "question": payload.question,
            "messages": [("user", payload.question)]
        }

        result = langgraph_app.invoke(input_data, config=config)

        answer = result.get("generation", "Tidak ada jawaban.")
        category = result.get("question_category")

        documents = result.get("documents", [])
        cited_documents: List[DocumentMetadata] = []

        if documents:
            for doc in documents:
                metadata = getattr(doc, "metadata", {}) or {}
                cited_documents.append(
                    DocumentMetadata(
                        title=metadata.get("title") or metadata.get("source"),
                        nomor_uu=metadata.get("nomor_uu") or metadata.get("nomor"),
                        pasal=metadata.get("pasal"),
                        jenis_dokumen=metadata.get("jenis_dokumen") or metadata.get("jenis")
                    )
                )

        is_fallback = not documents or "tidak ditemukan" in answer.lower()

        return ChatResponse(
            answer=answer,
            category=category,
            cited_documents=cited_documents,
            is_fallback=is_fallback
        )

    except Exception as e:
        logger.exception("Error processing chat request")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
