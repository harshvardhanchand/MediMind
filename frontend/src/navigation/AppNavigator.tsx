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
    console.log('🔍 AppNavigator: parseResetLink called with PKCE flow URL:', url);

    const urlObj = new URL(url);
    console.log('🔍 AppNavigator: URL object created:', {
      protocol: urlObj.protocol,
      hostname: urlObj.hostname,
      pathname: urlObj.pathname,
      hash: urlObj.hash,
      search: urlObj.search
    });


    const searchParams = new URLSearchParams(urlObj.search);
    const code = searchParams.get('code');
    const error_description = searchParams.get('error_description');


    const fragment = urlObj.hash?.substring(1) || '';
    const fragmentParams = new URLSearchParams(fragment);
    const fragmentCode = fragmentParams.get('code');
    const fragmentError = fragmentParams.get('error_description');

    console.log('🔍 AppNavigator: URL params:', {
      searchCode: code,
      fragmentCode: fragmentCode,
      searchError: error_description,
      fragmentError: fragmentError
    });


    const finalError = error_description || fragmentError;
    if (finalError) {
      console.warn('❌ AppNavigator: Password reset link contains error:', finalError);
      return { error_description: finalError, type: 'recovery' };
    }


    const finalCode = code || fragmentCode;
    if (finalCode) {
      console.log('✅ AppNavigator: PKCE code found, exchanging for session...');

      try {
        const { data, error: sessionError } = await supabaseClient.auth.exchangeCodeForSession(finalCode);

        console.log('🔍 AppNavigator: exchangeCodeForSession result:', {
          success: !sessionError,
          error: sessionError?.message,
          hasUser: !!data?.user,
          userEmail: data?.user?.email
        });

        if (sessionError) {
          console.error('❌ AppNavigator: Failed to exchange code for session:', sessionError);
          return { error_description: 'Invalid or expired reset link', type: 'recovery' };
        }

        console.log('✅ AppNavigator: PKCE code exchange successful for password reset');
        return { type: 'recovery' };
      } catch (exchangeError) {
        console.error('❌ AppNavigator: Exception during code exchange:', exchangeError);
        return { error_description: 'Failed to process reset link', type: 'recovery' };
      }
    }

    console.log('❌ AppNavigator: No valid PKCE code found in URL');
    return null;
  } catch (error) {
    console.error('❌ AppNavigator: Error parsing reset link:', error);
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
      console.log('🔍 AppNavigator: getInitialURL called for PKCE flow');
      const url = await Linking.getInitialURL();
      console.log('🔍 AppNavigator: getInitialURL result:', url);

      if (url?.includes('reset') || url?.includes('code=') || url?.includes('#')) {
        console.log('✅ AppNavigator: URL contains reset, code, or hash - parsing with PKCE...');
        await parseResetLink(url);
        return url;
      }
      console.log('❌ AppNavigator: URL does not contain reset, code, or hash');
      return null;
    } catch (error) {
      console.warn('❌ AppNavigator: Error getting initial URL:', error);
      return null;
    }
  },
  subscribe(listener) {
    const subscription = Linking.addEventListener('url', async (event) => {
      console.log('🔍 AppNavigator: Deep link received for PKCE flow:', event.url);

      if (event.url?.includes('reset') || event.url?.includes('code=') || event.url?.includes('#')) {
        console.log('✅ AppNavigator: URL contains reset, code, or hash - parsing with PKCE...');
        await parseResetLink(event.url);
      } else {
        console.log('❌ AppNavigator: URL does not contain reset, code, or hash');
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