import React, { createContext, useContext, useCallback, useEffect, useState } from 'react';
import {
  clearAuthToken as clearStoredToken,
  fetchProfile,
  loginUser,
  registerUser,
  setAuthToken as storeToken,
} from '../services/agentClient';

const AuthContext = createContext(null);

function usePersistedSession() {
  const storageAvailable =
    typeof window !== 'undefined' && typeof window.localStorage !== 'undefined';

  const readToken = useCallback(() => {
    if (!storageAvailable) {
      return null;
    }
    return window.localStorage.getItem('dailyDripToken');
  }, [storageAvailable]);

  const readUser = useCallback(() => {
    if (!storageAvailable) {
      return null;
    }
    const raw = window.localStorage.getItem('dailyDripUser');
    return raw ? JSON.parse(raw) : null;
  }, [storageAvailable]);

  const writeSession = useCallback(
    (token, user) => {
      if (!storageAvailable) {
        return;
      }
      if (token) {
        window.localStorage.setItem('dailyDripToken', token);
      } else {
        window.localStorage.removeItem('dailyDripToken');
      }
      if (user) {
        window.localStorage.setItem('dailyDripUser', JSON.stringify(user));
      } else {
        window.localStorage.removeItem('dailyDripUser');
      }
    },
    [storageAvailable],
  );

  return { readToken, readUser, writeSession };
}

export function AuthProvider({ children }) {
  const { readToken, readUser, writeSession } = usePersistedSession();
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [initializing, setInitializing] = useState(true);
  const [authLoading, setAuthLoading] = useState(false);
  const [error, setError] = useState(null);

  const applySession = useCallback(
    (nextToken, nextUser) => {
      setToken(nextToken);
      setUser(nextUser);
      if (nextToken) {
        storeToken(nextToken);
      } else {
        clearStoredToken();
      }
      writeSession(nextToken, nextUser);
    },
    [writeSession],
  );

  useEffect(() => {
    const savedToken = readToken();
    const savedUser = readUser();
    if (!savedToken) {
      setInitializing(false);
      return;
    }
    applySession(savedToken, savedUser);
    fetchProfile()
      .then((profile) => {
        applySession(savedToken, profile);
      })
      .catch(() => {
        applySession(null, null);
      })
      .finally(() => {
        setInitializing(false);
      });
  }, [readToken, readUser, applySession]);

  const handleAuth = useCallback(async (action, credentials) => {
    setAuthLoading(true);
    setError(null);
    try {
      const data = await action(credentials);
      applySession(data.token, data.user);
      return data.user;
    } catch (err) {
      const message = err?.message || 'Authentication failed.';
      setError(message);
      throw err;
    } finally {
      setAuthLoading(false);
    }
  }, [applySession]);

  const login = useCallback(
    (credentials) => handleAuth(loginUser, credentials),
    [handleAuth],
  );

  const register = useCallback(
    (details) => handleAuth(registerUser, details),
    [handleAuth],
  );

  const logout = useCallback(() => {
    applySession(null, null);
  }, [applySession]);

  const refreshProfile = useCallback(async () => {
    if (!token) {
      return null;
    }
    try {
      const profile = await fetchProfile();
      applySession(token, profile);
      return profile;
    } catch (err) {
      applySession(null, null);
      return null;
    }
  }, [token, applySession]);

  const value = {
    user,
    token,
    initializing,
    authLoading,
    error,
    login,
    register,
    logout,
    refreshProfile,
    clearError: () => setError(null),
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}
