import { computed, ref } from 'vue';
import { defineStore } from 'pinia';

type Theme = 'light' | 'dark';

type SidebarState = 'expanded' | 'collapsed';

export const useAppStore = defineStore('app', () => {
  const theme = ref<Theme>((localStorage.getItem('oneall_theme') as Theme) || 'light');
  const sidebar = ref<SidebarState>('expanded');
  const mainScrollLocked = ref(false);

  const isDark = computed(() => theme.value === 'dark');

  function toggleTheme() {
    theme.value = theme.value === 'light' ? 'dark' : 'light';
    localStorage.setItem('oneall_theme', theme.value);
    document.documentElement.setAttribute('data-theme', theme.value);
  }

  function toggleSidebar() {
    sidebar.value = sidebar.value === 'expanded' ? 'collapsed' : 'expanded';
  }

  function setMainScrollLocked(locked: boolean) {
    mainScrollLocked.value = locked;
  }

  return {
    theme,
    sidebar,
    mainScrollLocked,
    isDark,
    toggleTheme,
    toggleSidebar,
    setMainScrollLocked
  };
});
