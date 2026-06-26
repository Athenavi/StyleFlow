import { create } from 'zustand';
import api from '@/lib/api';

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
  setAuth: (user: User, token: string, refreshToken?: string) => void;
  login: (username: string, password: string) => Promise<void>;
  register: (data: { username: string; password: string; email: string; role: string }) => Promise<void>;
  logout: () => void;
  fetchMe: () => Promise<void>;
  isAuthenticated: () => boolean;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  token: null,
  loading: false,

  setAuth: (user, token, refreshToken) => {
    localStorage.setItem('access_token', token);
    if (refreshToken) localStorage.setItem('refresh_token', refreshToken);
    set({ user, token });
  },

  login: async (username, password) => {
    set({ loading: true });
    try {
      const res: any = await api.post('/auth/login', { username, password });
      const { access_token, refresh_token } = res;
      // Fetch user info
      localStorage.setItem('access_token', access_token);
      const meRes: any = await api.get('/auth/me');
      const user = meRes.data || meRes;
      get().setAuth(user, access_token, refresh_token);
    } finally {
      set({ loading: false });
    }
  },

  register: async (data) => {
    set({ loading: true });
    try {
      await api.post('/auth/register', data);
    } finally {
      set({ loading: false });
    }
  },

  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    set({ user: null, token: null });
  },

  fetchMe: async () => {
    const token = localStorage.getItem('access_token');
    if (!token) return;
    try {
      const res: any = await api.get('/auth/me');
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
