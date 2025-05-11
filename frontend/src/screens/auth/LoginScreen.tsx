import React, { useState } from 'react';
// import { View, Text, Button } from 'react-native'; // No longer directly needed
// import { styled } from 'nativewind'; // No longer directly needed
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { AuthStackParamList } from '../../navigation/types'; // Corrected path

import ScreenContainer from '../../components/layout/ScreenContainer'; // Corrected path
import StyledText from '../../components/common/StyledText'; // Corrected path
import StyledButton from '../../components/common/StyledButton'; // Corrected path
import StyledInput from '../../components/common/StyledInput'; // Corrected path

// const StyledView = styled(View);
// const StyledText = styled(RNText);

type LoginScreenNavigationProp = NativeStackNavigationProp<AuthStackParamList, 'Login'>;

const LoginScreen = () => {
  const navigation = useNavigation<LoginScreenNavigationProp>();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleLogin = () => {
    // TODO: Implement actual login logic
    console.log('Login attempt with:', email, password);
    navigation.navigate('Main' as never); // Navigate to Main app stack post-login
  };

  return (
    <ScreenContainer withPadding>
      <StyledText variant="h1" color="primary" tw="mb-4 text-center">Welcome Back!</StyledText>
      <StyledText variant="body1" color="textSecondary" tw="mb-8 text-center">
        Sign in to access your health dashboard.
      </StyledText>
      
      <StyledInput
        label="Email"
        value={email}
        onChangeText={setEmail}
        keyboardType="email-address"
        autoCapitalize="none"
        tw="mb-4"
      />
      <StyledInput
        label="Password"
        value={password}
        onChangeText={setPassword}
        secureTextEntry
        tw="mb-6"
      />
      <StyledButton 
        variant="primary" 
        onPress={handleLogin} 
        tw="w-full mb-4"
        labelStyle={{fontSize: 16}}
      >
        Log In
      </StyledButton>
      <StyledButton 
        variant="ghost" 
        onPress={() => navigation.navigate('SignUp')} 
        tw="w-full"
      >
        Don't have an account? Sign Up
      </StyledButton>
    </ScreenContainer>
  );
};

export default LoginScreen; 