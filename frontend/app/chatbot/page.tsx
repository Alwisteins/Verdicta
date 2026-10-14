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
  ShieldCheck
} from "lucide-react";
import { Suspense, useState } from "react";

const historyGroups = [
  {
    label: "Hari Ini",
    items: [
      {
        title: "Sanksi Pencemaran Nama Baik UU ITE",
        meta: "Pasal 45 ayat (4) | Delik Aduan",
        active: true,
        icon: Gavel
      },
      {
        title: "Analisis Ketenagakerjaan Pesangon PP 35",
        meta: "Formula PKWT & Kompensasi",
        icon: FileText
      }
    ]
  },
  {
    label: "Kemarin",
    items: [
      {
        title: "Syarat PT Perorangan vs PT Biasa",
        meta: "KBLI Usaha Mikro Kecil",
        icon: FileText
      },
      {
        title: "Sengketa Batas Tanah Sertifikat Ganda",
        meta: "Yurisprudensi MA No. 126/K/Pdt",
        icon: FolderOpen
      }
    ]
  },
  {
    label: "7 Hari Terakhir",
    items: [
      {
        title: "Hak Cuti Melahirkan UU Cipta Kerja",
        meta: "Perlindungan Upah Penuh",
        icon: FileText
      },
      {
        title: "Kompilasi Hukum Waris Islam",
        meta: "Ahli Waris Pengganti KHI",
        icon: Scale
      }
    ]
  }
];

const sources = [
  {
    id: "[1]",
    title: "UU No. 1 Tahun 2024 tentang Perubahan Kedua atas UU No. 11/2008 (UU ITE)",
    meta: "Fokus Pengaturan: Pasal 27A dan Pasal 45 Ayat (4)",
    status: "Berlaku"
  },
  {
    id: "[2]",
    title: "KUHP Nasional (UU No. 1 Tahun 2023 tentang Kitab Undang-Undang Hukum Pidana)",
    meta: "Fokus Pengaturan: Pasal 433 Bab XVII",
    status: "Transisi 2026"
  },
  {
    id: "[3]",
    title: "SKB Menkominfo, Jaksa Agung, dan Kapolri No. 229/2021, 154/2021, KB/2/VI/2021",
    meta: "Pedoman kriteria implementasi Pasal UU ITE dan restorative justice",
    status: "Pedoman Aktif"
  }
];

const followUps = [
  "Bagaimana prosedur pelaporan di SPKT?",
  "Apakah postingan di grup WhatsApp privat masuk kategori publik?",
  "Apa isi lengkap SKB Pedoman Implementasi?"
];

function CitationButton({ label }: { label: string }) {
  return (
    <button
      className="mx-1 inline-flex items-center gap-1 rounded-md border border-hairline/60 bg-panelSoft px-2 py-0.5 align-baseline font-mono text-[11px] font-semibold text-emerald transition hover:border-emerald hover:bg-emeraldSoft"
      type="button"
    >
      {label}
      <ArrowUpRight className="size-3" />
    </button>
  );
}

function ChatbotContent() {
  const searchParams = useSearchParams();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const defaultQuestion =
    "Apa sanksi pencemaran nama baik di media sosial dan bagaimana batas delik aduannya menurut aturan hukum terbaru?";
  const question = searchParams.get("q") || defaultQuestion;

  return (
    <main className="flex h-screen flex-col overflow-hidden bg-canvas text-ink">
      <header className="z-30 shrink-0 border-b border-hairline/40 bg-white shadow-ambient">
        <div className="flex w-full items-center justify-between gap-4 px-4 py-2.5 lg:px-6">
          <div className="flex items-center gap-3 lg:gap-5">
            <Link
              className="inline-flex items-center gap-1.5 rounded-full border border-hairline/70 px-3 py-1.5 text-sm font-semibold text-muted transition hover:bg-panelSoft hover:text-ink"
              href="/"
            >
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
                <span className="font-mono text-[10px] font-semibold uppercase text-emerald">Legal Intelligence</span>
              </span>
            </div>
          </div>

          <div className="hidden max-w-md items-center gap-2 rounded-full border border-hairline/50 bg-panelSoft px-3.5 py-1.5 md:flex">
            <span className="size-2 rounded-full bg-emerald" />
            <span className="font-mono text-xs text-muted">Topik:</span>
            <span className="truncate text-sm font-semibold text-ink">Pencemaran Nama Baik di Medsos & UU ITE</span>
          </div>

          <div className="flex items-center gap-2 lg:gap-3">
            <button
              className="inline-flex items-center gap-1.5 rounded-lg border border-hairline/70 px-3 py-1.5 text-sm font-semibold text-ink transition hover:bg-panelSoft"
              type="button"
            >
              <Plus className="size-4" />
              <span className="hidden sm:inline">Sesi Baru</span>
            </button>
            <button
              className="inline-flex size-9 items-center justify-center rounded-lg border border-hairline/70 text-muted transition hover:bg-panelSoft hover:text-ink md:hidden"
              type="button"
              onClick={() => setSidebarOpen((value) => !value)}
              aria-label="Buka riwayat konsultasi"
            >
              <Menu className="size-4" />
            </button>
            <div className="hidden h-4 w-px bg-hairline/70 lg:block" />
            <div className="flex items-center gap-2">
              <span className="relative flex size-8 items-center justify-center rounded-full border border-hairline bg-panelSoft text-sm font-bold">
                DP
                <span className="absolute bottom-0 right-0 size-2.5 rounded-full border-2 border-white bg-emerald" />
              </span>
              <span className="hidden flex-col xl:flex">
                <span className="text-sm font-semibold leading-tight">Adv. Dimas Prasetyo, S.H.</span>
                <span className="font-mono text-[10px] text-muted">Peradi Verified | ID: 8841</span>
              </span>
            </div>
          </div>
        </div>
      </header>

      <div className="relative flex min-h-0 flex-1 overflow-hidden">
        <aside
          className={`z-20 flex h-full w-72 shrink-0 flex-col justify-between border-r border-hairline/40 bg-white transition md:relative md:translate-x-0 lg:w-80 ${
            sidebarOpen ? "absolute inset-y-0 left-0 translate-x-0 shadow-deep" : "absolute inset-y-0 left-0 -translate-x-full md:translate-x-0"
          }`}
        >
          <div className="border-b border-hairline/40 p-3.5">
            <div className="mb-3 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Scale className="size-5 text-emerald" />
                <h2 className="text-sm font-bold">Riwayat Konsultasi</h2>
              </div>
              <button className="rounded-md p-1 text-muted transition hover:bg-panelSoft hover:text-ink" type="button">
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
            {historyGroups.map((group) => (
              <section key={group.label}>
                <p className="px-2 font-mono text-[10px] font-semibold uppercase text-muted">{group.label}</p>
                <div className="mt-1 space-y-1">
                  {group.items.map((item) => (
                    <a
                      key={item.title}
                      className={`flex items-start gap-2.5 rounded-lg px-2.5 py-2 transition ${
                        item.active
                          ? "border border-hairline/40 bg-panelMid/70 text-ink"
                          : "text-muted hover:bg-panelSoft hover:text-ink"
                      }`}
                      href="#"
                    >
                      <item.icon className={`mt-0.5 size-4 shrink-0 ${item.active ? "text-emerald" : "text-muted"}`} />
                      <span className="min-w-0 flex-1">
                        <span className="block truncate text-sm font-semibold">{item.title}</span>
                        <span className="block truncate text-[11px] text-muted">{item.meta}</span>
                      </span>
                    </a>
                  ))}
                </div>
              </section>
            ))}
          </div>

          <div className="space-y-1 border-t border-hairline/40 bg-canvas/60 p-3">
            <a className="flex items-center gap-2.5 rounded-md px-2.5 py-1.5 text-sm font-semibold text-muted transition hover:bg-panelSoft hover:text-ink" href="#">
              <Settings2 className="size-4" />
              Pengaturan
            </a>
            <a className="flex items-center gap-2.5 rounded-md px-2.5 py-1.5 text-sm font-semibold text-muted transition hover:bg-panelSoft hover:text-ink" href="#">
              <HelpCircle className="size-4" />
              Bantuan
            </a>
          </div>
        </aside>

        <section className="relative flex min-w-0 flex-1 flex-col overflow-hidden">
          <div className="mx-auto w-full max-w-6xl flex-1 space-y-6 overflow-y-auto px-4 py-6 pb-48 md:px-8 [scrollbar-width:thin]">
            <article className="rounded-xl border border-hairline/50 bg-white p-5 shadow-ambient">
              <div className="mb-3 flex flex-wrap items-center justify-between gap-3 border-b border-hairline/30 pb-3">
                <div className="flex items-center gap-2.5">
                  <span className="flex size-7 items-center justify-center rounded-full bg-navy text-xs font-bold text-white">DP</span>
                  <div>
                    <span className="text-sm font-bold">Pertanyaan Anda</span>
                    <span className="mx-1.5 text-hairline">|</span>
                    <span className="text-xs text-muted">Hari ini, 10:24 WIB</span>
                  </div>
                </div>
                <span className="inline-flex items-center gap-1 rounded-full border border-hairline/50 bg-panelSoft px-2.5 py-0.5 font-mono text-[10px] font-semibold text-muted">
                  <Gavel className="size-3.5 text-emerald" />
                  Pidana Siber & ITE
                </span>
              </div>
              <p className="text-lg font-semibold leading-8 text-ink">"{question}"</p>
            </article>

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
                  Diproses dalam 1.1s | Sinkronisasi JDIHN RI
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
                      <p className="text-xs text-muted">Disusun dari sumber resmi dan sitasi terverifikasi.</p>
                    </div>
                  </div>
                  <span className="inline-flex items-center gap-1 rounded-full border border-emerald/30 bg-emeraldSoft px-2.5 py-1 font-mono text-[10px] font-bold text-emerald">
                    <span className="size-1.5 rounded-full bg-emerald" />
                    Validitas: Berlaku
                  </span>
                </div>

                <div className="max-w-4xl space-y-6 text-sm leading-7 text-muted">
                  <section className="space-y-2">
                    <h2 className="flex items-center gap-2 text-base font-bold text-ink">
                      <span className="size-2 rounded-full bg-emerald" />
                      1. Ringkasan Yuridis
                    </h2>
                    <p className="border-l-2 border-hairline/50 pl-4">
                      Perbuatan pencemaran nama baik di ruang siber pasca-berlakunya{" "}
                      <strong className="font-semibold text-ink">UU No. 1 Tahun 2024</strong> mengalami rekualifikasi
                      sanksi dan pengetatan delik. Tindak pidana ini diklasifikasikan sebagai{" "}
                      <strong className="font-semibold text-ink">delik aduan absolut</strong> dengan ancaman pidana
                      penjara maksimal 2 tahun.
                    </p>
                  </section>

                  <section className="space-y-3">
                    <h2 className="flex items-center gap-2 text-base font-bold text-ink">
                      <span className="size-2 rounded-full bg-emerald" />
                      2. Unsur Delik & Sanksi Pidana
                    </h2>
                    <p className="border-l-2 border-hairline/50 pl-4">
                      Unsur perbuatan terpenuhi apabila seseorang dengan sengaja menyerang kehormatan atau nama baik
                      orang lain melalui sistem elektronik dengan maksud diketahui publik
                      <CitationButton label="[1] UU 1/2024 Ps. 45 (4)" />. Pelanggaran dapat dikenai pidana penjara
                      paling lama 2 tahun atau denda maksimal Rp400.000.000,00.
                    </p>

                    <div className="ml-4 space-y-3 rounded-xl border border-emerald/40 bg-panelSoft/70 p-4 shadow-ambient">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <div className="flex flex-wrap items-center gap-2">
                          <BookOpen className="size-4 text-emerald" />
                          <span className="font-mono text-xs font-bold text-ink">Rujukan Verbatim Pasal [1]</span>
                          <span className="rounded border border-hairline/40 bg-white px-2 py-0.5 text-[11px] font-semibold">
                            UU No. 1 Tahun 2024
                          </span>
                        </div>
                        <span className="inline-flex items-center gap-1 rounded-full border border-emerald/30 bg-emeraldSoft px-2 py-0.5 font-mono text-[10px] font-bold text-emerald">
                          <BadgeCheck className="size-3" />
                          94% Relevan
                        </span>
                      </div>
                      <blockquote className="rounded-r-lg border-l-4 border-emerald bg-white p-3.5 font-serif text-[15px] italic leading-7 text-ink">
                        "Setiap Orang yang dengan sengaja menyerang kehormatan atau nama baik orang lain ... dipidana
                        dengan pidana penjara paling lama 2 tahun dan/atau denda paling banyak Rp400.000.000,00."
                      </blockquote>
                      <div className="flex flex-wrap items-center justify-between gap-2 font-mono text-[10px] text-muted">
                        <span className="inline-flex items-center gap-1.5">
                          <Landmark className="size-3.5 text-emerald" />
                          LN RI Tahun 2024 Nomor 1, TLN No. 6909
                        </span>
                        <a
                          className="inline-flex items-center gap-1 rounded-md border border-hairline/60 bg-white px-3 py-1 font-semibold text-ink transition hover:border-emerald hover:text-emerald"
                          href="https://jdihn.go.id"
                          rel="noreferrer"
                          target="_blank"
                        >
                          Buka Dokumen Resmi
                          <ArrowUpRight className="size-3.5" />
                        </a>
                      </div>
                    </div>
                  </section>

                  <section className="space-y-2">
                    <h2 className="flex items-center gap-2 text-base font-bold text-ink">
                      <span className="size-2 rounded-full bg-emerald" />
                      3. Kualifikasi Delik & Hak Penuntutan
                    </h2>
                    <p className="border-l-2 border-hairline/50 pl-4">
                      Tindak pidana ini adalah <strong className="font-semibold text-ink">delik aduan absolut</strong>
                      <CitationButton label="[2] Pasal 27A UU ITE" />. Penyidik tidak dapat memproses perkara tanpa
                      pengaduan langsung dari korban perseorangan yang martabatnya diserang secara personal.
                    </p>
                  </section>

                  <section className="space-y-2">
                    <h2 className="flex items-center gap-2 text-base font-bold text-ink">
                      <span className="size-2 rounded-full bg-emerald" />
                      4. Pengecualian Hukum & Restorative Justice
                    </h2>
                    <p className="border-l-2 border-hairline/50 pl-4">
                      Perbuatan tidak dapat dipidana apabila dilakukan untuk membela kepentingan umum atau pembelaan diri
                      secara proporsional. Aparat penegak hukum juga diarahkan menempuh restorative justice pada tahap
                      awal <CitationButton label="[3] SKB Pedoman UU ITE" />.
                    </p>
                  </section>
                </div>

                <section className="space-y-3 border-t border-hairline/30 pt-5">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <h2 className="flex items-center gap-2 text-sm font-bold">
                      <FolderOpen className="size-4 text-emerald" />
                      Dasar Hukum & Dokumen Terkait
                    </h2>
                    <span className="rounded-full bg-panelMid px-2 py-0.5 font-mono text-[10px] font-bold text-emerald">
                      3 Sumber Terverifikasi JDIHN
                    </span>
                  </div>
                  <div className="space-y-2">
                    {sources.map((source) => (
                      <div
                        key={source.id}
                        className="flex flex-col justify-between gap-3 rounded-lg border border-hairline/40 bg-panelSoft/70 p-3 transition hover:border-emerald/40 sm:flex-row sm:items-center"
                      >
                        <div className="flex items-start gap-3">
                          <span className="mt-0.5 flex size-6 shrink-0 items-center justify-center rounded-md border border-hairline/40 bg-white font-mono text-[11px] font-bold text-emerald">
                            {source.id}
                          </span>
                          <div>
                            <p className="text-sm font-semibold leading-5">{source.title}</p>
                            <p className="mt-0.5 text-[11px] text-muted">{source.meta}</p>
                          </div>
                        </div>
                        <div className="flex shrink-0 items-center gap-2 pl-9 sm:pl-0">
                          <span className="rounded-full bg-emeraldSoft px-2 py-0.5 font-mono text-[10px] font-bold text-emerald">
                            {source.status}
                          </span>
                          <button className="rounded px-2 py-1 text-[11px] font-semibold text-muted transition hover:bg-white hover:text-ink" type="button">
                            Salin
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </section>
              </article>

              <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-hairline/40 bg-white p-3 shadow-ambient">
                <div className="flex flex-wrap items-center gap-1.5">
                  <button className="inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-semibold text-muted transition hover:bg-panelSoft hover:text-ink" type="button">
                    <Copy className="size-4" />
                    Salin Analisis
                  </button>
                  <button className="inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-semibold text-muted transition hover:bg-panelSoft hover:text-ink" type="button">
                    <FileText className="size-4" />
                    Ekspor PDF
                  </button>
                  <button className="inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-semibold text-muted transition hover:bg-panelSoft hover:text-ink" type="button">
                    <Share2 className="size-4" />
                    Bagikan
                  </button>
                </div>
                <button className="inline-flex items-center gap-1.5 rounded-md border border-hairline/50 px-3.5 py-1.5 text-sm font-semibold transition hover:bg-panelSoft" type="button">
                  <RefreshCw className="size-4" />
                  Regenerasi Analisis
                </button>
              </div>

              <div className="space-y-2 px-1">
                <p className="flex items-center gap-2 font-mono text-[10px] font-semibold uppercase text-muted">
                  <ShieldCheck className="size-4 text-emerald" />
                  Usulan Analisis Lanjutan
                </p>
                <div className="flex flex-wrap gap-2">
                  {followUps.map((item) => (
                    <button
                      key={item}
                      className="rounded-full border border-hairline/60 bg-white px-3.5 py-1.5 text-left text-xs font-semibold transition hover:border-ink hover:bg-panelSoft"
                      type="button"
                    >
                      {item} <ArrowRight className="inline size-3" />
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>

          <div className="absolute inset-x-0 bottom-0 z-30 bg-gradient-to-t from-canvas via-canvas/95 to-transparent px-4 pb-2 pt-6 md:px-8">
            <div className="mx-auto max-w-4xl space-y-2">
              <div className="rounded-xl border border-hairline/70 bg-white/95 p-2.5 shadow-deep backdrop-blur transition focus-within:border-ink focus-within:ring-2 focus-within:ring-emerald/20">
                <div className="flex items-center gap-2">
                  <button className="shrink-0 rounded-lg p-2 text-muted transition hover:bg-panelSoft hover:text-ink" title="Lampirkan Dokumen" type="button">
                    <Paperclip className="size-5" />
                  </button>
                  <input
                    className="w-full border-0 bg-transparent px-1 py-1 text-sm text-ink outline-none placeholder:text-slate-400 focus:ring-0"
                    placeholder="Tanyakan kelanjutan atau analisis pasal lainnya..."
                    type="text"
                  />
                  <span className="hidden shrink-0 items-center gap-1 rounded-md border border-hairline/40 bg-panelSoft px-2.5 py-1 font-mono text-[10px] text-muted sm:flex">
                    <span className="size-1.5 rounded-full bg-emerald" />
                    Basis: UU & Yurisprudensi
                  </span>
                  <button className="inline-flex shrink-0 items-center gap-1.5 rounded-lg bg-navy px-4 py-2 text-sm font-semibold text-white shadow-ambient transition hover:bg-slate-800" type="button">
                    Tanyakan
                    <ArrowRight className="size-4" />
                  </button>
                </div>
              </div>
              <p className="pb-1 text-center font-mono text-[10px] leading-4 text-muted">
                Verdicta memberikan informasi dokumen hukum resmi terintegrasi JDIHN. Hasil analisis AI bersifat informatif dan bukan pengganti nasihat hukum resmi dari advokat.
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
