'use client';

import { useState, useEffect, useCallback } from 'react';
import { authService } from '@/lib/auth';

interface User {
  username: string;
  email: string;
}

interface UseAuthReturn {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

// Decode JWT token to get user info
function decodeToken(token: string): { sub: string; exp: number } | null {
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    );
    return JSON.parse(jsonPayload);
  } catch {
    return null;
  }
}

export function useAuth(): UseAuthReturn {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check for existing token on mount
    const token = authService.getToken();
    if (token) {
      const decoded = decodeToken(token);
      if (decoded) {
        setUser({
          username: decoded.sub,
          email: `${decoded.sub}@dorufinansal.com`,
        });
      }
    }
    setIsLoading(false);
  }, []);

  const login = useCallback(async (username: string, password: string) => {
    setIsLoading(true);
    try {
      const result = await authService.login({ username, password });
      const decoded = decodeToken(result.access_token);
      if (decoded) {
        setUser({
          username: decoded.sub,
          email: `${decoded.sub}@dorufinansal.com`,
        });
      }
    } finally {
      setIsLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    authService.logout();
    setUser(null);
  }, []);

  return {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    logout,
  };
}
