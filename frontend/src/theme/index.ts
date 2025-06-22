import { MD3LightTheme as DefaultTheme, useTheme as usePaperTheme } from 'react-native-paper';

import { colors as appColors, AppColors } from './colors';

// Augment the PaperTheme to include our custom colors for type safety with useTheme
declare global {
  namespace ReactNativePaper {
    interface ThemeColors extends AppColors {}
    interface Theme {
      colors: ThemeColors;
    }
  }
}

export const theme = {
  ...DefaultTheme,
  colors: {
    ...DefaultTheme.colors,
    primary: appColors.accentPrimary,
    onPrimary: appColors.textOnPrimaryColor,
    primaryContainer: appColors.legacyPrimaryLight,
    onPrimaryContainer: appColors.legacyPrimaryDark,
    
    secondary: appColors.accentPrimary,
    onSecondary: appColors.textOnPrimaryColor,
    secondaryContainer: appColors.legacySecondaryLight,
    onSecondaryContainer: appColors.legacySecondaryDark,
    
    tertiary: appColors.accentPrimary,
    onTertiary: appColors.textOnPrimaryColor,
    tertiaryContainer: appColors.legacyAccentLight,
    onTertiaryContainer: appColors.legacyAccentDark,

    error: appColors.error,
    onError: appColors.textOnDestructiveColor,
    errorContainer: '#FFDAD6',
    onErrorContainer: '#410002',

    background: appColors.backgroundPrimary,
    onBackground: appColors.textPrimary,
    
    surface: appColors.backgroundSecondary,
    onSurface: appColors.textPrimary,
    surfaceVariant: appColors.backgroundTertiary,
    onSurfaceVariant: appColors.textSecondary,

    outline: appColors.borderStrong,
    outlineVariant: appColors.borderSubtle,
    
    shadow: appColors.legacyBlack,
    scrim: appColors.legacyBlack,

    // Custom colors directly available under theme.colors
    ...appColors, // Spreading all our custom colors here for easy access
  },
  // You can also customize fonts, roundness, etc.
  // roundness: 4, // Default is 4
  // fonts: configureFonts({config: baseFont}), // If you want to set up custom fonts
};

// Custom hook to get the typed theme
export const useTheme = () => usePaperTheme<typeof theme>(); 