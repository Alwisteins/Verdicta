export interface CitedDocument {
  title?: string;
  nomor_uu?: string;
  pasal?: string;
  jenis_dokumen?: string;
}

export interface RAGResponse {
  answer: string;
  category: string | null;
  cited_documents: CitedDocument[];
  is_fallback: boolean;
}

export interface ConversationMessage {
  role: "user" | "assistant";
  content: string;
}

export async function sendQuestionToRAGEngine(
  question: string,
  threadId: string,
  history: ConversationMessage[] = [],
): Promise<RAGResponse> {
  const ragEndpoint = process.env.RAG_ENGINE_URL || "http://127.0.0.1:8000/api/v1/chat";
  const apiKey = process.env.RAG_API_KEY;
  if (!apiKey) {
    throw new Error("RAG_API_KEY is not configured for the web server");
  }

  const res = await fetch(ragEndpoint, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-API-Key": apiKey,
    },
    body: JSON.stringify({
      question,
      thread_id: threadId,
      history,
    }),
  });

  if (!res.ok) {
    throw new Error(`RAG Engine error: ${res.status} ${res.statusText}`);
  }

  const data: RAGResponse = await res.json();
  return data;
}
