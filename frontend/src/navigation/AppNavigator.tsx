import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { View, ActivityIndicator, StyleSheet } from 'react-native';

import OnboardingNavigator from './OnboardingNavigator';
import { NotificationProvider } from '../context/NotificationContext';
import ErrorBoundary from '../components/common/ErrorBoundary';

// Import actual Auth screens
import LoginScreen from '../screens/auth/LoginScreen';
import SignUpScreen from '../screens/auth/SignUpScreen';
import ResetPasswordScreen from '../screens/auth/ResetPasswordScreen';
import { useAuth } from '../context/AuthContext';
import { theme } from '../theme'; // Assuming theme is correctly exported from ../theme

import MainTabNavigator from './MainTabNavigator';
import { RootStackParamList, AuthStackParamList } from './types';

// Wrap screens with error boundaries
const LoginScreenWithErrorBoundary = () => (
  <ErrorBoundary 
    level="screen" 
    context="LoginScreen"
    onError={(error, errorInfo) => {
      console.error('🚨 LoginScreen Error Boundary triggered:', error);
    }}
  >
    <LoginScreen />
  </ErrorBoundary>
);

const SignUpScreenWithErrorBoundary = () => (
  <ErrorBoundary 
    level="screen" 
    context="SignUpScreen"
    onError={(error, errorInfo) => {
      console.error('🚨 SignUpScreen Error Boundary triggered:', error);
    }}
  >
    <SignUpScreen />
  </ErrorBoundary>
);

const ResetPasswordScreenWithErrorBoundary = () => (
  <ErrorBoundary 
    level="screen" 
    context="ResetPasswordScreen"
    onError={(error, errorInfo) => {
      console.error('🚨 ResetPasswordScreen Error Boundary triggered:', error);
    }}
  >
    <ResetPasswordScreen />
  </ErrorBoundary>
);

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

// Root Stack
const RootStackNav = createNativeStackNavigator<RootStackParamList>();

const AppNavigator = () => {
  const { session, user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={theme.colors.primary} />
      </View>
    );
  }

  return (
    <RootStackNav.Navigator screenOptions={{ headerShown: false }}>
      {session ? (
        // User is authenticated
        user?.name ? (
          // User has completed profile - go to main app with notifications
          <RootStackNav.Screen name="Main">
            {() => (
              <AuthenticatedAppWrapper>
                <MainTabNavigator />
              </AuthenticatedAppWrapper>
            )}
          </RootStackNav.Screen>
        ) : (
          // User is authenticated but hasn't completed profile - show onboarding with notifications
          <RootStackNav.Screen name="Onboarding">
            {() => (
              <AuthenticatedAppWrapper>
                <OnboardingNavigator />
              </AuthenticatedAppWrapper>
            )}
          </RootStackNav.Screen>
        )
      ) : (
        // User is not authenticated - show auth screens (no NotificationProvider)
        <RootStackNav.Screen name="Auth" component={AuthNavigator} />
      )}
    </RootStackNav.Navigator>
  );
};

const styles = StyleSheet.create({
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: theme.colors.background, // Or another suitable background color from theme
  },
});

export default AppNavigator; 