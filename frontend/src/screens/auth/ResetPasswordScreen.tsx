import React, { useState, useEffect } from 'react';
import { Alert } from 'react-native';
import { useNavigation, useRoute, RouteProp } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import * as Linking from 'expo-linking';

import { AuthStackParamList, ResetPasswordRouteParams } from '../../navigation/types';
import { supabaseClient } from '../../services/supabase';
import { useTheme } from '../../theme';

import ScreenContainer from '../../components/layout/ScreenContainer';
import StyledText from '../../components/common/StyledText';
import StyledButton from '../../components/common/StyledButton';
import StyledInput from '../../components/common/StyledInput';

type ResetPasswordScreenNavigationProp = NativeStackNavigationProp<AuthStackParamList, 'ResetPassword'>;
type ResetPasswordScreenRouteProp = RouteProp<AuthStackParamList, 'ResetPassword'>;

const ResetPasswordScreen = () => {
  const navigation = useNavigation<ResetPasswordScreenNavigationProp>();
  const route = useRoute<ResetPasswordScreenRouteProp>();
  const theme = useTheme();
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isInitializing, setIsInitializing] = useState(true);

  // Helper to set session and update state
  const setAuthSession = async (accessToken: string, refreshToken: string) => {
    Alert.alert('Debug: RPS SetAuthSession', `Attempting to set session. AT: ${!!accessToken}, RT: ${!!refreshToken}`, [{ text: 'OK' }]);
    const { data, error: sessionError } = await supabaseClient.auth.setSession({
      access_token: accessToken,
      refresh_token: refreshToken,
    });

    if (sessionError) {
      console.error('Session error on setAuthSession:', sessionError);
      Alert.alert('Debug: RPS Session Set Error', `Session error: ${sessionError.message}`, [{ text: 'OK' }]);
      setError('Invalid or expired reset link. Please request a new password reset.');
      setIsAuthenticated(false);
    } else if (data.session) {
      console.log('Successfully set session for password reset from setAuthSession');
      Alert.alert('Debug: RPS Session Success', 'Successfully set session.', [{ text: 'OK' }]);
      setIsAuthenticated(true);
      setError(null);
    } else {
      Alert.alert('Debug: RPS No Session Data', 'Session set but no session data returned', [{ text: 'OK' }]);
      setError('Failed to authenticate with reset link.');
      setIsAuthenticated(false);
    }
  };


  useEffect(() => {
    Alert.alert('Debug: RPS Load', `Route Params: ${JSON.stringify(route.params)}`, [{ text: 'OK' }]);

    const initializePasswordReset = async () => {
      setIsInitializing(true);
      setError(null); // Clear previous errors

      // 1. Check for existing Supabase session (e.g., if user re-opens app quickly)
      const { data: { session: currentSession }, error: currentSessionError } = await supabaseClient.auth.getSession();
      if (currentSessionError) {
        console.error('Error fetching current session:', currentSessionError);
        // Non-fatal, proceed with link processing
      }
      if (currentSession) {
        console.log('Found existing Supabase session, user might be authenticated for reset.');
        // Check if this session is sufficient for password update (e.g. user.aud === 'authenticated')
        // Supabase updateUser requires an authenticated session.
        // If the link was already processed and session set, this is fine.
        setIsAuthenticated(true);
        setIsInitializing(false);
        Alert.alert('Debug: RPS Existing SB Session', 'Found active Supabase session.', [{ text: 'OK' }]);
        return;
      }


      // 2. Prioritize route params passed from AppNavigator
      const params = route.params;
      if (params) {
        Alert.alert('Debug: RPS Route Params Found', `Params: ${JSON.stringify(params)}`, [{ text: 'OK' }]);
        if (params.error_description) {
          setError(`Error from link: ${params.error_description}`);
          setIsAuthenticated(false);
          setIsInitializing(false);
          Alert.alert('Debug: RPS Error Param', `Error: ${params.error_description}`, [{ text: 'OK' }]);
          return;
        }

        if (params.type === 'recovery' && params.accessToken && params.refreshToken) {
          Alert.alert('Debug: RPS Route Params Valid', 'Using tokens from route params.', [{ text: 'OK' }]);
          await setAuthSession(params.accessToken, params.refreshToken);
          setIsInitializing(false);
          return;
        }
         Alert.alert('Debug: RPS Route Params Incomplete', 'Route params present but not sufficient for immediate session set.', [{ text: 'OK' }]);
      } else {
        Alert.alert('Debug: RPS No Route Params', 'No route params found.', [{ text: 'OK' }]);
      }

      // 3. If no/incomplete route params, or if they didn't lead to authentication,
      //    try to get the initial URL (could be redundant if AppNavigator already handled, but good fallback)
      let initialUrlProcessed = false;
      try {
        const initialUrl = await Linking.getInitialURL();
        if (initialUrl) {
          Alert.alert('Debug: RPS Initial URL', `Found: ${initialUrl}`, [{ text: 'OK' }]);
          // Avoid reprocessing if params from AppNavigator were already sufficient
          if (!(params && params.accessToken && params.refreshToken)) {
             initialUrlProcessed = await processResetLink(initialUrl, 'Initial URL');
          } else {
            Alert.alert('Debug: RPS Initial URL Skipped', 'Skipped processing initialURL as route params were sufficient.', [{ text: 'OK' }]);
          }
        } else {
           Alert.alert('Debug: RPS No Initial URL', 'No initial URL found by RPS.', [{ text: 'OK' }]);
        }
      } catch (e) {
        console.error("Error getting initial URL in RPS:", e);
        Alert.alert('Debug: RPS Initial URL Error', `Error: ${e}`, [{ text: 'OK' }]);
      }

      if (isAuthenticated || initialUrlProcessed && isAuthenticated) { // if processResetLink set isAuthenticated
        setIsInitializing(false);
        return;
      }

      // 4. Set up listener for incoming links if not yet authenticated
      //    This handles cases where the link arrives after the screen is already mounted.
      const subscription = Linking.addEventListener('url', async (event) => {
        Alert.alert('Debug: RPS Deep Link Event', `URL: ${event.url}`, [{ text: 'OK' }]);
        await processResetLink(event.url, 'Event Listener');
      });

      // If after all checks, not authenticated and no initial URL or params led to auth.
      if (!isAuthenticated && !initialUrlProcessed && !params?.accessToken) {
         Alert.alert('Debug: RPS Final State', 'No tokens from params, initial URL, or event. Showing prompt.', [{ text: 'OK' }]);
         setError('Please click the password reset link in your email to continue.');
      }

      setIsInitializing(false);
      return () => subscription?.remove();
    };

    initializePasswordReset();
  }, [route.params]); // Re-run if route.params change

  // processResetLink now primarily for URL strings from Linking module
  const processResetLink = async (url: string, context: string): Promise<boolean> => {
    Alert.alert('Debug: RPS Process Link', `Context: ${context}, URL: ${url}`, [{ text: 'OK' }]);
    try {
      const urlObj = new URL(url);
      let searchParams = new URLSearchParams();

      if (urlObj.hash && urlObj.hash.length > 1) {
        searchParams = new URLSearchParams(urlObj.hash.substring(1));
        Alert.alert('Debug: RPS Link Hash', `Fragment: ${urlObj.hash.substring(1)}`, [{ text: 'OK' }]);
      }
      if (searchParams.get('type') !== 'recovery' && urlObj.search) {
         const queryOnlyParams = new URLSearchParams(urlObj.search);
         if(queryOnlyParams.get('type') === 'recovery'){
            searchParams = queryOnlyParams;
            Alert.alert('Debug: RPS Link Query', `Query: ${urlObj.search}`, [{ text: 'OK' }]);
         }
      }

      const accessToken = searchParams.get('access_token');
      const refreshToken = searchParams.get('refresh_token');
      const type = searchParams.get('type');
      const errorDesc = searchParams.get('error_description');

      Alert.alert('Debug: RPS Link Extracted', `Type: ${type}, AT: ${!!accessToken}, RT: ${!!refreshToken}, Err: ${errorDesc}`, [{ text: 'OK' }]);

      if (errorDesc) {
        setError(`Error from link: ${errorDesc}`);
        setIsAuthenticated(false);
        return false;
      }

      if (type === 'recovery' && accessToken && refreshToken) {
        await setAuthSession(accessToken, refreshToken);
        return true; // Indicates successful processing
      } else {
        Alert.alert('Debug: RPS Link Invalid', 'Link from Linking module not sufficient.', [{ text: 'OK' }]);
        // Avoid overwriting error if already set by route.params
        if(!error) setError('Invalid password reset link from email.');
        return false;
      }
    } catch (err) {
      console.error('Error processing reset link string:', err);
      Alert.alert('Debug: RPS Link Process Error', `Error: ${err}`, [{ text: 'OK' }]);
      setError('Failed to process password reset link. Please try again.');
      return false;
    }
  };

  const handleResetPassword = async () => {
    // Alert.alert('Debug: Reset Start', 'handleResetPassword called', [{ text: 'OK' }]);
    if (!isAuthenticated) {
      Alert.alert('Error', 'Authentication failed. Please ensure you have clicked a valid password reset link.', [{ text: 'OK' }]);
      setError('Authentication required. Please use the link from your email.');
      return;
    }

    // Alert.alert('Debug: Authenticated', 'User is authenticated, proceeding with reset', [{ text: 'OK' }]);
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

    // Alert.alert('Debug: Validation Passed', 'All validations passed, updating password', [{ text: 'OK' }]);
    setLoading(true);
    setError(null);

    try {
      // console.log('Updating password...');
      // Alert.alert('Debug: Supabase Update', 'Calling supabase updateUser', [{ text: 'OK' }]);
      const { data, error: updateError } = await supabaseClient.auth.updateUser({
        password: newPassword,
      });

      if (updateError) {
        console.error('Password update error:', updateError);
        // Alert.alert('Debug: Update Error', `Password update error: ${updateError.message}`, [{ text: 'OK' }]);
        setError(updateError.message);
      } else if (data) {
        // console.log('Password updated successfully');
        // Alert.alert('Debug: Update Success', 'Password updated successfully in Supabase', [{ text: 'OK' }]);
        Alert.alert(
          'Success',
          'Password updated successfully! You can now log in with your new password.',
          [
            {
              text: 'OK',
              onPress: () => {
                supabaseClient.auth.signOut(); // Sign out to ensure clean state
                navigation.navigate('Login');
              },
            },
          ]
        );
      }
    } catch (catchError: any) {
      console.error('Catch error during password update:', catchError);
      // Alert.alert('Debug: Catch Error', `Catch error during password update: ${catchError.message}`, [{ text: 'OK' }]);
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