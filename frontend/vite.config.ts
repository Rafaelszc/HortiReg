import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

const proxy = {
  "/auth": "http://127.0.0.1:8000",
  "/pedidos": "http://127.0.0.1:8000",
  "/produtos": "http://127.0.0.1:8000",
};

export default defineConfig({
  plugins: [react()],
  // 127.0.0.1 explícito: "localhost" pode resolver para ::1 e o wait-on do CI não conecta.
  server: { host: "127.0.0.1", proxy },
  preview: { host: "127.0.0.1", proxy },
});
