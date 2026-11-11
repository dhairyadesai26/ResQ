/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "var(--background)",
        foreground: "var(--foreground)",
        surface: {
          DEFAULT: "var(--surface)",
          muted: "var(--surface-muted)",
          border: "var(--surface-border)",
        },
        primary: {
          DEFAULT: "#0284c7", // sky-600
          foreground: "#ffffff",
          hover: "#0369a1",
        },
        accent: {
          DEFAULT: "#38bdf8", // sky-400
          foreground: "#0f172a",
        },
        status: {
          running: "#10b981",    // emerald-500
          stopped: "#64748b",    // slate-500
          recovering: "#f59e0b", // amber-500
          failed: "#f43f5e",     // rose-500
          starting: "#38bdf8",   // sky-400
        }
      },
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "monospace"],
      },
      boxShadow: {
        glow: "0 0 15px -3px rgba(14, 165, 233, 0.15)",
        card: "0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px -1px rgba(0, 0, 0, 0.1)",
      }
    },
  },
  plugins: [],
}

