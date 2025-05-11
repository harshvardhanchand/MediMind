import React, { useState } from 'react';
import { View, StyleSheet, ScrollView } from 'react-native';
import { Button, TextInput, Title, Paragraph, HelperText, Snackbar } from 'react-native-paper';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RootStackParamList } from '../navigation/AppNavigator';
import { supabaseClient } from '../services/supabase';

type RegisterScreenNavigationProp = NativeStackNavigationProp<RootStackParamList, 'Register'>;

const RegisterScreen = () => {
  const navigation = useNavigation<RegisterScreenNavigationProp>();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [showSnackbar, setShowSnackbar] = useState(false);

  const isEmailValid = () => {
    return /\S+@\S+\.\S+/.test(email);
  };

  const isPasswordValid = () => {
    return password.length >= 8 && 
           /[A-Z]/.test(password) && 
           /[a-z]/.test(password) && 
           /[0-9]/.test(password);
  };

  const doPasswordsMatch = () => {
    return password === confirmPassword;
  };

  const handleRegister = async () => {
    if (!isEmailValid()) {
      setError('Please enter a valid email address');
      setShowSnackbar(true);
      return;
    }

    if (!isPasswordValid()) {
      setError('Password must be at least 8 characters and include uppercase, lowercase, and numbers');
      setShowSnackbar(true);
      return;
    }

    if (!doPasswordsMatch()) {
      setError('Passwords do not match');
      setShowSnackbar(true);
      return;
    }

    setLoading(true);
    setError('');

    try {
      // Call Supabase auth for registration
      const { error: signUpError } = await supabaseClient.auth.signUp({
        email,
        password,
      });

      if (signUpError) {
        throw signUpError;
      }

      setSuccess('Registration successful! Please check your email for verification.');
      setShowSnackbar(true);
      
      // Clear form
      setEmail('');
      setPassword('');
      setConfirmPassword('');
      
      // Redirect to login after a delay
      setTimeout(() => {
        navigation.navigate('Login');
      }, 2000);
    } catch (err: any) {
      console.error('Registration error:', err);
      setError(err.message || 'Failed to register. Please try again.');
      setShowSnackbar(true);
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <View style={styles.formContainer}>
        <Title style={styles.title}>Create Account</Title>
        <Paragraph style={styles.subtitle}>
          Join Medical Data Hub to securely manage your health data
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
          Password must be at least 8 characters and include uppercase, lowercase, and numbers
        </HelperText>

        <TextInput
          label="Confirm Password"
          value={confirmPassword}
          onChangeText={setConfirmPassword}
          mode="outlined"
          secureTextEntry
          style={styles.input}
          error={confirmPassword.length > 0 && !doPasswordsMatch()}
        />
        <HelperText type="error" visible={confirmPassword.length > 0 && !doPasswordsMatch()}>
          Passwords do not match
        </HelperText>

        <Button
          mode="contained"
          onPress={handleRegister}
          loading={loading}
          disabled={loading}
          style={styles.button}
        >
          Register
        </Button>

        <Button
          mode="text"
          onPress={() => navigation.navigate('Login')}
          style={styles.linkButton}
        >
          Already have an account? Sign In
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
        {error || success}
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

export default RegisterScreen; 