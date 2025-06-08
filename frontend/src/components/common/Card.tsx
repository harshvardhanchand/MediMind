import React, { ReactNode } from 'react';
import { View, TouchableOpacity, StyleProp, ViewStyle } from 'react-native';
import { styled } from 'nativewind';

import { useTheme } from '../../theme';

import StyledText from './StyledText';

const StyledView = styled(View);
const StyledTouchableOpacity = styled(TouchableOpacity);

interface CardProps {
  children: ReactNode;
  title?: string;
  tw?: string;
  style?: StyleProp<ViewStyle>;
  contentTw?: string; // Tailwind classes for the inner content view
  noPadding?: boolean;
  onPress?: () => void;
  /**
   * Adds a subtle shadow, similar to some Apple Health summary cards.
   * Defaults to false for a flatter look on most cards.
   */
  withShadow?: boolean; 
}

const Card: React.FC<CardProps> = ({
  children = null,
  title,
  tw = '',
  style,
  contentTw = '',
  noPadding = false,
  onPress,
  withShadow = false,
}) => {
  const { colors } = useTheme();

  let cardBaseTw = 'bg-white rounded-xl'; // Use standard color instead of custom
  if (!noPadding) {
    cardBaseTw += ' p-4'; // Default internal padding
  }

  if (withShadow) {
    // A very subtle shadow, try to emulate iOS card shadows if desired
    // Tailwind's default shadows might be too strong or not configured for native properly.
    // For native, shadow props are often applied via style prop directly.
    // This is a conceptual Tailwind shadow, might need platform-specific shadow props in `style`.
    cardBaseTw += ' shadow-md'; // Or a custom shadow like shadow-card
  }

  const content = (
    <StyledView className={`flex-1 ${contentTw || ''}`.trim()}>
      {title ? (
        <StyledText variant="h3" tw="mb-3 font-semibold text-gray-900">
          {title}
        </StyledText>
      ) : null}
      {children}
    </StyledView>
  );

  if (onPress) {
    return (
      <StyledTouchableOpacity
        onPress={onPress}
        className={`${cardBaseTw} ${tw || ''}`.trim()}
        style={style}
        activeOpacity={0.8}
      >
        {content}
      </StyledTouchableOpacity>
    );
  }

  return (
    <StyledView 
      className={`${cardBaseTw} ${tw || ''}`.trim()}
      style={style}
    >
      {content}
    </StyledView>
  );
};

export default Card; 