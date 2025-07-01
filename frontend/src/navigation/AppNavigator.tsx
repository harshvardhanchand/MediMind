import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { View, ActivityIndicator, StyleSheet, Alert } from 'react-native';
import * as Linking from 'expo-linking';

import OnboardingNavigator from './OnboardingNavigator';
import { NotificationProvider } from '../context/NotificationContext';
import LoginScreen from '../screens/auth/LoginScreen';
import SignUpScreen from '../screens/auth/SignUpScreen';
import ResetPasswordScreen from '../screens/auth/ResetPasswordScreen';
import { useAuth } from '../context/AuthContext';
import { theme } from '../theme';
import MainTabNavigator from './MainTabNavigator';
import { RootStackParamList, AuthStackParamList, ResetPasswordRouteParams } from './types';


import { withScreenErrorBoundary } from '../utils/withErrorBoundary';

const LoginScreenWithErrorBoundary = withScreenErrorBoundary(LoginScreen, 'LoginScreen');
const SignUpScreenWithErrorBoundary = withScreenErrorBoundary(SignUpScreen, 'SignUpScreen');
const ResetPasswordScreenWithErrorBoundary = withScreenErrorBoundary(ResetPasswordScreen, 'ResetPasswordScreen');

// Auth Stack
const AuthStackNav = createNativeStackNavigator<AuthStackParamList>();
const AuthNavigator = ({ resetPasswordParams }: { resetPasswordParams?: ResetPasswordRouteParams }) => (
  <AuthStackNav.Navigator
    screenOptions={{ headerShown: false }}
    initialRouteName={resetPasswordParams ? "ResetPassword" : "Login"}
  >
    <AuthStackNav.Screen name="Login" component={LoginScreenWithErrorBoundary} />
    <AuthStackNav.Screen name="SignUp" component={SignUpScreenWithErrorBoundary} />
    <AuthStackNav.Screen
      name="ResetPassword"
      component={ResetPasswordScreenWithErrorBoundary}
      initialParams={resetPasswordParams} // Pass params here
    />
  </AuthStackNav.Navigator>
);

// Authenticated App Wrapper - wraps authenticated screens with NotificationProvider
const AuthenticatedAppWrapper = ({ children }: { children: React.ReactNode }) => (
  <NotificationProvider>
    {children}
  </NotificationProvider>
);


const MainWithNotifications = React.memo(() => (
  <AuthenticatedAppWrapper>
    <MainTabNavigator />
  </AuthenticatedAppWrapper>
));

const OnboardingWithNotifications = React.memo(() => (
  <AuthenticatedAppWrapper>
    <OnboardingNavigator />
  </AuthenticatedAppWrapper>
));


const SplashScreen = () => (
  <View style={styles.splashContainer}>
    <ActivityIndicator size="large" color={theme.colors.primary} />
    {/* Add your app logo or branding here */}
  </View>
);


const RootStackNav = createNativeStackNavigator<RootStackParamList>();

// Utility function to parse reset link parameters
const parseResetLink = (url: string): ResetPasswordRouteParams | null => {
  try {
    console.log('🔧 Parsing reset link:', url);

    const urlObj = new URL(url);
    let params = new URLSearchParams();

    // Check hash fragment first (Supabase typically uses this for recovery)
    if (urlObj.hash && urlObj.hash.length > 1) {
      const fragment = urlObj.hash.substring(1);
      params = new URLSearchParams(fragment);
    }

    // If no hash params with 'type=recovery', check query parameters
    if (params.get('type') !== 'recovery' && urlObj.search) {
      const queryParams = new URLSearchParams(urlObj.search);
      if (queryParams.get('type') === 'recovery') {
        params = queryParams;
      }
    }

    // Also check Expo Linking parsed path and query params as a fallback
    // This handles cases like medimind://ResetPassword?type=recovery...
    const expoParsedUrl = Linking.parse(url);
    if (params.get('type') !== 'recovery' && expoParsedUrl.queryParams) {
      const queryParams = expoParsedUrl.queryParams as any;
      if (queryParams.type === 'recovery') {
        params = new URLSearchParams(expoParsedUrl.path?.split('?')[1] || '');
        // Manually add from expoParsedUrl.queryParams if some are missing
        Object.entries(queryParams).forEach(([key, value]) => {
          if (!params.has(key) && typeof value === 'string') {
            params.set(key, value);
          }
        });
      }
    }


    const type = params.get('type');
    const error_description = params.get('error_description');

    if (error_description) {

      console.warn('Password reset link contains error:', error_description);
      return { error_description, type };
    }


    if (expoParsedUrl.path === 'ResetPassword' || url.includes('ResetPassword')) {
      console.log('🔗 URL indicates ResetPassword screen - Supabase already verified the token');
      return { type: 'recovery' }; // Any ResetPassword redirect means recovery
    }


    console.log('🔧 Link is not a valid recovery link with tokens or known error.');
    return null;
  } catch (error) {
    console.error('Error parsing reset link:', error);
    return null;
  }
};

const AuthFlow = React.memo(({ resetPasswordParams }: { resetPasswordParams?: ResetPasswordRouteParams }) => {
  return <AuthNavigator resetPasswordParams={resetPasswordParams} />;
});

const RegularAuthFlow = React.memo(() => (
  <AuthNavigator />
));

const AppNavigator = () => {
  const { session, user, isLoading, signOut } = useAuth();

  const [hasCheckedSession, setHasCheckedSession] = React.useState(false);
  // Store the full params for password reset
  const [resetPasswordParams, setResetPasswordParams] = React.useState<ResetPasswordRouteParams | undefined>(undefined);


  React.useEffect(() => {
    let mounted = true;

    const processUrl = (url: string | null) => {
      if (mounted && url) {
        const params = parseResetLink(url);
        if (params) {
          console.log('🔐 Password reset params extracted in AppNavigator:', params);
          setResetPasswordParams(params);
        }
      }
    };

    const checkForPasswordReset = async () => {
      try {
        // Short timeout for getInitialURL as it can hang on Android in some cases
        const initialUrl = await Promise.race([
          Linking.getInitialURL(),
          new Promise<string | null>(resolve => setTimeout(() => resolve(null), 1500))
        ]);
        processUrl(initialUrl);
      } catch (error) {
        console.warn('Error checking initial URL for password reset:', error);
      }
    };

    checkForPasswordReset();

    const subscription = Linking.addEventListener('url', (event) => {
      console.log('🔗 Deep link received in AppNavigator:', event.url);
      processUrl(event.url);
    });

    return () => {
      mounted = false;
      subscription?.remove();
    };
  }, []);

  React.useEffect(() => {
    // If session becomes null (e.g., after password update and sign out) and we had reset params, clear them.
    if (!session && resetPasswordParams) {
      console.log('🔐 Session cleared, removing password reset params.');
      setResetPasswordParams(undefined);
    }
  }, [session]); // Only depends on session

  React.useEffect(() => {
    if (!isLoading && !hasCheckedSession) {
      setHasCheckedSession(true);
      // If user has session, but no name (profile incomplete), and not in password reset flow
      if (session && !user?.name && !resetPasswordParams) {
        console.log('🔄 App restarted with incomplete profile - signing out for clean restart');
        signOut();
      }
    }
  }, [isLoading, hasCheckedSession, session, user, resetPasswordParams, signOut]);

  // Determine navigation logic
  let content;
  if (isLoading) {
    content = <RootStackNav.Screen name="Splash" component={SplashScreen} />;
  } else if (resetPasswordParams) {
    content = (
      <RootStackNav.Screen name="Auth">
        {() => <AuthFlow resetPasswordParams={resetPasswordParams} />}
      </RootStackNav.Screen>
    );
  } else if (session && user?.name) {
    content = <RootStackNav.Screen name="Main" component={MainWithNotifications} />;
  } else if (session) {
    content = <RootStackNav.Screen name="Onboarding" component={OnboardingWithNotifications} />;
  } else {
    content = <RootStackNav.Screen name="Auth" component={RegularAuthFlow} />;
  }

  return (
    <RootStackNav.Navigator screenOptions={{ headerShown: false }}>
      {content}
    </RootStackNav.Navigator>
  );
};

const styles = StyleSheet.create({
  splashContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: theme.colors.background,
  },
});

export default AppNavigator;