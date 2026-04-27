import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#18202f",
        muted: "#647084",
        line: "#d9dee8",
        panel: "#ffffff",
        canvas: "#f5f7fb",
        brand: "#216869",
        accent: "#d77a61"
      },
      boxShadow: {
        soft: "0 10px 30px rgba(22, 31, 48, 0.08)"
      }
    }
  },
  plugins: []
};
export default config;

