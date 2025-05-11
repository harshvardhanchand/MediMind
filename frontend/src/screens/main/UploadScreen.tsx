import React from 'react';
import { View, Text, Button } from 'react-native';
import { styled } from 'nativewind';
import { useNavigation } from '@react-navigation/native';

const StyledView = styled(View);
const StyledText = styled(Text);

const UploadScreen = () => {
  const navigation = useNavigation();

  return (
    <StyledView className="flex-1 items-center justify-center p-4">
      <StyledText className="text-xl mb-4">Upload Document</StyledText>
      {/* Document upload UI will go here */}
      <Button title="Back to Home" onPress={() => navigation.navigate('Home' as never)} />
    </StyledView>
  );
};

export default UploadScreen; 