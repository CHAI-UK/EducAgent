import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  return {
    root: "web",
    base: "./",
    plugins: [react()],
    server: {
      proxy: {
        "/api": env.EDUCAGENT_API_TARGET ?? "http://127.0.0.1:8000",
      },
    },
    build: {
      outDir: "dist",
      emptyOutDir: true,
    },
  };
});
