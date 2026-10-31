"use client";

import { FormEvent, useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  ArrowRight,
  Building2,
  Eye,
  EyeOff,
  Gavel,
  Lock,
  Mail,
  Scale,
  ShieldCheck,
  User,
  Zap,
} from "lucide-react";

type AuthMode = "masuk" | "daftar";

const trustItems = [
  {
    icon: Lock,
    text: "Data Anda terlindungi & enkripsi privasi terjamin",
  },
  {
    icon: Gavel,
    text: "Akses fitur gratis untuk publik & praktisi",
  },
  {
    icon: Building2,
    text: "Tersinkronisasi standar integritas JDIHN",
  },
];

function GoogleMark() {
  return (
    <svg aria-hidden="true" className="size-5 shrink-0" viewBox="0 0 24 24">
      <path
        d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.82-2.4 3.68v3.05h3.88c2.27-2.09 3.66-5.17 3.66-9.17z"
        fill="#4285F4"
      />
      <path
        d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.88-3.05c-1.08.72-2.45 1.16-4.05 1.16-3.12 0-5.77-2.1-6.72-4.93H1.25v3.15C3.26 21.36 7.33 24 12 24z"
        fill="#34A853"
      />
      <path
        d="M5.28 14.27c-.25-.72-.38-1.49-.38-2.27s.14-1.55.38-2.27V6.58H1.25C.45 8.18 0 9.97 0 12s.45 3.82 1.25 5.42l4.03-3.15z"
        fill="#FBBC05"
      />
      <path
        d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.33 0 3.26 2.64 1.25 6.58l4.03 3.15c.95-2.83 3.6-4.98 6.72-4.98z"
        fill="#EA4335"
      />
    </svg>
  );
}

export default function AuthPage() {
  const router = useRouter();
  const [mode, setMode] = useState<AuthMode>("masuk");
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errorMsg, setErrorMsg] = useState("");
  const isRegister = mode === "daftar";

  useEffect(() => {
    async function checkUser() {
      try {
        const res = await fetch("/api/user");
        const data = await res.json();
        if (data.user) {
          router.push("/chatbot");
        }
      } catch (err) {
        console.error("Auth page check user error", err);
      }
    }
    checkUser();
  }, [router]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);
    setErrorMsg("");

    try {
      const res = await fetch("/api/auth", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          action: mode === "daftar" ? "register" : "login",
          email,
          password,
          name: isRegister ? name : undefined,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        setErrorMsg(data.error || "Gagal memproses permintaan.");
        setIsSubmitting(false);
        return;
      }

      router.push("/chatbot");
    } catch (err) {
      console.error(err);
      setErrorMsg("Terjadi kesalahan jaringan.");
      setIsSubmitting(false);
    }
  }

  function handleGoogleLogin() {
    setIsSubmitting(true);
    window.location.href = "/api/auth/google";
  }

  return (
    <main className="relative flex min-h-screen flex-col overflow-hidden bg-canvas text-ink">
      <div className="pointer-events-none absolute inset-x-0 top-0 -z-10 h-80 bg-[linear-gradient(180deg,rgba(218,226,253,0.72),rgba(248,249,255,0))]" />
      <div className="pointer-events-none absolute inset-0 -z-10 bg-[radial-gradient(circle_at_50%_16%,rgba(104,219,169,0.14),transparent_36%),radial-gradient(circle_at_14%_45%,rgba(190,198,224,0.18),transparent_30%),radial-gradient(circle_at_86%_72%,rgba(211,228,254,0.32),transparent_34%)]" />

      <header className="w-full px-4 pt-6 md:px-10">
        <nav className="mx-auto flex max-w-4xl items-center justify-between rounded-full border border-hairline/70 bg-white/85 px-5 py-3 shadow-ambient backdrop-blur md:px-6">
          <Link
            className="group flex items-center gap-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald"
            href="/">
            <span className="flex size-10 items-center justify-center rounded-xl bg-navy text-emerald-300 shadow-ambient transition group-hover:scale-105">
              <Scale className="size-5" />
            </span>
            <span className="flex flex-col">
              <span className="text-xl font-bold leading-6 tracking-normal text-ink">Verdicta</span>
              <span className="hidden font-mono text-[10px] font-semibold uppercase leading-4 tracking-[0.18em] text-muted sm:block">
                AI Legal Intelligence
              </span>
            </span>
          </Link>

          <Link
            className="inline-flex items-center justify-center gap-2 rounded-full border border-hairline bg-white/60 px-4 py-2 text-sm font-semibold text-ink transition hover:bg-panelSoft focus:outline-none focus:ring-2 focus:ring-emerald"
            href="/">
            <ArrowLeft className="size-4 text-muted" />
            <span className="hidden sm:inline">Kembali ke Beranda</span>
            <span className="sm:hidden">Beranda</span>
          </Link>
        </nav>
      </header>

      <section className="flex w-full flex-1 flex-col items-center justify-center px-4 py-8">
        <div className="w-full max-w-[460px]">
          <div className="relative overflow-hidden rounded-[24px] border border-hairline/70 bg-white p-6 shadow-deep sm:p-10">
            <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-transparent via-emerald to-transparent opacity-60" />

            <div className="mb-7 flex rounded-full border border-hairline/40 bg-panelSoft p-1">
              {(["masuk", "daftar"] as AuthMode[]).map((tab) => (
                <button
                  key={tab}
                  className={`flex-1 rounded-full px-6 py-2 text-center text-sm font-semibold transition ${
                    mode === tab ? "bg-navy text-white shadow-ambient" : "text-muted hover:text-ink"
                  }`}
                  type="button"
                  onClick={() => setMode(tab)}>
                  {tab === "masuk" ? "Masuk" : "Daftar"}
                </button>
              ))}
            </div>

            <div className="text-center sm:text-left">
              <h1 className="text-[22px] font-bold leading-[30px] tracking-normal text-ink">
                {isRegister ? "Buat Akun Verdicta" : "Selamat Datang di Verdicta"}
              </h1>
              <p className="mt-2 text-sm leading-6 text-muted">
                {isRegister
                  ? "Mulai konsultasi instan dengan basis data undang-undang dan yurisprudensi Indonesia."
                  : "Akses asisten AI hukum terpercaya dan simpan riwayat konsultasi Anda dengan aman."}
              </p>
            </div>

            <div className="mt-6">
              <button
                className="flex w-full items-center justify-center gap-3 rounded-xl border border-hairline bg-white px-4 py-3 text-sm font-semibold text-ink shadow-ambient transition hover:border-slate-400 hover:bg-panelSoft focus:outline-none focus:ring-2 focus:ring-emerald/50"
                type="button"
                onClick={handleGoogleLogin}>
                <GoogleMark />
                Lanjutkan dengan Google
              </button>
              <p className="mt-2 flex items-center justify-center gap-1.5 text-center text-xs leading-5 text-muted">
                <Zap className="size-3.5 text-emerald" />
                Akses cepat tanpa perlu mengingat kata sandi.
              </p>
            </div>

            <div className="relative my-6">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-hairline/60" />
              </div>
              <div className="relative flex justify-center">
                <span className="bg-white px-3 font-mono text-[10px] font-semibold uppercase tracking-[0.18em] text-muted">
                  atau gunakan email
                </span>
              </div>
            </div>

            <form className="space-y-4" onSubmit={handleSubmit}>
              {errorMsg && (
                <div className="rounded-xl bg-red-50 p-3 text-xs font-semibold text-red-600 border border-red-200">
                  {errorMsg}
                </div>
              )}

              {isRegister ? (
                <label className="block space-y-1.5">
                  <span className="block font-mono text-xs font-semibold tracking-wide text-ink">
                    Nama Lengkap
                  </span>
                  <span className="relative block">
                    <User className="absolute left-3.5 top-1/2 size-4 -translate-y-1/2 text-muted" />
                    <input
                      className="block w-full rounded-xl border border-hairline bg-canvas py-2.5 pl-10 pr-4 text-sm text-ink outline-none transition placeholder:text-slate-400 focus:border-ink focus:ring-1 focus:ring-ink"
                      placeholder="Adv. Ahmad Kurniawan, S.H."
                      type="text"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                    />
                  </span>
                </label>
              ) : null}

              <label className="block space-y-1.5">
                <span className="block font-mono text-xs font-semibold tracking-wide text-ink">
                  Alamat Email
                </span>
                <span className="relative block">
                  <Mail className="absolute left-3.5 top-1/2 size-4 -translate-y-1/2 text-muted" />
                  <input
                    className="block w-full rounded-xl border border-hairline bg-canvas py-2.5 pl-10 pr-4 text-sm text-ink outline-none transition placeholder:text-slate-400 focus:border-ink focus:ring-1 focus:ring-ink"
                    placeholder="nama@email.com"
                    required
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                  />
                </span>
              </label>

              <label className="block space-y-1.5">
                <span className="flex items-center justify-between">
                  <span className="block font-mono text-xs font-semibold tracking-wide text-ink">
                    Kata Sandi
                  </span>
                  <a
                    className={`font-mono text-xs font-semibold tracking-wide text-muted transition hover:text-ink hover:underline ${
                      isRegister ? "invisible" : ""
                    }`}
                    href="#">
                    Lupa kata sandi?
                  </a>
                </span>
                <span className="relative block">
                  <Lock className="absolute left-3.5 top-1/2 size-4 -translate-y-1/2 text-muted" />
                  <input
                    className="block w-full rounded-xl border border-hairline bg-canvas py-2.5 pl-10 pr-11 text-sm text-ink outline-none transition placeholder:text-slate-400 focus:border-ink focus:ring-1 focus:ring-ink"
                    placeholder="••••••••"
                    required
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                  />
                  <button
                    className="absolute inset-y-0 right-0 flex items-center pr-3.5 text-muted transition hover:text-ink focus:outline-none"
                    type="button"
                    onClick={() => setShowPassword((value) => !value)}
                    aria-label={showPassword ? "Sembunyikan kata sandi" : "Tampilkan kata sandi"}>
                    {showPassword ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
                  </button>
                </span>
              </label>

              <button
                className="mt-4 flex w-full items-center justify-center gap-2 rounded-xl bg-navy px-4 py-3 text-sm font-semibold text-white shadow-ambient transition hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-emerald"
                type="submit">
                {isSubmitting ? "Memproses..." : isRegister ? "Daftar Akun" : "Masuk ke Akun"}
                <ArrowRight className="size-4" />
              </button>
            </form>

            <div className="mt-6 border-t border-hairline/40 pt-5 text-center text-xs leading-5 text-muted">
              {isRegister ? "Sudah memiliki akun?" : "Belum punya akun?"}
              <button
                className="ml-1 text-sm font-semibold text-ink transition hover:underline focus:outline-none"
                type="button"
                onClick={() => setMode(isRegister ? "masuk" : "daftar")}>
                {isRegister ? "Masuk sekarang" : "Daftar gratis"}
              </button>
            </div>
          </div>

          <div className="mt-8 space-y-2.5 px-2">
            {trustItems.map((item) => (
              <div
                key={item.text}
                className="flex items-center gap-2.5 text-xs leading-5 text-muted">
                <item.icon className="size-4 shrink-0 text-emerald" />
                <span>{item.text}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      <footer className="w-full border-t border-hairline/50 bg-panelSoft/70 px-4 py-5 backdrop-blur md:px-10">
        <div className="mx-auto flex max-w-4xl flex-col items-center justify-between gap-3 text-center md:flex-row md:text-left">
          <p className="max-w-2xl text-xs leading-5 text-muted">
            Dengan melanjutkan, Anda menyetujui{" "}
            <a className="font-semibold text-ink hover:underline" href="#">
              Ketentuan Layanan
            </a>{" "}
            dan{" "}
            <a className="font-semibold text-ink hover:underline" href="#">
              Kebijakan Privasi
            </a>{" "}
            Verdicta. Analisis AI bersifat informatif sesuai kerangka hukum Indonesia dan tidak
            menggantikan nasihat advokat berizin.
          </p>
          <div className="flex shrink-0 items-center gap-4 font-mono text-[10px] font-semibold tracking-[0.16em] text-muted">
            <span>UU PDP Patuh</span>
            <span className="size-1 rounded-full bg-hairline" />
            <span>JDIHN Terhubung</span>
          </div>
        </div>
      </footer>
    </main>
  );
}
