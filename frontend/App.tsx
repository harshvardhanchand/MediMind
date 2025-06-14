import React, { useRef } from 'react';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { Provider as PaperProvider } from 'react-native-paper';
import { NavigationContainer, NavigationContainerRef } from '@react-navigation/native';
import { StatusBar } from 'expo-status-bar';
import { theme } from './src/theme';
import AppNavigator from './src/navigation/AppNavigator';
import "./src/global.css"; // Import global styles
import { AuthProvider } from './src/context/AuthContext'; // Import AuthProvider
import DeepLinkingService from './src/services/deepLinkingService';

export default function App() {
  const navigationRef = useRef<NavigationContainerRef<any>>(null);
  const deepLinkService = DeepLinkingService.getInstance();

  const handleNavigationReady = () => {
    if (navigationRef.current) {
      deepLinkService.setNavigationRef(navigationRef.current);
    }
  };

  return (
    <SafeAreaProvider>
      <AuthProvider>
        <PaperProvider theme={theme}>
          <NavigationContainer 
            ref={navigationRef}
            onReady={handleNavigationReady}
          >
            <StatusBar style="auto" />
            <AppNavigator />
          </NavigationContainer>
        </PaperProvider>
      </AuthProvider>
    </SafeAreaProvider>
  );
}
