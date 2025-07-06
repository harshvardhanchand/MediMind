import React, { useState, useEffect } from 'react'
import { Alert, ActivityIndicator, View } from 'react-native'
import * as Linking from 'expo-linking'
import { useNavigation } from '@react-navigation/native'
import { NativeStackNavigationProp } from '@react-navigation/native-stack'
import { AuthStackParamList } from '../../navigation/types'
import { supabaseClient } from '../../services/supabase'
import { useTheme } from '../../theme'
import { useAuth } from '../../context/AuthContext'
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
  const { isRecoveringPassword } = useAuth()

  const [loading, setLoading] = useState(false)
  const [formError, setFormError] = useState<string>()
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')




  const handleResetPassword = async () => {
    if (!isRecoveringPassword) {
      setFormError('Invalid session. Please use the link from your email again.')
      return
    }
    if (!newPassword.trim()) {
      setFormError('Please enter a new password.')
      return
    }
    if (newPassword !== confirmPassword) {
      setFormError('Passwords do not match.')
      return
    }
    if (newPassword.length < 8) {
      setFormError('Password must be at least 8 characters long.')
      return
    }

    setLoading(true)
    setFormError(undefined)

    const { data, error: updateError } = await supabaseClient.auth.updateUser({ password: newPassword })

    setLoading(false)

    if (updateError) {
      setFormError(updateError.message)
    } else {
      Alert.alert(
        'Success',
        'Your password has been updated successfully!',
        [{ text: 'OK', onPress: () => navigation.navigate('Login') }]
      )
    }
  }


  if (!isRecoveringPassword) {
    return (
      <ScreenContainer withPadding={false}>
        <StyledView className="flex-1 justify-center items-center px-4">
          <StyledText color="error" className="text-center mb-4">
            This link is invalid or has expired. Please request a new one.
          </StyledText>
          <StyledButton variant="textPrimary" onPress={() => navigation.navigate('Login')}>
            Back to Login
          </StyledButton>
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

      {formError && (
        <StyledText variant="caption" color="error" className="text-center mb-4">
          {formError}
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
