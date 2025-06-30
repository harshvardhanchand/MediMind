import React, { useRef, useEffect } from 'react';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { Provider as PaperProvider } from 'react-native-paper';
import { NavigationContainer, NavigationContainerRef } from '@react-navigation/native';
import { StatusBar } from 'expo-status-bar';
import { enableScreens } from 'react-native-screens';
import { theme } from './src/theme';
import AppNavigator from './src/navigation/AppNavigator';
import { AuthProvider } from './src/context/AuthContext';
import DeepLinkingService from './src/services/deepLinkingService';
import { analytics } from './src/services/analytics';
import { crashReporting } from './src/services/crashReporting';
import ErrorBoundary from './src/components/common/ErrorBoundary';

enableScreens();

export default function App() {
  const navigationRef = useRef<NavigationContainerRef<any>>(null);

  useEffect(() => {
    crashReporting.init();
    const deepLinkingService = DeepLinkingService.getInstance();
    deepLinkingService.setNavigationRef(navigationRef.current!);
    analytics.trackAppOpen();
  }, []);

  return (
    <ErrorBoundary
      level="global"
      context="App"
      onError={(error, errorInfo) => {
        console.error(' Global Error Boundary triggered:', error);
        crashReporting.captureException(error, {
          componentStack: errorInfo.componentStack,
          level: 'global',
          context: 'App',
        });
      }}
    >
      <SafeAreaProvider>
        <PaperProvider theme={theme}>
          <AuthProvider>
            <NavigationContainer ref={navigationRef}>
              <AppNavigator />
            </NavigationContainer>
          </AuthProvider>
          <StatusBar style="auto" />
        </PaperProvider>
      </SafeAreaProvider>
    </ErrorBoundary>
  );
}
