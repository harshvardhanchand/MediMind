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
    primary: appColors.primary,
    onPrimary: appColors.white, // Text color on primary background
    primaryContainer: appColors.primaryLight,
    onPrimaryContainer: appColors.primaryDark,
    
    secondary: appColors.accent, // Using accent as secondary for Paper
    onSecondary: appColors.white,
    secondaryContainer: appColors.accentLight,
    onSecondaryContainer: appColors.accentDark,
    
    tertiary: appColors.accent, // Or another color if you have a specific tertiary
    onTertiary: appColors.white,
    tertiaryContainer: appColors.accentLight,
    onTertiaryContainer: appColors.accentDark,

    error: appColors.error,
    onError: appColors.white,
    errorContainer: '#FFDAD6', // A light red for error backgrounds
    onErrorContainer: '#410002', // Dark red text on errorContainer

    background: appColors.backgroundScreen, // Screen background
    onBackground: appColors.textPrimary,    // Text on screen background
    
    surface: appColors.backgroundCard,      // Card/surface background
    onSurface: appColors.textPrimary,       // Text on card/surface
    surfaceVariant: appColors.gray50,       // Slightly different surface variant
    onSurfaceVariant: appColors.textSecondary, // Text on surfaceVariant

    outline: appColors.gray300,
    outlineVariant: appColors.gray200,
    
    shadow: appColors.black,
    scrim: appColors.black, // For modal backdrop, etc.

    // Custom colors directly available under theme.colors
    ...appColors, // Spreading all our custom colors here for easy access
  },
  // You can also customize fonts, roundness, etc.
  // roundness: 4, // Default is 4
  // fonts: configureFonts({config: baseFont}), // If you want to set up custom fonts
};

// Custom hook to get the typed theme
export const useTheme = () => usePaperTheme<typeof theme>(); 