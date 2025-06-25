import React, { useState, useMemo } from 'react';
import { View, TextInput, TextInputProps, StyleProp, ViewStyle, TextStyle, TouchableOpacity } from 'react-native';
import { styled } from 'nativewind';
import { Ionicons } from '@expo/vector-icons';

import { useTheme } from '../../theme';
import StyledText from './StyledText';

const StyledNativeInput = styled(TextInput);
const StyledView = styled(View);
const StyledTouchableOpacity = styled(TouchableOpacity);

// Type-safe icon names
type IoniconName = keyof typeof Ionicons.glyphMap;

interface StyledInputProps extends Omit<TextInputProps, 'style' | 'placeholderTextColor'> {
  label?: string;
  error?: string;
  variant?: 'default' | 'formListItem';
  className?: string; // Renamed from 'tw' for consistency
  inputClassName?: string; // Renamed from 'inputTw'
  inputStyle?: StyleProp<TextStyle>;
  containerStyle?: StyleProp<ViewStyle>;
  leftIconName?: IoniconName;
  rightIconName?: IoniconName;
  iconSize?: number;
  onRightIconPress?: () => void;
  showBottomBorder?: boolean;
}

const StyledInput: React.FC<StyledInputProps> = ({
  label,
  error,
  variant = 'default',
  className = '',
  inputClassName = '',
  inputStyle,
  containerStyle,
  leftIconName,
  rightIconName,
  iconSize = 20,
  onRightIconPress,
  showBottomBorder = true,
  ...restOfProps
}) => {
  const { colors } = useTheme();
  const [isFocused, setIsFocused] = useState(false);

  // Centralized variant mapping
  const VARIANTS = {
    default: {
      containerTw: 'w-full',
      wrapperTw: (hasError: boolean, focused: boolean) => [
        'flex-row items-center rounded-xl bg-background-tertiary',
        hasError ? 'border-2' : focused ? 'border-2' : 'border-0',
      ].join(' '),
      inputTw: 'py-3 px-4 text-base flex-1 h-12 leading-5',
      borderColor: (hasError: boolean, focused: boolean) =>
        hasError ? colors.accentDestructive :
          focused ? colors.accentPrimary :
            'transparent',
    },
    formListItem: {
      containerTw: className, // For formListItem, use passed className directly
      wrapperTw: (hasError: boolean, focused: boolean, showBottom: boolean) => [
        'flex-row items-center px-4 py-4 bg-transparent',
        showBottom ? 'border-b' : '',
      ].join(' '),
      inputTw: 'p-0 h-auto flex-1 text-base bg-transparent leading-5',
      borderColor: (hasError: boolean, focused: boolean, showBottom: boolean) =>
        !showBottom ? 'transparent' :
          hasError ? colors.accentDestructive :
            focused ? colors.accentPrimary :
              colors.borderSubtle,
    },
  } as const;

  const variantConfig = VARIANTS[variant];

  // Memoized computed styles for performance
  const computedStyles = useMemo(() => {
    const hasError = !!error;

    let wrapperClass: string;
    let borderColor: string;
    let containerClass: string;

    if (variant === 'default') {
      const config = variantConfig as typeof VARIANTS.default;
      wrapperClass = config.wrapperTw(hasError, isFocused);
      borderColor = config.borderColor(hasError, isFocused);
      containerClass = `${config.containerTw} ${className}`.trim();
    } else {
      const config = variantConfig as typeof VARIANTS.formListItem;
      wrapperClass = config.wrapperTw(hasError, isFocused, showBottomBorder);
      borderColor = config.borderColor(hasError, isFocused, showBottomBorder);
      containerClass = config.containerTw;
    }

    const inputClass = `${variantConfig.inputTw} ${inputClassName}`.trim();

    return {
      containerClass,
      wrapperClass,
      inputClass,
      wrapperStyle: { borderColor },
      inputStyle: [inputStyle],
    };
  }, [variant, error, isFocused, showBottomBorder, className, inputClassName, inputStyle, colors, variantConfig]);

  const renderIcon = (iconName?: IoniconName, side: 'left' | 'right' = 'left') => {
    if (!iconName) return null;

    const iconStyle = {
      marginRight: side === 'left' ? 8 : 0,
      marginLeft: side === 'right' ? 8 : variant === 'formListItem' ? 0 : 12,
    };

    const IconWrapper = side === 'right' && onRightIconPress ? StyledTouchableOpacity : StyledView;
    const wrapperProps = side === 'right' && onRightIconPress
      ? { onPress: onRightIconPress, className: "p-1", accessibilityRole: "button" as const }
      : { className: "" };

    return (
      <IconWrapper {...wrapperProps}>
        <Ionicons
          name={iconName}
          size={iconSize}
          color={isFocused ? colors.accentPrimary : colors.textMuted}
          style={iconStyle}
        />
      </IconWrapper>
    );
  };

  return (
    <StyledView className={computedStyles.containerClass} style={containerStyle}>
      {label && (
        <StyledText
          variant="label"
          color="textSecondary"
          className={variant === 'formListItem' ? 'mb-1' : 'mb-1.5'}
        >
          {label}
        </StyledText>
      )}
      <StyledView
        className={computedStyles.wrapperClass}
        style={computedStyles.wrapperStyle}
      >
        {renderIcon(leftIconName, 'left')}
        <StyledNativeInput
          {...restOfProps}
          style={computedStyles.inputStyle}
          className={computedStyles.inputClass}
          placeholderTextColor={colors.textMuted}
          onFocus={(e) => {
            setIsFocused(true);
            restOfProps.onFocus?.(e);
          }}
          onBlur={(e) => {
            setIsFocused(false);
            restOfProps.onBlur?.(e);
          }}
          selectionColor={colors.accentPrimary}
          // Accessibility improvements
          accessibilityHint="Input field"
        />
        {renderIcon(rightIconName, 'right')}
      </StyledView>
      {error && (
        <StyledText
          variant="caption"
          style={{ color: colors.accentDestructive }}
          className="mt-1"
        >
          {error}
        </StyledText>
      )}
    </StyledView>
  );
};

export default StyledInput; 