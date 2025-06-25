import React, { useState, useEffect } from 'react';
import { Alert } from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import * as Linking from 'expo-linking';

import { AuthStackParamList } from '../../navigation/types';
import { supabaseClient } from '../../services/supabase';
import { useTheme } from '../../theme';

import ScreenContainer from '../../components/layout/ScreenContainer';
import StyledText from '../../components/common/StyledText';
import StyledButton from '../../components/common/StyledButton';
import StyledInput from '../../components/common/StyledInput';

type ResetPasswordScreenNavigationProp = NativeStackNavigationProp<AuthStackParamList, 'ResetPassword'>;

const ResetPasswordScreen = () => {
  const navigation = useNavigation<ResetPasswordScreenNavigationProp>();
  const route = useRoute();
  const theme = useTheme();
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isInitializing, setIsInitializing] = useState(true);

  useEffect(() => {
    const initializePasswordReset = async () => {
      try {
        setIsInitializing(true);

        // First, check if we already have a session (user came from email link)
        const { data: { session }, error: sessionError } = await supabaseClient.auth.getSession();

        if (sessionError) {
          console.error('Session error:', sessionError);
          setError('Failed to verify reset session. Please try again.');
          setIsInitializing(false);
          return;
        }

        if (session) {
          console.log('Found existing session for password reset');
          setIsAuthenticated(true);
          setError(null);
          setIsInitializing(false);
          return;
        }

        // If no session, try to get the URL and process it
        const initialUrl = await Linking.getInitialURL();
        if (initialUrl) {
          console.log('Processing initial URL:', initialUrl);
          await processResetLink(initialUrl);
        } else {
          // No URL and no session - user needs to click the email link
          setError('Please click the password reset link in your email to continue.');
        }

        // Set up listener for incoming links
        const subscription = Linking.addEventListener('url', (event) => {
          console.log('Received deep link:', event.url);
          processResetLink(event.url);
        });

        setIsInitializing(false);
        return () => subscription?.remove();
      } catch (error) {
        console.error('Error initializing password reset:', error);
        setError('Failed to initialize password reset. Please try again.');
        setIsInitializing(false);
      }
    };

    initializePasswordReset();
  }, []);

  const processResetLink = async (url: string) => {
    try {
      console.log('Processing reset link:', url);

      // Parse both hash fragments and query parameters
      const urlObj = new URL(url);
      let params = new URLSearchParams();

      // Check hash fragment first (Supabase typically uses this)
      if (urlObj.hash) {
        const fragment = urlObj.hash.substring(1);
        params = new URLSearchParams(fragment);
      }

      // If no hash params, check query parameters
      if (!params.has('access_token') && urlObj.search) {
        params = new URLSearchParams(urlObj.search);
      }

      const accessToken = params.get('access_token');
      const refreshToken = params.get('refresh_token');
      const type = params.get('type');

      console.log('Extracted params:', {
        hasAccessToken: !!accessToken,
        hasRefreshToken: !!refreshToken,
        type
      });

      if (type === 'recovery' && accessToken && refreshToken) {
        console.log('Setting session with extracted tokens');

        const { data, error: sessionError } = await supabaseClient.auth.setSession({
          access_token: accessToken,
          refresh_token: refreshToken,
        });

        if (sessionError) {
          console.error('Session error:', sessionError);
          setError('Invalid or expired reset link. Please request a new password reset.');
        } else if (data.session) {
          console.log('Successfully set session for password reset');
          setIsAuthenticated(true);
          setError(null);
        } else {
          setError('Failed to authenticate with reset link.');
        }
      } else {
        console.log('Invalid reset link format or missing parameters');
        setError('Invalid password reset link. Please request a new password reset.');
      }
    } catch (error) {
      console.error('Error processing reset link:', error);
      setError('Failed to process password reset link. Please try again.');
    }
  };

  const handleResetPassword = async () => {
    if (!isAuthenticated) {
      setError('Please click the password reset link in your email first.');
      return;
    }

    if (!newPassword.trim()) {
      setError("Please enter a new password.");
      return;
    }

    if (newPassword !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    if (newPassword.length < 6) {
      setError("Password must be at least 6 characters long.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      console.log('Updating password...');
      const { data, error: updateError } = await supabaseClient.auth.updateUser({
        password: newPassword,
      });

      if (updateError) {
        console.error('Password update error:', updateError);
        setError(updateError.message);
      } else if (data) {
        console.log('Password updated successfully');
        Alert.alert(
          'Success',
          'Password updated successfully! You can now log in with your new password.',
          [
            {
              text: 'OK',
              onPress: () => {
                // Sign out to ensure clean state
                supabaseClient.auth.signOut();
                navigation.navigate('Login');
              },
            },
          ]
        );
      }
    } catch (catchError: any) {
      console.error('Catch error:', catchError);
      setError(catchError.message || "An unexpected error occurred.");
    } finally {
      setLoading(false);
    }
  };

  if (isInitializing) {
    return (
      <ScreenContainer withPadding>
        <StyledText variant="h1" color="primary" className="mb-4 text-center">
          Reset Password
        </StyledText>
        <StyledText variant="body1" color="textSecondary" className="mb-8 text-center">
          Initializing password reset...
        </StyledText>
      </ScreenContainer>
    );
  }

  return (
    <ScreenContainer withPadding>
      <StyledText variant="h1" color="primary" className="mb-4 text-center">
        Reset Password
      </StyledText>

      {!isAuthenticated ? (
        <>
          <StyledText variant="body1" color="textSecondary" className="mb-8 text-center">
            Please click the password reset link in your email to continue.
          </StyledText>

          {error && (
            <StyledText variant="caption" color="error" className="text-center mb-4">
              {error}
            </StyledText>
          )}

          <StyledButton
            variant="textPrimary"
            onPress={() => navigation.navigate('Login')}
            className="w-full"
          >
            Back to Login
          </StyledButton>
        </>
      ) : (
        <>
          <StyledText variant="body1" color="textSecondary" className="mb-8 text-center">
            Enter your new password below.
          </StyledText>

          <StyledInput
            label="New Password"
            value={newPassword}
            onChangeText={setNewPassword}
            secureTextEntry
            autoComplete="new-password"
            textContentType="newPassword"
            autoCorrect={false}
            spellCheck={false}
            className="mb-4"
            editable={!loading}
          />

          <StyledInput
            label="Confirm New Password"
            value={confirmPassword}
            onChangeText={setConfirmPassword}
            secureTextEntry
            autoComplete="new-password"
            textContentType="newPassword"
            autoCorrect={false}
            spellCheck={false}
            className="mb-6"
            editable={!loading}
          />

          {error && (
            <StyledText variant="caption" color="error" className="text-center mb-4">
              {error}
            </StyledText>
          )}

          <StyledButton
            variant="filledPrimary"
            onPress={handleResetPassword}
            className="w-full mb-4"
            disabled={loading}
            loading={loading}
          >
            Update Password
          </StyledButton>

          <StyledButton
            variant="textPrimary"
            onPress={() => navigation.navigate('Login')}
            className="w-full"
            disabled={loading}
          >
            Back to Login
          </StyledButton>
        </>
      )}
    </ScreenContainer>
  );
};

export default ResetPasswordScreen; 