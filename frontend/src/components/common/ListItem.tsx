import React, { ReactNode } from 'react';
import { View, TouchableOpacity, StyleProp, ViewStyle, TextStyle } from 'react-native';
import { styled } from 'nativewind';
import { Ionicons } from '@expo/vector-icons';

import { useTheme } from '../../theme';

import StyledText from './StyledText';

const StyledView = styled(View);
const StyledTouchableOpacity = styled(TouchableOpacity);

interface ListItemProps {
  label: string;
  labelStyle?: StyleProp<TextStyle>;
  subtitle?: string;
  subtitleStyle?: StyleProp<TextStyle>;
  value?: string | ReactNode; // Can be simple text or a custom component
  valueStyle?: StyleProp<TextStyle>;
  onPress?: () => void;
  iconLeft?: string; // Ionicon name
  iconLeftColor?: string;
  iconLeftSize?: number;
  iconRight?: string; // Ionicon name for chevron or other indicators
  iconRightColor?: string;
  iconRightSize?: number;
  className?: string; // Tailwind classes for the main container
  style?: StyleProp<ViewStyle>;
  showBottomBorder?: boolean;
  children?: ReactNode; // Alternative to `value` for more complex right-side content
}

const ListItem: React.FC<ListItemProps> = ({
  label,
  labelStyle,
  subtitle,
  subtitleStyle,
  value,
  valueStyle,
  onPress,
  iconLeft,
  iconLeftColor,
  iconLeftSize = 22,
  iconRight = 'chevron-forward-outline', // Default to chevron if onPress is present
  iconRightColor,
  iconRightSize = 20,
  className = '',
  style,
  showBottomBorder = false,
  children,
}) => {
  const { colors } = useTheme();

  const ContainerComponent = onPress ? StyledTouchableOpacity : StyledView;

  let containerBaseTw = 'flex-row items-center py-3.5'; // py-3.5 for ~14dp vertical padding
  if (showBottomBorder) {
    containerBaseTw += ' border-b border-borderSubtle';
  }

  const finalIconLeftColor = iconLeftColor || colors.textSecondary;
  const finalIconRightColor = iconRightColor || colors.textMuted; // Chevron is usually muted

  return (
    <ContainerComponent
      onPress={onPress}
      className={`${containerBaseTw} ${className}`.trim()}
      style={style}
      activeOpacity={onPress ? 0.6 : 1}
    >
      {iconLeft && (
        <Ionicons
          name={iconLeft as any}
          size={iconLeftSize}
          color={finalIconLeftColor}
          className="mr-5"
        />
      )}
      <StyledView className="flex-1">
        <StyledText variant="body1" color="textPrimary" style={labelStyle} className="font-medium">
          {label}
        </StyledText>
        {subtitle && (
          <StyledText variant="caption" color="textSecondary" style={subtitleStyle} className="mt-0.5">
            {subtitle}
          </StyledText>
        )}
      </StyledView>
      {children ? (
        children // Render custom children for the right side if provided
      ) : value !== undefined ? (
        typeof value === 'string' ? (
          <StyledText variant="body1" color="textSecondary" style={valueStyle} className="ml-2">
            {value}
          </StyledText>
        ) : (
          <StyledView className="ml-2">
            {value}
          </StyledView>
        )
      ) : null}
      {onPress && iconRight && (
        <Ionicons
          name={iconRight as any}
          size={iconRightSize}
          color={finalIconRightColor}
          className="ml-2"
        />
      )}
    </ContainerComponent>
  );
};

export default ListItem; 