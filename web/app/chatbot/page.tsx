"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import {
  ArrowLeft,
  ArrowRight,
  ArrowUpRight,
  BadgeCheck,
  BookOpen,
  CheckCircle2,
  Copy,
  FileText,
  FolderOpen,
  Gavel,
  HelpCircle,
  History,
  Landmark,
  Menu,
  Paperclip,
  Plus,
  RefreshCw,
  Scale,
  Search,
  Settings2,
  Share2,
  ShieldCheck,
} from "lucide-react";
import { Suspense, useState, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface ThreadItem {
  id: string;
  title: string;
  createdAt: string;
}

interface MessageItem {
  id: string;
  threadId: string;
  role: "USER" | "ASSISTANT" | "SYSTEM";
  content: string;
  category: string | null;
  citedDocuments: any;
  isFallback: boolean;
  createdAt: string;
}

interface UserProfile {
  id: string;
  name: string | null;
  email: string;
  image: string | null;
}

const historyGroups = [
  {
    label: "Hari Ini",
    items: [
      {
        title: "Sanksi Pencemaran Nama Baik UU ITE",
        meta: "Pasal 45 ayat (4) | Delik Aduan",
        active: true,
        icon: Gavel,
      },
      {
        title: "Analisis Ketenagakerjaan Pesangon PP 35",
        meta: "Formula PKWT & Kompensasi",
        icon: FileText,
      },
    ],
  },
  {
    label: "Kemarin",
    items: [
      {
        title: "Syarat PT Perorangan vs PT Biasa",
        meta: "KBLI Usaha Mikro Kecil",
        icon: FileText,
      },
      {
        title: "Sengketa Batas Tanah Sertifikat Ganda",
        meta: "Yurisprudensi MA No. 126/K/Pdt",
        icon: FolderOpen,
      },
    ],
  },
  {
    label: "7 Hari Terakhir",
    items: [
      {
        title: "Hak Cuti Melahirkan UU Cipta Kerja",
        meta: "Perlindungan Upah Penuh",
        icon: FileText,
      },
      {
        title: "Kompilasi Hukum Waris Islam",
        meta: "Ahli Waris Pengganti KHI",
        icon: Scale,
      },
    ],
  },
];

const sources = [
  {
    id: "[1]",
    title: "UU No. 1 Tahun 2024 tentang Perubahan Kedua atas UU No. 11/2008 (UU ITE)",
    meta: "Fokus Pengaturan: Pasal 27A dan Pasal 45 Ayat (4)",
    status: "Berlaku",
  },
  {
    id: "[2]",
    title: "KUHP Nasional (UU No. 1 Tahun 2023 tentang Kitab Undang-Undang Hukum Pidana)",
    meta: "Fokus Pengaturan: Pasal 433 Bab XVII",
    status: "Transisi 2026",
  },
  {
    id: "[3]",
    title: "SKB Menkominfo, Jaksa Agung, dan Kapolri No. 229/2021, 154/2021, KB/2/VI/2021",
    meta: "Pedoman kriteria implementasi Pasal UU ITE dan restorative justice",
    status: "Pedoman Aktif",
  },
];

const followUps = [
  "Bagaimana prosedur pelaporan di SPKT?",
  "Apakah postingan di grup WhatsApp privat masuk kategori publik?",
  "Apa isi lengkap SKB Pedoman Implementasi?",
];

function CitationButton({ label }: { label: string }) {
  return (
    <button
      className="mx-1 inline-flex items-center gap-1 rounded-md border border-hairline/60 bg-panelSoft px-2 py-0.5 align-baseline font-mono text-[11px] font-semibold text-emerald transition hover:border-emerald hover:bg-emeraldSoft"
      type="button">
      {label}
      <ArrowUpRight className="size-3" />
    </button>
  );
}

function ChatbotContent() {
  const searchParams = useSearchParams();
  const [activeThreadId, setActiveThreadId] = useState<string | null>(searchParams.get("threadId"));
  const [inputMessage, setInputMessage] = useState("");
  const [messages, setMessages] = useState<MessageItem[]>([]);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [threads, setThreads] = useState<ThreadItem[]>([]);
  const [loadingThreads, setLoadingThreads] = useState(true);
  const [user, setUser] = useState<UserProfile | null>(null);
  const [imageError, setImageError] = useState(false);

  useEffect(() => {
    async function loadData() {
      try {
        const [threadsRes, userRes] = await Promise.all([
          fetch("/api/threads"),
          fetch("/api/user"),
        ]);
        const threadsData = await threadsRes.json();
        if (threadsData.threads) {
          setThreads(threadsData.threads);
        }
        const userData = await userRes.json();
        if (userData.user) {
          setUser(userData.user);
        }
      } catch (err) {
        console.error("Failed to load data", err);
      } finally {
        setLoadingThreads(false);
      }
    }
    loadData();
  }, []);

  useEffect(() => {
    if (!activeThreadId || activeThreadId === "new") {
      setMessages([]);
      return;
    }

    async function loadMessages() {
      setLoadingMessages(true);
      try {
        const res = await fetch(`/api/messages?threadId=${activeThreadId}`);
        const data = await res.json();
        if (data.messages) {
          setMessages(data.messages);
        }
      } catch (err) {
        console.error("Failed to load messages", err);
      } finally {
        setLoadingMessages(false);
      }
    }
    loadMessages();
  }, [activeThreadId]);

  async function createNewThread() {
    setActiveThreadId("new");
    setInputMessage("");
  }

  async function handleSendMessage() {
    if (!inputMessage.trim()) return;

    let currentThreadId = activeThreadId;
    const textToSend = inputMessage.trim();
    setInputMessage("");

    if (!currentThreadId || currentThreadId === "new") {
      try {
        const title = textToSend.slice(0, 40);
        const res = await fetch("/api/threads", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ title }),
        });
        const data = await res.json();
        if (data.thread) {
          setThreads((prev) => [data.thread, ...prev]);
          currentThreadId = data.thread.id;
          setActiveThreadId(data.thread.id);
        }
      } catch (err) {
        console.error("Failed to create thread", err);
        return;
      }
    }

    if (!currentThreadId) return;

    // Optimistically add user message
    const tempUserMsg: MessageItem = {
      id: "temp-" + Date.now(),
      threadId: currentThreadId,
      role: "USER",
      content: textToSend,
      category: null,
      citedDocuments: null,
      isFallback: false,
      createdAt: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempUserMsg]);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          threadId: currentThreadId,
          question: textToSend,
          userId: user?.id,
        }),
      });

      const assistantMsg = await res.json();
      if (res.ok && assistantMsg) {
        setMessages((prev) => [...prev, assistantMsg]);
      } else {
        console.error("Failed response from chat api", assistantMsg);
      }
    } catch (err) {
      console.error("Failed to send message", err);
    }
  }
  const defaultQuestion =
    "Apa sanksi pencemaran nama baik di media sosial dan bagaimana batas delik aduannya menurut aturan hukum terbaru?";
  const question = searchParams.get("q") || defaultQuestion;

  const displayName = user?.name || (user?.email ? user.email.split("@")[0] : "User");
  const initial = displayName.charAt(0).toUpperCase();

  return (
    <main className="flex h-screen flex-col overflow-hidden bg-canvas text-ink">
      <header className="z-30 shrink-0 border-b border-hairline/40 bg-white shadow-ambient">
        <div className="flex w-full items-center justify-between gap-4 px-4 py-2.5 lg:px-6">
          <div className="flex items-center gap-3 lg:gap-5">
            <Link
              className="inline-flex items-center gap-1.5 rounded-full border border-hairline/70 px-3 py-1.5 text-sm font-semibold text-muted transition hover:bg-panelSoft hover:text-ink"
              href="/">
              <ArrowLeft className="size-4" />
              Beranda
            </Link>
            <div className="hidden h-4 w-px bg-hairline/70 sm:block" />
            <div className="flex items-center gap-2">
              <span className="flex size-8 items-center justify-center rounded-lg bg-navy text-emerald-300">
                <Gavel className="size-4" />
              </span>
              <span className="flex flex-col">
                <span className="text-lg font-bold leading-none text-ink">Verdicta</span>
                <span className="font-mono text-[10px] font-semibold uppercase text-emerald">
                  Legal Intelligence
                </span>
              </span>
            </div>
          </div>

          <div className="hidden max-w-md items-center gap-2 rounded-full border border-hairline/50 bg-panelSoft px-3.5 py-1.5 md:flex">
            <span className="size-2 rounded-full bg-emerald" />
            <span className="font-mono text-xs text-muted">Topik:</span>
            <span className="truncate text-sm font-semibold text-ink">
              Pencemaran Nama Baik di Medsos & UU ITE
            </span>
          </div>

          <div className="flex items-center gap-2 lg:gap-3">
            <button
              className="inline-flex items-center gap-1.5 rounded-lg border border-hairline/70 px-3 py-1.5 text-sm font-semibold text-ink transition hover:bg-panelSoft"
              type="button"
              onClick={createNewThread}>
              <Plus className="size-4" />
              <span className="hidden sm:inline">Sesi Baru</span>
            </button>
            <button
              className="inline-flex size-9 items-center justify-center rounded-lg border border-hairline/70 text-muted transition hover:bg-panelSoft hover:text-ink md:hidden"
              type="button"
              onClick={() => setSidebarOpen((value) => !value)}
              aria-label="Buka riwayat konsultasi">
              <Menu className="size-4" />
            </button>
            <div className="hidden h-4 w-px bg-hairline/70 lg:block" />
            <div className="flex items-center gap-2">
              <div className="relative flex size-8 items-center justify-center">
                {user?.image && !imageError ? (
                  <img
                    src={user.image}
                    alt={displayName}
                    className="size-8 rounded-full border border-hairline object-cover"
                    onError={() => setImageError(true)}
                  />
                ) : (
                  <span className="flex size-8 items-center justify-center rounded-full border border-hairline bg-panelSoft text-sm font-bold uppercase text-ink">
                    {initial}
                  </span>
                )}
                <span className="absolute bottom-0 right-0 size-2.5 rounded-full border-2 border-white bg-emerald" />
              </div>
              <span className="hidden flex-col xl:flex">
                <span className="text-sm font-semibold leading-tight">{displayName}</span>
                <span className="font-mono text-[10px] text-muted">
                  {user?.email || "Pengguna Verdicta"}
                </span>
              </span>
            </div>
          </div>
        </div>
      </header>

      <div className="relative flex min-h-0 flex-1 overflow-hidden">
        <aside
          className={`z-20 flex h-full w-72 shrink-0 flex-col justify-between border-r border-hairline/40 bg-white transition md:relative md:translate-x-0 lg:w-80 ${
            sidebarOpen
              ? "absolute inset-y-0 left-0 translate-x-0 shadow-deep"
              : "absolute inset-y-0 left-0 -translate-x-full md:translate-x-0"
          }`}>
          <div className="border-b border-hairline/40 p-3.5">
            <div className="mb-3 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Scale className="size-5 text-emerald" />
                <h2 className="text-sm font-bold">Riwayat Konsultasi</h2>
              </div>
              <button
                className="rounded-md p-1 text-muted transition hover:bg-panelSoft hover:text-ink"
                type="button">
                <History className="size-4" />
              </button>
            </div>
            <label className="relative block">
              <Search className="absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted" />
              <input
                className="w-full rounded-md border border-hairline/50 bg-canvas py-1.5 pl-8 pr-3 text-xs outline-none placeholder:text-slate-400 focus:border-emerald focus:ring-1 focus:ring-emerald"
                placeholder="Cari riwayat..."
                type="search"
              />
            </label>
          </div>

          <div className="min-h-0 flex-1 space-y-4 overflow-y-auto px-2.5 py-3 [scrollbar-width:thin]">
            <section>
              <p className="px-2 font-mono text-[10px] font-semibold uppercase text-muted">
                Riwayat Percakapan
              </p>
              <div className="mt-1 space-y-1">
                {loadingThreads ? (
                  <p className="px-2 py-2 text-xs text-muted">Memuat riwayat...</p>
                ) : threads.length === 0 ? (
                  <p className="px-2 py-2 text-xs text-muted">Belum ada riwayat sesi.</p>
                ) : (
                  threads.map((thread, idx) => {
                    const isActive = activeThreadId === thread.id || (!activeThreadId && idx === 0);
                    return (
                      <button
                        key={thread.id}
                        className={`w-full text-left flex items-start gap-2.5 rounded-lg px-2.5 py-2 transition ${
                          isActive
                            ? "border border-hairline/40 bg-panelMid/70 text-ink"
                            : "text-muted hover:bg-panelSoft hover:text-ink"
                        }`}
                        onClick={() => {
                          setActiveThreadId(thread.id);
                        }}
                        type="button">
                        <Gavel
                          className={`mt-0.5 size-4 shrink-0 ${isActive ? "text-emerald" : "text-muted"}`}
                        />
                        <span className="min-w-0 flex-1">
                          <span className="block truncate text-sm font-semibold">
                            {thread.title}
                          </span>
                          <span className="block truncate text-[11px] text-muted">
                            {new Date(thread.createdAt).toLocaleDateString("id-ID", {
                              day: "numeric",
                              month: "short",
                              hour: "2-digit",
                              minute: "2-digit",
                            })}
                          </span>
                        </span>
                      </button>
                    );
                  })
                )}
              </div>
            </section>
          </div>

          <div className="space-y-1 border-t border-hairline/40 bg-canvas/60 p-3">
            <a
              className="flex items-center gap-2.5 rounded-md px-2.5 py-1.5 text-sm font-semibold text-muted transition hover:bg-panelSoft hover:text-ink"
              href="#">
              <Settings2 className="size-4" />
              Pengaturan
            </a>
            <a
              className="flex items-center gap-2.5 rounded-md px-2.5 py-1.5 text-sm font-semibold text-muted transition hover:bg-panelSoft hover:text-ink"
              href="#">
              <HelpCircle className="size-4" />
              Bantuan
            </a>
          </div>
        </aside>

        <section className="relative flex min-w-0 flex-1 flex-col overflow-hidden">
          <div className="mx-auto w-full max-w-6xl flex-1 space-y-6 overflow-y-auto px-4 py-6 pb-48 md:px-8 [scrollbar-width:thin]">
            {loadingMessages ? (
              <div className="flex h-40 items-center justify-center text-sm text-muted">
                Memuat pesan percakapan...
              </div>
            ) : messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-20 text-center">
                <div className="mb-4 flex size-14 items-center justify-center rounded-2xl bg-panelMid text-emerald">
                  <Gavel className="size-7" />
                </div>
                <h2 className="text-lg font-bold text-ink">Mulai Konsultasi Hukum Baru</h2>
                <p className="mt-1 max-w-md text-sm text-muted">
                  Ketikkan pertanyaan hukum atau masalah yang ingin Anda konsultasikan pada kolom di
                  bawah. Sesi akan otomatis tersimpan setelah pesan terkirim.
                </p>
              </div>
            ) : (
              messages.map((msg) => (
                <div key={msg.id} className="space-y-4">
                  {msg.role === "USER" ? (
                    <article className="rounded-xl border border-hairline/50 bg-white p-5 shadow-ambient">
                      <div className="mb-3 flex flex-wrap items-center justify-between gap-3 border-b border-hairline/30 pb-3">
                        <div className="flex items-center gap-2.5">
                          {user?.image && !imageError ? (
                            <img
                              src={user.image}
                              alt={displayName}
                              className="size-7 rounded-full border border-hairline object-cover"
                              onError={() => setImageError(true)}
                            />
                          ) : (
                            <span className="flex size-7 items-center justify-center rounded-full bg-navy text-xs font-bold uppercase text-white">
                              {initial}
                            </span>
                          )}
                          <div>
                            <span className="text-sm font-bold">Pertanyaan Anda</span>
                            <span className="mx-1.5 text-hairline">|</span>
                            <span className="text-xs text-muted">
                              {new Date(msg.createdAt).toLocaleTimeString("id-ID", {
                                hour: "2-digit",
                                minute: "2-digit",
                              })}{" "}
                              WIB
                            </span>
                          </div>
                        </div>
                        <span className="inline-flex items-center gap-1 rounded-full border border-hairline/50 bg-panelSoft px-2.5 py-0.5 font-mono text-[10px] font-semibold text-muted">
                          <Gavel className="size-3.5 text-emerald" />
                          {msg.category || "Hukum Umum"}
                        </span>
                      </div>
                      <p className="text-lg font-semibold leading-8 text-ink">"{msg.content}"</p>
                    </article>
                  ) : (
                    <div className="space-y-4">
                      <div className="flex flex-wrap items-center justify-between gap-2 px-1">
                        <div className="flex items-center gap-2.5">
                          <span className="flex size-7 items-center justify-center rounded-lg bg-emerald text-white">
                            <Scale className="size-4" />
                          </span>
                          <div className="flex flex-wrap items-center gap-2">
                            <span className="font-bold">Analisis Yuridis AI</span>
                            <span className="hidden h-3 w-px bg-hairline sm:block" />
                            <span className="inline-flex items-center gap-1 rounded bg-panelMid px-2 py-0.5 font-mono text-[10px] font-semibold">
                              <span className="size-1.5 rounded-full bg-emerald" />
                              Model: Verdicta JDIHN RAG
                            </span>
                          </div>
                        </div>
                        <span className="flex items-center gap-1.5 text-xs text-muted">
                          <CheckCircle2 className="size-4 text-emerald" />
                          Sinkronisasi JDIHN RI
                        </span>
                      </div>

                      <article className="space-y-6 rounded-xl border border-hairline/50 bg-white p-5 shadow-ambient md:p-6">
                        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-hairline/30 pb-4">
                          <div className="flex items-center gap-3">
                            <span className="flex size-9 items-center justify-center rounded-lg bg-panelSoft text-emerald">
                              <Gavel className="size-5" />
                            </span>
                            <div>
                              <h1 className="text-lg font-bold">Hasil Analisis Yuridis</h1>
                              <p className="text-xs text-muted">
                                Disusun dari sumber resmi dan sitasi terverifikasi.
                              </p>
                            </div>
                          </div>
                          <span className="inline-flex items-center gap-1 rounded-full border border-emerald/30 bg-emeraldSoft px-2.5 py-1 font-mono text-[10px] font-bold text-emerald">
                            <span className="size-1.5 rounded-full bg-emerald" />
                            Validitas: {msg.isFallback ? "Fallback" : "Berlaku"}
                          </span>
                        </div>

                        <div className="max-w-4xl text-sm leading-7 text-ink">
                          <div className="prose prose-slate max-w-none text-ink text-sm leading-relaxed prose-headings:font-bold prose-headings:text-ink prose-p:my-2.5 prose-ul:my-2 prose-ol:my-2 prose-li:my-0.5 prose-blockquote:border-l-4 prose-blockquote:border-emerald prose-blockquote:bg-panelSoft/50 prose-blockquote:px-4 prose-blockquote:py-2.5 prose-blockquote:italic prose-blockquote:rounded-r-lg prose-blockquote:my-3 prose-hr:my-4 prose-hr:border-hairline/60">
                            <ReactMarkdown remarkPlugins={[remarkGfm]}>
                              {msg.content}
                            </ReactMarkdown>
                          </div>
                        </div>

                        {msg.citedDocuments &&
                          Array.isArray(msg.citedDocuments) &&
                          msg.citedDocuments.length > 0 && (
                            <section className="space-y-3 border-t border-hairline/30 pt-5">
                              <div className="flex flex-wrap items-center justify-between gap-2">
                                <h2 className="flex items-center gap-2 text-sm font-bold">
                                  <FolderOpen className="size-4 text-emerald" />
                                  Dasar Hukum & Dokumen Terkait
                                </h2>
                              </div>
                              <div className="space-y-2">
                                {msg.citedDocuments.map((doc: any, i: number) => (
                                  <div
                                    key={i}
                                    className="flex flex-col justify-between gap-3 rounded-lg border border-hairline/40 bg-panelSoft/70 p-3 transition hover:border-emerald/40 sm:flex-row sm:items-center">
                                    <div className="flex items-start gap-3">
                                      <span className="mt-0.5 flex size-6 shrink-0 items-center justify-center rounded-md border border-hairline/40 bg-white font-mono text-[11px] font-bold text-emerald">
                                        [{i + 1}]
                                      </span>
                                      <div>
                                        <p className="text-sm font-semibold leading-5">
                                          {doc.title || doc.nomor_uu || "Dokumen Hukum"}
                                        </p>
                                        <p className="mt-0.5 text-[11px] text-muted">
                                          {doc.pasal ? `Pasal: ${doc.pasal}` : ""}{" "}
                                          {doc.jenis_dokumen ? `| ${doc.jenis_dokumen}` : ""}
                                        </p>
                                      </div>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </section>
                          )}
                      </article>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>

          <div className="absolute inset-x-0 bottom-0 z-30 bg-gradient-to-t from-canvas via-canvas/95 to-transparent px-4 pb-2 pt-6 md:px-8">
            <div className="mx-auto max-w-4xl space-y-2">
              <div className="rounded-xl border border-hairline/70 bg-white/95 p-2.5 shadow-deep backdrop-blur transition focus-within:border-ink focus-within:ring-2 focus-within:ring-emerald/20">
                <div className="flex items-center gap-2">
                  <button
                    className="shrink-0 rounded-lg p-2 text-muted transition hover:bg-panelSoft hover:text-ink"
                    title="Lampirkan Dokumen"
                    type="button">
                    <Paperclip className="size-5" />
                  </button>
                  <input
                    className="w-full border-0 bg-transparent px-1 py-1 text-sm text-ink outline-none placeholder:text-slate-400 focus:ring-0"
                    placeholder="Tanyakan kelanjutan atau analisis pasal lainnya..."
                    type="text"
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") {
                        e.preventDefault();
                        handleSendMessage();
                      }
                    }}
                  />
                  <span className="hidden shrink-0 items-center gap-1 rounded-md border border-hairline/40 bg-panelSoft px-2.5 py-1 font-mono text-[10px] text-muted sm:flex">
                    <span className="size-1.5 rounded-full bg-emerald" />
                    Basis: UU & Yurisprudensi
                  </span>
                  <button
                    className="inline-flex shrink-0 items-center gap-1.5 rounded-lg bg-navy px-4 py-2 text-sm font-semibold text-white shadow-ambient transition hover:bg-slate-800"
                    type="button"
                    onClick={handleSendMessage}>
                    Tanyakan
                    <ArrowRight className="size-4" />
                  </button>
                </div>
              </div>
              <p className="pb-1 text-center font-mono text-[10px] leading-4 text-muted">
                Verdicta memberikan informasi dokumen hukum resmi terintegrasi JDIHN. Hasil analisis
                AI bersifat informatif dan bukan pengganti nasihat hukum resmi dari advokat.
              </p>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}

export default function ChatbotPage() {
  return (
    <Suspense fallback={<main className="min-h-screen bg-canvas" />}>
      <ChatbotContent />
    </Suspense>
  );
}
