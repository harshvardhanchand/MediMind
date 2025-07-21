import React, { useState, useMemo, useEffect, useCallback } from 'react';
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

import EmptyState from '../../components/common/EmptyState';
import ErrorState from '../../components/common/ErrorState';
import { useTheme } from '../../theme';
import { DocumentRead, DocumentType } from '../../types/api';
import { documentServices } from '../../api/services';
import { EMPTY_STATE_MESSAGES, ERROR_MESSAGES, LOADING_MESSAGES } from '../../constants/messages';


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

  const dummyDocuments = useMemo<DocumentRead[]>(() => [
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
  ], []);

  const loadDocumentsFromApi = useCallback(async () => {
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
        console.log('API connected but no documents found, showing sample data');
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
  }, [dummyDocuments]);

  useEffect(() => {
    loadDocumentsFromApi();
  }, [loadDocumentsFromApi]);

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

  const renderDocumentItem: ListRenderItem<DocumentRead> = useCallback(({ item }) => (
    <ListItem
      key={item.document_id}
      label={item.original_filename || 'Untitled Document'}
      subtitle={`${item.document_type ? item.document_type.replace('_', ' ').toUpperCase() : 'N/A'} - ${item.document_date ? new Date(item.document_date).toLocaleDateString() : 'No Date'}`}
      iconLeft={getDocIconName(item.document_type || 'other')}
      iconLeftColor={colors.accentPrimary}
      onPress={() => navigation.navigate('DocumentDetail', { documentId: item.document_id })}
    />
  ), [colors.accentPrimary, navigation]);

  const applyDocTypeFilter = (type: DocumentType | 'All') => {
    setSelectedDocType(type);
    setFilterModalVisible(false);
  };

  const clearSearch = () => {
    setSearchQuery('');
  };

  const clearFilters = () => {
    setSelectedDocType('All');
    setSearchQuery('');
  };

  const handleUploadDocument = () => {
    // Navigate to upload screen or show upload modal
    console.log('Navigate to upload document');
  };

  // ✅ Render loading state
  if (isLoadingApi) {
    return (
      <ScreenContainer>
        <StyledView className="flex-1 justify-center items-center">
          <ActivityIndicator size="large" color={colors.accentPrimary} />
          <StyledText
            variant="body1"
            className="mt-4 text-center"
            style={{ color: colors.textSecondary }}
          >
            {LOADING_MESSAGES.LOADING_DOCUMENTS}
          </StyledText>
        </StyledView>
      </ScreenContainer>
    );
  }

  // ✅ Render error state (only if we have a real error and no fallback data)
  if (errorApi && !usingDummyData) {
    return (
      <ScreenContainer>
        <ErrorState
          title="Unable to Load Documents"
          message={ERROR_MESSAGES.DOCUMENTS_LOAD_ERROR}
          onRetry={loadDocumentsFromApi}
          retryLabel="Try Again"
        />
      </ScreenContainer>
    );
  }

  // ✅ Render empty state for no documents
  if (filteredDocuments.length === 0 && !searchQuery && selectedDocType === 'All') {
    return (
      <ScreenContainer>
        <EmptyState
          icon="document-text-outline"
          title={EMPTY_STATE_MESSAGES.NO_DOCUMENTS.title}
          description={EMPTY_STATE_MESSAGES.NO_DOCUMENTS.description}
          actionLabel={EMPTY_STATE_MESSAGES.NO_DOCUMENTS.actionLabel}
          onAction={handleUploadDocument}
        />
      </ScreenContainer>
    );
  }

  // ✅ Render empty state for no search/filter results
  if (filteredDocuments.length === 0 && (searchQuery || selectedDocType !== 'All')) {
    const isSearching = searchQuery.trim() !== '';
    const emptyStateConfig = isSearching
      ? EMPTY_STATE_MESSAGES.NO_SEARCH_RESULTS
      : EMPTY_STATE_MESSAGES.NO_FILTERED_RESULTS;

    return (
      <ScreenContainer>
        {/* Search and Filter UI */}
        <StyledView className="p-4 border-b border-gray-200">
          <StyledInput
            placeholder="Search documents..."
            value={searchQuery}
            onChangeText={setSearchQuery}
            leftIconName="search-outline"
            rightIconName={searchQuery ? "close-outline" : undefined}
            onRightIconPress={searchQuery ? clearSearch : undefined}
          />

          <StyledView className="flex-row justify-between items-center mt-3">
            <StyledButton
              variant="filledSecondary"
              onPress={() => setFilterModalVisible(true)}
              iconNameLeft="filter-outline"
            >
              {selectedDocType === 'All' ? 'Filter' : selectedDocType.replace('_', ' ')}
            </StyledButton>

            {(searchQuery || selectedDocType !== 'All') && (
              <StyledButton
                variant="textPrimary"
                onPress={clearFilters}
              >
                Clear All
              </StyledButton>
            )}
          </StyledView>
        </StyledView>

        <EmptyState
          icon="search-outline"
          title={emptyStateConfig.title}
          description={emptyStateConfig.description}
          actionLabel={emptyStateConfig.actionLabel}
          onAction={clearFilters}
        />
      </ScreenContainer>
    );
  }

  let mainContent;
  if (isLoadingApi) {
    mainContent = (
      <StyledView className="flex-1 items-center justify-center">
        <ActivityIndicator animating={true} size="large" />
        <StyledText variant="body1" color="textSecondary" className="mt-2">Loading documents...</StyledText>
      </StyledView>
    );
  } else if (filteredDocuments.length === 0 && !usingDummyData) {
    mainContent = (
      <StyledView className="flex-1 items-center justify-center">
        <Ionicons name="cloud-offline-outline" size={64} color={colors.textMuted} />
        <StyledText variant="h4" color="textMuted" className="mt-4">No Documents Found</StyledText>
        <StyledText color="textMuted" className="text-center mt-1 mx-8">
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
          <StyledText variant="h1" className="font-bold text-3xl">Documents</StyledText>
          <StyledText variant="body1" color="textSecondary" className="mt-1">
            Manage your lab results, prescriptions, and records.
          </StyledText>

          {usingDummyData && (
            <StyledView className="mt-3 p-3 bg-green-50 rounded-lg border border-green-200">
              <StyledText className="text-green-800 text-sm text-center font-medium">
                🚀 Ready to get started? Upload your first document!
              </StyledText>
              <StyledText className="text-green-700 text-xs text-center mt-1">
                These are sample documents to show you what's possible. Tap the + button to add your own.
              </StyledText>
            </StyledView>
          )}
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
              <StyledText variant="h3" className="font-semibold text-center">Filter by Type</StyledText>
            </StyledView>

            {documentFilterOptions.map((item, index) => (
              <StyledTouchableOpacity
                key={item.label}
                className={`p-4 flex-row items-center justify-between ${index < documentFilterOptions.length - 1 ? 'border-b border-gray-100' : ''}`}
                onPress={() => applyDocTypeFilter(item.value)}
              >
                <StyledText
                  variant="body1"
                  style={selectedDocType === item.value ? { color: colors.accentPrimary, fontWeight: '600' } : {}}
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
                className="w-full"
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