"use client";

import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import type { AuthError, Session, User } from "@supabase/supabase-js";
import { supabase } from "@/lib/supabase";

type EmailAuthCredentials = {
  email: string;
  password: string;
  emailRedirectTo?: string;
};

type EmailAuthResult = {
  error: AuthError | null;
  hasSession: boolean;
  requiresEmailConfirmation: boolean;
};

type OAuthAuthResult = {
  error: AuthError | null;
};

type SignOutResult = {
  error: AuthError | null;
};

type AuthContextValue = {
  user: User | null;
  session: Session | null;
  loading: boolean;
  signIn: (credentials: EmailAuthCredentials) => Promise<EmailAuthResult>;
  signUp: (credentials: EmailAuthCredentials) => Promise<EmailAuthResult>;
  signInWithGoogle: (redirectTo: string) => Promise<OAuthAuthResult>;
  signOut: () => Promise<SignOutResult>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;

    async function hydrateSession() {
      // Check if there's an access_token in the URL hash (OAuth callback)
      if (typeof window !== "undefined" && window.location.hash.includes("access_token")) {
        const hashParams = new URLSearchParams(window.location.hash.substring(1));
        const accessToken = hashParams.get("access_token");
        const refreshToken = hashParams.get("refresh_token");

        if (accessToken && refreshToken) {
          const { data, error } = await supabase.auth.setSession({
            access_token: accessToken,
            refresh_token: refreshToken,
          });

          if (!active) return;

          if (!error && data.session) {
            // Clean up the URL hash immediately
            window.history.replaceState(null, "", window.location.pathname + window.location.search);
            // Don't set state here - onAuthStateChange will handle it
            // This ensures proper persistence before state updates
            return;
          }
        }
      }

      // Small delay to ensure any pending session persistence completes
      await new Promise((resolve) => setTimeout(resolve, 50));

      const {
        data: { session: nextSession },
      } = await supabase.auth.getSession();

      if (!active) {
        return;
      }

      setSession(nextSession);
      setUser(nextSession?.user ?? null);
      setLoading(false);
    }

    void hydrateSession();

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, nextSession) => {
      if (!active) {
        return;
      }

      setSession(nextSession);
      setUser(nextSession?.user ?? null);
      setLoading(false);
    });

    return () => {
      active = false;
      subscription.unsubscribe();
    };
  }, []);

  async function signIn(
    credentials: EmailAuthCredentials
  ): Promise<EmailAuthResult> {
    const { data, error } = await supabase.auth.signInWithPassword(credentials);

    if (!error) {
      setSession(data.session);
      setUser(data.session?.user ?? null);
    }

    return {
      error,
      hasSession: Boolean(data.session),
      requiresEmailConfirmation: false,
    };
  }

  async function signUp(
    credentials: EmailAuthCredentials
  ): Promise<EmailAuthResult> {
    const { email, password, emailRedirectTo } = credentials;
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
      options: emailRedirectTo ? { emailRedirectTo } : undefined,
    });

    if (!error) {
      setSession(data.session);
      setUser(data.session?.user ?? null);
    }

    return {
      error,
      hasSession: Boolean(data.session),
      requiresEmailConfirmation: !error && !data.session,
    };
  }

  async function signInWithGoogle(
    redirectTo: string
  ): Promise<OAuthAuthResult> {
    const { error } = await supabase.auth.signInWithOAuth({
      provider: "google",
      options: {
        redirectTo,
      },
    });

    return { error };
  }

  async function signOut(): Promise<SignOutResult> {
    const { error } = await supabase.auth.signOut();

    if (!error) {
      setSession(null);
      setUser(null);
    }

    return { error };
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        session,
        loading,
        signIn,
        signUp,
        signInWithGoogle,
        signOut,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider.");
  }

  return context;
}
