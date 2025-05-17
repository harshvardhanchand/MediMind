import React, { useState } from 'react';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { AuthStackParamList } from '../../navigation/types';
import { supabaseClient } from '../../services/supabase';
import ScreenContainer from '../../components/layout/ScreenContainer';
import StyledText from '../../components/common/StyledText';
import StyledButton from '../../components/common/StyledButton';
import StyledInput from '../../components/common/StyledInput';
import { useTheme } from '../../theme';

type SignUpScreenNavigationProp = NativeStackNavigationProp<AuthStackParamList, 'SignUp'>;

const SignUpScreen = () => {
  const navigation = useNavigation<SignUpScreenNavigationProp>();
  const theme = useTheme();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const validateEmail = (text: string) => /\S+@\S+\.\S+/.test(text);
  const validatePassword = (text: string) => text.length >= 8; // Basic length check, can be enhanced

  const handleSignUp = async () => {
    setError(null);
    setSuccessMessage(null);

    if (!validateEmail(email)) {
      setError('Please enter a valid email address.');
      return;
    }
    if (!validatePassword(password)) {
      setError('Password must be at least 8 characters long.');
      return;
    }
    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    setLoading(true);
    try {
      const { data, error: signUpError } = await supabaseClient.auth.signUp({
        email: email,
        password: password,
      });

      if (signUpError) {
        setError(signUpError.message);
      } else if (data.user) {
        // Check if user requires email confirmation
        if (data.user.identities && data.user.identities.length > 0 && !data.user.email_confirmed_at) {
          setSuccessMessage('Registration successful! Please check your email to verify your account.');
        } else {
          // This case might occur if email confirmation is disabled or user is auto-confirmed
          setSuccessMessage('Registration successful! You can now log in.');
          // Optionally, navigate to login or let AuthContext handle if session is created
        }
        setEmail('');
        setPassword('');
        setConfirmPassword('');
      } else {
        setError('An unexpected error occurred during sign up.');
      }
    } catch (catchError: any) {
      setError(catchError.message || 'An unexpected error occurred.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScreenContainer withPadding>
      <StyledText variant="h1" color="primary" tw="mb-4 text-center">Create Account</StyledText>
      <StyledText variant="body1" color="textSecondary" tw="mb-8 text-center">
        Join us to manage your health data securely.
      </StyledText>
      
      <StyledInput
        label="Email"
        value={email}
        onChangeText={setEmail}
        keyboardType="email-address"
        autoCapitalize="none"
        tw="mb-4"
        editable={!loading}
      />
      <StyledInput
        label="Password"
        value={password}
        onChangeText={setPassword}
        secureTextEntry
        tw="mb-4" // Adjusted margin
        editable={!loading}
      />
      <StyledInput
        label="Confirm Password"
        value={confirmPassword}
        onChangeText={setConfirmPassword}
        secureTextEntry
        tw="mb-6"
        editable={!loading}
      />

      {error && (
        <StyledText variant="caption" color="error" tw="text-center mb-4">
          {error}
        </StyledText>
      )}
      {successMessage && (
        <StyledText variant="caption" color="success" tw="text-center mb-4"> 
          {successMessage}
        </StyledText>
      )}

      <StyledButton 
        variant="filledPrimary"
        onPress={handleSignUp} 
        tw="w-full mb-4"
        disabled={loading}
        loading={loading}
      >
        Create Account
      </StyledButton>
      <StyledButton 
        variant="textPrimary"
        onPress={() => navigation.navigate('Login')} 
        tw="w-full"
        disabled={loading}
      >
        Already have an account? Log In
      </StyledButton>
    </ScreenContainer>
  );
};

export default SignUpScreen; 