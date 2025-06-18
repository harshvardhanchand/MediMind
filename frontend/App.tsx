import React, { useRef, useEffect } from 'react';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { Provider as PaperProvider } from 'react-native-paper';
import { NavigationContainer, NavigationContainerRef } from '@react-navigation/native';
import { StatusBar } from 'expo-status-bar';
import { theme } from './src/theme';
import AppNavigator from './src/navigation/AppNavigator';
import "./src/global.css"; // Import global styles
import { AuthProvider } from './src/context/AuthContext'; // Import AuthProvider
import DeepLinkingService from './src/services/deepLinkingService';
import { analytics } from './src/services/analytics';
import { crashReporting } from './src/services/crashReporting';
import ErrorBoundary from './src/components/common/ErrorBoundary';

const linking = {
  prefixes: ['medimind://'],
  config: {
    screens: {
      Auth: {
        screens: {
          ResetPassword: 'ResetPassword',
        },
      },
    },
  },
};

export default function App() {
  const navigationRef = useRef<NavigationContainerRef<any>>(null);

  useEffect(() => {
    // Initialize services
    crashReporting.init();
    
    // Initialize deep linking service
    const deepLinkingService = DeepLinkingService.getInstance();
    deepLinkingService.setNavigationRef(navigationRef.current!);

    // Track app open
    analytics.trackAppOpen();
  }, []);

  return (
    <ErrorBoundary 
      level="global" 
      context="App"
      onError={(error, errorInfo) => {
        console.error('🚨 Global Error Boundary triggered:', error);
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
            <NavigationContainer ref={navigationRef} linking={linking}>
              <AppNavigator />
            </NavigationContainer>
          </AuthProvider>
          <StatusBar style="auto" />
        </PaperProvider>
      </SafeAreaProvider>
    </ErrorBoundary>
  );
}
