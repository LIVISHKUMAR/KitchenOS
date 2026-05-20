import { create } from 'zustand';
import { authApi, getAuthState, type TokenPayload } from '../api/auth';

interface AuthState {
  isAuthenticated: boolean;
  branchId: string | null;
  tenantId: string | null;
  role: string | null;
  user: TokenPayload | null;
  error: string | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<boolean>;
  logout: () => void;
  checkAuth: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  isAuthenticated: false,
  branchId: null,
  tenantId: null,
  role: null,
  user: null,
  error: null,
  isLoading: false,

  checkAuth: () => {
    const state = getAuthState();
    set({
      isAuthenticated: state.isAuthenticated,
      branchId: state.branchId,
      tenantId: state.tenantId,
      role: state.role,
    });
  },

  login: async (email: string, password: string) => {
    set({ isLoading: true, error: null });
    try {
      const res = await authApi.login(email, password);
      localStorage.setItem('access_token', res.data.access_token);
      localStorage.setItem('refresh_token', res.data.refresh_token);
      const state = getAuthState();
      set({
        isAuthenticated: true,
        branchId: state.branchId,
        tenantId: state.tenantId,
        role: state.role,
        isLoading: false,
      });
      return true;
    } catch (err: any) {
      const message = err.response?.data?.detail || 'Login failed';
      set({ error: message, isLoading: false });
      return false;
    }
  },

  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    set({ isAuthenticated: false, branchId: null, tenantId: null, role: null });
  },
}));
