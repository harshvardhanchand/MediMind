import React, { useState, useMemo, useEffect } from 'react';
import { View, FlatList, ListRenderItem, TouchableOpacity, Modal, Pressable, RefreshControl } from 'react-native';
import { styled } from 'nativewind';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { Ionicons } from '@expo/vector-icons';
import { ActivityIndicator } from 'react-native-paper';

import { MainAppStackParamList } from '../../navigation/types';
import ScreenContainer from '../../components/layout/ScreenContainer';
import StyledText from '../../components/common/StyledText';
import StyledButton from '../../components/common/StyledButton';
import StyledInput from '../../components/common/StyledInput';
import ListItem from '../../components/common/ListItem';
import Card from '../../components/common/Card';
import { useTheme } from '../../theme';
import { DocumentRead, DocumentType } from '../../types/api';
import { documentServices } from '../../api/services';


const StyledView = styled(View);
const StyledTouchableOpacity = styled(TouchableOpacity);
const StyledPressable = styled(Pressable);

const getDocIconName = (docType: string | DocumentType) => {
  const typeString = docType.toString().toLowerCase();
  switch (typeString) {
    case DocumentType.LAB_RESULT.toLowerCase(): return 'flask-outline';
    case DocumentType.PRESCRIPTION.toLowerCase(): return 'medkit-outline';
    case DocumentType.IMAGING_REPORT.toLowerCase(): return 'images-outline';
    case 'notes': return 'document-text-outline';
    case 'vaccination': return 'shield-checkmark-outline';
    default: return 'document-outline';
  }
};

type DocumentsScreenNavigationProp = NativeStackNavigationProp<MainAppStackParamList, 'Documents'>;

const documentFilterOptions = [
  { label: 'All', value: 'All' as const },
  { label: 'Lab Result', value: DocumentType.LAB_RESULT },
  { label: 'Prescription', value: DocumentType.PRESCRIPTION },
  { label: 'Imaging Report', value: DocumentType.IMAGING_REPORT },
  { label: 'Other', value: DocumentType.OTHER },
];

const DocumentsScreen = () => {
  const navigation = useNavigation<DocumentsScreenNavigationProp>();
  const { colors } = useTheme();
  
  const [apiDocuments, setApiDocuments] = useState<DocumentRead[]>([]);
  const [isLoadingApi, setIsLoadingApi] = useState(false);
  const [errorApi, setErrorApi] = useState<string | null>(null);
  const [usingDummyData, setUsingDummyData] = useState(false);

  const [searchQuery, setSearchQuery] = useState('');
  const [filterModalVisible, setFilterModalVisible] = useState(false);
  const [selectedDocType, setSelectedDocType] = useState<DocumentType | 'All'>('All');

  // Dummy data fallback
  const dummyDocuments: DocumentRead[] = [
    {
      document_id: 'dummy-doc1',
      user_id: 'dummy-user',
      original_filename: 'Lab Report - Blood Test.pdf',
      document_type: DocumentType.LAB_RESULT,
      storage_path: 'dummy/path',
      upload_timestamp: '2024-05-10T00:00:00Z',
      processing_status: 'completed' as any,
      document_date: '2024-05-10',
      source_name: 'Central Lab',
    },
    {
      document_id: 'dummy-doc2',
      user_id: 'dummy-user',
      original_filename: 'Prescription - Amoxicillin.pdf',
      document_type: DocumentType.PRESCRIPTION,
      storage_path: 'dummy/path',
      upload_timestamp: '2024-05-08T00:00:00Z',
      processing_status: 'completed' as any,
      document_date: '2024-05-08',
      source_name: 'Dr. Smith',
    },
    {
      document_id: 'dummy-doc3',
      user_id: 'dummy-user',
      original_filename: 'X-Ray - Chest Scan.pdf',
      document_type: DocumentType.IMAGING_REPORT,
      storage_path: 'dummy/path',
      upload_timestamp: '2024-05-05T00:00:00Z',
      processing_status: 'completed' as any,
      document_date: '2024-05-05',
      source_name: 'Radiology Center',
    },
    {
      document_id: 'dummy-doc4',
      user_id: 'dummy-user',
      original_filename: 'Consultation Notes.pdf',
      document_type: DocumentType.OTHER,
      storage_path: 'dummy/path',
      upload_timestamp: '2024-05-03T00:00:00Z',
      processing_status: 'completed' as any,
      document_date: '2024-05-03',
      source_name: 'Dr. Johnson',
    },
  ];

  const loadDocumentsFromApi = async () => {
    setIsLoadingApi(true);
    setErrorApi(null);
    setUsingDummyData(false);
    
    try {
      console.log('Trying to fetch real documents from API...');
      const response = await documentServices.getDocuments(); 
      
      if (response.data && response.data.length > 0) {
        console.log(`Loaded ${response.data.length} real documents from API`);
        setApiDocuments(response.data);
        setUsingDummyData(false);
      } else {
        console.log('API returned empty data, using dummy documents');
        setApiDocuments(dummyDocuments);
        setUsingDummyData(true);
      }
    } catch (err: any) {
      console.log('API call failed, falling back to dummy data:', err.message);
      setApiDocuments(dummyDocuments);
      setUsingDummyData(true);
      setErrorApi(null); // Clear error since we're showing dummy data
    } finally {
      setIsLoadingApi(false);
    }
  };

  useEffect(() => {
    loadDocumentsFromApi();
  }, []);

  const filteredDocuments = useMemo(() => {
    let docsToFilter = [...apiDocuments];

    if (selectedDocType !== 'All') {
      docsToFilter = docsToFilter.filter(doc => doc.document_type === selectedDocType);
    }

    if (searchQuery.trim() !== '') {
      const lowercasedQuery = searchQuery.toLowerCase();
      docsToFilter = docsToFilter.filter(doc => 
        doc.original_filename?.toLowerCase().includes(lowercasedQuery) ||
        doc.document_type?.toString().toLowerCase().includes(lowercasedQuery) ||
        (doc.document_date && new Date(doc.document_date).toLocaleDateString().toLowerCase().includes(lowercasedQuery)) ||
        doc.source_name?.toLowerCase().includes(lowercasedQuery)
      );
    }
    return docsToFilter;
  }, [searchQuery, selectedDocType, apiDocuments]);

  const renderDocumentItem: ListRenderItem<DocumentRead> = ({ item }) => (
    <ListItem
      key={item.document_id}
      label={item.original_filename || 'Untitled Document'}
      subtitle={`${item.document_type ? item.document_type.replace('_', ' ').toUpperCase() : 'N/A'} - ${item.document_date ? new Date(item.document_date).toLocaleDateString() : 'No Date'}`}
      iconLeft={getDocIconName(item.document_type || 'other')}
      iconLeftColor={colors.accentPrimary}
      onPress={() => navigation.navigate('DocumentDetail', { documentId: item.document_id })}
    />
  );

  const applyDocTypeFilter = (type: DocumentType | 'All') => {
    setSelectedDocType(type);
    setFilterModalVisible(false);
  };

  let mainContent;
  if (isLoadingApi) {
    mainContent = (
      <StyledView className="flex-1 items-center justify-center">
        <ActivityIndicator animating={true} size="large" />
        <StyledText variant="body1" color="textSecondary" tw="mt-2">Loading documents...</StyledText>
      </StyledView>
    );
  } else if (filteredDocuments.length === 0 && !usingDummyData) {
    mainContent = (
        <StyledView className="flex-1 items-center justify-center">
            <Ionicons name="cloud-offline-outline" size={64} color={colors.textMuted} />
            <StyledText variant="h4" color="textMuted" tw="mt-4">No Documents Found</StyledText>
            <StyledText color="textMuted" tw="text-center mt-1 mx-8">
                Try adjusting your search or filter criteria, or upload a new document.
            </StyledText>
        </StyledView>
    );
  } else {
    mainContent = (
        <FlatList<DocumentRead>
            data={filteredDocuments}
            keyExtractor={(item) => item.document_id}
            renderItem={renderDocumentItem}
            showsVerticalScrollIndicator={false}
            contentContainerStyle={{ paddingHorizontal: 16, paddingBottom: 80 }}
            ItemSeparatorComponent={() => <StyledView className="h-px bg-borderSubtle ml-14" />}
            refreshControl={
                <RefreshControl
                    refreshing={isLoadingApi}
                    onRefresh={loadDocumentsFromApi}
                />
            }
        />
    );
  }

  return (
    <ScreenContainer scrollable={false} withPadding={false}>
      <StyledView className="flex-1 pt-6">
        <StyledView className="px-4 pb-4">
          <StyledText variant="h1" tw="font-bold text-3xl">Documents</StyledText>
          <StyledText variant="body1" color="textSecondary" tw="mt-1">
            Manage your lab results, prescriptions, and records.
          </StyledText>
          
          {usingDummyData && (
            <StyledView className="mt-3 p-2 bg-yellow-100 rounded border border-yellow-300">
              <StyledText tw="text-yellow-800 text-sm text-center">
                📱 Showing sample data (API not connected)
              </StyledText>
            </StyledView>
          )}
        </StyledView>
        
        <StyledView className="px-4 mb-4 flex-row items-center">
          <StyledView className="flex-1 mr-3">
            <StyledInput
              placeholder="Search documents..."
              value={searchQuery}
              onChangeText={setSearchQuery}
              leftIconName="search-outline"
            />
          </StyledView>
          <StyledButton 
            variant="textPrimary" 
            onPress={() => {
              console.log("Filter button pressed!"); // Debug log
              setFilterModalVisible(true);
            }}
            tw="p-2 min-w-12 min-h-12 justify-center items-center"
          >
            <Ionicons name="filter-outline" size={26} color={colors.accentPrimary} />
          </StyledButton>
        </StyledView>
        
        {mainContent}
      </StyledView>
      
      <StyledTouchableOpacity
        className="absolute bottom-6 right-6 bg-accentPrimary rounded-full p-4 shadow-lg"
        onPress={() => navigation.navigate('Upload' as any)}
        activeOpacity={0.8}
      >
        <Ionicons name="add-outline" size={28} color={colors.textOnPrimaryColor} />
      </StyledTouchableOpacity>

      <Modal
        animationType="slide"
        transparent={true}
        visible={filterModalVisible}
        onRequestClose={() => setFilterModalVisible(false)}
      >
        <StyledView className="flex-1 justify-end bg-black/50">
          <StyledPressable 
            className="flex-1"
            onPress={() => setFilterModalVisible(false)}
          />
          <StyledView className="bg-white rounded-t-xl">
            <StyledView className="p-4 border-b border-gray-200">
              <StyledText variant="h3" tw="font-semibold text-center">Filter by Type</StyledText>
            </StyledView>
            
            {documentFilterOptions.map((item, index) => (
              <StyledTouchableOpacity
                key={item.label}
                className={`p-4 flex-row items-center justify-between ${index < documentFilterOptions.length - 1 ? 'border-b border-gray-100' : ''}`}
                onPress={() => applyDocTypeFilter(item.value)}
              >
                <StyledText 
                  variant="body1" 
                  style={selectedDocType === item.value ? {color: colors.accentPrimary, fontWeight: '600'} : {}}
                >
                  {item.label}
                </StyledText>
                {selectedDocType === item.value && (
                  <Ionicons name="checkmark-circle" size={24} color={colors.accentPrimary} />
                )}
              </StyledTouchableOpacity>
            ))}
            
            <StyledView className="p-4 border-t border-gray-200">
              <StyledButton 
                variant="filledPrimary" 
                onPress={() => setFilterModalVisible(false)} 
                tw="w-full"
              >
                Close
              </StyledButton>
            </StyledView>
          </StyledView>
        </StyledView>
      </Modal>
    </ScreenContainer>
  );
};

export default DocumentsScreen; 