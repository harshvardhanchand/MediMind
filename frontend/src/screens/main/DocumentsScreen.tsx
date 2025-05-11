import React from 'react';
import { View, FlatList, TouchableOpacity, ListRenderItem } from 'react-native';
import { styled } from 'nativewind';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { MainAppStackParamList } from '../../navigation/types';
import { FileText, Calendar, Filter, ChevronRight, Search } from 'lucide-react-native';

import ScreenContainer from '../../components/layout/ScreenContainer';
import StyledText from '../../components/common/StyledText';
import StyledButton from '../../components/common/StyledButton';
import StyledInput from '../../components/common/StyledInput';

const StyledView = styled(View);
const StyledTouchableOpacity = styled(TouchableOpacity);

// Define document type
interface Document {
  id: string;
  name: string;
  type: string;
  date: string;
  iconBg: string;
  iconColor: string;
}

// Dummy data with more detailed properties
const dummyDocuments: Document[] = [
  { 
    id: '1', 
    name: 'Lab Results - Blood Test', 
    type: 'Lab Result', 
    date: 'Oct 15, 2023',
    iconBg: 'bg-primaryLight',
    iconColor: '#007AFF'
  },
  { 
    id: '2', 
    name: 'Prescription - Amoxicillin', 
    type: 'Prescription', 
    date: 'Oct 12, 2023',
    iconBg: 'bg-accentLight',
    iconColor: '#4CAF50'
  },
  { 
    id: '3', 
    name: 'X-Ray - Chest', 
    type: 'X-Ray', 
    date: 'Sep 20, 2023',
    iconBg: 'bg-gray-100',
    iconColor: '#8E8E93'
  },
  { 
    id: '4', 
    name: 'Doctor Notes - Annual Checkup', 
    type: 'Notes', 
    date: 'Sep 5, 2023',
    iconBg: 'bg-primaryLight',
    iconColor: '#007AFF'
  },
  { 
    id: '5', 
    name: 'Vaccination Record - COVID-19', 
    type: 'Vaccination', 
    date: 'Aug 10, 2023',
    iconBg: 'bg-accentLight',
    iconColor: '#4CAF50'
  }
];

type DocumentsScreenNavigationProp = NativeStackNavigationProp<MainAppStackParamList, 'Documents'>;

const DocumentsScreen = () => {
  const navigation = useNavigation<DocumentsScreenNavigationProp>();

  const renderDocumentItem: ListRenderItem<Document> = ({ item }) => (
    <StyledTouchableOpacity 
      tw="p-3 mb-3 bg-white rounded-lg shadow flex-row items-center"
      onPress={() => navigation.navigate('DocumentDetail', { documentId: item.id })}
    >
      <StyledView tw={`${item.iconBg} p-2 rounded-md mr-3`}>
        <FileText size={20} color={item.iconColor} />
      </StyledView>
      <StyledView tw="flex-1">
        <StyledText variant="label" tw="font-semibold text-gray-800">{item.name}</StyledText>
        <StyledText variant="caption" color="textSecondary">Type: {item.type}</StyledText>
        <StyledView tw="flex-row items-center mt-1">
          <Calendar size={12} color="#8E8E93" />
          <StyledText variant="caption" color="textSecondary" tw="ml-1">{item.date}</StyledText>
        </StyledView>
      </StyledView>
      <ChevronRight size={16} color="#8E8E93" />
    </StyledTouchableOpacity>
  );

  return (
    <ScreenContainer scrollable={false} withPadding>
      {/* Header */}
      <StyledView tw="pt-2 pb-4">
        <StyledText variant="h1" color="primary">Documents</StyledText>
        <StyledText variant="body2" color="textSecondary" tw="mt-1">
          View lab results, prescriptions, and other medical records
        </StyledText>
      </StyledView>
      
      {/* Search & Filter */}
      <StyledView tw="flex-row items-center mb-4">
        <StyledView tw="flex-1 mr-2">
          <StyledInput
            placeholder="Search documents..."
            left={<Search size={18} color="#8E8E93" />}
            tw="bg-white"
          />
        </StyledView>
        <StyledButton 
          variant="secondary" 
          mode="outlined"
          icon={() => <Filter size={18} color="#8E8E93" />}
          tw="p-1"
        >
          Filter
        </StyledButton>
      </StyledView>
      
      {/* Documents List */}
      <StyledView tw="flex-1">
        <FlatList<Document>
          data={dummyDocuments}
          keyExtractor={(item) => item.id}
          renderItem={renderDocumentItem}
          showsVerticalScrollIndicator={false}
        />
      </StyledView>
      
      {/* Add Document Button */}
      <StyledView tw="pt-3">
        <StyledButton 
          variant="primary"
          onPress={() => navigation.navigate('Upload')} 
          tw="w-full"
        >
          Upload New Document
        </StyledButton>
      </StyledView>
    </ScreenContainer>
  );
};

export default DocumentsScreen; 