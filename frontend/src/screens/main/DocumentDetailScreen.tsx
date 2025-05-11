import React from 'react';
import { View, Text, Button, ScrollView } from 'react-native';
import { styled } from 'nativewind';
import { useNavigation, useRoute, RouteProp } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { MainAppStackParamList } from '../../navigation/types';

const StyledView = styled(View);
const StyledText = styled(Text);
const StyledScrollView = styled(ScrollView);

type DocumentDetailScreenNavigationProp = NativeStackNavigationProp<MainAppStackParamList, 'DocumentDetail'>;
type DocumentDetailScreenRouteProp = RouteProp<MainAppStackParamList, 'DocumentDetail'>;

const DocumentDetailScreen = () => {
  const navigation = useNavigation<DocumentDetailScreenNavigationProp>();
  const route = useRoute<DocumentDetailScreenRouteProp>();
  const { documentId } = route.params;

  // In a real app, fetch document details using documentId
  const document = {
    id: documentId,
    name: `Details for Document ${documentId}`,
    type: 'Sample Type',
    date: '2023-10-01',
    content: 'This is the full content or extracted data of the document. It could be a long string or a structured object.',
    extractedDataSummary: 'AI Extracted: Glucose level: 120 mg/dL, Cholesterol: 190 mg/dL. Review needed.'
  };

  return (
    <StyledScrollView className="flex-1 p-4 bg-gray-50">
      <StyledText className="text-2xl font-bold mb-2">{document.name}</StyledText>
      <StyledText className="text-md text-gray-600 mb-1">Type: {document.type}</StyledText>
      <StyledText className="text-md text-gray-600 mb-4">Date: {document.date}</StyledText>
      
      <StyledView className="p-3 mb-4 bg-white rounded-lg shadow">
        <StyledText className="text-lg font-semibold mb-2">Extracted Data Summary</StyledText>
        <StyledText className="text-gray-700 mb-3">{document.extractedDataSummary}</StyledText>
        <Button 
          title="Review & Correct Data" 
          onPress={() => navigation.navigate('DataReview', { documentId })}
        />
      </StyledView>

      <StyledView className="p-3 mb-4 bg-white rounded-lg shadow">
        <StyledText className="text-lg font-semibold mb-2">Full Document Content/Image</StyledText>
        <StyledText className="text-gray-700">{/* Placeholder for actual document view (e.g., PDF or Image) */}</StyledText>
        <StyledText className="text-gray-700">{document.content}</StyledText>
      </StyledView>

      <Button title="Back to Documents" onPress={() => navigation.goBack()} />
    </StyledScrollView>
  );
};

export default DocumentDetailScreen; 