import React, { ReactNode } from 'react';
import { Text as RNText, TextProps as RNTextProps, StyleProp, TextStyle } from 'react-native';
import { styled } from 'nativewind';

import { useTheme } from '../../theme'; // Ensure this path is correct
import { colors as appColors } from '../../theme/colors'; // Import base colors for keys

const NativeWindText = styled(RNText);

interface StyledTextProps extends RNTextProps {
  children: ReactNode;
  variant?:
  | 'h1'
  | 'h2'
  | 'h3'
  | 'h4'
  | 'body1' // Standard body text
  | 'body2' // Slightly smaller or different weight body text
  | 'caption'
  | 'label'   // For form labels or similar
  | 'button'  // Text style for buttons if not handled by button component itself
  | 'subtle'; // For less important text
  color?: keyof typeof appColors | string; // Use keys from our actual colors.ts export or a custom string
  tw?: string; // For additional ad-hoc Tailwind classes
}

const StyledText: React.FC<StyledTextProps> = ({
  children,
  variant = 'body1',
  color,
  tw = '',
  style, // Allow passing custom style prop
  ...props
}) => {
  const theme = useTheme(); // This theme includes merged Paper + our appColors
  let finalTextColor: string;

  if (typeof color === 'string') {
    // Check if it's a key in our appColors first
    const colorValue = appColors[color as keyof typeof appColors];
    if (colorValue && typeof colorValue === 'string') {
      finalTextColor = colorValue;
    } else {
      // Assume it's a custom hex color string
      finalTextColor = color;
    }
  } else {
    // Default colors based on variant
    switch (variant) {
      case 'h1':
      case 'h2':
      case 'h3':
      case 'h4':
        finalTextColor = theme.colors.textPrimary;
        break;
      case 'caption':
      case 'subtle':
        finalTextColor = theme.colors.textSecondary;
        break;
      case 'label':
        finalTextColor = theme.colors.textSecondary;
        break;
      default: // body1, body2, button, etc.
        finalTextColor = theme.colors.textPrimary;
    }
  }

  // Define styles for variants using Tailwind classes primarily
  // These can be combined with specific TextStyle props if needed for things Tailwind doesn't cover well (e.g., specific font family if not global)
  let variantTwClasses = '';

  switch (variant) {
    case 'h1':
      variantTwClasses = 'text-4xl font-bold'; // Example: Adjust size as per your design system
      break;
    case 'h2':
      variantTwClasses = 'text-3xl font-bold';
      break;
    case 'h3':
      variantTwClasses = 'text-2xl font-semibold';
      break;
    case 'h4':
      variantTwClasses = 'text-xl font-semibold';
      break;
    case 'body1':
      variantTwClasses = 'text-base';
      break;
    case 'body2':
      variantTwClasses = 'text-sm';
      break;
    case 'caption':
      variantTwClasses = 'text-xs';
      break;
    case 'label':
      variantTwClasses = 'text-sm font-medium';
      break;
    case 'button':
      variantTwClasses = 'text-base font-medium text-center';
      break;
    case 'subtle':
      variantTwClasses = 'text-sm';
      break;
    default:
      variantTwClasses = 'text-base';
      break;
  }

  return (
    <NativeWindText
      {...props}
      className={`${variantTwClasses} ${tw}`.trim()}
      style={[{ color: finalTextColor }, style]} // Apply variant style, then custom color, then passed style
    >
      {children}
    </NativeWindText>
  );
};

export default StyledText; 