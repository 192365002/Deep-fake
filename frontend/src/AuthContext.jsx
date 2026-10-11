// ─── Auth Context — Supabase Authentication + Session Restoration ─────────────
import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { supabase, isSupabaseConfigured } from './supabase';
import { healthCheck } from './api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [backendOnline, setBackendOnline] = useState(null);

  // Backend health check on mount
  useEffect(() => {
    healthCheck()
      .then(() => setBackendOnline(true))
      .catch(() => setBackendOnline(false));
  }, []);

  // ─── Token and User Persistence Helper ────────────────────────────────────────
  const persistUser = useCallback((userData, token) => {
    if (userData) {
      localStorage.setItem('ss_user', JSON.stringify(userData));
      if (token) localStorage.setItem('auth_token', token);
      setUser(userData);
    } else {
      localStorage.removeItem('ss_user');
      localStorage.removeItem('auth_token');
      setUser(null);
    }
  }, []);

  // ─── Session Restoration & Live Auth State Listener ───────────────────────────
  useEffect(() => {
    let mounted = true;

    if (isSupabaseConfigured()) {
      // 1. Get initial session
      supabase.auth.getSession().then(({ data: { session } }) => {
        if (!mounted) return;
        if (session?.user) {
          const u = session.user;
          const userData = {
            uid: u.id,
            id: u.id,
            email: u.email,
            displayName: u.user_metadata?.full_name || u.user_metadata?.name || u.email?.split('@')[0],
            role: u.user_metadata?.role || 'user',
          };
          persistUser(userData, session.access_token);
        } else {
          // Restore from localStorage if offline/demo
          const stored = localStorage.getItem('ss_user');
          if (stored) {
            try { setUser(JSON.parse(stored)); } catch {}
          }
        }
        setLoading(false);
      });

      // 2. Subscribe to auth changes (login, logout, token refresh)
      const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
        if (!mounted) return;
        if (session?.user) {
          const u = session.user;
          const userData = {
            uid: u.id,
            id: u.id,
            email: u.email,
            displayName: u.user_metadata?.full_name || u.user_metadata?.name || u.email?.split('@')[0],
            role: u.user_metadata?.role || 'user',
          };
          persistUser(userData, session.access_token);
        } else if (event === 'SIGNED_OUT') {
          persistUser(null, null);
        }
      });

      return () => {
        mounted = false;
        subscription?.unsubscribe();
      };
    } else {
      // ── Demo / Offline mode fallback ──
      const stored = localStorage.getItem('ss_user');
      if (stored) {
        try { setUser(JSON.parse(stored)); } catch {}
      }
      setLoading(false);
    }
  }, [persistUser]);

  // ─── Email & Password Login ───────────────────────────────────────────────────
  const login = async (email, password) => {
    if (isSupabaseConfigured()) {
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });

      if (error) throw error;

      const u = data.user;
      const userData = {
        uid: u.id,
        id: u.id,
        email: u.email,
        displayName: u.user_metadata?.full_name || u.user_metadata?.name || u.email?.split('@')[0],
        role: u.user_metadata?.role || 'user',
      };
      persistUser(userData, data.session?.access_token);
      return userData;
    } else {
      // Demo mode fallback
      await new Promise((r) => setTimeout(r, 600));
      const cleanEmail = email.replace(/[^a-zA-Z0-9]/g, '_');
      const token = 'demo_' + cleanEmail;
      const userData = { uid: cleanEmail, id: cleanEmail, email, displayName: email.split('@')[0], role: 'user' };
      persistUser(userData, token);
      return userData;
    }
  };

  // ─── Sign Up ──────────────────────────────────────────────────────────────────
  const signUp = async (email, password, displayName) => {
    if (isSupabaseConfigured()) {
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: {
            full_name: displayName || email.split('@')[0],
            name: displayName || email.split('@')[0],
          },
        },
      });

      if (error) throw error;

      if (data.session) {
        const u = data.user;
        const userData = {
          uid: u.id,
          id: u.id,
          email: u.email,
          displayName: u.user_metadata?.full_name || displayName || email.split('@')[0],
          role: 'user',
        };
        persistUser(userData, data.session.access_token);
        return userData;
      }

      return {
        message: 'Registration successful! Please check your email to verify your account.',
        requiresEmailConfirmation: true,
      };
    } else {
      return login(email, password);
    }
  };

  // ─── Google OAuth Sign-In ─────────────────────────────────────────────────────
  const loginWithGoogle = async () => {
    if (isSupabaseConfigured()) {
      const { error } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: {
          redirectTo: window.location.origin + '/home',
        },
      });
      if (error) throw error;
    } else {
      await new Promise((r) => setTimeout(r, 400));
      const userData = { uid: 'google_demo_uuid_1010', id: 'google_demo_uuid_1010', email: 'demo@socialshield.ai', displayName: 'Demo Google User', role: 'user' };
      persistUser(userData, 'demo_google_token_' + Date.now());
      return userData;
    }
  };

  // ─── Password Reset Flow ──────────────────────────────────────────────────────
  const resetPassword = async (email) => {
    if (isSupabaseConfigured()) {
      const { error } = await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: window.location.origin + '/auth?mode=reset',
      });
      if (error) throw error;
      return { message: 'Password reset link sent to your email.' };
    } else {
      return { message: 'Demo mode: password reset instructions sent.' };
    }
  };

  const updatePassword = async (newPassword) => {
    if (isSupabaseConfigured()) {
      const { error } = await supabase.auth.updateUser({
        password: newPassword,
      });
      if (error) throw error;
      return { message: 'Password updated successfully!' };
    }
    return { message: 'Password updated (demo).' };
  };

  // ─── Logout ───────────────────────────────────────────────────────────────────
  const logout = async () => {
    if (isSupabaseConfigured()) {
      try {
        await supabase.auth.signOut();
      } catch (err) {
        console.error('Supabase signOut error:', err);
      }
    }
    persistUser(null, null);
  };

  // ─── Update User Profile Fields ───────────────────────────────────────────────
  const updateUser = async (fields) => {
    if (isSupabaseConfigured()) {
      try {
        const { error } = await supabase.auth.updateUser({
          data: fields,
        });
        if (error) throw error;
      } catch (err) {
        console.error('Supabase profile update failed:', err);
      }
    }
    setUser((prev) => {
      const next = { ...prev, ...fields };
      localStorage.setItem('ss_user', JSON.stringify(next));
      return next;
    });
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        backendOnline,
        login,
        signUp,
        loginWithGoogle,
        resetPassword,
        updatePassword,
        logout,
        updateUser,
        isSupabaseConfigured: isSupabaseConfigured(),
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
