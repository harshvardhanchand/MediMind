import React, { ReactNode } from 'react';
import { View, ScrollView, SafeAreaView, StatusBar as RNStatusBar } from 'react-native'; // Renamed StatusBar to avoid conflict
import { styled } from 'nativewind';
import { useTheme } from '../../theme'; // Import your custom useTheme

const StyledSafeAreaView = styled(SafeAreaView);
const StyledView = styled(View);
const StyledScrollView = styled(ScrollView);

interface ScreenContainerProps {
  children: ReactNode;
  scrollable?: boolean;
  /**
   * @description Applies horizontal and vertical padding to the main content area.
   * For Apple Health style, often set to false, and padding is handled by inner components (Cards, Lists).
   * Default is true for basic spacing.
   */
  withPadding?: boolean;
  backgroundColor?: string;
  statusBarContent?: 'light-content' | 'dark-content';
}

const ScreenContainer: React.FC<ScreenContainerProps> = ({
  children,
  scrollable = false,
  withPadding = true, // Consider making this false by default for more Apple-like control
  backgroundColor,
  statusBarContent,
}) => {
  const { colors } = useTheme();
  // Default to the new backgroundPrimary for the Apple Health look
  const finalBgColor = backgroundColor || colors.backgroundPrimary; 

  let barStyle: 'light-content' | 'dark-content';
  if (statusBarContent) {
    barStyle = statusBarContent;
  } else {
    // Heuristic: if background is dark, use light text, else dark text.
    // With backgroundPrimary being light, this will default to 'dark-content'
    const r = parseInt(finalBgColor.substring(1, 3), 16);
    const g = parseInt(finalBgColor.substring(3, 5), 16);
    const b = parseInt(finalBgColor.substring(5, 7), 16);
    const brightness = (r * 299 + g * 587 + b * 114) / 1000;
    barStyle = brightness < 128 ? 'light-content' : 'dark-content'; // Standard brightness threshold
  }

  // Adjusted default padding. Consider if more top/bottom padding is needed or handled by content.
  const paddingClass = withPadding ? "px-4 py-4" : ""; 
  
  // Removed global shadow. Shadows should be on cards/elements, not the screen itself.
  const containerStyle = {
    backgroundColor: finalBgColor,
    flex: 1,
  };

  const content = (
    scrollable ? (
      <StyledScrollView 
        className={`flex-1 ${paddingClass}`}
        contentContainerStyle={{ flexGrow: 1 }}
        keyboardShouldPersistTaps="handled"
        showsVerticalScrollIndicator={false}
        bounces={true}
      >
        {children}
      </StyledScrollView>
    ) : (
      <StyledView className={`flex-1 ${paddingClass}`}>
        {children}
      </StyledView>
    )
  );

  return (
    <StyledSafeAreaView style={containerStyle}>
      <RNStatusBar barStyle={barStyle} backgroundColor={finalBgColor} translucent={false} />
      {content}
    </StyledSafeAreaView>
  );
};

export default ScreenContainer; 