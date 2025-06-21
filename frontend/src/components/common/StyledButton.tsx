import React, { ReactNode } from 'react';
import { TouchableOpacity, View, ViewStyle, TextStyle, ActivityIndicator, StyleProp } from 'react-native';
import { styled } from 'nativewind';
import Ionicons from 'react-native-vector-icons/Ionicons';

import { useTheme } from '../../theme';

import StyledText from './StyledText'; // Assuming StyledText is in the same directory

const StyledTouchableOpacity = styled(TouchableOpacity);
const StyledView = styled(View); // For icon container

interface StyledButtonProps {
  children: ReactNode; // Button label
  onPress?: () => void;
  variant?: 'filledPrimary' | 'filledSecondary' | 'textPrimary' | 'textDestructive';
  disabled?: boolean;
  loading?: boolean;
  tw?: string; // For additional Tailwind container classes
  style?: StyleProp<ViewStyle>; // Custom container style override
  textStyle?: StyleProp<TextStyle>; // Custom text style override
  // New props for simple icon name handling
  iconNameLeft?: string;
  iconNameRight?: string;
  iconSize?: number;
  // Keep existing ReactNode icon props for full customization if needed, but prioritize iconName*
  iconLeft?: ReactNode; 
  iconRight?: ReactNode;
}

const StyledButton: React.FC<StyledButtonProps> = ({
  children,
  onPress,
  variant = 'filledPrimary',
  disabled = false,
  loading = false,
  tw = '',
  style,
  textStyle,
  iconNameLeft,
  iconNameRight,
  iconSize = 18, // Default icon size
  iconLeft,      // Custom ReactNode icon
  iconRight,     // Custom ReactNode icon
}) => {
  const { colors } = useTheme();

  let containerBaseTw = 'flex-row items-center justify-center py-3 px-4 rounded-lg'; // Adjusted padding slightly
  const textBaseTw = 'font-semibold text-base text-center';
  let specificContainerTw = '';
  let determinedIconColor = colors.textOnPrimaryColor; // Default for filledPrimary
  let determinedTextColor = colors.textOnPrimaryColor;

  if (disabled || loading) {
    containerBaseTw += ' opacity-60'; // Slightly more opacity for disabled state
  }

  switch (variant) {
    case 'filledSecondary':
      specificContainerTw = 'bg-backgroundTertiary';
      determinedTextColor = colors.accentPrimary;
      determinedIconColor = colors.accentPrimary;
      break;
    case 'textPrimary':
      containerBaseTw = 'py-2 px-3';
      specificContainerTw = 'bg-transparent';
      determinedTextColor = colors.accentPrimary;
      determinedIconColor = colors.accentPrimary;
      break;
    case 'textDestructive':
      containerBaseTw = 'py-2 px-3';
      specificContainerTw = 'bg-transparent';
      determinedTextColor = colors.accentDestructive;
      determinedIconColor = colors.accentDestructive;
      break;
    case 'filledPrimary': // Default
    default:
      specificContainerTw = `bg-accentPrimary`;
      determinedTextColor = colors.textOnPrimaryColor;
      determinedIconColor = colors.textOnPrimaryColor;
      break;
  }

  const renderIcon = (name?: string, node?: ReactNode, side: 'left' | 'right' = 'left') => {
    if (node) return node; // Prioritize custom ReactNode icon
    if (!name) return null;
    const marginClass = side === 'left' && children ? 'mr-2' : (side === 'right' && children ? 'ml-2' : '');
          return <Ionicons name={name as any} size={iconSize} color={determinedIconColor} className={marginClass} />;
  };

  return (
    <StyledTouchableOpacity
      onPress={onPress}
      disabled={disabled || loading}
      className={`${containerBaseTw} ${specificContainerTw} ${tw}`.trim()}
      style={style}
      activeOpacity={0.7}
    >
      {loading ? (
        <ActivityIndicator color={determinedIconColor} size="small" />
      ) : (
        <>
          {renderIcon(iconNameLeft, iconLeft, 'left')}
          <StyledText 
            tw={`${textBaseTw}`.trim()} 
            style={[{ color: determinedTextColor }, textStyle]} // Apply color directly via style to ensure override
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