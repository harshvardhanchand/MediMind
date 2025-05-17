import React, { createContext, useState, useEffect, useContext, ReactNode } from 'react';
import { Session, User } from '@supabase/supabase-js';
import { supabaseClient } from '../services/supabase';
import * as SecureStore from 'expo-secure-store';

const AUTH_TOKEN_KEY = 'auth_token';

interface AuthContextType {
  session: Session | null;
  user: User | null;
  isLoading: boolean;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{children: ReactNode}> = ({ children }) => {
  const [session, setSession] = useState<Session | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchSession = async () => {
      try {
        const { data, error } = await supabaseClient.auth.getSession();
        if (error) {
          console.error('Error fetching session:', error);
          // Potentially handle error (e.g. set an error state)
        } else {
          setSession(data.session);
          setUser(data.session?.user ?? null);
          if (data.session?.access_token) {
            await SecureStore.setItemAsync(AUTH_TOKEN_KEY, data.session.access_token);
          } else {
            await SecureStore.deleteItemAsync(AUTH_TOKEN_KEY);
          }
        }
      } catch (e) {
        console.error('Unexpected error fetching session:', e);
      } finally {
        setIsLoading(false);
      }
    };

    fetchSession();

    const { data: authListenerData } = supabaseClient.auth.onAuthStateChange(
      async (_event, newSession) => {
        setSession(newSession);
        setUser(newSession?.user ?? null);
        if (newSession?.access_token) {
          await SecureStore.setItemAsync(AUTH_TOKEN_KEY, newSession.access_token);
        } else {
          await SecureStore.deleteItemAsync(AUTH_TOKEN_KEY);
        }
      }
    );

    return () => {
      authListenerData?.subscription.unsubscribe();
    };
  }, []);

  const signOut = async () => {
    setIsLoading(true); // Optional: indicate loading during sign out
    const { error } = await supabaseClient.auth.signOut();
    if (error) {
        console.error('Error signing out:', error.message);
        // You might want to set an error state here for the UI to pick up
    }
    // Session and user will be set to null by onAuthStateChange listener
    // SecureStore token removal also handled by listener
    setIsLoading(false); // Optional: stop loading after sign out attempt
  };

  return (
    <AuthContext.Provider value={{ session, user, isLoading, signOut }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}; 