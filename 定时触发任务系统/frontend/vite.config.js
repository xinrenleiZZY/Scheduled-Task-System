import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  build: {
    outDir: '../backend/static',
    emptyOutDir: true
  },
  server: {
    port: 6130,
    proxy: {
      '/api': {
        target: 'http://localhost:6100',
        changeOrigin: true
      }
    }
  }
})
