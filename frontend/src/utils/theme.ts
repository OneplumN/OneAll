export type ThemeMode = 'light' | 'dark';

const STORAGE_KEY = 'oa-theme-mode';

export function applyThemeMode(mode: ThemeMode) {
  const root = document.documentElement;
  root.dataset.theme = mode;
  root.classList.toggle('dark', mode === 'dark');
}

export function loadThemeMode(): ThemeMode {
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored === 'light' || stored === 'dark') return stored;
  const prefersDark = window.matchMedia?.('(prefers-color-scheme: dark)')?.matches ?? false;
  return prefersDark ? 'dark' : 'light';
}

export function persistThemeMode(mode: ThemeMode) {
  localStorage.setItem(STORAGE_KEY, mode);
}

