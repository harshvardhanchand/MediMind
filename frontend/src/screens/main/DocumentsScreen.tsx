import React, { useState, useMemo } from 'react';
import { View, FlatList, ListRenderItem, TouchableOpacity, Modal, Pressable } from 'react-native';
import { styled } from 'nativewind';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { MainAppStackParamList } from '../../navigation/types';
import Ionicons from 'react-native-vector-icons/Ionicons';

import ScreenContainer from '../../components/layout/ScreenContainer';
import StyledText from '../../components/common/StyledText';
import StyledButton from '../../components/common/StyledButton';
import StyledInput from '../../components/common/StyledInput';
import ListItem from '../../components/common/ListItem';
import Card from '../../components/common/Card';
import { useTheme } from '../../theme';

const StyledView = styled(View);
const StyledTouchableOpacity = styled(TouchableOpacity);
const StyledPressable = styled(Pressable);

// Define document type
interface Document {
  id: string;
  name: string;
  type: string;
  date: string;
}

// Dummy data with more detailed properties
const dummyDocuments: Document[] = [
  { id: '1', name: 'Lab Results - Blood Test', type: 'lab_result', date: 'Oct 15, 2023' },
  { id: '2', name: 'Prescription - Amoxicillin', type: 'prescription', date: 'Oct 12, 2023' },
  { id: '3', name: 'X-Ray - Chest', type: 'imaging', date: 'Sep 20, 2023' },
  { id: '4', name: 'Doctor Notes - Annual Checkup', type: 'notes', date: 'Sep 5, 2023' },
  { id: '5', name: 'Vaccination Record - COVID-19', type: 'vaccination', date: 'Aug 10, 2023' },
  { id: '6', name: 'MRI Scan - Brain', type: 'imaging', date: 'Jul 11, 2023' },
  { id: '7', name: 'Allergy Test Results', type: 'lab_result', date: 'Jun 22, 2023' },
  { id: '8', name: 'Prescription - Ibuprofen', type: 'prescription', date: 'May 30, 2023' },
];

// Re-use or import from HomeScreen if centralized
const getDocIconName = (docType: string) => {
  switch (docType) {
    case 'lab_result': return 'flask-outline';
    case 'prescription': return 'medkit-outline';
    case 'imaging': return 'images-outline';
    case 'notes': return 'document-text-outline';
    case 'vaccination': return 'shield-checkmark-outline';
    default: return 'document-outline';
  }
};

type DocumentsScreenNavigationProp = NativeStackNavigationProp<MainAppStackParamList, 'Documents'>;

const DocumentTypes = ['All', 'Lab Result', 'Prescription', 'Imaging', 'Notes', 'Vaccination'];

const DocumentsScreen = () => {
  const navigation = useNavigation<DocumentsScreenNavigationProp>();
  const { colors } = useTheme();
  const [searchQuery, setSearchQuery] = useState('');
  const [filterModalVisible, setFilterModalVisible] = useState(false);
  const [selectedDocType, setSelectedDocType] = useState('All');

  const filteredDocuments = useMemo(() => {
    let docs = dummyDocuments;

    // Apply document type filter first
    if (selectedDocType !== 'All') {
      docs = docs.filter(doc => doc.type === selectedDocType);
    }

    // Then apply search query on the already type-filtered list (or all if type is 'All')
    if (searchQuery.trim() !== '') {
      const lowercasedQuery = searchQuery.toLowerCase();
      docs = docs.filter(doc => 
        doc.name.toLowerCase().includes(lowercasedQuery) ||
        doc.type.toLowerCase().includes(lowercasedQuery) || // Searching type again might be redundant if already filtered by type
        doc.date.toLowerCase().includes(lowercasedQuery) // Example: search by date string
      );
    }
    
    // TODO: Apply date range and sorting filters here if added later
    return docs;
  }, [searchQuery, selectedDocType, dummyDocuments]); // dummyDocuments in deps if it can change

  const renderDocumentItem: ListRenderItem<Document> = ({ item, index }) => (
    <ListItem
      key={item.id}
      label={item.name}
      subtitle={`${item.type.replace('_', ' ').toUpperCase()} - ${item.date}`}
      iconLeft={getDocIconName(item.type)}
      iconLeftColor={colors.accentPrimary}
      onPress={() => navigation.navigate('DocumentDetail', { documentId: item.id })}
    />
  );

  const applyDocTypeFilter = (type: string) => {
    setSelectedDocType(type);
    setFilterModalVisible(false);
  };

  return (
    <ScreenContainer scrollable={false} withPadding={false}>
      <StyledView className="flex-1 pt-6">
        {/* Header */}
        <StyledView className="px-4 pb-4">
          <StyledText variant="h1" tw="font-bold text-3xl">Documents</StyledText>
          <StyledText variant="body1" color="textSecondary" tw="mt-1">
            Manage your lab results, prescriptions, and records.
          </StyledText>
        </StyledView>
        
        {/* Search & Filter */}
        <StyledView className="px-4 mb-4 flex-row items-center">
          <StyledView className="flex-1 mr-3">
            <StyledInput
              placeholder="Search by name, type, or date..."
              value={searchQuery}
              onChangeText={setSearchQuery}
              leftIconName="search-outline"
            />
          </StyledView>
          <StyledButton 
            variant="textPrimary" 
            onPress={() => setFilterModalVisible(true)}
            tw="p-0"
          >
            <Ionicons name="filter-outline" size={26} color={colors.accentPrimary} />
          </StyledButton>
        </StyledView>
        
        {filteredDocuments.length === 0 ? (
            <StyledView className="flex-1 items-center justify-center">
                <Ionicons name="cloud-offline-outline" size={64} color={colors.textMuted} />
                <StyledText variant="h4" color="textMuted" tw="mt-4">No Documents Found</StyledText>
                <StyledText color="textMuted" tw="text-center mt-1 mx-8">
                    Try adjusting your search or filter criteria, or upload a new document.
                </StyledText>
            </StyledView>
        ) : (
            <FlatList<Document>
                data={filteredDocuments}
                keyExtractor={(item) => item.id}
                renderItem={renderDocumentItem}
                showsVerticalScrollIndicator={false}
                contentContainerStyle={{ paddingHorizontal: 16, paddingBottom: 80 }}
                ItemSeparatorComponent={() => <StyledView className="h-px bg-borderSubtle ml-14" />}
            />
        )}
      </StyledView>
      
      {/* FAB for Upload New Document */}
      <StyledTouchableOpacity
        className="absolute bottom-6 right-6 bg-accentPrimary rounded-full p-4 shadow-lg"
        onPress={() => navigation.navigate('Upload' as any)}
        activeOpacity={0.8}
      >
        <Ionicons name="add-outline" size={28} color={colors.textOnPrimaryColor} />
      </StyledTouchableOpacity>

      {/* Filter Modal */}
      <Modal
        animationType="fade"
        transparent={true}
        visible={filterModalVisible}
        onRequestClose={() => setFilterModalVisible(false)}
      >
        <StyledPressable 
            className="flex-1 justify-center items-center bg-black/50"
            onPress={() => setFilterModalVisible(false)}
        >
            <Card tw="w-4/5 max-w-sm bg-backgroundSecondary rounded-xl p-0">
                <StyledText variant="h3" tw="p-4 font-semibold border-b border-borderSubtle">Filter by Type</StyledText>
                <FlatList 
                    data={DocumentTypes}
                    keyExtractor={(item) => item}
                    renderItem={({item}) => (
                        <ListItem
                            label={item}
                            onPress={() => applyDocTypeFilter(item)}
                            tw={`px-4 ${selectedDocType === item ? 'bg-accentPrimary/10' : ''}`}
                            labelStyle={selectedDocType === item ? {color: colors.accentPrimary, fontWeight: '600'} : {}}
                            iconRight={selectedDocType === item ? 'checkmark-circle-outline' : undefined}
                            iconRightColor={colors.accentPrimary}
                            showBottomBorder
                        />
                    )}
                />
                <StyledButton variant="textPrimary" onPress={() => setFilterModalVisible(false)} tw="p-4 self-center">
                    Close
                </StyledButton>
            </Card>
        </StyledPressable>
      </Modal>
    </ScreenContainer>
  );
};

export default DocumentsScreen; 