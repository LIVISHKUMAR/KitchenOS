import apiClient from './client';

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface RegisterResponse {
  tenant: { id: string; name: string; slug: string; email: string };
  user: { id: string; email: string; first_name: string; role: string };
  branch_id: string;
  access_token: string;
  refresh_token: string;
}

export interface TokenPayload {
  sub: string;
  tenant_id: string;
  branch_id: string;
  role: string;
  exp: number;
}

export function decodeToken(token: string): TokenPayload | null {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return payload as TokenPayload;
  } catch {
    return null;
  }
}

export function getAuthState(): { isAuthenticated: boolean; branchId: string | null; tenantId: string | null; role: string | null } {
  const token = localStorage.getItem('access_token');
  if (!token) return { isAuthenticated: false, branchId: null, tenantId: null, role: null };
  const payload = decodeToken(token);
  if (!payload || payload.exp * 1000 < Date.now()) {
    return { isAuthenticated: false, branchId: null, tenantId: null, role: null };
  }
  return {
    isAuthenticated: true,
    branchId: payload.branch_id,
    tenantId: payload.tenant_id,
    role: payload.role,
  };
}

export const authApi = {
  login: (email: string, password: string) => {
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);
    return apiClient.post<LoginResponse>('/auth/token', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
  },

  register: (data: { name: string; email: string; password: string; phone?: string }) =>
    apiClient.post<RegisterResponse>('/auth/register', data),

  refresh: (refreshToken: string) =>
    apiClient.post<LoginResponse>('/auth/refresh', { refresh_token: refreshToken }),

  logout: () => apiClient.post('/auth/logout'),
};
