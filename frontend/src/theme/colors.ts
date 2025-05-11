// Modern medical app color palette inspired by professional healthcare applications
export const colors = {
  // Primary brand colors
  primary: '#0EA5E9', // Vibrant medical blue (updated from iOS blue to a softer blue)
  primaryDark: '#0284C7', // Darker shade for hover/press states
  primaryLight: '#D3E4FD', // Light shade for backgrounds or highlights

  // Secondary colors
  secondary: '#F1F0FB', // Light background for secondary elements
  secondaryDark: '#E2E0F5', // Darker shade for hover/press states
  secondaryLight: '#F8F7FE', // Lightest shade for subtle highlights

  // Accent colors
  accent: '#4ADE80', // Refreshing green for positive actions/success
  accentDark: '#22C55E', // Darker shade for hover/press states
  accentLight: '#F2FCE2', // Light shade for backgrounds

  // Additional medical palette
  medical: {
    blue: '#0EA5E9', // Main medical blue
    lightblue: '#D3E4FD', // Light blue background
    green: '#4ADE80', // Healthy green
    lightgreen: '#F2FCE2', // Light green background
    purple: '#9b87f5', // Medical purple (for medication related elements)
    lightpurple: '#E5DEFF', // Light purple background
    red: '#ea384c', // Warning/alert red
    lightred: '#FEE2E2', // Light red background
    gray: '#403E43', // Medical dark gray
    lightgray: '#F1F0FB', // Medical light gray background
  },

  // Neutrals - a comprehensive set of grays
  black: '#121212', // True black for high contrast text or elements
  gray900: '#1F2937', // Very dark gray, near black
  gray800: '#374151', // Dark gray
  gray700: '#4B5563', // Medium-dark gray
  gray600: '#6B7280', // Standard gray for secondary text
  gray500: '#9CA3AF', // Medium gray for borders, icons
  gray400: '#D1D5DB', // Light gray
  gray300: '#E5E7EB', // Very light gray, for dividers
  gray200: '#F3F4F6', // Background grays
  gray100: '#F9FAFB', // Lightest gray, often for page backgrounds
  gray50:  '#F9FAFB', // Almost white (updated to be closer to white for cleaner look)
  white: '#FFFFFF', // True white

  // Semantic colors
  success: '#4ADE80', // Green for success messages, confirmations
  warning: '#F59E0B', // Orange for warnings, attention needed
  error: '#ea384c', // Red for errors, critical alerts
  info: '#3B82F6', // Blue for informational messages

  // Backgrounds
  backgroundScreen: '#F9FAFB', // Default screen background (updated to lighter color)
  backgroundCard: '#FFFFFF', // Default card/modal background (white)
  backgroundInput: '#F9FAFB', // Input field background
  backgroundSurface: '#FFFFFF', // Surface background

  // Text colors
  textPrimary: '#1F2937', // For primary text, headings (updated to more modern gray)
  textSecondary: '#6B7280', // For secondary text, descriptions
  textDisabled: '#9CA3AF', // For disabled text
  textPlaceholder: '#9CA3AF', // For input placeholders

  // Border colors
  border: '#E5E7EB', // Default border color
  borderFocus: '#0EA5E9', // Border color when element is focused
};

export type AppColors = typeof colors; 