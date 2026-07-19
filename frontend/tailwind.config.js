// defines our exact, locked color tokens and font families — nothing here should ever be
// overridden with an arbitrary hex in a component.

/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: "#000000",
        secondary: "#919191",
        tertiary: "#919191",
        error: "#FF5449",
        success: "#1E7A46",
        surface: "#FFFFFF",
        border: "rgba(0, 0, 0, 0.08)",
      },
      fontFamily: {
        display: ["Archivo", "sans-serif"],
        body: ["IBM Plex Sans", "sans-serif"],
        mono: ["IBM Plex Mono", "monospace"],
      },
    },
  },
  plugins: [],
};