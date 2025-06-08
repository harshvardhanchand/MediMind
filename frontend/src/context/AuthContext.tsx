import React, { createContext, useState, useEffect, useContext, ReactNode } from 'react';
import { Session, User } from '@supabase/supabase-js';

import { supabaseClient } from '../services/supabase';

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
        console.log('🔍 Starting session fetch...');
        
        const { data, error } = await supabaseClient.auth.getSession();
        console.log('🔍 Supabase getSession result:', {
          hasSession: !!data.session,
          hasUser: !!data.session?.user,
          hasToken: !!data.session?.access_token,
          error: error?.message
        });
        
        if (error) {
          console.error('Error fetching session:', error);
        } else {
          setSession(data.session);
          setUser(data.session?.user ?? null);
        }
      } catch (e) {
        console.error('Unexpected error fetching session:', e);
      } finally {
        setIsLoading(false);
      }
    };

    fetchSession();

    const { data: authListenerData } = supabaseClient.auth.onAuthStateChange(
      async (event, newSession) => {
        
        setSession(newSession);
        setUser(newSession?.user ?? null);
      }
    );

    return () => {
      authListenerData?.subscription.unsubscribe();
    };
  }, []);

  const signOut = async () => {
    setIsLoading(true);
    const { error } = await supabaseClient.auth.signOut();
    if (error) {
        console.error('Error signing out:', error.message);
    }
    setIsLoading(false);
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