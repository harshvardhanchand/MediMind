import React from 'react';
import { View, Image } from 'react-native';
import { styled } from 'nativewind';
import { useNavigation } from '@react-navigation/native';
import { LogIn, ArrowRight, Shield, Clipboard, Activity } from 'lucide-react-native';

import ScreenContainer from '../components/layout/ScreenContainer';
import StyledText from '../components/common/StyledText';
import StyledButton from '../components/common/StyledButton';

const StyledView = styled(View);
const StyledImage = styled(Image);

const OnboardingScreen = () => {
  const navigation = useNavigation();

  return (
    <ScreenContainer withPadding scrollable={false} backgroundColor="#F9FAFB">
      <StyledView tw="flex-1 justify-center">
        {/* Logo/Icon Area */}
        <StyledView tw="items-center mb-8">
          <StyledView tw="w-24 h-24 rounded-full bg-primary/10 items-center justify-center mb-4">
            <Activity size={48} color="#0EA5E9" />
          </StyledView>
        </StyledView>
        
        {/* Welcome Text */}
        <StyledText variant="h1" color="primary" tw="mb-3 text-center">
          Welcome to MedInsight!
        </StyledText>
        
        <StyledText variant="body1" tw="mb-10 text-center px-4" color="textSecondary">
          Your personal health data, simplified and secured. Take control of your medical records effortlessly.
        </StyledText>
        
        {/* Feature Highlights */}
        <StyledView tw="mb-8">
          <StyledView tw="flex-row items-center mb-4">
            <StyledView tw="w-10 h-10 rounded-full bg-blue-100 items-center justify-center mr-3">
              <Clipboard size={20} color="#0EA5E9" />
            </StyledView>
            <StyledView tw="flex-1">
              <StyledText variant="h4" color="textPrimary">Organize Medical Records</StyledText>
              <StyledText variant="caption" color="textSecondary">Store and access all documents in one place</StyledText>
            </StyledView>
          </StyledView>
          
          <StyledView tw="flex-row items-center">
            <StyledView tw="w-10 h-10 rounded-full bg-green-100 items-center justify-center mr-3">
              <Shield size={20} color="#4ADE80" />
            </StyledView>
            <StyledView tw="flex-1">
              <StyledText variant="h4" color="textPrimary">Secure & Private</StyledText>
              <StyledText variant="caption" color="textSecondary">Your data is encrypted and protected</StyledText>
            </StyledView>
          </StyledView>
        </StyledView>
      </StyledView>
      
      {/* Buttons Area */}
      <StyledView tw="w-full">
        <StyledButton 
          variant="primary"
          onPress={() => navigation.navigate('Auth' as never)} 
          tw="w-full"
          icon={() => <ArrowRight size={20} color="#FFFFFF" />}
          contentStyle={{ flexDirection: 'row-reverse', justifyContent: 'space-between' }}
          labelStyle={{ fontSize: 17, fontWeight: 'bold' }}
        >
          Get Started
        </StyledButton>
        
        <StyledButton 
          variant="ghost" 
          onPress={() => navigation.navigate('Auth' as never)}
          tw="mt-4 w-full"
          icon={() => <LogIn size={18} color="#0EA5E9" />}
        >
          I already have an account
        </StyledButton>
      </StyledView>
    </ScreenContainer>
  );
};

export default OnboardingScreen; 