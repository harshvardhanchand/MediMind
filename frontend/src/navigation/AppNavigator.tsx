import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { View, ActivityIndicator, StyleSheet, Alert } from 'react-native';
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
import { RootStackParamList, AuthStackParamList, ResetPasswordRouteParams } from './types';


import { withScreenErrorBoundary } from '../utils/withErrorBoundary';

const LoginScreenWithErrorBoundary = withScreenErrorBoundary(LoginScreen, 'LoginScreen');
const SignUpScreenWithErrorBoundary = withScreenErrorBoundary(SignUpScreen, 'SignUpScreen');
const ResetPasswordScreenWithErrorBoundary = withScreenErrorBoundary(ResetPasswordScreen, 'ResetPasswordScreen');


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
      initialParams={resetPasswordParams}
    />
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


const parseResetLink = async (url: string): Promise<ResetPasswordRouteParams | null> => {
  try {
    console.log('🔧 Parsing reset link:', url);


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
      console.log('🔐 Setting up Supabase session for password reset...');

      const { error: sessionError } = await supabaseClient.auth.setSession({
        access_token,
        refresh_token,
      });

      if (sessionError) {
        console.error('Failed to set up Supabase session:', sessionError);
        return { error_description: 'Invalid or expired reset link', type };
      }

      console.log('✅ Supabase session set up successfully for password reset');
      return { type: 'recovery' };
    }

    console.log('🔧 Link is not a valid recovery link with tokens.');
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

  const [resetPasswordParams, setResetPasswordParams] = React.useState<ResetPasswordRouteParams | undefined>(undefined);


  React.useEffect(() => {
    let mounted = true;

    const processUrl = async (url: string | null) => {
      if (mounted && url) {
        const params = await parseResetLink(url);
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

    if (!session && resetPasswordParams) {
      console.log('🔐 Session cleared, removing password reset params.');
      setResetPasswordParams(undefined);
    }
  }, [session]);

  React.useEffect(() => {
    if (!isLoading && !hasCheckedSession) {
      setHasCheckedSession(true);

      if (session && !user?.name && !resetPasswordParams) {
        console.log('🔄 App restarted with incomplete profile - signing out for clean restart');
        signOut();
      }
    }
  }, [isLoading, hasCheckedSession, session, user, resetPasswordParams, signOut]);


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