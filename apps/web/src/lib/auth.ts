/**
 * Auth utilities for DoruMake Admin Panel
 */

const TOKEN_KEY = 'dorumake_token';
const TOKEN_EXPIRY_KEY = 'dorumake_token_expiry';

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface AuthToken {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export const authService = {
  /**
   * Login and get JWT token
   */
  async login(credentials: LoginCredentials): Promise<AuthToken> {
    const formData = new URLSearchParams();
    formData.append('username', credentials.username);
    formData.append('password', credentials.password);

    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Login failed' }));
      throw new Error(error.detail || 'Login failed');
    }

    const data: AuthToken = await response.json();

    // Store token in localStorage
    this.setToken(data.access_token, data.expires_in);

    return data;
  },

  /**
   * Logout - clear stored token
   */
  logout(): void {
    if (typeof window !== 'undefined') {
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(TOKEN_EXPIRY_KEY);
    }
  },

  /**
   * Get stored token
   */
  getToken(): string | null {
    if (typeof window === 'undefined') return null;

    const expiry = localStorage.getItem(TOKEN_EXPIRY_KEY);
    if (expiry && Date.now() > parseInt(expiry, 10)) {
      // Token expired
      this.logout();
      return null;
    }

    return localStorage.getItem(TOKEN_KEY);
  },

  /**
   * Set token with expiry
   */
  setToken(token: string, expiresIn: number): void {
    if (typeof window === 'undefined') return;

    localStorage.setItem(TOKEN_KEY, token);
    // Set expiry 5 minutes before actual expiry for safety
    const expiryTime = Date.now() + (expiresIn - 300) * 1000;
    localStorage.setItem(TOKEN_EXPIRY_KEY, expiryTime.toString());
  },

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    return !!this.getToken();
  },

  /**
   * Get auth headers for API requests
   */
  getAuthHeaders(): Record<string, string> {
    const token = this.getToken();
    if (!token) return {};
    return {
      Authorization: `Bearer ${token}`,
    };
  },
};
