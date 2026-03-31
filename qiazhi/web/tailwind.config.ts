import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: "#1a1a1e",
        mist: "#e8e4dc",
        jade: "#2d6a4f",
      },
    },
  },
  plugins: [],
};

export default config;
