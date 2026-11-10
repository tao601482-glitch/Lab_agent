import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue(), vueDevTools()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    proxy: {
      //API接口代理
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      },
      //静态文件代理
      '/uploads': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      },
      // 兼容数据库中历史图片的 /upload/ 地址
      '/upload': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      }
    }
  }
})
