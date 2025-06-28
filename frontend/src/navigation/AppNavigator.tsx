import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { View, ActivityIndicator, StyleSheet } from 'react-native';

import OnboardingNavigator from './OnboardingNavigator';
import { NotificationProvider } from '../context/NotificationContext';
import ErrorBoundary from '../components/common/ErrorBoundary';
import LoginScreen from '../screens/auth/LoginScreen';
import SignUpScreen from '../screens/auth/SignUpScreen';
import ResetPasswordScreen from '../screens/auth/ResetPasswordScreen';
import { useAuth } from '../context/AuthContext';
import { theme } from '../theme';
import MainTabNavigator from './MainTabNavigator';
import { RootStackParamList, AuthStackParamList } from './types';


function withScreenErrorBoundary<P extends object>(
  Component: React.ComponentType<P>,
  contextName: string
) {
  return (props: P) => (
    <ErrorBoundary
      level="screen"
      context={contextName}
      onError={(error, errorInfo) => {
        console.error(`🚨 ${contextName} Error Boundary triggered:`, error);
      }}
    >
      <Component {...props} />
    </ErrorBoundary>
  );
}

const LoginScreenWithErrorBoundary = withScreenErrorBoundary(LoginScreen, 'LoginScreen');
const SignUpScreenWithErrorBoundary = withScreenErrorBoundary(SignUpScreen, 'SignUpScreen');
const ResetPasswordScreenWithErrorBoundary = withScreenErrorBoundary(ResetPasswordScreen, 'ResetPasswordScreen');

// Auth Stack
const AuthStackNav = createNativeStackNavigator<AuthStackParamList>();
const AuthNavigator = () => (
  <AuthStackNav.Navigator screenOptions={{ headerShown: false }}>
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

const AppNavigator = () => {
  const { session, user, isLoading, signOut, refreshUser } = useAuth();

  // Track if this is a fresh app start vs ongoing session
  const [hasCheckedSession, setHasCheckedSession] = React.useState(false);

  // Only reset incomplete profiles on fresh app start, not during active onboarding
  React.useEffect(() => {
    if (!isLoading && !hasCheckedSession) {
      setHasCheckedSession(true);

      // If user has session but no profile on app start, reset them
      if (session && !user?.name) {
        console.log('🔄 App restarted with incomplete profile - signing out for clean restart');
        signOut();
      }
    }
  }, [isLoading, hasCheckedSession]);

  return (
    <RootStackNav.Navigator screenOptions={{ headerShown: false }}>
      {isLoading ? (
        // Show splash screen while loading
        <RootStackNav.Screen name="Splash" component={SplashScreen} />
      ) : session && user?.name ? (
        // User is authenticated AND has completed profile - go to main app
        <RootStackNav.Screen name="Main" component={MainWithNotifications} />
      ) : session ? (
        // User is authenticated but incomplete profile - allow onboarding to continue
        <RootStackNav.Screen name="Onboarding" component={OnboardingWithNotifications} />
      ) : (
        // User is not authenticated - show auth screens
        <RootStackNav.Screen name="Auth" component={AuthNavigator} />
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