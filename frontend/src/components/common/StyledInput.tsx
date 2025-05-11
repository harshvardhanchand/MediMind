import React from 'react';
import { TextInput as PaperTextInput, TextInputProps as PaperTextInputProps } from 'react-native-paper';
import { styled } from 'nativewind';
import { useTheme } from '../../theme';
import { ViewStyle, TextStyle } from 'react-native';

// Styled PaperTextInput that can accept className for margin, etc.
const NativeWindPaperTextInput = styled(PaperTextInput);

interface StyledInputProps extends Omit<PaperTextInputProps, 'theme'> {
  tw?: string; // For Tailwind classes like margin
  variant?: 'outlined' | 'filled' | 'flat'; // Custom variants we support
}

const StyledInput: React.FC<StyledInputProps> = ({
  variant = 'outlined', // Default variant
  mode = 'outlined', // Default Paper input mode
  tw = '',
  style,
  left,
  right,
  label,
  ...props
}) => {
  const theme = useTheme();

  // Map our custom variants to PaperTextInput modes
  let paperMode = mode;
  if (variant === 'filled') {
    paperMode = 'flat';
  } else if (variant === 'flat') {
    paperMode = 'flat';
  }

  // Base styles for all inputs
  const baseStyle: ViewStyle & TextStyle = {
    backgroundColor: theme.colors.backgroundInput,
    fontSize: 15,
    borderRadius: 8,
  };

  // Variant-specific styles
  const variantStyle: ViewStyle & TextStyle = {};
  
  if (variant === 'outlined') {
    variantStyle.borderColor = theme.colors.border;
  } else if (variant === 'filled') {
    variantStyle.backgroundColor = theme.colors.gray50;
  } else if (variant === 'flat') {
    variantStyle.backgroundColor = 'transparent';
    variantStyle.borderBottomWidth = 1;
    variantStyle.borderRadius = 0;
    variantStyle.borderBottomColor = theme.colors.border;
  }

  // Custom outline styles
  const outlineStyle: ViewStyle = {
    borderRadius: 8,
    borderWidth: 1,
  };

  // We cannot easily modify the left prop directly, 
  // as it's a React element and doesn't have a direct style property we can modify.
  // Instead, we rely on Paper's internal handling for icon spacing.

  return (
    <NativeWindPaperTextInput
      {...props}
      mode={paperMode}
      theme={{
        ...theme,
        colors: {
          ...theme.colors,
          primary: theme.colors.primary,
          onSurfaceVariant: theme.colors.textSecondary, // Label color
          error: theme.colors.error,
        }
      }}
      label={label}
      left={left}
      right={right}
      style={[baseStyle, variantStyle, style]}
      outlineStyle={variant === 'outlined' ? outlineStyle : undefined}
      className={tw}
      placeholderTextColor={theme.colors.textPlaceholder}
      activeOutlineColor={theme.colors.primary}
      outlineColor={theme.colors.border}
      selectionColor={`${theme.colors.primary}80`} // 50% opacity version of primary
      // Modern inputs often maintain case as typed
      autoCapitalize="none"
      // Adding a slight padding for better text visibility
      contentStyle={{ paddingLeft: 4 }}
    />
  );
};

export default StyledInput; 