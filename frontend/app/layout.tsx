import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Verdicta - AI Legal Assistant Indonesia",
  description:
    "Asisten AI hukum Indonesia untuk memahami pasal, sanksi, dan analisis regulasi dengan sumber JDIHN."
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="id">
      <body className="font-sans antialiased">{children}</body>
    </html>
  );
}
