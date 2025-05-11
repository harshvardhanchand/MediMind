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
  withPadding?: boolean;
  backgroundColor?: string;
  statusBarContent?: 'light-content' | 'dark-content';
}

const ScreenContainer: React.FC<ScreenContainerProps> = ({
  children,
  scrollable = false,
  withPadding = true,
  backgroundColor,
  statusBarContent,
}) => {
  const { colors } = useTheme();
  const finalBgColor = backgroundColor || colors.backgroundScreen;

  // Determine StatusBar content based on background or explicit prop
  let barStyle: 'light-content' | 'dark-content';
  if (statusBarContent) {
    barStyle = statusBarContent;
  } else {
    // Basic heuristic for text color on background
    const isBgDark = parseInt(finalBgColor.substring(1, 3), 16) * 0.299 + 
                     parseInt(finalBgColor.substring(3, 5), 16) * 0.587 + 
                     parseInt(finalBgColor.substring(5, 7), 16) * 0.114 < 186;
    barStyle = isBgDark ? 'light-content' : 'dark-content';
  }

  // Updated padding using tailwind classes
  const paddingClass = withPadding ? "px-4 py-2" : ""; // Horizontal padding with less vertical padding
  
  // Create a common style object for consistent visual appearance
  const containerStyle = {
    backgroundColor: finalBgColor,
    flex: 1,
    // Add subtle shadow for depth
    shadowColor: 'rgba(0, 0, 0, 0.03)',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.8,
    shadowRadius: 2,
  };

  if (scrollable) {
    return (
      <StyledSafeAreaView style={containerStyle}>
        <RNStatusBar barStyle={barStyle} backgroundColor={finalBgColor} />
        <StyledScrollView 
          className={`flex-1 ${paddingClass}`}
          contentContainerStyle={{ flexGrow: 1 }}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false} // Hide scrollbar for cleaner look
          bounces={true} // Allow bouncing for better UX
        >
          {children}
        </StyledScrollView>
      </StyledSafeAreaView>
    );
  }

  return (
    <StyledSafeAreaView style={containerStyle}>
      <RNStatusBar barStyle={barStyle} backgroundColor={finalBgColor} />
      <StyledView className={`flex-1 ${paddingClass}`}>
        {children}
      </StyledView>
    </StyledSafeAreaView>
  );
};

export default ScreenContainer; 