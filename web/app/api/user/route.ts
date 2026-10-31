import { NextResponse } from "next/server";
import { prisma } from "../../../lib/prisma";

export async function GET(request: Request) {
  try {
    const url = new URL(request.url);
    const userId = url.searchParams.get("userId");

    let user = null;
    if (userId) {
      user = await prisma.user.findUnique({ where: { id: userId } });
    }
    if (!user) {
      user = await prisma.user.findFirst();
    }

    return NextResponse.json({ success: true, user });
  } catch (error) {
    console.error("Fetch user error:", error);
    return NextResponse.json({ success: false, user: null }, { status: 500 });
  }
}
