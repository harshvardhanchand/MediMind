import React, { useState } from 'react';
import { View, TextInput, TextInputProps, StyleProp, ViewStyle, TextStyle, Platform, TouchableOpacity } from 'react-native';
import { styled } from 'nativewind';
import Ionicons from 'react-native-vector-icons/Ionicons';

import { useTheme } from '../../theme';

import StyledText from './StyledText';

const StyledNativeInput = styled(TextInput);
const StyledView = styled(View);
const StyledIconTouchableOpacity = styled(TouchableOpacity);

interface StyledInputProps extends Omit<TextInputProps, 'style' | 'placeholderTextColor'> {
  label?: string;
  error?: string;
  variant?: 'default' | 'formListItem';
  tw?: string; // Tailwind for the outer container
  inputTw?: string; // Tailwind for the TextInput itself (use sparingly, prefer variants)
  inputStyle?: StyleProp<TextStyle>; // Custom style for the TextInput
  containerStyle?: StyleProp<ViewStyle>; // Custom style for the outer container
  leftIconName?: string;
  rightIconName?: string;
  iconSize?: number;
  onRightIconPress?: () => void;
  showBottomBorder?: boolean; // Specific to formListItem variant
}

const StyledInput: React.FC<StyledInputProps> = ({
  label,
  error,
  variant = 'default',
  tw = '',
  inputTw = '',
  inputStyle,
  containerStyle,
  leftIconName,
  rightIconName,
  iconSize = 20,
  onRightIconPress,
  showBottomBorder = true, // Default to true for formListItem, can be overridden
  ...restOfProps
}) => {
  const { colors } = useTheme();
  const [isFocused, setIsFocused] = useState(false);

  let containerOuterBaseTw = 'w-full';
  let inputWrapperBaseTw = 'flex-row items-center border'; // Base for wrapper
  let textInputBaseTw = 'py-3 px-4 text-base text-textPrimary flex-1 h-12 leading-5';
  let currentBorderColor = colors.accentPrimary; // Default to accent for focused state
  let inputBgTw = 'bg-backgroundTertiary';

  if (variant === 'default') {
    inputWrapperBaseTw += ' rounded-xl'; // More rounded for search bars
    if (error) {
      currentBorderColor = colors.accentDestructive;
      inputWrapperBaseTw += ' border-2'; // Keep border visible and thicker for error
    } else if (isFocused) {
      currentBorderColor = colors.accentPrimary;
      inputWrapperBaseTw += ' border-2'; // Make border active and thicker on focus
    } else {
      currentBorderColor = 'transparent'; // No visible border when not focused and no error
      // inputWrapperBaseTw += ' border-borderSubtle'; // Optionally, a very subtle border instead of transparent
    }
    inputWrapperBaseTw += ` ${inputBgTw}`;
  } else if (variant === 'formListItem') {
    containerOuterBaseTw = tw; // For formListItem, outer container takes full `tw` from props for its specific layout
    inputWrapperBaseTw = `flex-row items-center bg-transparent px-4 py-3.5 ${showBottomBorder ? 'border-b' : ''}`;
    textInputBaseTw = 'p-0 h-auto text-base text-textPrimary flex-1 bg-transparent leading-5';
    inputBgTw = 'bg-transparent'; // Input itself is transparent
    currentBorderColor = showBottomBorder ? colors.borderSubtle : 'transparent'; // Default border for form list item
    if (error && showBottomBorder) {
        currentBorderColor = colors.accentDestructive;
    } else if (isFocused && showBottomBorder) {
        currentBorderColor = colors.accentPrimary;
    }
    // For formListItem, border width comes from 'border-b' (1px) or is none.
  }
  
  const finalTextInputTw = `${textInputBaseTw} ${inputTw}`.trim();
  const finalContainerTw = variant === 'formListItem' ? containerOuterBaseTw : `${containerOuterBaseTw} ${tw}`.trim();
  const finalInputWrapperTw = `${inputWrapperBaseTw}`.trim();

  const combinedTextInputStyle: StyleProp<TextStyle> = [{}, inputStyle];

  return (
    <StyledView className={finalContainerTw} style={containerStyle}>
      {label && (
        <StyledText 
          variant="label" 
          color="textSecondary" 
          tw={variant === 'formListItem' ? 'mb-1' : 'mb-1.5'}
        >
          {label}
        </StyledText>
      )}
      <StyledView 
        className={finalInputWrapperTw}
        style={{ borderColor: currentBorderColor }} 
      >
        {leftIconName && (
          <Ionicons 
            name={leftIconName} 
            size={iconSize} 
            color={isFocused ? colors.accentPrimary : colors.textMuted} 
            className={`pr-2 ${variant === 'formListItem' ? 'pl-0' : 'pl-3'}`}
          />
        )}
        <StyledNativeInput
          {...restOfProps}
          style={combinedTextInputStyle}
          className={finalTextInputTw}
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
        />
        {rightIconName && (
          <StyledIconTouchableOpacity onPress={onRightIconPress} tw={`pr-2 ${variant === 'formListItem' ? 'pr-0' : 'pl-2'}`}>
            <Ionicons 
              name={rightIconName} 
              size={iconSize} 
              color={isFocused ? colors.accentPrimary : colors.textMuted} 
            />
          </StyledIconTouchableOpacity>
        )}
      </StyledView>
      {error && (
        <StyledText variant="caption" style={{ color: colors.accentDestructive }} tw="mt-1">
          {error}
        </StyledText>
      )}
    </StyledView>
  );
};

export default StyledInput; 