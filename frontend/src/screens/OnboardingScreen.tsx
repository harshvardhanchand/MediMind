import React from 'react';
import { View, Image } from 'react-native';
import { styled } from 'nativewind';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { LogIn, ArrowRight, Shield, Clipboard, Activity, AlertTriangle } from 'lucide-react-native';

import { RootStackParamList } from '../navigation/types';
import ScreenContainer from '../components/layout/ScreenContainer';
import StyledText from '../components/common/StyledText';
import StyledButton from '../components/common/StyledButton';
import { useTheme } from '../theme';

const StyledView = styled(View);
const StyledImage = styled(Image);

const OnboardingScreen = () => {
  const navigation = useNavigation<NativeStackNavigationProp<RootStackParamList>>();
  const { colors } = useTheme();

  return (
    <ScreenContainer withPadding scrollable={false} backgroundColor="#F9FAFB">
      <StyledView tw="flex-1 justify-center">
        {/* Logo/Icon Area */}
        <StyledView tw="items-center mb-8">
          <StyledView tw="w-24 h-24 rounded-full bg-primary/10 items-center justify-center mb-4">
            <Activity size={48} color={colors.primary} />
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
              <Clipboard size={20} color={colors.primary} />
            </StyledView>
            <StyledView tw="flex-1">
              <StyledText variant="h4" color="textPrimary">Organize Medical Records</StyledText>
              <StyledText variant="caption" color="textSecondary">Store and access all documents in one place</StyledText>
            </StyledView>
          </StyledView>
          
          <StyledView tw="flex-row items-center">
            <StyledView tw="w-10 h-10 rounded-full bg-green-100 items-center justify-center mr-3">
              <Shield size={20} color={colors.success} />
            </StyledView>
            <StyledView tw="flex-1">
              <StyledText variant="h4" color="textPrimary">Secure & Private</StyledText>
              <StyledText variant="caption" color="textSecondary">Your data is encrypted and protected</StyledText>
            </StyledView>
          </StyledView>
        </StyledView>
      </StyledView>
      
      {/* Disclaimer and Terms Placeholder */}
      <StyledView tw="mb-6 px-2">
        <StyledView tw="flex-row items-center p-3 rounded-lg bg-warningContainer/50">
          <AlertTriangle size={24} color={colors.warning} style={{marginRight: 12}} />
          <StyledView tw="flex-1">
            <StyledText variant="label" color="textSecondary" tw="font-semibold">Important Disclaimer</StyledText>
            <StyledText variant="caption" color="textSecondary">
              MedInsight helps organize your health data. It does not provide medical advice, diagnosis, or treatment. Always consult a healthcare professional for medical concerns.
            </StyledText>
          </StyledView>
        </StyledView>
        <StyledText variant="caption" color="textMuted" tw="text-center mt-4">
          By continuing, you agree to our Terms of Service and Privacy Policy.
        </StyledText>
      </StyledView>

      {/* Buttons Area */}
      <StyledView tw="w-full">
        <StyledButton 
          variant="filledPrimary"
          onPress={() => navigation.navigate('Auth')} 
          tw="w-full"
          iconRight={<ArrowRight size={20} color={colors.onPrimary} />}
        >
          Get Started
        </StyledButton>
        
        <StyledButton 
          variant="textPrimary"
          onPress={() => navigation.navigate('Auth')}
          tw="mt-4 w-full"
          iconLeft={<LogIn size={18} color={colors.primary} />}
        >
          I already have an account
        </StyledButton>
      </StyledView>
    </ScreenContainer>
  );
};

export default OnboardingScreen; 