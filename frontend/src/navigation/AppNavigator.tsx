import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { View, ActivityIndicator, StyleSheet } from 'react-native';
import * as Linking from 'expo-linking';
import { supabaseClient } from '../services/supabase';

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

const parseResetLink = async (url: string) => {
  try {
    console.log(' Parsing reset link:', url);

    const urlObj = new URL(url);
    const fragment = urlObj.hash?.substring(1) || '';
    const params = new URLSearchParams(fragment);

    const type = params.get('type');
    const access_token = params.get('access_token');
    const refresh_token = params.get('refresh_token');
    const error_description = params.get('error_description');

    if (error_description) {
      console.warn('Password reset link contains error:', error_description);
      return { error_description, type };
    }

    if (type === 'recovery' && access_token && refresh_token) {
      console.log('Setting up Supabase session for password reset...');

      const { error: sessionError } = await supabaseClient.auth.setSession({
        access_token,
        refresh_token,
      });

      if (sessionError) {
        console.error('Failed to set up Supabase session:', sessionError);
        return { error_description: 'Invalid or expired reset link', type };
      }

      console.log(' Supabase session set up successfully for password reset');
      return { type: 'recovery' };
    }

    console.log('Link is not a valid recovery link with tokens.');
    return null;
  } catch (error) {
    console.error('Error parsing reset link:', error);
    return null;
  }
};

export const linking = {
  prefixes: ['https://www.medimind.co.in'],
  config: {
    screens: {
      Auth: {
        screens: {
          ResetPassword: 'reset',
        }
      },
    }
  },
  async getInitialURL() {
    try {
      const url = await Linking.getInitialURL();
      if (url?.includes('reset') || url?.includes('#')) {
        await parseResetLink(url);
        return url;
      }
      return null;
    } catch (error) {
      console.warn('Error getting initial URL:', error);
      return null;
    }
  },
  subscribe(listener) {
    const subscription = Linking.addEventListener('url', async (event) => {
      console.log(' Deep link received:', event.url);

      if (event.url?.includes('reset-password') || event.url?.includes('#')) {
        await parseResetLink(event.url);
      }

      listener(event.url);
    });

    return () => subscription?.remove();
  },
};

const AuthStackNav = createNativeStackNavigator<AuthStackParamList>();

const AuthNavigator = () => (
  <AuthStackNav.Navigator
    screenOptions={{ headerShown: false }}
    initialRouteName="Login"
  >
    <AuthStackNav.Screen name="Login" component={LoginScreenWithErrorBoundary} />
    <AuthStackNav.Screen name="SignUp" component={SignUpScreenWithErrorBoundary} />
    <AuthStackNav.Screen name="ResetPassword" component={ResetPasswordScreenWithErrorBoundary} />
  </AuthStackNav.Navigator>
);

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
  </View>
);

const RootStackNav = createNativeStackNavigator<RootStackParamList>();

const AppNavigator = () => {
  const { session, user, isLoading } = useAuth();

  console.log('Navigation state:', {
    isLoading,
    hasSession: !!session,
    hasUserName: !!user?.name,
  });

  return (
    <RootStackNav.Navigator screenOptions={{ headerShown: false }}>
      {isLoading ? (

        <RootStackNav.Group>
          <RootStackNav.Screen name="Splash" component={SplashScreen} />
        </RootStackNav.Group>
      ) : !session ? (

        <RootStackNav.Group>
          <RootStackNav.Screen name="Auth" component={AuthNavigator} />
        </RootStackNav.Group>
      ) : (

        <RootStackNav.Group>
          {!user?.name ? (
            <RootStackNav.Screen name="Onboarding" component={OnboardingWithNotifications} />
          ) : (
            <RootStackNav.Screen name="Main" component={MainWithNotifications} />
          )}

          <RootStackNav.Screen name="Auth" component={AuthNavigator} />
        </RootStackNav.Group>
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