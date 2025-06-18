import React, { useState } from 'react';
// import { View, Text, Button } from 'react-native'; // No longer directly needed
// import { styled } from 'nativewind'; // No longer directly needed
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { ActivityIndicator, View } from 'react-native'; // Added View for centering ActivityIndicator if needed
import * as Linking from 'expo-linking';

import { AuthStackParamList } from '../../navigation/types'; // Corrected path
import { supabaseClient } from '../../services/supabase'; // Import Supabase client
import { useTheme } from '../../theme'; // Import useTheme
// import { theme } from '../../theme'; // Assuming theme exports colors - Color will be hardcoded for now

import ScreenContainer from '../../components/layout/ScreenContainer'; // Corrected path
import StyledText from '../../components/common/StyledText'; // Corrected path
import StyledButton from '../../components/common/StyledButton'; // Corrected path
import StyledInput from '../../components/common/StyledInput'; // Corrected path

// const StyledView = styled(View);
// const StyledText = styled(RNText);

type LoginScreenNavigationProp = NativeStackNavigationProp<AuthStackParamList, 'Login'>;

const LoginScreen = () => {
  const navigation = useNavigation<LoginScreenNavigationProp>();
  const theme = useTheme(); // Get theme object
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loadingLogin, setLoadingLogin] = useState(false);
  const [loadingDevLogin, setLoadingDevLogin] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLogin = async () => {
    setLoadingLogin(true);
    setError(null);
    try {
      const { data, error: authError } = await supabaseClient.auth.signInWithPassword({
        email: email,
        password: password,
      });

      if (authError) {
        setError(authError.message);
      } else if (data.session) {
        // Login successful - AuthContext will handle navigation automatically
        console.log("Login successful, AuthContext will handle navigation");
      } else {
        setError("An unexpected error occurred during login.");
      }
    } catch (catchError: any) {
      setError(catchError.message || "An unexpected error occurred.");
    } finally {
      setLoadingLogin(false);
    }
  };

  const DEV_EMAIL = 'test@example.com'; // Replace with your test user
  const DEV_PASSWORD = 'password123'; // Replace with your test user's password

  const handleDevLogin = async () => {
    console.warn(`Attempting DEV login with ${DEV_EMAIL}. Ensure this user exists in your Supabase auth table.`);
    setLoadingDevLogin(true);
    setError(null);
    try {
      const { data, error: authError } = await supabaseClient.auth.signInWithPassword({
        email: DEV_EMAIL,
        password: DEV_PASSWORD,
      });

      if (authError) {
        setError(authError.message);
      } else if (data.session) {
        console.log("Dev login successful, AuthContext will handle navigation");
      } else {
        setError("An unexpected error occurred during dev login.");
      }
    } catch (catchError: any) {
      setError(catchError.message || "An unexpected error occurred.");
    } finally {
      setLoadingDevLogin(false);
    }
  };

  const handleForgotPassword = async () => {
    if (!email.trim()) {
      setError("Please enter your email address first.");
      return;
    }

    try {
      
      const resetPasswordURL = 'medimind://ResetPassword';
      
      
      const { error: resetError } = await supabaseClient.auth.resetPasswordForEmail(email, {
        redirectTo: resetPasswordURL,
      });

      if (resetError) {
        console.error('Reset password error:', resetError);
        setError(resetError.message);
      } else {
        setError(null);
        console.log('Password reset email sent successfully');
        alert("Password reset email sent! Please check your inbox and click the link to reset your password.");
      }
    } catch (catchError: any) {
      console.error('Catch error in forgot password:', catchError);
      setError(catchError.message || "An unexpected error occurred.");
    }
  };

  const isLoading = loadingLogin || loadingDevLogin;

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
        autoComplete="username"
        textContentType="emailAddress"
        autoCapitalize="none"
        tw="mb-4"
        editable={!isLoading}
      />
      <StyledInput
        label="Password"
        value={password}
        onChangeText={setPassword}
        secureTextEntry
        autoComplete="current-password"
        textContentType="password"
        autoCorrect={false}
        spellCheck={false}
        tw="mb-6"
        editable={!isLoading}
      />

      {error && (
        <StyledText variant="caption" color="error" tw="text-center mb-4">
          {error}
        </StyledText>
      )}

      <StyledButton 
        variant="filledPrimary"
        onPress={handleLogin} 
        tw="w-full mb-4"
        disabled={isLoading}
        loading={loadingLogin}
      >
        Log In
      </StyledButton>
      
      <StyledButton 
        variant="textPrimary"
        onPress={handleForgotPassword} 
        tw="w-full mb-4"
        disabled={isLoading}
      >
        Forgot Password?
      </StyledButton>
      
      <StyledButton 
        variant="textPrimary"
        onPress={() => navigation.navigate('SignUp')} 
        tw="w-full mb-4"
        disabled={isLoading}
      >
        Don't have an account? Sign Up
      </StyledButton>

      {__DEV__ && (
        <StyledButton 
          variant="filledSecondary"
          onPress={handleDevLogin} 
          tw="w-full mt-4"
          disabled={isLoading}
          loading={loadingDevLogin}
        >
          Dev: Quick Login (User: {DEV_EMAIL})
        </StyledButton>
      )}
    </ScreenContainer>
  );
};

export default LoginScreen; 