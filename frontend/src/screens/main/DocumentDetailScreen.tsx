import React, { useLayoutEffect, useState, useEffect } from 'react';
import { ScrollView, View, TouchableOpacity, Alert, Dimensions, Platform, ActivityIndicator, Image, Modal, Pressable, RefreshControl } from 'react-native';
import { styled } from 'nativewind';
import { useNavigation, useRoute, RouteProp, useFocusEffect } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { MaterialIcons } from '@expo/vector-icons';
import { WebView } from 'react-native-webview';

import { MainAppStackParamList } from '../../navigation/types';
import ScreenContainer from '../../components/layout/ScreenContainer';
import StyledText from '../../components/common/StyledText';
import StyledButton from '../../components/common/StyledButton';
import Card from '../../components/common/Card';
import ListItem from '../../components/common/ListItem';
import { useTheme } from '../../theme';
import { DocumentRead, ExtractedDataResponse, ProcessingStatus } from '../../types/api';
import { documentServices, extractedDataServices } from '../../api/services';

const StyledView = styled(View);
const StyledScrollView = styled(ScrollView);
const StyledTouchableOpacity = styled(TouchableOpacity);
const StyledPressable = styled(Pressable);

type DocumentDetailScreenNavigationProp = NativeStackNavigationProp<MainAppStackParamList, 'DocumentDetail'>;
type DocumentDetailScreenRouteProp = RouteProp<MainAppStackParamList, 'DocumentDetail'>;

const DocumentDetailScreen = () => {
  const navigation = useNavigation<DocumentDetailScreenNavigationProp>();
  const route = useRoute<DocumentDetailScreenRouteProp>();
  const { colors } = useTheme();
  const { documentId } = route.params;

  // State for actual document data
  const [document, setDocument] = useState<DocumentRead | null>(null);
  const [extractedData, setExtractedData] = useState<ExtractedDataResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // PDF/Image viewer state
  const [isLoadingPdf, setIsLoadingPdf] = useState(false);
  const [pdfError, setPdfError] = useState<string | null>(null);
  const [showPdfViewer, setShowPdfViewer] = useState(false);
  const [showImageViewer, setShowImageViewer] = useState(false);
  const [imageUriForModal, setImageUriForModal] = useState<string | undefined>(undefined);

  // Load document data on mount
  useEffect(() => {
    loadDocumentData();
  }, [documentId]);

  // Refresh data when screen comes into focus (e.g., after navigating back from DataReviewScreen)
  useFocusEffect(
    React.useCallback(() => {
      loadDocumentData();
    }, [documentId])
  );

  const loadDocumentData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      // Fetch document details
      const documentResponse = await documentServices.getDocumentById(documentId);
      setDocument(documentResponse.data);

      // Fetch extracted data if available
      try {
        const extractedResponse = await extractedDataServices.getExtractedData(documentId);
        setExtractedData(extractedResponse.data);
      } catch (extractedError) {
        console.log('No extracted data available yet:', extractedError);
        setExtractedData(null);
      }
    } catch (err: any) {
      console.error('Failed to load document:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to load document');
    } finally {
      setIsLoading(false);
    }
  };

  // Get document URL for viewing
  const getDocumentViewUrl = (doc: DocumentRead): string => {
    // Construct the URL to view the document from your backend
    // This assumes your backend has an endpoint to serve documents
    const baseUrl = process.env.API_URL || 'http://192.168.1.4:8000';
    return `${baseUrl}/api/documents/${doc.document_id}/view`;
  };

  // Determine document type based on file metadata
  const getDocumentType = (doc: DocumentRead): 'pdf' | 'image' | 'other' => {
    const contentType = doc.file_metadata?.content_type?.toLowerCase();
    if (contentType?.includes('pdf')) return 'pdf';
    if (contentType?.includes('image')) return 'image';
    return 'other';
  };

  const { width } = Dimensions.get('window');

  useLayoutEffect(() => {
    if (document) {
      navigation.setOptions({
        headerTitle: document.original_filename || 'Document Details', 
        headerRight: () => (
          <StyledTouchableOpacity 
            onPress={() => alert(`TODO: Edit ${document.original_filename}`)}
            tw="p-1.5"
          >
            <StyledText style={{ color: colors.accentPrimary, fontSize: 17 }}>Edit</StyledText>
          </StyledTouchableOpacity>
        ),
        headerStyle: { backgroundColor: colors.backgroundSecondary },
        headerTitleStyle: { color: colors.textPrimary },
        headerTintColor: colors.accentPrimary,
      });
    }
  }, [navigation, colors, document]);

  if (isLoading) {
    return (
      <ScreenContainer>
        <StyledView className="flex-1 justify-center items-center">
          <ActivityIndicator size="large" color={colors.accentPrimary} />
          <StyledText variant="body1" color="textSecondary" tw="mt-4">Loading document...</StyledText>
        </StyledView>
      </ScreenContainer>
    );
  }

  if (error || !document) {
    return (
      <ScreenContainer>
        <StyledView className="flex-1 justify-center items-center p-4">
          <MaterialIcons name="error-outline" size={64} color={colors.error} />
          <StyledText variant="h4" color="error" tw="mt-4 mb-2 text-center">Error Loading Document</StyledText>
          <StyledText color="textSecondary" tw="text-center mb-4">{error || 'Document not found'}</StyledText>
          <StyledButton variant="filledPrimary" onPress={loadDocumentData}>
            <StyledText>Retry</StyledText>
          </StyledButton>
        </StyledView>
      </ScreenContainer>
    );
  }

  const getDisplayStatus = () => {
    if (extractedData?.review_status) {
      // If we have extracted data, show its review status
      switch (extractedData.review_status) {
        case 'pending_review':
          return 'REVIEW REQUIRED';
        case 'reviewed_corrected':
          return 'REVIEWED & CORRECTED';
        case 'reviewed_approved':
          return 'APPROVED';
        default:
          return extractedData.review_status.replace('_', ' ').toUpperCase();
      }
    }
    // Fallback to document processing status
    return document.processing_status?.replace('_', ' ').toUpperCase();
  };

  const documentInfoItems = [
    { label: 'Type', value: document.document_type?.replace('_', ' ').toUpperCase(), icon: 'document-text-outline' },
    { label: 'Date', value: document.document_date || 'No date specified', icon: 'calendar-outline' },
    { label: 'Status', value: getDisplayStatus(), icon: 'information-circle-outline' },
    { label: 'Source', value: document.source_name || 'Not specified', icon: 'location-outline' },
  ];

  const togglePdfViewer = () => setShowPdfViewer(!showPdfViewer);

  const openImageViewer = (uri: string) => {
    setImageUriForModal(uri);
    setShowImageViewer(true);
  };

  const closeImageViewer = () => {
    setShowImageViewer(false);
    setImageUriForModal(undefined);
  };

  // Helper function to get PDF.js viewer URL
  const getPDFViewerUrl = (url: string) => {
    const encodedUrl = encodeURIComponent(url);
    return `https://mozilla.github.io/pdf.js/web/viewer.html?file=${encodedUrl}`;
  };

  const handlePdfLoadEnd = () => {
    setIsLoadingPdf(false);
    setPdfError(null);
  };

  const handlePdfError = () => {
    setIsLoadingPdf(false);
    setPdfError('Failed to load PDF document');
  };

  const documentType = getDocumentType(document);
  const documentViewUrl = getDocumentViewUrl(document);

  return (
    <ScreenContainer scrollable={false} withPadding={false} backgroundColor={colors.backgroundPrimary}>
      {/* Custom Header */}
      <StyledView className="flex-row items-center px-3 py-3 border-b border-borderSubtle bg-backgroundSecondary">
        <StyledTouchableOpacity onPress={() => navigation.goBack()} className="p-1 mr-2">
          <MaterialIcons name="chevron-left" size={28} color={colors.accentPrimary} />
        </StyledTouchableOpacity>
        <StyledText variant="h3" tw="font-semibold flex-1 text-center" numberOfLines={1} ellipsizeMode="tail">
          {document.original_filename || 'Document Details'}
        </StyledText>
        <StyledView className="w-8" /> {/* Spacer to balance back button */}
      </StyledView>

      <StyledScrollView className="flex-1" refreshControl={<RefreshControl refreshing={isLoading} onRefresh={loadDocumentData} />}>
        <StyledView className="p-4">
          <Card title="Document Information" tw="mb-6">
            {documentInfoItems.map((item, index) => (
              item.value && (
                <ListItem
                  key={item.label}
                  label={item.label}
                  value={item.value}
                  iconLeft={item.icon}
                  iconLeftColor={colors.textSecondary}
                  showBottomBorder={index < documentInfoItems.filter(i => i.value).length - 1}
                />
              )
            ))}
          </Card>

          {/* View Original Document Card */}
          <Card title="Original Document" tw="mb-6">
            <ListItem 
              label={document.original_filename || 'Document'}
              subtitle={`Uploaded ${new Date(document.upload_timestamp).toLocaleDateString()}`}
              iconLeft="document"
              iconLeftColor={colors.accentPrimary}
              onPress={() => {
                Alert.alert(
                  'Document Viewer', 
                  'Document viewing functionality is coming soon! For now, you can see the extracted data below.',
                  [{ text: 'OK' }]
                );
              }}
            />
          </Card>

          <Card title="Extracted Data" tw="mb-6">
            {extractedData ? (
              <StyledView>
                {extractedData.content ? (
                  <StyledView>
                    {/* Handle the case where content is an array of medical events */}
                    {Array.isArray(extractedData.content) ? (
                      <StyledView>
                        {/* Group medical events by type */}
                        {extractedData.content.filter((event: any) => event.event_type === 'Medication').length > 0 && (
                          <StyledView className="mb-4">
                            <StyledText variant="h4" tw="font-semibold mb-3 text-textPrimary">Medications</StyledText>
                            {extractedData.content
                              .filter((event: any) => event.event_type === 'Medication')
                              .map((med: any, index: number) => (
                                <ListItem
                                  key={index}
                                  label={med.description || `Medication ${index + 1}`}
                                  subtitle={`${med.value || ''} ${med.units || ''}`.trim()}
                                  iconLeft="medkit"
                                  iconLeftColor={colors.dataColor5}
                                  showBottomBorder={index < extractedData.content.filter((e: any) => e.event_type === 'Medication').length - 1}
                                />
                              ))}
                          </StyledView>
                        )}

                        {/* Lab Results - look for any numeric medical values */}
                        {extractedData.content.filter((event: any) => 
                          event.event_type === 'LabResult' || 
                          (event.value && event.units && event.event_type !== 'Medication')
                        ).length > 0 && (
                          <StyledView className="mb-4">
                            <StyledText variant="h4" tw="font-semibold mb-3 text-textPrimary">Lab Results</StyledText>
                            {extractedData.content
                              .filter((event: any) => 
                                event.event_type === 'LabResult' || 
                                (event.value && event.units && event.event_type !== 'Medication')
                              )
                              .map((result: any, index: number) => (
                                <ListItem
                                  key={index}
                                  label={result.description || result.test_name || 'Lab Test'}
                                  value={`${result.value || ''} ${result.units || ''}`.trim()}
                                  showBottomBorder={index < extractedData.content.filter((e: any) => 
                                    e.event_type === 'LabResult' || 
                                    (e.value && e.units && e.event_type !== 'Medication')
                                  ).length - 1}
                                />
                              ))}
                          </StyledView>
                        )}

                        {/* Diagnoses */}
                        {extractedData.content.filter((event: any) => event.event_type === 'Diagnosis').length > 0 && (
                          <StyledView className="mb-4">
                            <StyledText variant="h4" tw="font-semibold mb-3 text-textPrimary">Diagnoses</StyledText>
                            {extractedData.content
                              .filter((event: any) => event.event_type === 'Diagnosis')
                              .map((diagnosis: any, index: number) => (
                                <ListItem
                                  key={index}
                                  label={diagnosis.description}
                                  iconLeft="medical"
                                  iconLeftColor={colors.dataColor3}
                                  showBottomBorder={index < extractedData.content.filter((e: any) => e.event_type === 'Diagnosis').length - 1}
                                />
                              ))}
                          </StyledView>
                        )}

                        {/* Instructions/Notes */}
                        {extractedData.content.filter((event: any) => 
                          event.event_type === 'PatientInstruction' || 
                          event.event_type === 'Note'
                        ).length > 0 && (
                          <StyledView className="mb-4">
                            <StyledText variant="h4" tw="font-semibold mb-3 text-textPrimary">Notes</StyledText>
                            <StyledText variant="body1" color="textSecondary">
                              {extractedData.content
                                .filter((event: any) => 
                                  event.event_type === 'PatientInstruction' || 
                                  event.event_type === 'Note'
                                )
                                .map((note: any) => note.description)
                                .join('. ')}
                            </StyledText>
                          </StyledView>
                        )}
                      </StyledView>
                    ) : (
                      /* Handle dictionary structure if it exists */
                      <StyledView>
                        {extractedData.content.lab_results && (
                          <StyledView className="mb-4">
                            <StyledText variant="h4" tw="font-semibold mb-3 text-textPrimary">Lab Results</StyledText>
                            {Object.entries(extractedData.content.lab_results).map(([key, value], index) => (
                              <ListItem
                                key={key}
                                label={key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                                value={String(value)}
                                showBottomBorder={index < Object.entries(extractedData.content.lab_results).length - 1}
                              />
                            ))}
                          </StyledView>
                        )}

                        {extractedData.content.medications && (
                          <StyledView className="mb-4">
                            <StyledText variant="h4" tw="font-semibold mb-3 text-textPrimary">Medications</StyledText>
                            {Array.isArray(extractedData.content.medications) ? 
                              extractedData.content.medications.map((med: any, index: number) => (
                                <ListItem
                                  key={index}
                                  label={med.name || `Medication ${index + 1}`}
                                  subtitle={`${med.dosage || ''} ${med.frequency || ''}`.trim()}
                                  iconLeft="medkit"
                                  iconLeftColor={colors.dataColor5}
                                  showBottomBorder={index < extractedData.content.medications.length - 1}
                                />
                              )) : null
                            }
                          </StyledView>
                        )}

                        {extractedData.content.notes && (
                          <StyledView className="mb-4">
                            <StyledText variant="h4" tw="font-semibold mb-3 text-textPrimary">Notes</StyledText>
                            <StyledText variant="body1" color="textSecondary">
                              {extractedData.content.notes}
                            </StyledText>
                          </StyledView>
                        )}
                      </StyledView>
                    )}
                  </StyledView>
                ) : (
                  <StyledText color="textMuted" tw="py-4 text-center">
                    No structured content extracted yet.
                  </StyledText>
                )}
              </StyledView>
            ) : (
              <StyledText color="textMuted" tw="py-4 text-center">
                {document.processing_status === ProcessingStatus.PENDING ? 
                  'Document is being processed. Extracted data will appear here once processing is complete.' :
                  'No extracted data available yet.'
                }
              </StyledText>
            )}

            <StyledButton 
              variant="filledPrimary" 
              tw="mt-4"
              onPress={() => navigation.navigate('DataReview', { documentId })}
              iconNameLeft="checkmark-circle"
            >
              <StyledText>Review & Correct Data</StyledText>
            </StyledButton>
          </Card>
        </StyledView>
      </StyledScrollView>

      {/* Image Viewer Modal */}
      {documentType === 'image' && imageUriForModal && (
        <Modal
          animationType="fade"
          transparent={true}
          visible={showImageViewer}
          onRequestClose={closeImageViewer}
        >
          <StyledView className="flex-1 justify-center items-center bg-black/80">
            <StyledPressable className="absolute top-10 right-5 z-10 p-2" onPress={closeImageViewer}>
              <MaterialIcons name="close" size={32} color="white" />
            </StyledPressable>
            <Image 
              source={{ uri: imageUriForModal }}
              style={{ width: '90%', height: '80%'}}
              resizeMode="contain"
            />
          </StyledView>
        </Modal>
      )}
    </ScreenContainer>
  );
};

export default DocumentDetailScreen; 