import React from 'react';
import { Alert } from 'react-native';
import StyledButton from '../common/StyledButton';
import { crashReporting } from '../../services/crashReporting';

interface CrashTestButtonProps {
  variant?: 'filledPrimary' | 'textPrimary';
}

const CrashTestButton: React.FC<CrashTestButtonProps> = ({ variant = 'textPrimary' }) => {
  const handleTestCrash = () => {
    if (!__DEV__) {
      Alert.alert('Test Mode Only', 'Crash testing is only available in development mode.');
      return;
    }

    Alert.alert(
      'Test Crash Reporting',
      'Choose a test type:',
      [
        {
          text: 'Cancel',
          style: 'cancel',
        },
        {
          text: 'Manual Exception',
          onPress: () => {
            crashReporting.testCrash();
            Alert.alert('Success', 'Test exception sent to crash reporting service.');
          },
        },
        {
          text: 'Component Crash',
          onPress: () => {
            // This will trigger the Error Boundary
            throw new Error('Test component crash from CrashTestButton');
          },
        },
        {
          text: 'Async Error',
          onPress: async () => {
            try {
              // Simulate an async error
              await new Promise((_, reject) => {
                setTimeout(() => reject(new Error('Test async error')), 100);
              });
            } catch (error) {
              crashReporting.captureException(error as Error, {
                context: 'async_test_error',
                component: 'CrashTestButton',
              });
              Alert.alert('Success', 'Test async exception sent to crash reporting service.');
            }
          },
        },
      ]
    );
  };

  if (!__DEV__) {
    return null; // Don't show in production
  }

  return (
    <StyledButton
      variant={variant}
      onPress={handleTestCrash}
    >
      Test Crash Reporting
    </StyledButton>
  );
};

export default CrashTestButton; 