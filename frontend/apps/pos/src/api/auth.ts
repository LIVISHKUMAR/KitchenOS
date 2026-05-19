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
