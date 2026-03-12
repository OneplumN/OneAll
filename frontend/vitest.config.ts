import { defineConfig } from 'vitest/config';
import vue from '@vitejs/plugin-vue';
import vueJsx from '@vitejs/plugin-vue-jsx';
import { fileURLToPath, URL } from 'node:url';

export default defineConfig({
  plugins: [vue(), vueJsx()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './vitest.setup.ts',
    pool: 'forks',
    maxWorkers: 1,
    include: ['src/**/*.{test,spec}.{ts,tsx}'],
    exclude: ['tests/e2e/**', 'node_modules/**', 'dist/**']
  }
});
