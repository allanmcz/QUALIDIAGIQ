import type { Config } from "tailwindcss";

const tributiqBrand = {
  navy: "#0D1B4B",
  "navy-soft": "#1A2A6B",
  "navy-deep": "#070F2E",
  orange: "#F26E2A",
  "orange-soft": "#F89A6B",
  "orange-deep": "#C8541C",
  white: "#FFFFFF",
  "gray-50": "#F8F9FA",
  "gray-100": "#F1F3F5",
  "gray-200": "#E5E7EB",
  "gray-400": "#9CA3AF",
  "gray-700": "#374151",
  "gray-900": "#111827",
};

/**
 * Níveis de score — P0-08 WCAG AA.
 * - tokens base: gráficos / fundos;
 * - *-ink: texto sobre fundo claro (≥ 4,5:1 com #FFFFFF; validar se mudar o canvas).
 */
const scoreLevels = {
  indefinido: "#9CA3AF",
  "indefinido-ink": "#57534E",
  baixo: "#DC2626",
  "baixo-ink": "#991B1B",
  medio: "#EAB308",
  "medio-ink": "#A16207",
  alto: "#16A34A",
  "alto-ink": "#166534",
  excelente: "#0D7F3F",
  "excelente-ink": "#0A5C2E",
};

const config = {
  darkMode: ["class"],
  content: [
    "./pages/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./app/**/*.{ts,tsx}",
    "./src/**/*.{ts,tsx}",
  ],
  prefix: "",
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        brand: tributiqBrand,
        score: scoreLevels,
      },
      fontFamily: {
        sans: [
          "var(--font-inter)",
          "var(--font-montserrat)",
          "system-ui",
          "sans-serif",
        ],
        display: [
          "var(--font-inter)",
          "var(--font-montserrat)",
          "system-ui",
          "sans-serif",
        ],
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
        card: "0.75rem",
        pill: "9999px",
      },
      boxShadow: {
        card: "0 1px 3px rgba(13,27,75,0.06), 0 4px 12px rgba(13,27,75,0.04)",
        popover: "0 10px 30px rgba(13,27,75,0.15)",
        elevated: "0 20px 50px rgba(13,27,75,0.20)",
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
} satisfies Config;

export default config;
