import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
  },
  define: {
    CESIUM_BASE_URL: JSON.stringify('/cesium'),
  },
})
