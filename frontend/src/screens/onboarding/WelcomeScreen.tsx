import React from 'react';
import { View, TouchableOpacity, Alert } from 'react-native';
import { styled } from 'nativewind';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { Ionicons } from '@expo/vector-icons';

import { OnboardingStackParamList } from '../../navigation/types';
import ScreenContainer from '../../components/layout/ScreenContainer';
import StyledText from '../../components/common/StyledText';
import { useTheme } from '../../theme';
import { useAuth } from '../../context/AuthContext';

const StyledView = styled(View);
const StyledTouchableOpacity = styled(TouchableOpacity);

type WelcomeScreenNavigationProp = NativeStackNavigationProp<OnboardingStackParamList, 'Welcome'>;

const WelcomeScreen = () => {
  const navigation = useNavigation<WelcomeScreenNavigationProp>();
  const { colors } = useTheme();
  const { signOut } = useAuth();

  const handleGetStarted = () => {
    navigation.navigate('Features');
  };

  const handleLogout = () => {
    Alert.alert(
      'Sign Out',
      'Are you sure you want to sign out? Your profile progress will be lost.',
      [
        {
          text: 'Cancel',
          style: 'cancel',
        },
        {
          text: 'Sign Out',
          style: 'destructive',
          onPress: async () => {
            try {
              await signOut();
            } catch (error) {
              console.error('Error signing out:', error);
            }
          },
        },
      ]
    );
  };

  return (
    <ScreenContainer scrollable={false} withPadding={false}>
      <StyledView className="flex-1 bg-gradient-to-b from-blue-500 to-purple-600" style={{ backgroundColor: '#667eea' }}>
        {/* Logout Button */}
        <StyledView className="absolute top-12 right-4 z-10">
          <StyledTouchableOpacity
            onPress={handleLogout}
            className="bg-white/20 rounded-full p-3"
            style={{ backgroundColor: 'rgba(255, 255, 255, 0.2)' }}
          >
            <Ionicons name="log-out-outline" size={24} color="white" />
          </StyledTouchableOpacity>
        </StyledView>

        <StyledView className="flex-1 justify-center items-center px-8">
          {/* Logo/Icon */}
          <StyledView className="mb-8 bg-white rounded-full p-6 shadow-lg">
            <Ionicons name="medical" size={64} color="#667eea" />
          </StyledView>

          {/* Welcome Text */}
          <StyledText
            variant="h1"
            className="text-white text-4xl font-bold text-center mb-4"
          >
            Welcome to MediMind
          </StyledText>

          <StyledText
            variant="h2"
            className="text-white text-xl font-medium text-center mb-8"
          >
            Your AI-Powered Health Companion
          </StyledText>

          {/* Hero Illustration */}
          <StyledView className="mb-12 items-center">
            <StyledView className="bg-white/20 rounded-2xl p-8 mb-6" style={{ backgroundColor: 'rgba(255, 255, 255, 0.2)' }}>
              <StyledView className="flex-row items-center justify-center space-x-4">
                <StyledView className="bg-white rounded-lg p-3">
                  <Ionicons name="document-text" size={32} color="#667eea" />
                </StyledView>
                <Ionicons name="arrow-forward" size={24} color="white" />
                <StyledView className="bg-white rounded-lg p-3">
                  <Ionicons name="bulb" size={32} color="#764ba2" />
                </StyledView>
                <Ionicons name="arrow-forward" size={24} color="white" />
                <StyledView className="bg-white rounded-lg p-3">
                  <Ionicons name="analytics" size={32} color="#667eea" />
                </StyledView>
              </StyledView>
            </StyledView>

            <StyledText
              variant="body1"
              className="text-white text-center text-lg leading-relaxed"
              style={{ opacity: 0.9 }}
            >
              Take control of your health data with intelligent{'\n'}
              organization and personalized insights
            </StyledText>
          </StyledView>

          {/* Get Started Button */}
          <StyledTouchableOpacity
            onPress={handleGetStarted}
            className="bg-white rounded-full px-12 py-4 shadow-lg"
            style={{ elevation: 5 }}
          >
            <StyledView className="flex-row items-center">
              <StyledText
                variant="body1"
                className="text-purple-600 font-bold text-lg mr-2"
              >
                Get Started
              </StyledText>
              <Ionicons name="arrow-forward" size={20} color="#667eea" />
            </StyledView>
          </StyledTouchableOpacity>

          {/* Bottom spacing */}
          <StyledView className="h-16" />
        </StyledView>
      </StyledView>
    </ScreenContainer>
  );
};

export default WelcomeScreen; 