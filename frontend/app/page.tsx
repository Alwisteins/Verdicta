"use client";

import { FormEvent, useRef, useState } from "react";
import {
  ArrowRight,
  ArrowLeftRight,
  BadgeCheck,
  BookOpen,
  BriefcaseBusiness,
  Building2,
  ClipboardList,
  FileCheck2,
  FileText,
  Gavel,
  History,
  Landmark,
  LockKeyhole,
  Scale,
  Search,
  ShieldCheck,
  ShieldQuestion,
  ShoppingBag,
  Upload
} from "lucide-react";

const promptActions = [
  { label: "Cari Pasal", icon: Scale, text: "Cari bunyi dan tafsir resmi dari " },
  { label: "Analisis Kasus", icon: Search, text: "Analisis konsekuensi hukum untuk kasus " },
  {
    label: "Bandingkan Aturan",
    icon: ArrowLeftRight,
    text: "Bandingkan pertentangan aturan antara UU dan PP terkait "
  },
  {
    label: "Sanksi & Denda",
    icon: ShieldQuestion,
    tone: "danger",
    text: "Berapa besaran denda dan ancaman sanksi pidana dalam kasus "
  },
  { label: "Definisi Hukum", icon: BookOpen, text: "Apa definisi dan unsur yuridis formal dari istilah " }
];

const features = [
  {
    title: "Penjelasan Bahasa Awam",
    label: "Bahasa Sederhana",
    icon: BadgeCheck,
    iconClass: "border-amber-200 bg-amber-50 text-amber-600",
    copy: "Ringkasan poin-poin utama tanpa istilah Latin yang membingungkan.",
    meta: "Struktur penalaran jelas & aplikatif"
  },
  {
    title: "Kutipan Otentik & Verbatim",
    label: "JDIHN Validated",
    icon: FileText,
    iconClass: "border-blue-200 bg-blue-50 text-slate-700",
    copy: "Rujukan bunyi pasal asli yang terverifikasi langsung dari Lembaran Negara & JDIHN.",
    meta: "Hierarki regulasi UU hingga Ayat"
  },
  {
    title: "Bebas Halusinasi",
    label: "Standar RAG Yuridis",
    icon: LockKeyhole,
    iconClass: "border-emerald-200 bg-emerald-50 text-emerald-700",
    copy: "Arsitektur RAG tertutup yang hanya merujuk pada dokumen hukum resmi yang berlaku.",
    meta: "Penyaringan aturan kadaluwarsa otomatis"
  }
];

const cases = [
  {
    tag: "Ketenagakerjaan",
    icon: BriefcaseBusiness,
    title: "Berapa pesangon PHK menurut aturan UU Cipta Kerja?",
    copy: "Hitungkan kompensasi, masa kerja, dan uang penggantian hak.",
    prompt: "Berapa pesangon PHK menurut aturan UU Cipta Kerja untuk karyawan dengan masa kerja 6 tahun?"
  },
  {
    tag: "Bisnis & UMKM",
    icon: Building2,
    title: "Apa saja syarat dan kelebihan membuat PT Perorangan?",
    copy: "Kemudahan izin berusaha tanpa akta notaris untuk modal mikro.",
    prompt: "Apa saja syarat, batasan, dan kelebihan membuat PT Perorangan untuk UMKM?"
  },
  {
    tag: "Pidana Siber",
    icon: ShieldCheck,
    title: "Bagaimana aturan hukum dan sanksi penipuan transaksi online?",
    copy: "Penerapan Pasal 28 UU ITE dan jerat pasal penipuan KUHP baru.",
    prompt: "Bagaimana aturan hukum dan sanksi penipuan transaksi online di Indonesia?"
  },
  {
    tag: "Hak Konsumen",
    icon: ShoppingBag,
    title: "Apa hak konsumen jika barang yang dibeli secara online rusak?",
    copy: "UUPK No. 8/1999 tentang ganti rugi dan tanggung jawab penjual.",
    prompt: "Apa hak konsumen jika barang yang dibeli secara online rusak saat diterima?"
  }
];

const sources = [
  {
    title: "JDIHN Nasional",
    icon: Landmark,
    copy: "Sinkronisasi berkala dengan Lembaran Negara RI, Tambahan Lembaran Negara, dan Berita Negara.",
    meta: "Terhubung Sistem Nasional"
  },
  {
    title: "Hierarki Regulasi Lengkap",
    icon: ClipboardList,
    copy: "Mencakup UUD 1945, UU/Perppu, PP, Perpres, hingga Permen yang masih berkekuatan hukum tetap.",
    meta: "Uji Validitas Peraturan"
  },
  {
    title: "Audit & Validasi Yuridis",
    icon: FileCheck2,
    copy: "Mekanisme sitasi terbuka yang selalu menyertakan nomor dokumen dan tautan publik resmi.",
    meta: "Sitasi Otentik Terbuka"
  }
];

function StatusPill({ children }: { children: React.ReactNode }) {
  return (
    <span className="rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 font-mono text-[10px] font-medium text-emerald-700">
      {children}
    </span>
  );
}

export default function Home() {
  const queryRef = useRef<HTMLTextAreaElement>(null);
  const [query, setQuery] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  function submitPrompt(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);
    window.setTimeout(() => setIsSubmitting(false), 700);
  }

  function fillPrompt(text: string) {
    setQuery(text);
    queryRef.current?.scrollIntoView({ block: "center", behavior: "smooth" });
    queryRef.current?.focus();
  }

  return (
    <main className="min-h-screen bg-canvas text-ink">
      <header className="sticky top-4 z-50 mx-auto flex w-[calc(100%-2rem)] max-w-5xl items-center justify-between rounded-full border border-hairline/70 bg-white/85 px-5 py-3 shadow-ambient backdrop-blur md:top-6 md:px-6">
        <a className="flex items-center gap-2 font-bold tracking-tight" href="#">
          <span className="flex size-8 items-center justify-center rounded-lg bg-navy text-amber-300">
            <Gavel className="size-4" />
          </span>
          <span>Verdicta</span>
        </a>
        <nav className="hidden items-center gap-6 text-sm font-medium md:flex">
          <a className="text-emerald" href="#">
            Beranda
          </a>
          <a className="text-muted transition hover:text-ink" href="#fitur">
            Fitur Utama
          </a>
          <a className="text-muted transition hover:text-ink" href="#contoh">
            Contoh Kasus
          </a>
        </nav>
        <div className="flex items-center gap-2">
          <button className="hidden items-center gap-1.5 rounded-full px-3 py-1.5 text-sm font-medium text-muted transition hover:bg-panelSoft hover:text-ink sm:inline-flex">
            <History className="size-4" />
            Riwayat
          </button>
          <button className="rounded-full bg-navy px-5 py-2 text-sm font-semibold text-white shadow-ambient transition hover:bg-slate-800">
            Masuk / Daftar
          </button>
        </div>
      </header>

      <section className="mx-auto max-w-7xl px-4 pb-12 pt-12 md:px-10">
        <div className="mx-auto mb-8 max-w-4xl text-center">
          <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-hairline/70 bg-panelSoft px-3.5 py-1 text-[11px] font-semibold tracking-wide">
            <BadgeCheck className="size-4 text-emerald" />
            <span>Asisten AI Hukum Yuridis Pertama Terbuka untuk Publik</span>
          </div>
          <h1 className="mx-auto max-w-3xl text-3xl font-bold leading-tight tracking-normal text-ink md:text-[40px] md:leading-[48px]">
            Pahami Hukum Indonesia Lebih Mudah dan Tepercaya
          </h1>
          <p className="mx-auto mt-4 max-w-2xl text-base leading-7 text-muted">
            Tanyakan pasal, sanksi pidana, hingga analisis kasus sehari-hari. Dapatkan penjelasan bahasa awam dan kutipan resmi perundang-undangan.
          </p>
        </div>

        <form
          onSubmit={submitPrompt}
          className="mx-auto max-w-4xl rounded-2xl border border-hairline bg-white/90 p-4 shadow-deep backdrop-blur md:p-6"
        >
          <div className="mb-3 flex flex-wrap gap-2 border-b border-panelMid pb-3">
            {promptActions.map((action) => (
              <button
                key={action.label}
                className="inline-flex items-center gap-1.5 rounded-full border border-hairline/60 bg-panelSoft px-3 py-1 text-xs font-semibold transition hover:bg-panelMid"
                type="button"
                onClick={() => fillPrompt(action.text)}
              >
                <action.icon className={`size-3.5 ${action.tone === "danger" ? "text-danger" : "text-emerald"}`} />
                {action.label}
              </button>
            ))}
          </div>
          <textarea
            id="legal-query"
            ref={queryRef}
            className="min-h-24 w-full resize-none border-0 bg-transparent p-2 text-base leading-7 text-ink outline-none placeholder:text-slate-400 focus:ring-0"
            placeholder="Ketik pertanyaan, pasal, atau istilah hukum di sini..."
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                event.currentTarget.form?.requestSubmit();
              }
            }}
          />
          <div className="mt-2 flex flex-col gap-3 border-t border-panelMid pt-3 sm:flex-row sm:items-center sm:justify-between">
            <label className="inline-flex cursor-pointer items-center justify-center gap-2 rounded-lg border border-dashed border-hairline px-3 py-2 font-mono text-[11px] font-medium text-muted transition hover:border-slate-500 hover:text-ink sm:justify-start">
              <Upload className="size-4" />
              Unggah Dokumen (Opsional)
              <input className="hidden" type="file" accept=".pdf,.doc,.docx" />
            </label>
            <button
              className="inline-flex items-center justify-center gap-2 rounded-lg bg-navy px-6 py-2.5 text-sm font-semibold text-white shadow-ambient transition hover:bg-slate-800"
              type="submit"
            >
              {isSubmitting ? "Membuka..." : "Tanyakan"}
              <ArrowRight className="size-4" />
            </button>
          </div>
        </form>
        <p className="mt-3 flex items-center justify-center gap-2 text-center font-mono text-[10px] text-muted">
          <BadgeCheck className="size-3.5 text-emerald" />
          Terintegrasi dengan basis data resmi JDIHN (UU, PP, Perpres, dan KUHP).
        </p>
      </section>

      <section className="border-t border-hairline/50" id="fitur">
        <div className="mx-auto max-w-7xl px-4 py-14 md:px-10">
          <div className="mx-auto mb-9 max-w-2xl text-center">
            <p className="font-mono text-xs font-semibold uppercase tracking-widest text-emerald">Standar Layanan</p>
            <h2 className="mt-2 text-2xl font-semibold md:text-3xl">Kapabilitas & Standar Layanan Verdicta</h2>
            <p className="mt-3 text-sm leading-6 text-muted">Kecerdasan Buatan berstandar yuridis formal yang dirancang agar mudah dipahami masyarakat luas.</p>
          </div>
          <div className="grid gap-6 md:grid-cols-3">
            {features.map((feature) => (
              <article key={feature.title} className="rounded-2xl border border-hairline bg-panel p-6 shadow-ambient transition hover:border-slate-300 hover:shadow-lift">
                <div className="mb-5 flex items-center justify-between gap-3">
                  <span className={`flex size-11 items-center justify-center rounded-xl border ${feature.iconClass}`}>
                    <feature.icon className="size-5" />
                  </span>
                  <StatusPill>{feature.label}</StatusPill>
                </div>
                <h3 className="text-lg font-semibold">{feature.title}</h3>
                <p className="mt-3 min-h-14 text-sm leading-6 text-muted">{feature.copy}</p>
                <p className="mt-5 border-t border-panelMid pt-3 font-mono text-[10px] font-medium text-emerald">
                  {feature.meta}
                </p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-4 py-12 md:px-10" id="contoh">
        <div className="mb-8 grid gap-4 md:grid-cols-[1fr_360px] md:items-end">
          <div>
            <span className="rounded-full border border-blue-200 bg-blue-50 px-3 py-1 font-mono text-[10px] font-medium text-slate-700">
              Eksplorasi Kasus Populer
            </span>
            <h2 className="mt-4 text-2xl font-semibold md:text-3xl">Pertanyaan Hukum yang Sering Ditanyakan</h2>
          </div>
          <p className="text-sm leading-6 text-muted">Pilih salah satu kasus di bawah untuk langsung mencoba simulasi konsultasi interaktif dengan Verdicta.</p>
        </div>
        <div className="grid gap-6 md:grid-cols-2">
          {cases.map((item) => (
            <button
              key={item.title}
              className="group rounded-2xl border border-hairline bg-panel p-6 text-left shadow-ambient transition hover:border-slate-300 hover:shadow-lift"
              type="button"
              onClick={() => fillPrompt(item.prompt)}
            >
              <div className="mb-5 flex items-center justify-between gap-3">
                <span className="rounded-full bg-blue-50 px-3 py-1 font-mono text-[10px] font-medium text-slate-700">{item.tag}</span>
                <span className="flex size-9 items-center justify-center rounded-xl bg-panelSoft text-slate-700">
                  <item.icon className="size-4" />
                </span>
              </div>
              <h3 className="text-lg font-semibold">{item.title}</h3>
              <p className="mt-2 text-sm leading-6 text-muted">{item.copy}</p>
              <p className="mt-4 inline-flex items-center gap-1 text-sm font-semibold text-emerald">
                Tanyakan Kasus Ini
                <ArrowRight className="size-4 transition group-hover:translate-x-1" />
              </p>
            </button>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-4 py-14 md:px-10" id="sumber-data">
        <div className="mx-auto mb-9 max-w-3xl text-center">
          <p className="font-mono text-xs font-semibold uppercase tracking-widest text-emerald">Transparansi & Integritas</p>
          <h2 className="mt-2 text-2xl font-semibold md:text-3xl">Sumber Data Terverifikasi & Transparan</h2>
          <p className="mt-3 text-sm leading-6 text-muted">Fondasi data hukum publik yang tersinkronisasi langsung dengan portal resmi Republik Indonesia.</p>
        </div>
        <div className="grid gap-6 md:grid-cols-3">
          {sources.map((source) => (
            <article key={source.title} className="rounded-2xl border border-hairline bg-panel p-6 shadow-ambient">
              <span className="mb-5 flex size-11 items-center justify-center rounded-xl border border-blue-100 bg-blue-50 text-slate-700">
                <source.icon className="size-5" />
              </span>
              <h3 className="text-lg font-semibold">{source.title}</h3>
              <p className="mt-3 min-h-20 text-sm leading-6 text-muted">{source.copy}</p>
              <p className="mt-5 border-t border-panelMid pt-3 font-mono text-[10px] font-medium text-emerald">{source.meta}</p>
            </article>
          ))}
        </div>
      </section>

      <footer className="border-t border-hairline bg-panelSoft">
        <div className="mx-auto flex max-w-7xl flex-col gap-5 px-4 py-8 md:flex-row md:items-center md:justify-between md:px-10">
          <div>
            <div className="flex items-center gap-2 text-sm font-semibold">
              <Gavel className="size-4 text-amber-500" />
              Verdicta Intelligence (c) 2025
            </div>
            <p className="mt-2 max-w-2xl text-xs leading-5 text-muted">
              Verdicta memberikan informasi dokumen hukum resmi terintegrasi JDIHN. Hasil analisis AI bersifat informatif dan bukan pengganti nasihat hukum resmi dari advokat.
            </p>
          </div>
          <nav className="flex flex-wrap gap-x-5 gap-y-2 font-mono text-[10px] text-muted">
            <a className="hover:text-ink" href="#">
              Ketentuan Layanan
            </a>
            <a className="hover:text-ink" href="#">
              Kebijakan Privasi (UU PDP)
            </a>
            <a className="hover:text-ink" href="#sumber-data">
              Basis Data JDIHN
            </a>
            <a className="hover:text-ink" href="#">
              Kontak Advokat Mitra
            </a>
          </nav>
        </div>
      </footer>
    </main>
  );
}
