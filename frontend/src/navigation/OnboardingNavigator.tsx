import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';

import { OnboardingStackParamList } from './types';
import WelcomeScreen from '../screens/onboarding/WelcomeScreen';
import FeaturesScreen from '../screens/onboarding/FeaturesScreen';
import CreateProfileScreen from '../screens/onboarding/CreateProfileScreen';

const OnboardingStack = createNativeStackNavigator<OnboardingStackParamList>();

const OnboardingNavigator = () => {
  return (
    <OnboardingStack.Navigator 
      screenOptions={{ 
        headerShown: false,
        gestureEnabled: false, // Prevent swipe back during onboarding
      }}
      initialRouteName="Welcome"
    >
      <OnboardingStack.Screen name="Welcome" component={WelcomeScreen} />
      <OnboardingStack.Screen name="Features" component={FeaturesScreen} />
      <OnboardingStack.Screen name="CreateProfile" component={CreateProfileScreen} />
    </OnboardingStack.Navigator>
  );
};

export default OnboardingNavigator; 