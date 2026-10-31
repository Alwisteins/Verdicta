import { NextResponse } from "next/server";
import { prisma } from "../../../lib/prisma";
import bcrypt from "bcryptjs";

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { action, email, password, name } = body;

    if (action === "google") {
      if (!email) {
        return NextResponse.json(
          { error: "Email is required for Google login" },
          { status: 400 }
        );
      }

      let user = await prisma.user.findUnique({ where: { email } });
      if (!user) {
        user = await prisma.user.create({
          data: {
            email,
            name: name || email.split("@")[0],
            password: "",
          },
        });
      }

      return NextResponse.json({
        success: true,
        user: { id: user.id, email: user.email, name: user.name },
      });
    }

    if (!email || !password) {
      return NextResponse.json(
        { error: "Email and password are required" },
        { status: 400 }
      );
    }

    if (action === "register") {
      const existingUser = await prisma.user.findUnique({ where: { email } });
      if (existingUser) {
        return NextResponse.json(
          { error: "Email sudah terdaftar" },
          { status: 400 }
        );
      }

      const hashedPassword = await bcrypt.hash(password, 10);
      const user = await prisma.user.create({
        data: {
          email,
          name: name || null,
          password: hashedPassword,
        },
      });

      return NextResponse.json({
        success: true,
        user: { id: user.id, email: user.email, name: user.name },
      });
    } else {
      // login
      const user = await prisma.user.findUnique({ where: { email } });
      if (!user) {
        return NextResponse.json(
          { error: "Email atau kata sandi salah" },
          { status: 400 }
        );
      }

      const isValid = user.password ? await bcrypt.compare(password, user.password) : false;
      if (!isValid) {
        return NextResponse.json(
          { error: "Email atau kata sandi salah" },
          { status: 400 }
        );
      }

      return NextResponse.json({
        success: true,
        user: { id: user.id, email: user.email, name: user.name },
      });
    }
  } catch (error) {
    console.error("Auth error:", error);
    return NextResponse.json(
      { error: "Terjadi kesalahan pada server" },
      { status: 500 }
    );
  }
}
