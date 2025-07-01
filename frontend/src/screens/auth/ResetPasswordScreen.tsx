import React, { useState, useEffect } from 'react';
import { Alert } from 'react-native';
import { useNavigation, useRoute, RouteProp } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import * as Linking from 'expo-linking';
import { AuthStackParamList, ResetPasswordRouteParams } from '../../navigation/types';
import { supabaseClient } from '../../services/supabase';
import ScreenContainer from '../../components/layout/ScreenContainer';
import StyledText from '../../components/common/StyledText';
import StyledButton from '../../components/common/StyledButton';
import StyledInput from '../../components/common/StyledInput';

type ResetPasswordScreenNavigationProp = NativeStackNavigationProp<AuthStackParamList, 'ResetPassword'>;
type ResetPasswordScreenRouteProp = RouteProp<{ ResetPassword: ResetPasswordRouteParams }, 'ResetPassword'>;

const ResetPasswordScreen = () => {
  const navigation = useNavigation<ResetPasswordScreenNavigationProp>();
  const route = useRoute<ResetPasswordScreenRouteProp>();
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | undefined>(undefined);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    // Check route params first (passed from AppNavigator)
    if (route.params) {
      if (route.params.error_description) {
        setError(`Reset link error: ${route.params.error_description}. Please request a new password reset link.`);
        setReady(false);
        return;
      }
      if (route.params.type === 'recovery') {
        console.log('Recovery type detected from route params');
        setReady(true);
        setError(undefined);
        return;
      }
    }

    const createSessionFromUrl = async (url: string) => {
      try {

        const urlObj = new URL(url);
        const hashParams = new URLSearchParams(urlObj.hash.substring(1));

        const accessToken = hashParams.get('access_token');
        const refreshToken = hashParams.get('refresh_token');
        const type = hashParams.get('type');

        if (type === 'recovery' && accessToken && refreshToken) {
          console.log('Setting session from recovery tokens');
          const { data, error } = await supabaseClient.auth.setSession({
            access_token: accessToken,
            refresh_token: refreshToken,
          });

          if (error) {
            console.error('Error setting session:', error);
            setError('Invalid or expired reset link. Please request a new password reset.');
          } else if (data.session) {
            console.log('Session set successfully for password recovery');
            setReady(true);
            setError(undefined);
          }
        } else if (url.includes('ResetPassword')) {

          console.log('Processing reset password URL:', url);
          setReady(true);
          setError(undefined);
        }
      } catch (err) {
        console.error('Error parsing recovery URL:', err);
        setError('Failed to process password reset link.');
      }
    };

    // Handle initial URL if app was opened via deep link
    Linking.getInitialURL().then(async (url) => {
      if (url) {
        await createSessionFromUrl(url);
      }
    });

    // Listen for incoming deep links
    const linkingSubscription = Linking.addEventListener('url', async ({ url }) => {
      if (url) {
        await createSessionFromUrl(url);
      }
    });

    // Listen for Supabase auth state changes
    const { data: { subscription: authSubscription } } = supabaseClient.auth.onAuthStateChange((event, session) => {
      console.log('Auth state change:', event, session?.user?.id);
      if (event === 'PASSWORD_RECOVERY') {
        console.log('Password recovery event detected');
        setError(undefined);
        setReady(true);
      }
    });

    // Symmetrical cleanup
    return () => {
      linkingSubscription?.remove();
      authSubscription.unsubscribe();
    };
  }, [route.params]);

  const handleResetPassword = async () => {
    if (!ready) {
      setError('Please tap the reset link in your email first.');
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
    if (newPassword.length < 8) {
      setError("Password must be at least 8 characters long.");
      return;
    }

    setLoading(true);
    setError(undefined);

    try {
      const { data, error: updateError } = await supabaseClient.auth.updateUser({
        password: newPassword,
      });

      if (updateError) {
        console.error('Password update error:', updateError);


        const errorMessage = updateError.message.toLowerCase();
        if (errorMessage.includes('expired') || errorMessage.includes('invalid') ||
          errorMessage.includes('token') || errorMessage.includes('session')) {
          setError('Your password reset link has expired or been used already. Please request a new password reset link from the login screen.');
        } else if (errorMessage.includes('weak') || errorMessage.includes('password')) {
          setError('Password is too weak. Please choose a stronger password with at least 8 characters.');
        } else {
          setError(`Failed to update password: ${updateError.message}`);
        }
      } else if (data) {
        console.log('Password updated successfully');
        Alert.alert(
          'Success',
          'Password updated successfully! You can now log in with your new password.',
          [
            {
              text: 'OK',
              onPress: () => {
                supabaseClient.auth.signOut();
                navigation.navigate('Login');
              },
            },
          ]
        );
      }
    } catch (catchError: any) {
      console.error('Catch error during password update:', catchError);


      const errorMessage = catchError.message || 'An unexpected error occurred.';
      if (errorMessage.toLowerCase().includes('network') || errorMessage.toLowerCase().includes('fetch')) {
        setError('Network error. Please check your connection and try again.');
      } else {
        setError(`Failed to update password: ${errorMessage}`);
      }
    } finally {
      setLoading(false);
    }
  };


  if (!ready) {
    return (
      <ScreenContainer withPadding>
        <StyledText variant="h1" color="primary" className="mb-4 text-center">
          Reset Password
        </StyledText>
        <StyledText variant="body1" color="textSecondary" className="mb-8 text-center">
          Tap the reset link in your email to continue...
        </StyledText>
        <StyledButton
          variant="textPrimary"
          onPress={() => navigation.navigate('Login')}
          className="w-full"
        >
          Back to Login
        </StyledButton>
      </ScreenContainer>
    );
  }

  return (
    <ScreenContainer withPadding>
      <StyledText variant="h1" color="primary" className="mb-4 text-center">
        Reset Password
      </StyledText>
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
    </ScreenContainer>
  );
};

export default ResetPasswordScreen; 