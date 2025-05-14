// Apple Health Inspired Color Palette
// References: iOS Human Interface Guidelines, common Health app visual language.

export const colors = {
  // --- Core Palette (Apple Health Inspired) ---
  // Backgrounds
  backgroundPrimary: '#F9F9F9',    // Standard screen background (very light gray)
  backgroundSecondary: '#FFFFFF',  // Card and primary content areas (pure white)
  backgroundTertiary: '#EFEFF4',   // Grouped table view style backgrounds, subtle divisions

  // Text
  textPrimary: '#000000',          // Primary text (black for high contrast)
  textSecondary: '#8A8A8E',        // Secondary text (iOS secondary label color)
  textMuted: '#AEAEB2',            // Muted text for less emphasis, placeholders (iOS tertiary label color)
  textOnPrimaryColor: '#FFFFFF',   // Text that appears on primary accent colored backgrounds
  textOnDestructiveColor: '#FFFFFF',// Text that appears on destructive accent colored backgrounds

  // Accents & Interactive Elements
  accentPrimary: '#007AFF',        // Standard Apple blue for interactive elements
  accentPrimaryPressed: '#0056B3', // Darker shade for pressed state of accentPrimary
  accentDestructive: '#FF3B30',    // Standard Apple red for errors, destructive actions
  accentDestructivePressed: '#D32F2F', // Darker shade for pressed state of accentDestructive

  // Borders & Dividers
  borderSubtle: '#E5E5EA',        // Light gray for subtle borders, list separators (iOS separator color)
  borderStrong: '#D1D1D6',          // More prominent borders if needed

  // --- Categorical & Data Visualization Colors (Inspired by Apple Health graph colors) ---
  // These can be expanded. Names are generic for flexibility.
  dataColor1: '#5AC8FA', // Light Blue
  dataColor2: '#34C759', // Green
  dataColor3: '#FF9500', // Orange
  dataColor4: '#FF2D55', // Pink
  dataColor5: '#AF52DE', // Purple (similar to iOS purple)
  dataColor6: '#FF6B2D', // A reddish-orange or coral
  dataColor7: '#00C7BE', // Teal / Aqua
  dataColor8: '#5856D6', // Indigo

  // --- Semantic UI Colors (Derived from core palette for consistency) ---
  success: '#34C759',             // Green (same as dataColor2 for consistency)
  warning: '#FF9500',             // Orange (same as dataColor3)
  error: '#FF3B30',               // Red (same as accentDestructive)
  info: '#007AFF',                // Blue (same as accentPrimary)

  // --- Component-Specific Overrides or Unique Colors (Legacy or Specific Needs) ---
  // These are from your old palette. Review if they are still needed or can be mapped to the new system.
  // If kept, consider renaming for clarity if their semantic meaning has changed.
  legacyPrimary: '#0EA5E9',
  legacyPrimaryDark: '#0284C7',
  legacyPrimaryLight: '#D3E4FD',

  legacySecondary: '#F1F0FB',
  legacySecondaryDark: '#E2E0F5',
  legacySecondaryLight: '#F8F7FE',

  legacyAccent: '#4ADE80',
  legacyAccentDark: '#22C55E',
  legacyAccentLight: '#F2FCE2',

  legacyMedical: {
    blue: '#0EA5E9',
    lightblue: '#D3E4FD',
    green: '#4ADE80',
    lightgreen: '#F2FCE2',
    purple: '#9b87f5',
    lightpurple: '#E5DEFF',
    red: '#ea384c',
    lightred: '#FEE2E2',
    gray: '#403E43',
    lightgray: '#F1F0FB',
  },

  // Neutrals (mostly covered by new text/background/border definitions, review for redundancy)
  // Some specific grays might still be useful if the semantic ones aren't enough.
  legacyBlack: '#121212',
  legacyGray900: '#1F2937', 
  legacyGray800: '#374151',
  legacyGray700: '#4B5563',
  legacyGray600: '#6B7280',
  legacyGray500: '#9CA3AF',
  legacyGray400: '#D1D5DB',
  legacyGray300: '#E5E7EB',
  legacyGray200: '#F3F4F6',

  // Old Semantic (mostly covered by new semantic colors using Apple accents)
  legacySuccess: '#4ADE80',
  legacyWarning: '#F59E0B',
  legacyError: '#ea384c',
  legacyInfo: '#3B82F6',

  // Old Backgrounds (mostly covered by new backgroundPrimary/Secondary/Tertiary)
  legacyBackgroundInput: '#F9FAFB',

  // Old Text (mostly covered by new textPrimary/Secondary/Muted)
  legacyTextPrimary: '#1F2937',
  legacyTextSecondary: '#6B7280',
  legacyTextDisabled: '#9CA3AF',
  legacyTextPlaceholder: '#9CA3AF',

  // Old Borders (mostly covered by new borderSubtle/Strong)
  legacyBorderFocus: '#0EA5E9',
};

export type AppColors = typeof colors; 