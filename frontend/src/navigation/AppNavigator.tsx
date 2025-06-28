import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { View, ActivityIndicator, StyleSheet } from 'react-native';
import * as Linking from 'expo-linking';

import OnboardingNavigator from './OnboardingNavigator';
import { NotificationProvider } from '../context/NotificationContext';
import LoginScreen from '../screens/auth/LoginScreen';
import SignUpScreen from '../screens/auth/SignUpScreen';
import ResetPasswordScreen from '../screens/auth/ResetPasswordScreen';
import { useAuth } from '../context/AuthContext';
import { theme } from '../theme';
import MainTabNavigator from './MainTabNavigator';
import { RootStackParamList, AuthStackParamList } from './types';


import { withScreenErrorBoundary } from '../utils/withErrorBoundary';

const LoginScreenWithErrorBoundary = withScreenErrorBoundary(LoginScreen, 'LoginScreen');
const SignUpScreenWithErrorBoundary = withScreenErrorBoundary(SignUpScreen, 'SignUpScreen');
const ResetPasswordScreenWithErrorBoundary = withScreenErrorBoundary(ResetPasswordScreen, 'ResetPasswordScreen');

// Auth Stack
const AuthStackNav = createNativeStackNavigator<AuthStackParamList>();
const AuthNavigator = ({ isPasswordReset = false }: { isPasswordReset?: boolean }) => (
  <AuthStackNav.Navigator
    screenOptions={{ headerShown: false }}
    initialRouteName={isPasswordReset ? "ResetPassword" : "Login"}
  >
    <AuthStackNav.Screen name="Login" component={LoginScreenWithErrorBoundary} />
    <AuthStackNav.Screen name="SignUp" component={SignUpScreenWithErrorBoundary} />
    <AuthStackNav.Screen name="ResetPassword" component={ResetPasswordScreenWithErrorBoundary} />
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

// Utility function for robust URL parsing
const isPasswordResetUrl = (url: string): boolean => {
  try {
    const parsed = Linking.parse(url);

    // Check if it's a ResetPassword route
    if (parsed.path === 'ResetPassword') {
      return true;
    }

    // Check for Supabase recovery type in query params
    if (parsed.queryParams && parsed.queryParams.type === 'recovery') {
      return true;
    }


    const urlObj = new URL(url);
    if (urlObj.hash) {
      const hashParams = new URLSearchParams(urlObj.hash.substring(1));
      if (hashParams.get('type') === 'recovery') {
        return true;
      }
    }

    return false;
  } catch (error) {
    console.warn('Failed to parse URL for password reset detection:', error);

    return url.includes('type=recovery') || url.includes('ResetPassword');
  }
};


const AuthFlow = React.memo(({ isPasswordReset = false }: { isPasswordReset?: boolean }) => {
  return <AuthNavigator isPasswordReset={isPasswordReset} />;
});

const RegularAuthFlow = React.memo(() => (
  <AuthNavigator isPasswordReset={false} />
));

const AppNavigator = () => {
  const { session, user, isLoading, signOut } = useAuth();

  const [hasCheckedSession, setHasCheckedSession] = React.useState(false);
  const [isPasswordReset, setIsPasswordReset] = React.useState(false);

  // Password reset detection - moved to main AppNavigator
  React.useEffect(() => {
    let mounted = true;

    const checkForPasswordReset = async () => {
      try {
        const timeoutPromise = new Promise<string | null>(resolve =>
          setTimeout(() => resolve(null), 1000)
        );

        const initialUrl = await Promise.race([
          Linking.getInitialURL(),
          timeoutPromise
        ]);

        if (mounted && initialUrl && isPasswordResetUrl(initialUrl)) {
          console.log('🔐 Password reset flow detected in AppNavigator');
          setIsPasswordReset(true);
        }
      } catch (error) {
        console.warn('Error checking initial URL for password reset:', error);
      }
    };

    checkForPasswordReset();

    const subscription = Linking.addEventListener('url', (event) => {
      if (mounted && event.url && isPasswordResetUrl(event.url)) {
        console.log('🔐 Password reset link received in AppNavigator');
        setIsPasswordReset(true);
      }
    });

    return () => {
      mounted = false;
      subscription?.remove();
    };
  }, []);

  React.useEffect(() => {
    if (!session && isPasswordReset) {
      console.log('🔐 Session cleared after password reset - resetting flag');
      setIsPasswordReset(false);
    }
  }, [session, isPasswordReset]);

  React.useEffect(() => {
    if (!isLoading && !hasCheckedSession) {
      setHasCheckedSession(true);

      if (session && !user?.name && !isPasswordReset) {
        console.log('🔄 App restarted with incomplete profile - signing out for clean restart');
        signOut();
      }
    }
  }, [isLoading, hasCheckedSession, isPasswordReset]);

  return (
    <RootStackNav.Navigator screenOptions={{ headerShown: false }}>
      {isLoading ? (
        // Show splash screen while loading
        <RootStackNav.Screen name="Splash" component={SplashScreen} />
      ) : isPasswordReset ? (

        <RootStackNav.Screen name="Auth">
          {() => <AuthFlow isPasswordReset={true} />}
        </RootStackNav.Screen>
      ) : session && user?.name ? (

        <RootStackNav.Screen name="Main" component={MainWithNotifications} />
      ) : session ? (

        <RootStackNav.Screen name="Onboarding" component={OnboardingWithNotifications} />
      ) : (

        <RootStackNav.Screen name="Auth" component={RegularAuthFlow} />
      )}
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