import React, { useState, useEffect } from 'react'
import { Alert, ActivityIndicator, View } from 'react-native'
import * as Linking from 'expo-linking'
import { useNavigation } from '@react-navigation/native'
import { NativeStackNavigationProp } from '@react-navigation/native-stack'
import { AuthStackParamList } from '../../navigation/types'
import { supabaseClient } from '../../services/supabase'
import { useTheme } from '../../theme'
import ScreenContainer from '../../components/layout/ScreenContainer'
import StyledText from '../../components/common/StyledText'
import StyledButton from '../../components/common/StyledButton'
import StyledInput from '../../components/common/StyledInput'
import { styled } from 'nativewind'

const StyledView = styled(View)

type NavProp = NativeStackNavigationProp<AuthStackParamList, 'ResetPassword'>

export default function ResetPasswordScreen() {
  const navigation = useNavigation<NavProp>()
  const theme = useTheme()

  const [ready, setReady] = useState(false)
  const [error, setError] = useState<string>()
  const [loading, setLoading] = useState(false)
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')


  const handleDeepLink = async (url: string) => {
    try {
      const fragment = url.split('#')[1] || ''
      const params = new URLSearchParams(fragment)
      const access_token = params.get('access_token')
      const refresh_token = params.get('refresh_token')
      const type = params.get('type')

      if (type === 'recovery' && access_token && refresh_token) {
        const { error: sessionError } = await supabaseClient.auth.setSession({
          access_token,
          refresh_token,
        })
        if (sessionError) throw sessionError
        setReady(true)
        setError(undefined)
      } else {
        setError('Invalid reset link.')
      }
    } catch (err: any) {
      console.error('Error processing reset link:', err)
      setError(err.message || 'Failed to process reset link.')
    }
  }

  useEffect(() => {

    Linking.getInitialURL().then(url => {
      if (url) handleDeepLink(url)
    })

    const sub = Linking.addEventListener('url', e => handleDeepLink(e.url))
    return () => sub.remove()
  }, [])

  const handleResetPassword = async () => {
    if (!ready) {
      setError('Waiting to process reset link…')
      return
    }
    if (!newPassword.trim()) {
      setError('Please enter a new password.')
      return
    }
    if (newPassword !== confirmPassword) {
      setError('Passwords do not match.')
      return
    }
    if (newPassword.length < 8) {
      setError('Password must be at least 8 characters long.')
      return
    }

    setLoading(true)
    setError(undefined)
    const { error: updateError } = await supabaseClient.auth.updateUser({ password: newPassword })
    setLoading(false)

    if (updateError) {
      console.error('Password update error:', updateError)
      setError(updateError.message)
    } else {
      Alert.alert(
        'Success',
        'Your password has been updated. Please log in with your new password.',
        [{ text: 'OK', onPress: () => navigation.navigate('Login') }]
      )
    }
  }


  if (!ready) {
    return (
      <ScreenContainer withPadding={false}>
        <StyledView className="flex-1 justify-center items-center px-4">
          {error ? (
            <>
              <StyledText color="error" className="text-center mb-4">
                {error}
              </StyledText>
              <StyledButton variant="textPrimary" onPress={() => navigation.navigate('Login')}>
                Back to Login
              </StyledButton>
            </>
          ) : (
            <ActivityIndicator size="large" color={theme.colors.primary} />
          )}
        </StyledView>
      </ScreenContainer>
    )
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
        className="mb-4"
        editable={!loading}
      />
      <StyledInput
        label="Confirm Password"
        value={confirmPassword}
        onChangeText={setConfirmPassword}
        secureTextEntry
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
        disabled={loading}
        loading={loading}
        className="w-full mb-4"
      >
        Update Password
      </StyledButton>

      <StyledButton variant="textPrimary" onPress={() => navigation.navigate('Login')} disabled={loading}>
        Back to Login
      </StyledButton>
    </ScreenContainer>
  )
}
