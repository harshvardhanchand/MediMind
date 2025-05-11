import React, { useState } from 'react';
import { View, StyleSheet, ScrollView } from 'react-native';
import { Button, TextInput, Title, Paragraph, HelperText, Snackbar } from 'react-native-paper';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RootStackParamList } from '../navigation/AppNavigator';
import * as SecureStore from 'expo-secure-store';
import { supabaseClient } from '../services/supabase';

type LoginScreenNavigationProp = NativeStackNavigationProp<RootStackParamList, 'Login'>;

const LoginScreen = () => {
  const navigation = useNavigation<LoginScreenNavigationProp>();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showSnackbar, setShowSnackbar] = useState(false);

  const isEmailValid = () => {
    return /\S+@\S+\.\S+/.test(email);
  };

  const isPasswordValid = () => {
    return password.length >= 6;
  };

  const handleLogin = async () => {
    if (!isEmailValid() || !isPasswordValid()) {
      setError('Please enter a valid email and password');
      setShowSnackbar(true);
      return;
    }

    setLoading(true);
    setError('');

    try {
      // Call Supabase auth
      const { data, error: loginError } = await supabaseClient.auth.signInWithPassword({
        email,
        password
      });

      if (loginError) {
        throw loginError;
      }

      if (data?.session) {
        // Store auth token
        await SecureStore.setItemAsync('authToken', data.session.access_token);

        // Store refresh token if available
        if (data.session.refresh_token) {
          await SecureStore.setItemAsync('refreshToken', data.session.refresh_token);
        }

        // We don't need to navigate here because the AppNavigator 
        // will detect the token and switch to the authenticated screens
      }
    } catch (err: any) {
      console.error('Login error:', err);
      setError(err.message || 'Failed to login. Please try again.');
      setShowSnackbar(true);
    } finally {
      setLoading(false);
    }
  };

  const handleBypassLogin = () => {
    // For testing UI/UX, navigate directly to Home
    // In a real app, you might want to set some mock user state here too
    navigation.reset({
      index: 0,
      routes: [{ name: 'Home' }],
    });
  };

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <View style={styles.formContainer}>
        <Title style={styles.title}>Medical Data Hub</Title>
        <Paragraph style={styles.subtitle}>
          Securely manage your medical information
        </Paragraph>

        <TextInput
          label="Email"
          value={email}
          onChangeText={setEmail}
          mode="outlined"
          autoCapitalize="none"
          keyboardType="email-address"
          style={styles.input}
          error={email.length > 0 && !isEmailValid()}
        />
        <HelperText type="error" visible={email.length > 0 && !isEmailValid()}>
          Please enter a valid email address
        </HelperText>

        <TextInput
          label="Password"
          value={password}
          onChangeText={setPassword}
          mode="outlined"
          secureTextEntry
          style={styles.input}
          error={password.length > 0 && !isPasswordValid()}
        />
        <HelperText type="error" visible={password.length > 0 && !isPasswordValid()}>
          Password must be at least 6 characters
        </HelperText>

        <Button
          mode="contained"
          onPress={handleLogin}
          loading={loading}
          disabled={loading}
          style={styles.button}
        >
          Sign In
        </Button>

        <Button
          mode="text"
          onPress={() => navigation.navigate('Register')}
          style={styles.linkButton}
        >
          Don't have an account? Sign Up
        </Button>

        <Button
          mode="outlined"
          onPress={handleBypassLogin}
          style={styles.button}
        >
          Bypass Sign-In (Test)
        </Button>
      </View>
      
      <Snackbar
        visible={showSnackbar}
        onDismiss={() => setShowSnackbar(false)}
        duration={3000}
        action={{
          label: 'Dismiss',
          onPress: () => setShowSnackbar(false),
        }}
      >
        {error}
      </Snackbar>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flexGrow: 1,
    backgroundColor: '#F5F7FA',
    padding: 20,
  },
  formContainer: {
    flex: 1,
    justifyContent: 'center',
    marginBottom: 24,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#2A6BAC',
    marginTop: 20,
    marginBottom: 8,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 16,
    color: '#666',
    marginBottom: 32,
    textAlign: 'center',
  },
  input: {
    marginBottom: 4,
  },
  button: {
    marginTop: 16,
    paddingVertical: 8,
  },
  linkButton: {
    marginTop: 16,
  },
});

export default LoginScreen; 