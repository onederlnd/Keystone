import { createContext, useContext, useEffect, useState } from "react";
import * as api from "../api/client";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const token = localStorage.getItem("keystone_token");
    if (!token) {
      setLoading(false);
      return;
    }
    api
      .getMe()
      .then(setUser)
      .catch(() => localStorage.removeItem("keystone_token"))
      .finally(() => setLoading(false));
  }, []);

  async function signIn(email, password) {
    setError(null);
    try {
      const { access_token } = await api.login(email, password);
      localStorage.setItem("keystone_token", access_token);
      const me = await api.getMe();
      setUser(me);
      return true;
    } catch (err) {
      setError(
        err.response?.data?.detail || "Couldn't sign in — check your credentials."
      );
      return false;
    }
  }

  function signOut() {
    localStorage.removeItem("keystone_token");
    setUser(null);
    window.location.href = "/login";
  }

  return (
    <AuthContext.Provider value={{ user, loading, error, signIn, signOut }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
