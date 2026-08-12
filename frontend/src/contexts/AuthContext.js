import { createContext, useContext, useState, useCallback, useEffect } from "react";
import axios from "axios";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(() => localStorage.getItem("firma_token") || null);

  const checkAuth = useCallback(async () => {
    const t = localStorage.getItem("firma_token");
    if (!t) { setLoading(false); return; }
    try {
      const res = await axios.get(`${API}/auth/me`, {
        headers: { Authorization: `Bearer ${t}` },
        withCredentials: true,
      });
      setUser(res.data);
      setToken(t);
    } catch {
      localStorage.removeItem("firma_token");
      setUser(null);
      setToken(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { checkAuth(); }, [checkAuth]);

  const login = useCallback((userData) => {
    if (userData.token) {
      localStorage.setItem("firma_token", userData.token);
      setToken(userData.token);
    }
    setUser(userData);
  }, []);

  const logout = useCallback(async () => {
    try {
      await axios.post(`${API}/auth/logout`, {}, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        withCredentials: true,
      });
    } catch { /* ignore */ }
    localStorage.removeItem("firma_token");
    setUser(null);
    setToken(null);
  }, [token]);

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, token }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
