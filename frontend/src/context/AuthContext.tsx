import React, {
  createContext,
  useState,
  useEffect,
  useContext,
  ReactNode,
} from "react";
import { Session, User } from "@supabase/supabase-js";

import { supabaseClient } from "../services/supabase";
import { userServices } from "../api/services";
import { analytics } from "../services/analytics";
import { crashReporting } from "../services/crashReporting";

// Extended user type that includes both Supabase User and our API user data
export interface ExtendedUser extends User {
  name?: string | null;
  date_of_birth?: string | null;
  weight?: number | null;
  height?: number | null;
  gender?: "male" | "female" | "other" | null;
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

export const AuthProvider: React.FC<{ children: ReactNode }> = ({
  children,
}) => {
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
    } catch (error) { }
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
      setUser(currentSession.user);
    }
  };

  useEffect(() => {
    const fetchSession = async () => {
      try {
        console.log("🔍 Starting session fetch...");

        const { data, error } = await supabaseClient.auth.getSession();
        console.log("🔍 Supabase getSession result:", {
          hasSession: !!data.session,
          hasUser: !!data.session?.user,
          hasToken: !!data.session?.access_token,
          error: error?.message,
        });

        if (error) {
          console.error("Error fetching session:", error);
          setSession(null);
          setUser(null);
        } else {
          setSession(data.session);

          // Fetch user profile if session exists
          if (data.session) {
            console.log("🔍 Fetching user profile...");
            await fetchUserProfile(data.session);
            console.log("🔍 User profile fetch completed");
          } else {
            setUser(null);
          }
        }
      } catch (e) {
        console.error("Unexpected error fetching session:", e);
        setSession(null);
        setUser(null);
      } finally {
        console.log("🔍 Setting isLoading to false");
        setIsLoading(false);
      }
    };

    // Add timeout fallback to prevent infinite loading
    const timeoutId = setTimeout(() => {
      setIsLoading(false);
    }, 15000); // 15 second timeout

    fetchSession().finally(() => {
      clearTimeout(timeoutId);
    });

    const { data: authListenerData } = supabaseClient.auth.onAuthStateChange(
      async (event, newSession) => {
        // Handle password recovery state
        if (event === "PASSWORD_RECOVERY") {
          setIsRecoveringPassword(true);
        } else if (event === "SIGNED_IN" || event === "SIGNED_OUT") {
          // Unset recovery state on other major events
          setIsRecoveringPassword(false);
        }

        setSession(newSession);

        // Track authentication events
        if (event === "SIGNED_IN" && newSession) {
          analytics.setUserId(newSession.user.id);
          analytics.trackUserAction("user_login", {
            user_id: newSession.user.id,
            email: newSession.user.email,
          });

          // Set user context for crash reporting
          crashReporting.setUser(newSession.user.id, newSession.user.email);
          crashReporting.addBreadcrumb("User signed in", "auth", "info");

          try {
            setIsLoadingProfile(true);
            const userProfile = await userServices.getMe();

            const extendedUser = {
              ...newSession.user,
              ...userProfile.data,
            };

            setUser(extendedUser);
            setIsLoadingProfile(false);
          } catch (error) {
            crashReporting.captureException(error as Error, {
              context: "auth_user_profile_fetch",
              userId: newSession.user.id,
            });

            // Fallback to session user data
            setUser(newSession.user);
            setIsLoadingProfile(false);
          }
        } else if (event === "SIGNED_OUT") {
          analytics.trackUserAction("user_logout");
          crashReporting.addBreadcrumb("User signed out", "auth", "info");
          crashReporting.clearUser();
          setUser(null);
        } else if (event === "TOKEN_REFRESHED") {
          crashReporting.addBreadcrumb("Token refreshed", "auth", "info");
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
    analytics.trackUserAction("user_logout_initiated");
    const { error } = await supabaseClient.auth.signOut();
    if (error) {
      analytics.trackUserAction("user_logout_error", { error: error.message });
    }
    setIsLoading(false);
  };

  return (
    <AuthContext.Provider
      value={{
        session,
        user,
        isLoading,
        isLoadingProfile,
        isRecoveringPassword,
        signOut,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
