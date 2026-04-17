import { defineStore } from 'pinia';
import { ref } from 'vue';

import { applyThemeMode, loadThemeMode, persistThemeMode, type ThemeMode } from '@/utils/theme';

export const useThemeStore = defineStore('theme', () => {
  const mode = ref<ThemeMode>(loadThemeMode());

  function setMode(nextMode: ThemeMode) {
    mode.value = nextMode;
    persistThemeMode(nextMode);
    applyThemeMode(nextMode);
  }

  function toggle() {
    setMode(mode.value === 'dark' ? 'light' : 'dark');
  }

  return { mode, setMode, toggle };
});

