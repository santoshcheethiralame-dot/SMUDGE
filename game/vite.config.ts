import { defineConfig } from "vite";

// Ports are overridable so several checkouts can run side by side:
//   SMUDGE_GAME_PORT=8892 SMUDGE_API_PORT=8893 npm run dev
const api = process.env.SMUDGE_API_PORT ?? "8873";

export default defineConfig({
  server: {
    port: Number(process.env.SMUDGE_GAME_PORT ?? 8872),
    proxy: { "/api": `http://localhost:${api}` },
  },
  build: { chunkSizeWarningLimit: 2000 },
});
