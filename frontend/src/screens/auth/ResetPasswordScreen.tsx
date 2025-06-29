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
    Alert.alert('Debug: Screen Load', 'ResetPasswordScreen loaded', [{ text: 'OK' }]);

    const initializePasswordReset = async () => {
      try {
        Alert.alert('Debug: Init Start', 'Starting password reset initialization', [{ text: 'OK' }]);
        setIsInitializing(true);

        // First, check if we already have a session (user came from email link)
        const { data: { session }, error: sessionError } = await supabaseClient.auth.getSession();

        if (sessionError) {
          console.error('Session error:', sessionError);
          Alert.alert('Debug: Session Error', `Session error: ${sessionError.message}`, [{ text: 'OK' }]);
          setError('Failed to verify reset session. Please try again.');
          setIsInitializing(false);
          return;
        }

        if (session) {
          console.log('Found existing session for password reset');
          Alert.alert('Debug: Session Found', 'Found existing session for password reset', [{ text: 'OK' }]);
          setIsAuthenticated(true);
          setError(null);
          setIsInitializing(false);
          return;
        }

        Alert.alert('Debug: No Session', 'No existing session found', [{ text: 'OK' }]);

        // If no session, try to get the URL and process it
        const initialUrl = await Linking.getInitialURL();
        if (initialUrl) {
          console.log('Processing initial URL:', initialUrl);
          Alert.alert('Debug: Initial URL', `Found initial URL: ${initialUrl}`, [{ text: 'OK' }]);
          await processResetLink(initialUrl);
        } else {
          // No URL and no session - user needs to click the email link
          Alert.alert('Debug: No URL', 'No initial URL found', [{ text: 'OK' }]);
          setError('Please click the password reset link in your email to continue.');
        }

        // Set up listener for incoming links
        const subscription = Linking.addEventListener('url', (event) => {
          console.log('Received deep link:', event.url);
          Alert.alert('Debug: Deep Link Event', `Received deep link in ResetPassword: ${event.url}`, [{ text: 'OK' }]);
          processResetLink(event.url);
        });

        setIsInitializing(false);
        return () => subscription?.remove();
      } catch (error) {
        console.error('Error initializing password reset:', error);
        Alert.alert('Debug: Init Error', `Initialization error: ${error}`, [{ text: 'OK' }]);
        setError('Failed to initialize password reset. Please try again.');
        setIsInitializing(false);
      }
    };

    initializePasswordReset();
  }, []);

  const processResetLink = async (url: string) => {
    try {
      console.log('Processing reset link:', url);
      Alert.alert('Debug: Process Link', `Processing reset link: ${url}`, [{ text: 'OK' }]);

      // Parse both hash fragments and query parameters
      const urlObj = new URL(url);
      let params = new URLSearchParams();

      Alert.alert('Debug: URL Object', `Protocol: ${urlObj.protocol}\nHost: ${urlObj.host}\nPathname: ${urlObj.pathname}\nSearch: ${urlObj.search}\nHash: ${urlObj.hash}`, [{ text: 'OK' }]);

      // Check hash fragment first (Supabase typically uses this)
      if (urlObj.hash) {
        const fragment = urlObj.hash.substring(1);
        params = new URLSearchParams(fragment);
        Alert.alert('Debug: Hash Fragment', `Found hash fragment: ${fragment}`, [{ text: 'OK' }]);
      }

      // If no hash params, check query parameters
      if (!params.has('access_token') && urlObj.search) {
        params = new URLSearchParams(urlObj.search);
        Alert.alert('Debug: Query Params', `Using query parameters: ${urlObj.search}`, [{ text: 'OK' }]);
      }

      const accessToken = params.get('access_token');
      const refreshToken = params.get('refresh_token');
      const type = params.get('type');

      console.log('Extracted params:', {
        hasAccessToken: !!accessToken,
        hasRefreshToken: !!refreshToken,
        type
      });

      Alert.alert('Debug: Extracted Params', `Access Token: ${accessToken ? 'YES' : 'NO'}\nRefresh Token: ${refreshToken ? 'YES' : 'NO'}\nType: ${type}`, [{ text: 'OK' }]);

      if (type === 'recovery' && accessToken && refreshToken) {
        console.log('Setting session with extracted tokens');
        Alert.alert('Debug: Valid Tokens', 'Found valid recovery tokens - setting session', [{ text: 'OK' }]);

        const { data, error: sessionError } = await supabaseClient.auth.setSession({
          access_token: accessToken,
          refresh_token: refreshToken,
        });

        if (sessionError) {
          console.error('Session error:', sessionError);
          Alert.alert('Debug: Session Set Error', `Session error: ${sessionError.message}`, [{ text: 'OK' }]);
          setError('Invalid or expired reset link. Please request a new password reset.');
        } else if (data.session) {
          console.log('Successfully set session for password reset');
          Alert.alert('Debug: Session Success', 'Successfully set session for password reset', [{ text: 'OK' }]);
          setIsAuthenticated(true);
          setError(null);
        } else {
          Alert.alert('Debug: No Session Data', 'Session set but no session data returned', [{ text: 'OK' }]);
          setError('Failed to authenticate with reset link.');
        }
      } else {
        console.log('Invalid reset link format or missing parameters');
        Alert.alert('Debug: Invalid Link', `Invalid link format:\nType: ${type}\nAccess Token: ${accessToken ? 'YES' : 'NO'}\nRefresh Token: ${refreshToken ? 'YES' : 'NO'}`, [{ text: 'OK' }]);
        setError('Invalid password reset link. Please request a new password reset.');
      }
    } catch (error) {
      console.error('Error processing reset link:', error);
      Alert.alert('Debug: Process Error', `Error processing reset link: ${error}`, [{ text: 'OK' }]);
      setError('Failed to process password reset link. Please try again.');
    }
  };

  const handleResetPassword = async () => {
    Alert.alert('Debug: Reset Start', 'handleResetPassword called', [{ text: 'OK' }]);

    if (!isAuthenticated) {
      Alert.alert('Debug: Not Authenticated', 'User not authenticated for password reset', [{ text: 'OK' }]);
      setError('Please click the password reset link in your email first.');
      return;
    }

    Alert.alert('Debug: Authenticated', 'User is authenticated, proceeding with reset', [{ text: 'OK' }]);

    if (!newPassword.trim()) {
      Alert.alert('Debug: Validation', 'No new password entered', [{ text: 'OK' }]);
      setError("Please enter a new password.");
      return;
    }

    if (newPassword !== confirmPassword) {
      Alert.alert('Debug: Validation', 'Passwords do not match', [{ text: 'OK' }]);
      setError("Passwords do not match.");
      return;
    }

    if (newPassword.length < 6) {
      Alert.alert('Debug: Validation', 'Password too short', [{ text: 'OK' }]);
      setError("Password must be at least 6 characters long.");
      return;
    }

    Alert.alert('Debug: Validation Passed', 'All validations passed, updating password', [{ text: 'OK' }]);

    setLoading(true);
    setError(null);

    try {
      console.log('Updating password...');
      Alert.alert('Debug: Supabase Update', 'Calling supabase updateUser', [{ text: 'OK' }]);

      const { data, error: updateError } = await supabaseClient.auth.updateUser({
        password: newPassword,
      });

      if (updateError) {
        console.error('Password update error:', updateError);
        Alert.alert('Debug: Update Error', `Password update error: ${updateError.message}`, [{ text: 'OK' }]);
        setError(updateError.message);
      } else if (data) {
        console.log('Password updated successfully');
        Alert.alert('Debug: Update Success', 'Password updated successfully in Supabase', [{ text: 'OK' }]);
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
      Alert.alert('Debug: Catch Error', `Catch error during password update: ${catchError.message}`, [{ text: 'OK' }]);
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