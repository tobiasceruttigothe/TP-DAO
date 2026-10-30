import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: { port: 5173 },
  // Ant Design solo ya ocupa ~600 kB; las paginas se cargan aparte (React.lazy)
  build: { chunkSizeWarningLimit: 800 },
})
