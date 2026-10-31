import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { sendQuestionToRAGEngine } from "@/lib/rag-client";

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { threadId, question, userId } = body;

    if (!threadId || !question) {
      return NextResponse.json({ error: "threadId dan question wajib diisi" }, { status: 400 });
    }

    await prisma.message.create({
      data: {
        threadId,
        role: "USER",
        content: question,
      },
    });

    const ragData = await sendQuestionToRAGEngine(question, threadId);

    const assistantMessage = await prisma.message.create({
      data: {
        threadId,
        role: "ASSISTANT",
        content: ragData.answer,
        category: ragData.category,
        citedDocuments: ragData.cited_documents as any,
        isFallback: ragData.is_fallback,
      },
    });

    await prisma.thread.update({
      where: { id: threadId },
      data: { updatedAt: new Date() },
    });

    return NextResponse.json(assistantMessage);
  } catch (error) {
    console.error("Chat API error:", error);
    return NextResponse.json({ error: "Gagal terhubung ke RAG Engine" }, { status: 500 });
  }
}
