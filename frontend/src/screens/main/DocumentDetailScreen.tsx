import React, { useLayoutEffect, useState, useEffect } from 'react';
import { ScrollView, View, TouchableOpacity, Alert, Dimensions, Platform, ActivityIndicator, Image, Modal, Pressable, RefreshControl } from 'react-native';
import { styled } from 'nativewind';
import { useNavigation, useRoute, RouteProp, useFocusEffect } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { MaterialIcons } from '@expo/vector-icons';
import Pdf from 'react-native-pdf';


import { MainAppStackParamList } from '../../navigation/types';
import ScreenContainer from '../../components/layout/ScreenContainer';
import StyledText from '../../components/common/StyledText';
import StyledButton from '../../components/common/StyledButton';
import Card from '../../components/common/Card';
import ListItem from '../../components/common/ListItem';
import ErrorState from '../../components/common/ErrorState';
import { useTheme } from '../../theme';
import { DocumentRead, ExtractedDataResponse, ProcessingStatus } from '../../types/api';
import { documentServices, extractedDataServices } from '../../api/services';
import { ERROR_MESSAGES, LOADING_MESSAGES } from '../../constants/messages';

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

  const handleDeleteDocument = async () => {
    Alert.alert(
      'Delete Document',
      'Are you sure you want to delete this document? This action cannot be undone.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            setIsLoading(true);
            try {
              await documentServices.deleteDocument(documentId);
              Alert.alert('Success', 'Document deleted successfully.');
              navigation.goBack();
            } catch (err: any) {
              console.error('Error deleting document:', err);
              Alert.alert('Error', err.response?.data?.detail || err.message || 'Failed to delete document.');
            } finally {
              setIsLoading(false);
            }
          }
        },
      ]
    );
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
          <StyledView className="flex-row">
            <StyledTouchableOpacity
              onPress={() => alert(`TODO: Edit ${document.original_filename}`)}
              className="p-1.5"
            >
              <StyledText style={{ color: colors.accentPrimary, fontSize: 17 }}>Edit</StyledText>
            </StyledTouchableOpacity>
            <StyledTouchableOpacity
              onPress={handleDeleteDocument}
              className="p-1.5"
            >
              <StyledText style={{ color: colors.error, fontSize: 17 }}>Delete</StyledText>
            </StyledTouchableOpacity>
          </StyledView>
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

  if (error || !document) {
    return (
      <ScreenContainer>
        <ErrorState
          title="Unable to Load Document"
          message={error || ERROR_MESSAGES.DOCUMENTS_LOAD_ERROR}
          onRetry={loadDocumentData}
          retryLabel="Try Again"
          icon="document-text-outline"
        />
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

  const documentType = getDocumentType(document);
  const documentViewUrl = getDocumentViewUrl(document);

  return (
    <ScreenContainer scrollable={false} withPadding={false} backgroundColor={colors.backgroundPrimary}>
      {/* Custom Header */}
      <StyledView className="flex-row items-center px-3 py-3 border-b border-borderSubtle bg-backgroundSecondary">
        <StyledTouchableOpacity onPress={() => navigation.goBack()} className="p-1 mr-2">
          <MaterialIcons name="chevron-left" size={28} color={colors.accentPrimary} />
        </StyledTouchableOpacity>
        <StyledText variant="h3" className="font-semibold flex-1 text-center" numberOfLines={1} ellipsizeMode="tail">
          {document.original_filename || 'Document Details'}
        </StyledText>
        <StyledTouchableOpacity
          onPress={handleDeleteDocument}
          className="p-1 ml-2"
        >
          <MaterialIcons name="delete" size={24} color={colors.error} />
        </StyledTouchableOpacity>
      </StyledView>

      <StyledScrollView className="flex-1" refreshControl={<RefreshControl refreshing={isLoading} onRefresh={loadDocumentData} />}>
        <StyledView className="p-4">
          <Card title="Document Information" className="mb-6">
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
          <Card title="Original Document" className="mb-6">
            <ListItem
              label={document.original_filename || 'Document'}
              subtitle={`Uploaded ${new Date(document.upload_timestamp).toLocaleDateString()}`}
              iconLeft="document"
              iconLeftColor={colors.accentPrimary}
              onPress={() => {
                if (documentType === 'pdf') {
                  setShowPdfViewer(!showPdfViewer);
                } else if (documentType === 'image') {
                  openImageViewer(documentViewUrl);
                } else {
                  Alert.alert(
                    'Document Type Not Supported',
                    'Only PDF and image files are currently supported for viewing.',
                    [{ text: 'OK' }]
                  );
                }
              }}
            />

            {/* PDF Viewer */}
            {showPdfViewer && documentType === 'pdf' && (
              <StyledView className="mt-4 h-96 bg-backgroundSecondary rounded-lg overflow-hidden">
                <StyledView className="flex-row justify-between items-center p-3 border-b border-borderSubtle">
                  <StyledText variant="h4" className="font-semibold">PDF Viewer</StyledText>
                  <StyledTouchableOpacity onPress={() => setShowPdfViewer(false)}>
                    <MaterialIcons name="close" size={24} color={colors.textSecondary} />
                  </StyledTouchableOpacity>
                </StyledView>

                {isLoadingPdf && (
                  <StyledView className="absolute inset-0 justify-center items-center bg-backgroundPrimary/80 z-10">
                    <ActivityIndicator size="large" color={colors.accentPrimary} />
                    <StyledText className="mt-2" color="textSecondary">Loading PDF...</StyledText>
                  </StyledView>
                )}

                {pdfError ? (
                  <StyledView className="flex-1 justify-center items-center p-4">
                    <MaterialIcons name="error-outline" size={48} color={colors.error} />
                    <StyledText className="mt-2 text-center" color="error">{pdfError}</StyledText>
                    <StyledButton
                      variant="filledPrimary"
                      className="mt-4"
                      onPress={() => {
                        setPdfError(null);
                        setIsLoadingPdf(true);
                      }}
                    >
                      <StyledText>Retry</StyledText>
                    </StyledButton>
                  </StyledView>
                ) : (
                  <Pdf
                    source={{ uri: documentViewUrl, cache: true }}
                    onLoadProgress={(percent) => {
                      console.log(`PDF Loading: ${Math.round(percent * 100)}%`);
                    }}
                    onLoadComplete={(numberOfPages, filePath) => {
                      console.log(`PDF loaded with ${numberOfPages} pages`);
                      setIsLoadingPdf(false);
                      setPdfError(null);
                    }}
                    onPageChanged={(page, numberOfPages) => {
                      console.log(`Current page: ${page} of ${numberOfPages}`);
                    }}
                    onError={(error) => {
                      console.error('PDF Error:', error);
                      setIsLoadingPdf(false);
                      setPdfError('Failed to load PDF document');
                    }}
                    onPressLink={(uri) => {
                      console.log('PDF Link pressed:', uri);
                    }}
                    style={{
                      flex: 1,
                      width: Dimensions.get('window').width - 40,
                      backgroundColor: colors.backgroundSecondary,
                    }}
                    enablePaging={true}
                    enableRTL={false}
                    enableAnnotationRendering={true}
                    enableAntialiasing={true}
                    enableDoubleTapZoom={true}
                    minScale={1.0}
                    maxScale={3.0}
                    spacing={10}
                    horizontal={false}
                    showsHorizontalScrollIndicator={false}
                    showsVerticalScrollIndicator={true}
                    trustAllCerts={false}
                  />
                )}
              </StyledView>
            )}
          </Card>

          <Card title="Extracted Data" className="mb-6">
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
                            <StyledText variant="h4" className="font-semibold mb-3 text-textPrimary">Medications</StyledText>
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
                              <StyledText variant="h4" className="font-semibold mb-3 text-textPrimary">Lab Results</StyledText>
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
                            <StyledText variant="h4" className="font-semibold mb-3 text-textPrimary">Diagnoses</StyledText>
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
                              <StyledText variant="h4" className="font-semibold mb-3 text-textPrimary">Notes</StyledText>
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
                            <StyledText variant="h4" className="font-semibold mb-3 text-textPrimary">Lab Results</StyledText>
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
                            <StyledText variant="h4" className="font-semibold mb-3 text-textPrimary">Medications</StyledText>
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
                            <StyledText variant="h4" className="font-semibold mb-3 text-textPrimary">Notes</StyledText>
                            <StyledText variant="body1" color="textSecondary">
                              {extractedData.content.notes}
                            </StyledText>
                          </StyledView>
                        )}
                      </StyledView>
                    )}
                  </StyledView>
                ) : (
                  <StyledText color="textMuted" className="py-4 text-center">
                    No structured content extracted yet.
                  </StyledText>
                )}
              </StyledView>
            ) : (
              <StyledText color="textMuted" className="py-4 text-center">
                {document.processing_status === ProcessingStatus.PENDING ?
                  'Document is being processed. Extracted data will appear here once processing is complete.' :
                  'No extracted data available yet.'
                }
              </StyledText>
            )}

            <StyledButton
              variant="filledPrimary"
              className="mt-4"
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
              style={{ width: '90%', height: '80%' }}
              resizeMode="contain"
            />
          </StyledView>
        </Modal>
      )}
    </ScreenContainer>
  );
};

export default DocumentDetailScreen; 