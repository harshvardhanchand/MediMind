import React from 'react';
import { Button as PaperButton, ButtonProps as PaperButtonProps } from 'react-native-paper';
import { styled } from 'nativewind';
import { useTheme } from '../../theme';
import { TextStyle, ViewStyle } from 'react-native';

// Styled PaperButton that can accept className for margin, etc.
const NativeWindPaperButton = styled(PaperButton);

interface StyledButtonProps extends Omit<PaperButtonProps, 'theme'> {
  variant?: 'primary' | 'secondary' | 'accent' | 'error' | 'ghost' | 'outline' | 'link' | 'subtle';
  tw?: string; // For additional Tailwind classes passed directly
  // Explicitly allow the icon prop to accept a function that returns a React element
  icon?: PaperButtonProps['icon'];
}

const StyledButton: React.FC<StyledButtonProps> = ({
  variant = 'primary',
  mode = 'contained', // Default Paper button mode
  tw = '',
  style,
  labelStyle,
  children,
  icon,
  ...props
}) => {
  const theme = useTheme();

  let buttonColor: string | undefined;
  let textColor: string | undefined;
  let finalMode = mode;
  let additionalStyle: ViewStyle = {};
  let additionalLabelStyle: TextStyle = {
    fontWeight: '600', // Medium-bold font weight for all buttons
    letterSpacing: 0.3, // Slight letter spacing for better readability
  };

  switch (variant) {
    case 'secondary':
      buttonColor = theme.colors.secondary;
      textColor = theme.colors.gray800;
      if (mode === 'contained') finalMode = 'elevated';
      additionalStyle = { 
        borderRadius: 8,
        elevation: 0,
      };
      break;
    case 'accent':
      buttonColor = theme.colors.accent;
      textColor = theme.colors.white;
      additionalStyle = { 
        borderRadius: 8,
        elevation: 1,
      };
      break;
    case 'error':
      buttonColor = theme.colors.error;
      textColor = theme.colors.white;
      additionalStyle = { 
        borderRadius: 8,
        elevation: 1,
      };
      break;
    case 'outline':
      finalMode = 'outlined';
      buttonColor = 'transparent';
      textColor = theme.colors.primary;
      additionalStyle = { 
        borderRadius: 8,
        borderColor: theme.colors.primary,
        borderWidth: 1,
      };
      break;
    case 'ghost':
      finalMode = 'text';
      textColor = theme.colors.primary;
      additionalStyle = { 
        borderRadius: 8,
      };
      break;
    case 'subtle':
      finalMode = 'text';
      textColor = theme.colors.gray600;
      additionalStyle = { 
        borderRadius: 8,
      };
      break;
    case 'link':
      finalMode = 'text';
      textColor = theme.colors.primary;
      additionalLabelStyle = { 
        ...additionalLabelStyle,
        textDecorationLine: 'underline',
      };
      break;
    case 'primary': // Default
    default:
      buttonColor = theme.colors.primary;
      textColor = theme.colors.white;
      additionalStyle = { 
        borderRadius: 8,
        elevation: 1,
      };
      if (finalMode === 'text' || finalMode === 'outlined') {
        textColor = theme.colors.primary;
      }
      break;
  }

  return (
    <NativeWindPaperButton
      {...props}
      mode={finalMode}
      theme={theme}
      textColor={textColor}
      buttonColor={(finalMode === 'contained' || finalMode === 'elevated') ? buttonColor : undefined}
      className={tw}
      style={[
        { 
          borderRadius: 8,  // Consistent border radius for all buttons
        }, 
        additionalStyle, 
        style
      ]}
      labelStyle={[
        { 
          fontSize: 15,  // Consistent font size
          lineHeight: 20,  // Better vertical alignment
        }, 
        additionalLabelStyle, 
        labelStyle
      ]}
      icon={icon}
      uppercase={false} // Modern buttons typically don't use all uppercase
    >
      {children}
    </NativeWindPaperButton>
  );
};

export default StyledButton; 