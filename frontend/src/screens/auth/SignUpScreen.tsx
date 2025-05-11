import React from 'react';
import { View, Text, Button } from 'react-native';
import { styled } from 'nativewind';
import { useNavigation } from '@react-navigation/native';

const StyledView = styled(View);
const StyledText = styled(Text);

const SignUpScreen = () => {
  const navigation = useNavigation();

  return (
    <StyledView className="flex-1 items-center justify-center bg-gray-50 p-4">
      <StyledText className="text-2xl font-bold mb-6 text-gray-800">Sign Up</StyledText>
      <StyledText className="mb-4 text-gray-600">Sign up form will go here.</StyledText>
      <Button title="Sign Up" onPress={() => navigation.navigate('Main' as never)} /> 
      <Button title="Back to Login" onPress={() => navigation.goBack()} />
    </StyledView>
  );
};

export default SignUpScreen; 