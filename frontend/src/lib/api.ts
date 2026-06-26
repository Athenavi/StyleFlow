// 简单的 fetch 封装（替代 axios，避免路径别名问题）
const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

async function request(path: string, options: RequestInit = {}): Promise<any> {
  const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> || {}),
  };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers });

  if (res.status === 401 && typeof window !== 'undefined') {
    // Try refresh
    const refreshToken = localStorage.getItem('refresh_token');
    if (refreshToken) {
      const refreshRes = await fetch(`${BASE_URL}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
      if (refreshRes.ok) {
        const refreshData = await refreshRes.json();
        const newToken = refreshData.access_token;
        localStorage.setItem('access_token', newToken);
        headers['Authorization'] = `Bearer ${newToken}`;
        const retryRes = await fetch(`${BASE_URL}${path}`, { ...options, headers });
        if (retryRes.status === 204) return null;
        return retryRes.json();
      } else {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        throw new Error('Session expired');
      }
    } else {
      window.location.href = '/login';
      throw new Error('Not authenticated');
    }
  }

  if (res.status === 204) {
    return null;  // No Content
  }

  const data = await res.json();
  if (!res.ok) {
    throw { response: { data, status: res.status } };
  }
  return data;
}

const api = {
  get: (path: string, params?: any) => {
    const query = params ? '?' + new URLSearchParams(params).toString() : '';
    return request(`${path}${query}`);
  },
  post: (path: string, body?: any) =>
    request(path, { method: 'POST', body: body ? JSON.stringify(body) : undefined }),
  put: (path: string, body?: any) =>
    request(path, { method: 'PUT', body: body ? JSON.stringify(body) : undefined }),
  patch: (path: string, body?: any) =>
    request(path, { method: 'PATCH', body: body ? JSON.stringify(body) : undefined }),
  delete: (path: string) =>
    request(path, { method: 'DELETE' }),
};

export default api;
