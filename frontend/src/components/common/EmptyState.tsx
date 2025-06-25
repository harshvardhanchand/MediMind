import React from 'react';
import { View } from 'react-native';
import { styled } from 'nativewind';
import { Ionicons } from '@expo/vector-icons';

import StyledText from './StyledText';
import StyledButton from './StyledButton';
import { useTheme } from '../../theme';

const StyledView = styled(View);

interface EmptyStateProps {
  icon?: string;
  title: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
  variant?: 'default' | 'error' | 'loading';
}

const EmptyState: React.FC<EmptyStateProps> = ({
  icon = 'document-outline',
  title,
  description,
  actionLabel,
  onAction,
  variant = 'default'
}) => {
  const { colors } = useTheme();

  const getIconColor = () => {
    switch (variant) {
      case 'error': return colors.error;
      case 'loading': return colors.textSecondary;
      default: return colors.textSecondary;
    }
  };

  return (
    <StyledView className="flex-1 justify-center items-center px-8 py-12">
      <Ionicons
        name={icon as any}
        size={64}
        color={getIconColor()}
        style={{ marginBottom: 16 }}
      />

      <StyledText
        variant="h3"
        className="text-center mb-2"
        style={{ color: colors.textPrimary }}
      >
        {title}
      </StyledText>

      {description && (
        <StyledText
          variant="body1"
          className="text-center mb-6 leading-6"
          style={{ color: colors.textSecondary }}
        >
          {description}
        </StyledText>
      )}

      {actionLabel && onAction && (
        <StyledButton
          variant="filledPrimary"
          onPress={onAction}
        >
          {actionLabel}
        </StyledButton>
      )}
    </StyledView>
  );
};

export default EmptyState; 