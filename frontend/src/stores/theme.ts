import { create } from 'zustand';

type ThemeMode = 'light' | 'dark' | 'system';

interface ThemeState {
  mode: ThemeMode;
  resolved: 'light' | 'dark';
  setMode: (mode: ThemeMode) => void;
  init: () => void;
}

function getSystemTheme(): 'light' | 'dark' {
  if (typeof window === 'undefined') return 'light';
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

function resolveMode(mode: ThemeMode): 'light' | 'dark' {
  if (mode === 'system') return getSystemTheme();
  return mode;
}

function applyTheme(resolved: 'light' | 'dark') {
  if (typeof document === 'undefined') return;
  document.documentElement.setAttribute('data-theme', resolved);
  document.documentElement.className = resolved;
}

export const useThemeStore = create<ThemeState>((set, get) => ({
  mode: 'light',
  resolved: 'light',

  setMode: (mode: ThemeMode) => {
    const resolved = resolveMode(mode);
    localStorage.setItem('styleflow-theme', mode);
    applyTheme(resolved);
    set({ mode, resolved });
  },

  init: () => {
    const saved = (localStorage.getItem('styleflow-theme') || 'light') as ThemeMode;
    const resolved = resolveMode(saved);
    applyTheme(resolved);
    set({ mode: saved, resolved });

    // Listen for system theme changes
    if (typeof window !== 'undefined') {
      window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
        if (get().mode === 'system') {
          const newResolved = getSystemTheme();
          applyTheme(newResolved);
          set({ resolved: newResolved });
        }
      });
    }
  },
}));
