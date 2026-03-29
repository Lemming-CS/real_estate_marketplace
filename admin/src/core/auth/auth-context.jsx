import { createContext, useContext, useEffect, useMemo, useState } from 'react';

import { apiBlobRequest, apiRequest, isApiError } from '@/core/api/client';

const AUTH_STORAGE_KEY = 'marketplace-admin-auth';

const AuthContext = createContext(null);

function readStoredSession() {
  const rawValue = window.localStorage.getItem(AUTH_STORAGE_KEY);
  if (!rawValue) {
    return null;
  }

  try {
    return JSON.parse(rawValue);
  } catch {
    window.localStorage.removeItem(AUTH_STORAGE_KEY);
    return null;
  }
}

export function AuthProvider({ children }) {
  const [session, setSession] = useState(() => readStoredSession());
  const [currentUser, setCurrentUser] = useState(null);
  const [isBootstrapping, setIsBootstrapping] = useState(true);

  useEffect(() => {
    async function bootstrap() {
      const stored = readStoredSession();
      if (!stored?.accessToken) {
        setIsBootstrapping(false);
        return;
      }

      try {
        const user = await apiRequest('/auth/me', { token: stored.accessToken });
        if (!user.roles.includes('admin')) {
          throw new Error('Admin role required.');
        }
        setSession(stored);
        setCurrentUser(user);
      } catch {
        window.localStorage.removeItem(AUTH_STORAGE_KEY);
        setSession(null);
        setCurrentUser(null);
      } finally {
        setIsBootstrapping(false);
      }
    }

    bootstrap();
  }, []);

  const value = useMemo(
    () => ({
      currentUser,
      accessToken: session?.accessToken ?? null,
      refreshToken: session?.refreshToken ?? null,
      isAuthenticated: Boolean(session?.accessToken && currentUser),
      isBootstrapping,
      async login({ email, password }) {
        const response = await apiRequest('/admin/auth/login', {
          method: 'POST',
          body: { email, password },
        });

        const nextSession = {
          accessToken: response.access_token,
          refreshToken: response.refresh_token,
        };

        window.localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(nextSession));
        setSession(nextSession);
        setCurrentUser(response.user);
        return response;
      },
      async logout() {
        const refreshToken = session?.refreshToken;
        if (refreshToken) {
          try {
            await apiRequest('/auth/logout', {
              method: 'POST',
              body: { refresh_token: refreshToken },
            });
          } catch (error) {
            if (!isApiError(error)) {
              throw error;
            }
          }
        }

        window.localStorage.removeItem(AUTH_STORAGE_KEY);
        setSession(null);
        setCurrentUser(null);
      },
      async authenticatedRequest(path, options = {}) {
        if (!session?.accessToken) {
          throw new Error('No active session.');
        }
        return apiRequest(path, { ...options, token: session.accessToken });
      },
      async authenticatedBlobRequest(path, options = {}) {
        if (!session?.accessToken) {
          throw new Error('No active session.');
        }
        return apiBlobRequest(path, { ...options, token: session.accessToken });
      },
    }),
    [currentUser, isBootstrapping, session],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used inside AuthProvider.');
  }
  return context;
}
