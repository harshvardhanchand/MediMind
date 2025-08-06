import React, { createContext, useState, useEffect, useContext, ReactNode } from 'react';
import { Session, User } from '@supabase/supabase-js';

import { supabaseClient } from '../services/supabase';
import { userServices } from '../api/services';
import { analytics } from '../services/analytics';
import { crashReporting } from '../services/crashReporting';


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
  isLoadingProfile: boolean;
  isRecoveringPassword: boolean;
  signOut: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [session, setSession] = useState<Session | null>(null);
  const [user, setUser] = useState<ExtendedUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingProfile, setIsLoadingProfile] = useState(false);
  const [isRecoveringPassword, setIsRecoveringPassword] = useState(false);

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

        // Handle password recovery state
        if (event === 'PASSWORD_RECOVERY') {
          console.log('✅ AuthContext: PASSWORD_RECOVERY event received. Setting state.');
          setIsRecoveringPassword(true);
        } else if (event === 'SIGNED_IN' || event === 'SIGNED_OUT') {
          // Unset recovery state on other major events
          setIsRecoveringPassword(false);
        }

        setSession(newSession);

        // Track authentication events
        if (event === 'SIGNED_IN' && newSession) {
          analytics.setUserId(newSession.user.id);
          analytics.trackUserAction('user_login', {
            user_id: newSession.user.id,
            email: newSession.user.email,
          });

          // Set user context for crash reporting
          crashReporting.setUser(newSession.user.id, newSession.user.email);
          crashReporting.addBreadcrumb('User signed in', 'auth', 'info');

          console.log('🔍 SIGN_IN: Starting user profile fetch...');
          console.log('🔍 SIGN_IN: Session user data:', {
            id: newSession.user.id,
            email: newSession.user.email,
            hasName: !!newSession.user.user_metadata?.name
          });

          try {
            console.log('🔍 SIGN_IN: Calling userServices.getMe()...');
            setIsLoadingProfile(true);
            const userProfile = await userServices.getMe();

            console.log('🔍 SIGN_IN: Raw API response structure:', JSON.stringify(userProfile.data, null, 2));
            console.log('🔍 SIGN_IN: API response fields:', {
              hasData: !!userProfile.data,
              userName: userProfile.data?.name,
              userId: userProfile.data?.user_id,
              allFields: Object.keys(userProfile.data || {})
            });

            const extendedUser = {
              ...newSession.user,
              ...userProfile.data,
            };

            console.log('🔍 SIGN_IN: Extended user after merge:', JSON.stringify(extendedUser, null, 2));
            console.log('🔍 SIGN_IN: Extended user navigation check:', {
              hasName: !!extendedUser.name,
              userName: extendedUser.name,
              nameField: extendedUser.name,
              source: 'api_success'
            });

            setUser(extendedUser);
            setIsLoadingProfile(false);
          } catch (error) {
            console.error('🔍 SIGN_IN: Failed to fetch user profile:', error);
            console.log('🔍 SIGN_IN: Error details:', {
              message: error.message,
              status: error.response?.status,
              data: error.response?.data
            });

            crashReporting.captureException(error as Error, {
              context: 'auth_user_profile_fetch',
              userId: newSession.user.id,
            });

            console.log('🔍 SIGN_IN: Falling back to session user data:', {
              userId: newSession.user.id,
              email: newSession.user.email,
              source: 'fallback_session'
            });

            // Fallback to session user data
            setUser(newSession.user);
            setIsLoadingProfile(false);
          }
        } else if (event === 'SIGNED_OUT') {
          analytics.trackUserAction('user_logout');
          crashReporting.addBreadcrumb('User signed out', 'auth', 'info');
          crashReporting.clearUser();
          setUser(null);
        } else if (event === 'TOKEN_REFRESHED') {
          crashReporting.addBreadcrumb('Token refreshed', 'auth', 'info');
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
    analytics.trackUserAction('user_logout_initiated');
    const { error } = await supabaseClient.auth.signOut();
    if (error) {
      console.error('Error signing out:', error.message);
      analytics.trackUserAction('user_logout_error', { error: error.message });
    }
    setIsLoading(false);
  };

  return (
    <AuthContext.Provider value={{ session, user, isLoading, isLoadingProfile, isRecoveringPassword, signOut, refreshUser }}>
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