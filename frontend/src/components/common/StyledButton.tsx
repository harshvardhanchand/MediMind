import React, { ReactNode } from 'react';
import { TouchableOpacity, ActivityIndicator, StyleProp, ViewStyle, TextStyle } from 'react-native';
import { styled } from 'nativewind';
import { Ionicons } from '@expo/vector-icons';

import { useTheme } from '../../theme';
import StyledText from './StyledText';

const StyledTouchableOpacity = styled(TouchableOpacity);

// Type-safe icon names
type IoniconName = keyof typeof Ionicons.glyphMap;


interface StyledButtonProps {
  children: ReactNode;
  onPress?: () => void;
  variant?: 'filledPrimary' | 'filledSecondary' | 'textPrimary' | 'textDestructive';
  disabled?: boolean;
  loading?: boolean;
  className?: string; // Renamed from 'tw' for consistency
  style?: StyleProp<ViewStyle>;
  textStyle?: StyleProp<TextStyle>;
  // Type-safe icon name props
  iconNameLeft?: IoniconName;
  iconNameRight?: IoniconName;
  iconSize?: number;
  // Custom ReactNode icon props for advanced use cases
  iconLeft?: ReactNode;
  iconRight?: ReactNode;
}

const StyledButton: React.FC<StyledButtonProps> = ({
  children,
  onPress,
  variant = 'filledPrimary',
  disabled = false,
  loading = false,
  className = '',
  style,
  textStyle,
  iconNameLeft,
  iconNameRight,
  iconSize = 18,
  iconLeft,
  iconRight,
}) => {
  const { colors } = useTheme();

  // Centralized variant mapping
  const VARIANT_MAP = {
    filledPrimary: {
      containerTw: 'bg-accent-primary py-3 px-4',
      textColor: colors.textOnPrimaryColor,
      iconColor: colors.textOnPrimaryColor,
    },
    filledSecondary: {
      containerTw: 'bg-background-tertiary py-3 px-4',
      textColor: colors.accentPrimary,
      iconColor: colors.accentPrimary,
    },
    textPrimary: {
      containerTw: 'bg-transparent py-2 px-3',
      textColor: colors.accentPrimary,
      iconColor: colors.accentPrimary,
    },
    textDestructive: {
      containerTw: 'bg-transparent py-2 px-3',
      textColor: colors.accentDestructive,
      iconColor: colors.accentDestructive,
    },
  } as const;

  const { containerTw, textColor, iconColor } = VARIANT_MAP[variant];
  const opacityTw = (disabled || loading) ? ' opacity-60' : '';
  const baseTw = 'flex-row items-center justify-center rounded-lg';

  const renderIcon = (name?: IoniconName, node?: ReactNode, side: 'left' | 'right' = 'left') => {
    if (node) return node; // Prioritize custom ReactNode icon
    if (!name) return null;

    // Use inline style for margins since className doesn't work on Ionicons
    const marginStyle = {
      marginRight: side === 'left' && children ? 8 : 0,
      marginLeft: side === 'right' && children ? 8 : 0,
    };

    return (
      <Ionicons
        name={name}
        size={iconSize}
        color={iconColor}
        style={marginStyle}
      />
    );
  };

  return (
    <StyledTouchableOpacity
      onPress={onPress}
      disabled={disabled || loading}
      className={`${baseTw} ${containerTw}${opacityTw} ${className}`.trim()}
      style={style}
      activeOpacity={0.7}
      // Accessibility improvements
      accessibilityRole="button"
      accessibilityState={{ disabled: disabled || loading }}
    >
      {loading ? (
        <ActivityIndicator color={iconColor} size="small" />
      ) : (
        <>
          {renderIcon(iconNameLeft, iconLeft, 'left')}
          <StyledText
            className="font-semibold text-base text-center"
            style={[{ color: textColor }, textStyle]}
          >
            {children}
          </StyledText>
          {renderIcon(iconNameRight, iconRight, 'right')}
        </>
      )}
    </StyledTouchableOpacity>
  );
};

export default StyledButton; 