import { create } from 'zustand';

// 内联 API 调用（避免 Turbopack 路径别名解析问题）
const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

async function apiRequest(path: string, options: RequestInit = {}): Promise<any> {
  const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> || {}),
  };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers });
  const data = await res.json();

  if (!res.ok) {
    throw { response: { data, status: res.status } };
  }
  return data;
}

interface User {
  id: number;
  username: string;
  email: string;
  role: string;
  avatar: string;
  is_admin: boolean;
}

interface AuthState {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (data: { username: string; password: string; email: string; role: string }) => Promise<void>;
  logout: () => void;
  fetchMe: () => Promise<void>;
  isAuthenticated: () => boolean;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: null,
  loading: false,

  login: async (username, password) => {
    set({ loading: true });
    try {
      const res = await apiRequest('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ username, password }),
      });
      const { access_token, refresh_token } = res;
      localStorage.setItem('access_token', access_token);
      if (refresh_token) localStorage.setItem('refresh_token', refresh_token);

      const me = await apiRequest('/auth/me');
      const user = me.data || me;
      set({ user, token: access_token });
    } finally {
      set({ loading: false });
    }
  },

  register: async (data) => {
    set({ loading: true });
    try {
      await apiRequest('/auth/register', {
        method: 'POST',
        body: JSON.stringify(data),
      });
    } finally {
      set({ loading: false });
    }
  },

  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    set({ user: null, token: null });
    window.location.href = '/login';
  },

  fetchMe: async () => {
    const token = localStorage.getItem('access_token');
    if (!token) return;
    try {
      const res = await apiRequest('/auth/me');
      const user = res.data || res;
      set({ user, token });
    } catch {
      localStorage.removeItem('access_token');
    }
  },

  isAuthenticated: () => {
    return !!localStorage.getItem('access_token');
  },
}));
