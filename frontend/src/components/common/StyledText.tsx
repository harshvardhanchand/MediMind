import React, { ReactNode, useMemo } from 'react';
import { Text as RNText, TextProps, StyleProp, TextStyle } from 'react-native';
import { styled } from 'nativewind';

import { useTheme } from '../../theme';
import { colors as appColors } from '../../theme/colors';

const NativeWindText = styled(RNText);

// Centralized variant mapping - single source of truth
const VARIANT_MAP = {
  h1: { tw: 'text-4xl font-bold', colorKey: 'textPrimary' as const, accessibilityRole: 'header' as const },
  h2: { tw: 'text-3xl font-bold', colorKey: 'textPrimary' as const, accessibilityRole: 'header' as const },
  h3: { tw: 'text-2xl font-semibold', colorKey: 'textPrimary' as const, accessibilityRole: 'header' as const },
  h4: { tw: 'text-xl font-semibold', colorKey: 'textPrimary' as const, accessibilityRole: 'header' as const },
  body1: { tw: 'text-base', colorKey: 'textPrimary' as const, accessibilityRole: 'text' as const },
  body2: { tw: 'text-sm', colorKey: 'textPrimary' as const, accessibilityRole: 'text' as const },
  label: { tw: 'text-sm font-medium', colorKey: 'textSecondary' as const, accessibilityRole: 'text' as const },
  caption: { tw: 'text-xs', colorKey: 'textSecondary' as const, accessibilityRole: 'text' as const },
  subtle: { tw: 'text-sm', colorKey: 'textSecondary' as const, accessibilityRole: 'text' as const },
  button: { tw: 'text-base font-medium text-center', colorKey: 'textPrimary' as const, accessibilityRole: 'text' as const },
} as const;

type VariantKey = keyof typeof VARIANT_MAP;
type ColorKey = keyof typeof appColors;

interface StyledTextProps extends TextProps {
  children: ReactNode;
  variant?: VariantKey;
  color?: ColorKey | (string & {});
  className?: string;
}

const StyledText: React.FC<StyledTextProps> = ({
  children,
  variant = 'body1',
  color,
  className = '',
  style,
  ...props
}) => {
  const theme = useTheme();

  // Memoized computed values for performance
  const computedStyles = useMemo(() => {
    const { tw: baseTw, colorKey, accessibilityRole } = VARIANT_MAP[variant];

    // Simplified color resolution
    const resolvedColor = color && appColors[color as ColorKey]
      ? appColors[color as ColorKey] as string
      : color && /^#[0-9A-Fa-f]{6}$/.test(color)
        ? color
        : theme.colors[colorKey];

    const combinedClassName = `${baseTw} ${className}`.trim();

    return {
      className: combinedClassName,
      accessibilityRole,
      style: [{ color: resolvedColor }, style] as StyleProp<TextStyle>,
    };
  }, [variant, color, className, theme.colors, style]);

  return (
    <NativeWindText
      {...props}
      className={computedStyles.className}
      style={computedStyles.style}
      accessibilityRole={computedStyles.accessibilityRole}
    >
      {children}
    </NativeWindText>
  );
};

export default StyledText; 