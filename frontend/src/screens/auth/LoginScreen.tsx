import React, { useState } from 'react';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { AuthStackParamList } from '../../navigation/types';
import { supabaseClient } from '../../services/supabase';
import { useTheme } from '../../theme';
import ScreenContainer from '../../components/layout/ScreenContainer';
import StyledText from '../../components/common/StyledText';
import StyledButton from '../../components/common/StyledButton';
import StyledInput from '../../components/common/StyledInput';



type LoginScreenNavigationProp = NativeStackNavigationProp<AuthStackParamList, 'Login'>;

const RESET_PASSWORD_URL = 'https://www.medimind.co.in/reset';
const DEV_EMAIL = 'test@example.com';
const DEV_PASSWORD = 'password123';

const LoginScreen = () => {
  const navigation = useNavigation<LoginScreenNavigationProp>();
  const theme = useTheme();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loadingLogin, setLoadingLogin] = useState(false);
  const [loadingDevLogin, setLoadingDevLogin] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const performLogin = async (loginEmail: string, loginPassword: string, isDevLogin = false) => {
    const setLoading = isDevLogin ? setLoadingDevLogin : setLoadingLogin;

    setLoading(true);
    setError(null);

    try {
      const { data, error: authError } = await supabaseClient.auth.signInWithPassword({
        email: loginEmail,
        password: loginPassword,
      });

      if (authError) {
        setError(authError.message);
      } else if (data.session) {
        // AuthContext will handle navigation
      } else {
        setError("An unexpected error occurred during login.");
      }
    } catch (catchError: any) {
      setError(catchError.message || "An unexpected error occurred.");
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = () => performLogin(email, password, false);
  const handleDevLogin = () => performLogin(DEV_EMAIL, DEV_PASSWORD, true);

  const handleForgotPassword = async () => {
    if (!email.trim()) {
      setError("Please enter your email address first.");
      return;
    }

    try {
      const { data, error: resetError } = await supabaseClient.auth.resetPasswordForEmail(email, {
        redirectTo: RESET_PASSWORD_URL,
      });

      if (resetError) {
        setError(resetError.message);
      } else {
        setError(null);
        alert("Password reset email sent! Please check your inbox and click the link to reset your password.");
      }
    } catch (catchError: any) {
      setError(catchError.message || "An unexpected error occurred.");
    }
  };

  const isLoading = loadingLogin || loadingDevLogin;

  return (
    <ScreenContainer withPadding>
      <StyledText variant="h1" color="primary" className="mb-4 text-center">Welcome Back!</StyledText>
      <StyledText variant="body1" color="textSecondary" className="mb-8 text-center">
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
        className="mb-4"
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
        className="mb-6"
        editable={!isLoading}
      />

      {error && (
        <StyledText variant="caption" color="error" className="text-center mb-4">
          {error}
        </StyledText>
      )}

      <StyledButton
        variant="filledPrimary"
        onPress={handleLogin}
        className="w-full mb-4"
        disabled={isLoading}
        loading={loadingLogin}
      >
        Log In
      </StyledButton>

      <StyledButton
        variant="textPrimary"
        onPress={handleForgotPassword}
        className="w-full mb-4"
        disabled={isLoading}
      >
        Forgot Password
      </StyledButton>

      <StyledButton
        variant="textPrimary"
        onPress={() => navigation.navigate('SignUp')}
        className="w-full mb-4"
        disabled={isLoading}
      >
        Don't have an account? Sign Up
      </StyledButton>

      {__DEV__ && (
        <StyledButton
          variant="filledSecondary"
          onPress={handleDevLogin}
          className="w-full mt-4"
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