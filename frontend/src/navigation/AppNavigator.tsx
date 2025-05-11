import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { RootStackParamList, AuthStackParamList, MainAppStackParamList } from './types';

// Import actual OnboardingScreen
import OnboardingScreen from '../screens/OnboardingScreen';

// Import actual Auth screens
import LoginScreen from '../screens/auth/LoginScreen';
import SignUpScreen from '../screens/auth/SignUpScreen';

// Import actual Main screens
import HomeScreen from '../screens/main/HomeScreen';
import UploadScreen from '../screens/main/UploadScreen';
import DocumentsScreen from '../screens/main/DocumentsScreen';
import DocumentDetailScreen from '../screens/main/DocumentDetailScreen';
import DataReviewScreen from '../screens/main/DataReviewScreen';
import MedicationsScreen from '../screens/main/MedicationsScreen';
import VitalsScreen from '../screens/main/VitalsScreen';
import SymptomTrackerScreen from '../screens/main/SymptomTrackerScreen';
import ReportsScreen from '../screens/main/ReportsScreen';
import AssistantScreen from '../screens/main/AssistantScreen';
import SettingsScreen from '../screens/main/SettingsScreen';

// PlaceholderScreen is no longer needed here as all main screens are imported
// const PlaceholderScreen = ({ route }: any) => {
//   const { View, Text } = require('react-native');
//   return <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }}><Text>Screen: {route.name}</Text></View>;
// };

// Auth Stack
const AuthStack = createNativeStackNavigator<AuthStackParamList>();
const AuthNavigator = () => (
  <AuthStack.Navigator screenOptions={{ headerShown: false }}>
    <AuthStack.Screen name="Login" component={LoginScreen} />
    <AuthStack.Screen name="SignUp" component={SignUpScreen} />
  </AuthStack.Navigator>
);

// Main App Stack (could be a Tab navigator later)
const MainStack = createNativeStackNavigator<MainAppStackParamList>();
const MainNavigator = () => (
  <MainStack.Navigator screenOptions={{ headerShown: false }}>
    <MainStack.Screen name="Home" component={HomeScreen} />
    <MainStack.Screen name="Upload" component={UploadScreen} />
    <MainStack.Screen name="Documents" component={DocumentsScreen} />
    <MainStack.Screen name="DocumentDetail" component={DocumentDetailScreen} />
    <MainStack.Screen name="DataReview" component={DataReviewScreen} />
    <MainStack.Screen name="Medications" component={MedicationsScreen} />
    <MainStack.Screen name="Vitals" component={VitalsScreen} />
    <MainStack.Screen name="SymptomTracker" component={SymptomTrackerScreen} />
    <MainStack.Screen name="Reports" component={ReportsScreen} />
    <MainStack.Screen name="Assistant" component={AssistantScreen} />
    <MainStack.Screen name="Settings" component={SettingsScreen} />
  </MainStack.Navigator>
);

// Root Stack
const RootStack = createNativeStackNavigator<RootStackParamList>();

const AppNavigator = () => {
  const initialRouteName: keyof RootStackParamList = 'Onboarding';

  return (
    <RootStack.Navigator screenOptions={{ headerShown: false }}>
      <RootStack.Screen name="Onboarding" component={OnboardingScreen} />
      <RootStack.Screen name="Auth" component={AuthNavigator} />
      <RootStack.Screen name="Main" component={MainNavigator} />
    </RootStack.Navigator>
  );
};

export default AppNavigator; 