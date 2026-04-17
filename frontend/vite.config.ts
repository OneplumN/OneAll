import { fileURLToPath, URL } from 'node:url';

import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';

export default defineConfig({
  plugins: [vue()],
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) {
            return;
          }
          if (id.includes('echarts')) {
            return 'vendor-echarts';
          }
          if (id.includes('xlsx')) {
            return 'vendor-xlsx';
          }
          if (id.includes('highlight.js')) {
            return 'vendor-highlight';
          }
          if (id.includes('element-plus') || id.includes('@element-plus')) {
            return 'vendor-element';
          }
          if (
            id.includes('/vue/') ||
            id.includes('@vue') ||
            id.includes('pinia') ||
            id.includes('vue-router') ||
            id.includes('vue-i18n')
          ) {
            return 'vendor-vue';
          }
          if (id.includes('axios') || id.includes('dayjs')) {
            return 'vendor-utils';
          }
          return 'vendor';
        }
      }
    }
  },
  server: {
    port: 5173,
    host: '0.0.0.0',
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      }
    }
  },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  }
});
