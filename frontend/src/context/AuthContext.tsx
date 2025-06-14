import React, { createContext, useState, useEffect, useContext, ReactNode } from 'react';
import { Session, User } from '@supabase/supabase-js';

import { supabaseClient } from '../services/supabase';
import { userServices } from '../api/services';


// Extended user type that includes both Supabase User and our API user data
export interface ExtendedUser extends User {
  name?: string | null;
  date_of_birth?: string | null;
  weight?: number | null;
  height?: number | null;
  gender?: 'male' | 'female' | 'other' | null;
  profile_photo_url?: string | null;
  medical_conditions?: any[];
}

interface AuthContextType {
  session: Session | null;
  user: ExtendedUser | null;
  isLoading: boolean;
  signOut: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{children: ReactNode}> = ({ children }) => {
  const [session, setSession] = useState<Session | null>(null);
  const [user, setUser] = useState<ExtendedUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const refreshUser = async () => {
    if (!session) return;
    
    try {
      const response = await userServices.getMe();
      // Merge the API user data with the Supabase user data
      const updatedUser = {
        ...session.user,
        ...response.data,
      };
      setUser(updatedUser as ExtendedUser);
    } catch (error) {
      console.error('Error refreshing user data:', error);
    }
  };

  const fetchUserProfile = async (currentSession: Session) => {
    try {
      const response = await userServices.getMe();
      const updatedUser = {
        ...currentSession.user,
        ...response.data,
      };
      setUser(updatedUser as ExtendedUser);
    } catch (apiError) {
      console.error('Error fetching user profile:', apiError);
      // Keep the Supabase user data if API fails
      setUser(currentSession.user);
    }
  };

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
          setSession(null);
          setUser(null);
        } else {
          setSession(data.session);
          
          // Fetch user profile if session exists
          if (data.session) {
            console.log('🔍 Fetching user profile...');
            await fetchUserProfile(data.session);
            console.log('🔍 User profile fetch completed');
          } else {
            setUser(null);
          }
        }
      } catch (e) {
        console.error('Unexpected error fetching session:', e);
        setSession(null);
        setUser(null);
      } finally {
        console.log('🔍 Setting isLoading to false');
        setIsLoading(false);
      }
    };

    // Add timeout fallback to prevent infinite loading
    const timeoutId = setTimeout(() => {
      console.warn('⚠️ Auth initialization timeout - forcing loading to false');
      setIsLoading(false);
    }, 15000); // 15 second timeout

    fetchSession().finally(() => {
      clearTimeout(timeoutId);
    });

    const { data: authListenerData } = supabaseClient.auth.onAuthStateChange(
      async (event, newSession) => {
        console.log('🔍 Auth state change:', event, !!newSession);
        
        setSession(newSession);
        
        // Only fetch user profile for sign-in events or when we have a new session
        // Avoid redundant API calls on token refresh
        if (newSession && (event === 'SIGNED_IN' || event === 'TOKEN_REFRESHED')) {
          await fetchUserProfile(newSession);
        } else {
          setUser(newSession?.user ?? null);
        }
      }
    );

    return () => {
      clearTimeout(timeoutId);
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
    <AuthContext.Provider value={{ session, user, isLoading, signOut, refreshUser }}>
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