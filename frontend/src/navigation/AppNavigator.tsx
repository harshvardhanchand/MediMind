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
    Alert.alert('Debug: AppNav Parse Start', `URL: ${url}`, [{ text: 'OK' }]);

    const urlObj = new URL(url);
    let params = new URLSearchParams();

    // Check hash fragment first (Supabase typically uses this for recovery)
    if (urlObj.hash && urlObj.hash.length > 1) {
      const fragment = urlObj.hash.substring(1);
      params = new URLSearchParams(fragment);
      Alert.alert('Debug: AppNav Hash', `Fragment: ${fragment}`, [{ text: 'OK' }]);
    }

    // If no hash params with 'type=recovery', check query parameters
    if (params.get('type') !== 'recovery' && urlObj.search) {
      const queryParams = new URLSearchParams(urlObj.search);
      if (queryParams.get('type') === 'recovery') {
        params = queryParams;
        Alert.alert('Debug: AppNav Query', `Query: ${urlObj.search}`, [{ text: 'OK' }]);
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
        Alert.alert('Debug: AppNav ExpoParse', `Expo Query: ${JSON.stringify(expoParsedUrl.queryParams)}`, [{ text: 'OK' }]);
      }
    }


    const accessToken = params.get('access_token');
    const refreshToken = params.get('refresh_token');
    const type = params.get('type');
    const error_description = params.get('error_description');


    Alert.alert('Debug: AppNav Parsed', `Type: ${type}, AT: ${!!accessToken}, RT: ${!!refreshToken}, Err: ${error_description}`, [{ text: 'OK' }]);

    if (type === 'recovery' && accessToken && refreshToken) {
      return { accessToken, refreshToken, type };
    }
    if (error_description) {
      // If there's an error description, it's likely a failed attempt, still pass it
      console.warn('Password reset link contains error:', error_description);
      return { error_description, type };
    }

    // Check if the path itself indicates a reset password screen, even if tokens are not in URL yet
    // This is a weaker check, but helps if the URL is just for navigation
    if (expoParsedUrl.path === 'ResetPassword' || url.includes('ResetPassword')) {
      console.log('🔗 URL indicates ResetPassword screen, but no tokens found yet in AppNavigator.');
      // Return empty object to signify it's a password reset context,
      // ResetPasswordScreen will then try its own Linking.getInitialURL or listener
      return { type: 'recovery' }; // Indicate it's a recovery attempt
    }


    console.log('🔧 Link is not a valid recovery link with tokens or known error.');
    return null;
  } catch (error) {
    console.error('Error parsing reset link:', error);
    Alert.alert('Debug: AppNav Parse ERR', `Error: ${error}`, [{ text: 'OK' }]);
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
        Alert.alert('Debug: AppNav Process URL', `URL: ${url}`, [{ text: 'OK' }]);
        const params = parseResetLink(url);
        if (params) {
          console.log('🔐 Password reset params extracted in AppNavigator:', params);
          Alert.alert('Debug: AppNav Params Set', `Params: ${JSON.stringify(params)}`, [{ text: 'OK' }]);
          setResetPasswordParams(params);
        } else {
          Alert.alert('Debug: AppNav No Params', 'No valid reset params from URL', [{ text: 'OK' }]);
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
        Alert.alert('Debug: AppNav InitURLErr', `Error: ${error}`, [{ text: 'OK' }]);
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
      Alert.alert('Debug: AppNav Session Null', 'Clearing reset params', [{ text: 'OK' }]);
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


  // Debug current state
  React.useEffect(() => {
    Alert.alert('Debug: App State', `isLoading: ${isLoading}\nresetParams: ${JSON.stringify(resetPasswordParams)}\nhasSession: ${!!session}\nhasUserName: ${!!user?.name}`, [{ text: 'OK' }]);
  }, [isLoading, resetPasswordParams, session, user]);

  // Determine navigation logic
  let content;
  if (isLoading) {
    Alert.alert('Debug: Nav Decision', 'Showing Splash Screen', [{ text: 'OK' }]);
    content = <RootStackNav.Screen name="Splash" component={SplashScreen} />;
  } else if (resetPasswordParams) {
    Alert.alert('Debug: Nav Decision', 'Showing Password Reset Auth Flow', [{ text: 'OK' }]);
    content = (
      <RootStackNav.Screen name="Auth">
        {() => <AuthFlow resetPasswordParams={resetPasswordParams} />}
      </RootStackNav.Screen>
    );
  } else if (session && user?.name) {
    Alert.alert('Debug: Nav Decision', 'Showing Main App', [{ text: 'OK' }]);
    content = <RootStackNav.Screen name="Main" component={MainWithNotifications} />;
  } else if (session) {
    Alert.alert('Debug: Nav Decision', 'Showing Onboarding', [{ text: 'OK' }]);
    content = <RootStackNav.Screen name="Onboarding" component={OnboardingWithNotifications} />;
  } else {
    Alert.alert('Debug: Nav Decision', 'Showing Regular Auth Flow', [{ text: 'OK' }]);
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