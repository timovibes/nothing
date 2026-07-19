// registers Tailwind as a Vite plugin — this replaces the old PostCSS-based integration entirely in v4.

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
});