import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { RootStackParamList, AuthStackParamList } from './types';
import MainTabNavigator from './MainTabNavigator';

// Import actual OnboardingScreen
import OnboardingScreen from '../screens/OnboardingScreen';

// Import actual Auth screens
import LoginScreen from '../screens/auth/LoginScreen';
import SignUpScreen from '../screens/auth/SignUpScreen';

import { useAuth } from '../context/AuthContext';
import { View, ActivityIndicator, StyleSheet } from 'react-native';
import { theme } from '../theme'; // Assuming theme is correctly exported from ../theme

// Auth Stack
const AuthStackNav = createNativeStackNavigator<AuthStackParamList>();
const AuthNavigator = () => (
  <AuthStackNav.Navigator screenOptions={{ headerShown: false }}>
    <AuthStackNav.Screen name="Login" component={LoginScreen} />
    <AuthStackNav.Screen name="SignUp" component={SignUpScreen} />
  </AuthStackNav.Navigator>
);

// Root Stack
const RootStackNav = createNativeStackNavigator<RootStackParamList>();

const AppNavigator = () => {
  const { session, isLoading } = useAuth();

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
        <RootStackNav.Screen name="Main" component={MainTabNavigator} />
      ) : (
        <>
          <RootStackNav.Screen name="Onboarding" component={OnboardingScreen} />
          <RootStackNav.Screen name="Auth" component={AuthNavigator} />
        </>
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