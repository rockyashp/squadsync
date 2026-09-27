import React, { createContext, useContext, useState, useEffect } from 'react';
import { authApi } from '../api/authApi';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('squadsync_token'));
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('squadsync_user');
    try {
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });
  const [loading, setLoading] = useState(true);

  // Modal control state
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [authModalMode, setAuthModalMode] = useState('login'); // 'login' | 'register'

  // Hydrate user profile on mount if token exists
  useEffect(() => {
    async function loadUser() {
      const storedToken = localStorage.getItem('squadsync_token');
      if (!storedToken) {
        setLoading(false);
        return;
      }

      try {
        const res = await authApi.getMe();
        if (res?.data) {
          setUser(res.data);
          localStorage.setItem('squadsync_user', JSON.stringify(res.data));
        }
      } catch (err) {
        console.warn('Session expired or invalid, logging out.');
        localStorage.removeItem('squadsync_token');
        localStorage.removeItem('squadsync_user');
        setToken(null);
        setUser(null);
      } finally {
        setLoading(false);
      }
    }

    loadUser();
  }, []);

  const openLoginModal = () => {
    setAuthModalMode('login');
    setIsAuthModalOpen(true);
  };

  const openRegisterModal = () => {
    setAuthModalMode('register');
    setIsAuthModalOpen(true);
  };

  const closeAuthModal = () => {
    setIsAuthModalOpen(false);
  };

  const login = async (usernameOrEmail, password) => {
    const res = await authApi.login({
      username_or_email: usernameOrEmail,
      password: password,
    });

    const accessToken = res.data?.access_token || res.access_token;
    if (!accessToken) {
      throw new Error('Authentication token missing from response.');
    }

    localStorage.setItem('squadsync_token', accessToken);
    setToken(accessToken);

    // Fetch full profile details
    try {
      const meRes = await authApi.getMe();
      if (meRes?.data) {
        setUser(meRes.data);
        localStorage.setItem('squadsync_user', JSON.stringify(meRes.data));
      }
    } catch (e) {
      const fallbackUser = {
        email: usernameOrEmail.includes('@') ? usernameOrEmail : undefined,
        username: usernameOrEmail,
        gamer_tag: usernameOrEmail,
      };
      setUser(fallbackUser);
      localStorage.setItem('squadsync_user', JSON.stringify(fallbackUser));
    }

    closeAuthModal();
    return res;
  };

  const register = async (userData) => {
    // 1. Register account
    await authApi.register({
      username: userData.username,
      email: userData.email,
      password: userData.password,
    });

    // 2. Auto-login on successful registration
    return login(userData.email, userData.password);
  };

  const logout = async () => {
    try {
      await authApi.logout();
    } catch (e) {
      // Ignore network errors on logout
    } finally {
      localStorage.removeItem('squadsync_token');
      localStorage.removeItem('squadsync_user');
      setToken(null);
      setUser(null);
    }
  };

  const value = {
    user,
    token,
    loading,
    isAuthenticated: !!token && !!user,
    isAdmin: !!user?.is_admin,
    isAuthModalOpen,
    authModalMode,
    setAuthModalMode,
    openLoginModal,
    openRegisterModal,
    closeAuthModal,
    login,
    register,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
