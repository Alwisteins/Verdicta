import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}"
  ],
  theme: {
    extend: {
      colors: {
        canvas: "#f8f9ff",
        panel: "#ffffff",
        panelSoft: "#eff4ff",
        panelMid: "#e5eeff",
        ink: "#0b1c30",
        muted: "#45464d",
        hairline: "#c6c6cd",
        navy: "#131b2e",
        emerald: "#006c4a",
        emeraldSoft: "#ecfdf5",
        amberSoft: "#fffbeb",
        blueSoft: "#dbeafe",
        danger: "#ba1a1a"
      },
      fontFamily: {
        sans: ["var(--font-jakarta)", "Plus Jakarta Sans", "Inter", "sans-serif"],
        mono: ["var(--font-mono)", "JetBrains Mono", "ui-monospace", "monospace"],
        serif: ["var(--font-serif)", "Source Serif 4", "Georgia", "serif"]
      },
      boxShadow: {
        ambient: "0 1px 3px 0 rgba(15, 23, 42, 0.04), 0 1px 2px -1px rgba(15, 23, 42, 0.02)",
        lift: "0 10px 15px -3px rgba(15, 23, 42, 0.05), 0 4px 6px -4px rgba(15, 23, 42, 0.02)",
        deep: "0 20px 25px -5px rgba(15, 23, 42, 0.08), 0 8px 10px -6px rgba(15, 23, 42, 0.03)"
      }
    }
  },
  plugins: []
};

export default config;
