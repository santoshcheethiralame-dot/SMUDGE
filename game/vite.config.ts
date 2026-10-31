import { defineConfig } from "vite";

// Ports are overridable so several checkouts can run side by side:
//   SMUDGE_GAME_PORT=8892 SMUDGE_API_PORT=8893 npm run dev
const api = process.env.SMUDGE_API_PORT ?? "8873";

const proxy = { "/api": `http://localhost:${api}` };

// Demo from the production build: `npm run build && npm run preview`. Preview needs its own proxy,
// or /api 404s and the game quietly falls back to the fixture.
export default defineConfig({
  server: { port: Number(process.env.SMUDGE_GAME_PORT ?? 8872), proxy },
  preview: { port: Number(process.env.SMUDGE_GAME_PORT ?? 8872), proxy },
  build: { chunkSizeWarningLimit: 2000 },
});
