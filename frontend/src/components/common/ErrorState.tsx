import React from 'react';
import { View } from 'react-native';
import { styled } from 'nativewind';
import Ionicons from 'react-native-vector-icons/Ionicons';

import StyledText from './StyledText';
import StyledButton from './StyledButton';
import { useTheme } from '../../theme';

const StyledView = styled(View);

interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
  retryLabel?: string;
  showRetry?: boolean;
  icon?: string;
}

const ErrorState: React.FC<ErrorStateProps> = ({
  title = 'Something went wrong',
  message = 'We encountered an error while loading your data. Please try again.',
  onRetry,
  retryLabel = 'Try Again',
  showRetry = true,
  icon = 'alert-circle-outline'
}) => {
  const { colors } = useTheme();

  return (
    <StyledView className="flex-1 justify-center items-center px-8 py-12">
      <Ionicons 
        name={icon} 
        size={64} 
        color={colors.error} 
        style={{ marginBottom: 16 }}
      />
      
      <StyledText 
        variant="h3" 
        tw="text-center mb-2"
        style={{ color: colors.textPrimary }}
      >
        {title}
      </StyledText>
      
      <StyledText 
        variant="body1" 
        tw="text-center mb-6 leading-6"
        style={{ color: colors.textSecondary }}
      >
        {message}
      </StyledText>
      
      {showRetry && onRetry && (
        <StyledButton
          variant="filledPrimary"
          onPress={onRetry}
        >
          {retryLabel}
        </StyledButton>
      )}
    </StyledView>
  );
};

export default ErrorState; 