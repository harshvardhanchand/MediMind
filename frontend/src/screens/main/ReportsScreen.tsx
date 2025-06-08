import React from 'react';
import { View, Text, Button } from 'react-native';
import { styled } from 'nativewind';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';

import { MainAppStackParamList } from '../../navigation/types';

const StyledView = styled(View);
const StyledText = styled(Text);

type ReportsScreenNavigationProp = NativeStackNavigationProp<MainAppStackParamList, 'Reports'>;

const ReportsScreen = () => {
  const navigation = useNavigation<ReportsScreenNavigationProp>();

  return (
    <StyledView className="flex-1 items-center justify-center p-4">
      <StyledText className="text-xl mb-4">Reports & Summaries</StyledText>
      <StyledText className="text-center mb-4 text-gray-600">
        This section will allow you to generate and view reports based on your health data (e.g., trends in lab results, medication history, symptom patterns).
      </StyledText>
      {/* Placeholder for report generation options and display area */}
      <Button title="Back to Home" onPress={() => navigation.navigate('Home')} />
    </StyledView>
  );
};

export default ReportsScreen; 