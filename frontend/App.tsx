import React, { useEffect, useRef } from 'react';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { Provider as PaperProvider } from 'react-native-paper';
import { NavigationContainer, NavigationContainerRef } from '@react-navigation/native';
import { StatusBar } from 'expo-status-bar';
import { enableScreens } from 'react-native-screens';
import { theme } from './src/theme';
import AppNavigator, { linking } from './src/navigation/AppNavigator';
import { AuthProvider } from './src/context/AuthContext';
import { analytics } from './src/services/analytics';
import { crashReporting } from './src/services/crashReporting';
import DeepLinkingService from './src/services/deepLinkingService';
import ErrorBoundary from './src/components/common/ErrorBoundary';
import { GestureHandlerRootView } from 'react-native-gesture-handler';

enableScreens();

export default function App() {
  const navigationRef = useRef<NavigationContainerRef<any>>(null);
  const routeNameRef = useRef<string | undefined>(undefined);

  useEffect(() => {
    const initializeApp = async () => {
      crashReporting.init();
      await analytics.trackAppOpen();
    };

    initializeApp();
  }, []);

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
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
              <NavigationContainer
                ref={navigationRef}
                linking={linking}
                onReady={() => {
                  routeNameRef.current = navigationRef.current?.getCurrentRoute()?.name;
                  const deepLinkService = DeepLinkingService.getInstance();
                  if (navigationRef.current) {
                    deepLinkService.setNavigationRef(navigationRef.current);
                  }
                }}
                onStateChange={async () => {
                  const previousRouteName = routeNameRef.current;
                  const currentRouteName = navigationRef.current?.getCurrentRoute()?.name;

                  if (previousRouteName !== currentRouteName && currentRouteName) {
                    await analytics.trackScreenView(currentRouteName);
                  }
                  routeNameRef.current = currentRouteName;
                }}
              >
                <AppNavigator />
              </NavigationContainer>
            </AuthProvider>
            <StatusBar style="auto" />
          </PaperProvider>
        </SafeAreaProvider>
      </ErrorBoundary>
    </GestureHandlerRootView>
  );
}
