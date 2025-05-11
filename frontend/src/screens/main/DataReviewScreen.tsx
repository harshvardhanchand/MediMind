import React, { useState } from 'react';
import { View, Text, Button, TextInput, ScrollView } from 'react-native';
import { styled } from 'nativewind';
import { useNavigation, useRoute, RouteProp } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { MainAppStackParamList } from '../../navigation/types';

const StyledView = styled(View);
const StyledText = styled(Text);
const StyledScrollView = styled(ScrollView);
const StyledTextInput = styled(TextInput);

type DataReviewScreenNavigationProp = NativeStackNavigationProp<MainAppStackParamList, 'DataReview'>;
type DataReviewScreenRouteProp = RouteProp<MainAppStackParamList, 'DataReview'>;

const DataReviewScreen = () => {
  const navigation = useNavigation<DataReviewScreenNavigationProp>();
  const route = useRoute<DataReviewScreenRouteProp>();
  const { documentId } = route.params;

  // In a real app, fetch the AI extracted data for documentId
  const [extractedData, setExtractedData] = useState(
    JSON.stringify({ 
      medication: 'Amoxicillin', 
      dosage: '250mg', 
      frequency: 'Every 8 hours', 
      patientName: 'John Doe (auto-detected, may need correction)' 
    }, null, 2)
  );

  const handleSaveChanges = () => {
    console.log('Saving changes for document:', documentId, extractedData);
    // Add API call to save corrected data here
    navigation.goBack(); // Go back to document detail or wherever appropriate
  };

  return (
    <StyledScrollView className="flex-1 p-4 bg-gray-50">
      <StyledText className="text-2xl font-bold mb-4">Review Extracted Data</StyledText>
      <StyledText className="text-md text-gray-600 mb-1">Document ID: {documentId}</StyledText>
      <StyledText className="text-sm text-gray-500 mb-4">
        Please review the AI-extracted data below and make any necessary corrections.
      </StyledText>
      
      <StyledView className="mb-4 p-3 bg-white rounded-lg shadow">
        <StyledTextInput
          multiline
          value={extractedData}
          onChangeText={setExtractedData}
          className="h-64 p-2 border border-gray-300 rounded text-base leading-6"
          textAlignVertical="top"
        />
      </StyledView>

      <Button title="Save Changes" onPress={handleSaveChanges} />
      <View style={{ marginTop: 10 }}>
        <Button title="Cancel" onPress={() => navigation.goBack()} color="gray" />
      </View>
    </StyledScrollView>
  );
};

export default DataReviewScreen; 