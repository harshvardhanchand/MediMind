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
import ConfirmScreen from '../screens/auth/ConfirmScreen';
import { useAuth } from '../context/AuthContext';
import { theme } from '../theme';
import MainTabNavigator from './MainTabNavigator';
import { RootStackParamList, AuthStackParamList } from './types';

import { withScreenErrorBoundary } from '../utils/withErrorBoundary';

const LoginScreenWithErrorBoundary = withScreenErrorBoundary(LoginScreen, 'LoginScreen');
const SignUpScreenWithErrorBoundary = withScreenErrorBoundary(SignUpScreen, 'SignUpScreen');
const ResetPasswordScreenWithErrorBoundary = withScreenErrorBoundary(ResetPasswordScreen, 'ResetPasswordScreen');
const ConfirmScreenWithErrorBoundary = withScreenErrorBoundary(ConfirmScreen, 'ConfirmScreen');

const parseLink = async (url: string) => {
  try {
    const urlObj = new URL(url);
    const searchParams = new URLSearchParams(urlObj.search);
    const tokenHash = searchParams.get('token_hash');
    const type = searchParams.get('type');
    const error_description = searchParams.get('error_description');

    const fragment = urlObj.hash?.substring(1) || '';
    const fragmentParams = new URLSearchParams(fragment);
    const fragmentTokenHash = fragmentParams.get('token_hash');
    const fragmentType = fragmentParams.get('type');
    const fragmentError = fragmentParams.get('error_description');

    const finalError = error_description || fragmentError;
    if (finalError) {
      return { error_description: finalError, type: type || fragmentType || 'recovery' };
    }

    const finalTokenHash = tokenHash || fragmentTokenHash;
    const finalType = type || fragmentType;

    if (finalTokenHash && finalType) {
      try {

        const { data, error: sessionError } = await supabaseClient.auth.verifyOtp({
          token_hash: finalTokenHash,
          type: finalType as 'signup' | 'recovery'
        });

        if (sessionError) {
          const errorMsg = finalType === 'signup'
            ? 'Invalid or expired confirmation link'
            : 'Invalid or expired reset link';
          return { error_description: errorMsg, type: finalType };
        }

        return { type: finalType };
      } catch (exchangeError) {
        const errorMsg = finalType === 'signup'
          ? 'Failed to process confirmation link'
          : 'Failed to process reset link';
        return { error_description: errorMsg, type: finalType };
      }
    }

    return null;
  } catch (error) {
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
          Confirm: 'confirm',
        }
      },
    }
  },
  async getInitialURL() {
    try {
      const url = await Linking.getInitialURL();

      if (url?.includes('reset') || url?.includes('confirm') || url?.includes('token_hash=') || url?.includes('#')) {
        await parseLink(url);
        return url;
      }
      return null;
    } catch (error) {
      return null;
    }
  },
  subscribe(listener) {
    const subscription = Linking.addEventListener('url', async (event) => {
      if (event.url?.includes('reset') || event.url?.includes('confirm') || event.url?.includes('token_hash=') || event.url?.includes('#')) {
        await parseLink(event.url);
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
    <AuthStackNav.Screen name="Confirm" component={ConfirmScreenWithErrorBoundary} />
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