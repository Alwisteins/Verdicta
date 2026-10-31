import { NextResponse } from "next/server";
import { prisma } from "../../../lib/prisma";

export async function GET() {
  try {
    const threads = await prisma.thread.findMany({
      orderBy: { updatedAt: "desc" },
    });
    return NextResponse.json({ success: true, threads });
  } catch (error) {
    console.error("Fetch threads error:", error);
    return NextResponse.json({ success: true, threads: [] });
  }
}

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { title, userId } = body;

    const firstUser = userId ? await prisma.user.findUnique({ where: { id: userId } }) : await prisma.user.findFirst();
    if (!firstUser) {
      return NextResponse.json({ error: "No user found" }, { status: 400 });
    }

    const thread = await prisma.thread.create({
      data: {
        title: title || "Percakapan Baru",
        userId: firstUser.id,
      },
    });

    return NextResponse.json({ success: true, thread });
  } catch (error) {
    console.error("Create thread error:", error);
    return NextResponse.json({ error: "Failed to create thread" }, { status: 500 });
  }
}
