import React, { useState, useMemo, useEffect } from 'react';
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
import { DocumentRead, DocumentType } from '../../types/api';
import { documentServices } from '../../api/services';
import { ActivityIndicator } from 'react-native-paper';

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

  const [searchQuery, setSearchQuery] = useState('');
  const [filterModalVisible, setFilterModalVisible] = useState(false);
  const [selectedDocType, setSelectedDocType] = useState<DocumentType | 'All'>('All');

  const loadDocumentsFromApi = async () => {
    setIsLoadingApi(true);
    setErrorApi(null);
    try {
      const response = await documentServices.getDocuments(); 
      setApiDocuments(response.data || []);
    } catch (err: any) {
      console.error("Failed to fetch documents:", err);
      setErrorApi(err.message || 'Failed to load documents.');
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
  } else if (errorApi) {
    mainContent = (
      <StyledView className="flex-1 items-center justify-center p-4">
        <Ionicons name="alert-circle-outline" size={64} color={colors.error} />
        <StyledText variant="h4" color="error" tw="mt-4 mb-2 text-center">Error Loading Documents</StyledText>
        <StyledText color="textSecondary" tw="text-center mb-4">{errorApi}</StyledText>
        <StyledButton variant="filledPrimary" onPress={loadDocumentsFromApi}>Retry</StyledButton>
      </StyledView>
    );
  } else if (filteredDocuments.length === 0) {
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
            onPress={() => setFilterModalVisible(true)}
            tw="p-0"
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
                    data={documentFilterOptions}
                    keyExtractor={(item) => item.label}
                    renderItem={({item}) => (
                        <ListItem
                            label={item.label}
                            onPress={() => applyDocTypeFilter(item.value)}
                            tw={`px-4 ${selectedDocType === item.value ? 'bg-accentPrimary/10' : ''}`}
                            labelStyle={selectedDocType === item.value ? {color: colors.accentPrimary, fontWeight: '600'} : {}}
                            iconRight={selectedDocType === item.value ? 'checkmark-circle-outline' : undefined}
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