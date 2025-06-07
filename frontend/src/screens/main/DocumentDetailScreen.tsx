import React, { useLayoutEffect, useState } from 'react';
import { ScrollView, View, TouchableOpacity, Alert, Dimensions, Platform, ActivityIndicator, Image, Modal, Pressable } from 'react-native';
import { styled } from 'nativewind';
import { useNavigation, useRoute, RouteProp } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { MainAppStackParamList } from '../../navigation/types';
import { MaterialIcons } from '@expo/vector-icons';
import { WebView } from 'react-native-webview';

import ScreenContainer from '../../components/layout/ScreenContainer';
import StyledText from '../../components/common/StyledText';
import StyledButton from '../../components/common/StyledButton';
import Card from '../../components/common/Card';
import ListItem from '../../components/common/ListItem';
import { useTheme } from '../../theme';

const StyledView = styled(View);
const StyledScrollView = styled(ScrollView);
const StyledTouchableOpacity = styled(TouchableOpacity);
const StyledPressable = styled(Pressable);

type DocumentDetailScreenNavigationProp = NativeStackNavigationProp<MainAppStackParamList, 'DocumentDetail'>;
type DocumentDetailScreenRouteProp = RouteProp<MainAppStackParamList, 'DocumentDetail'>;

// Mock Document Data Structure (more detailed for display)
interface ExtractedField {
  label: string;
  value: string | number | null;
  unit?: string;
}

interface MockDocument {
  id: string;
  name: string;
  type: string;
  date: string;
  originalFilename?: string;
  processingStatus?: string; // e.g., 'Pending Review', 'Reviewed'
  extractedContent?: {
    // Example for a lab report
    lab_results?: ExtractedField[];
    // Example for a prescription
    medications?: Array<{
      name: ExtractedField;
      dosage: ExtractedField;
      frequency: ExtractedField;
    }>;
    notes?: string;
  };
  // Placeholder for actual document URI
  documentUri?: string; 
  documentType?: 'pdf' | 'image' | 'other'; // To determine viewer
}

const DocumentDetailScreen = () => {
  const navigation = useNavigation<DocumentDetailScreenNavigationProp>();
  const route = useRoute<DocumentDetailScreenRouteProp>();
  const { colors } = useTheme();
  const { documentId } = route.params;

  const [isLoadingPdf, setIsLoadingPdf] = useState(false);
  const [pdfError, setPdfError] = useState<string | null>(null);
  const [showPdfViewer, setShowPdfViewer] = useState(false);
  const [showImageViewer, setShowImageViewer] = useState(false);
  const [imageUriForModal, setImageUriForModal] = useState<string | undefined>(undefined);

  // Mock data - conditionally make one an image for testing
  const isImageDoc = documentId.includes('img'); // Simple way to toggle mock data type for testing
  const document: MockDocument = {
    id: documentId,
    name: isImageDoc ? 'Chest X-Ray Image' : `Lab Report - CBC`, 
    type: isImageDoc ? 'Imaging Result' : 'Lab Result',
    date: '2023-10-18',
    originalFilename: isImageDoc ? 'xray_chest.jpg' : 'lab_report_oct18.pdf',
    processingStatus: 'Reviewed',
    extractedContent: {
      lab_results: [
        { label: 'White Blood Cells', value: 7.2, unit: 'K/μL' },
        { label: 'Red Blood Cells', value: 4.5, unit: 'M/μL' },
        { label: 'Hemoglobin', value: 14.1, unit: 'g/dL' },
        { label: 'Hematocrit', value: 42.3, unit: '%' },
      ],
      notes: 'All values within normal range. Continue current treatment.'
    },
    documentUri: isImageDoc 
      ? 'https://images.unsplash.com/photo-1581091226809-50038c009EMW?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=60' // Placeholder image
      : 'https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf', 
    documentType: isImageDoc ? 'image' : 'pdf',
  };

  const { width } = Dimensions.get('window');

  useLayoutEffect(() => {
    if (document) {
      navigation.setOptions({
        headerTitle: document.name, 
        headerRight: () => (
          <StyledTouchableOpacity 
            onPress={() => alert(`TODO: Edit ${document.name}`)}
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

  if (!document) {
    return (
      <ScreenContainer>
        <StyledView className="flex-1 justify-center items-center">
          <StyledText>Document not found.</StyledText>
        </StyledView>
      </ScreenContainer>
    );
  }

  const documentInfoItems = [
    { label: 'Type', value: document.type, icon: 'document-text-outline' },
    { label: 'Date', value: document.date, icon: 'calendar-outline' },
    { label: 'Status', value: document.processingStatus, icon: 'information-circle-outline' },
    { label: 'Original File', value: document.originalFilename, icon: 'attach-outline' },
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

  return (
    <ScreenContainer scrollable={false} withPadding={false} backgroundColor={colors.backgroundPrimary}>
      {/* Custom Header */}
      <StyledView className="flex-row items-center px-3 py-3 border-b border-borderSubtle bg-backgroundSecondary">
        <StyledTouchableOpacity onPress={() => navigation.goBack()} className="p-1 mr-2">
          <MaterialIcons name="chevron-left" size={28} color={colors.accentPrimary} />
        </StyledTouchableOpacity>
        <StyledText variant="h3" tw="font-semibold flex-1 text-center" numberOfLines={1} ellipsizeMode="tail">
          {document.name}
        </StyledText>
        <StyledView className="w-8" /> {/* Spacer to balance back button */}
      </StyledView>

      <StyledScrollView className="flex-1">
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
          {document.documentUri && (
            <Card title="Original Document" tw="mb-6">
              {document.documentType === 'pdf' && (
                <>
                  <ListItem 
                    label={showPdfViewer ? 'Hide Document' : (document.originalFilename || 'View PDF')}
                    iconLeft={showPdfViewer ? 'visibility-off' : 'visibility'}
                    iconLeftColor={colors.accentPrimary}
                    onPress={togglePdfViewer}
                  />
                  {showPdfViewer && (
                    <StyledView className="mt-3 h-96 border border-borderSubtle rounded-md overflow-hidden">
                      {isLoadingPdf && (
                        <View style={{ position: 'absolute', top: '50%', left: '50%', transform: [{translateX: -15}, {translateY: -15}], zIndex: 1 }}>
                          <ActivityIndicator size="large" color={colors.accentPrimary} />
                        </View>
                      )}
                      {pdfError && (
                        <StyledText color="accentDestructive" tw="p-4 text-center">
                          Error loading PDF: {pdfError}
                        </StyledText>
                      )}
                      {document.documentUri && (
                        <WebView
                          source={{ uri: getPDFViewerUrl(document.documentUri) }}
                          style={{ flex: 1 }}
                          onLoadStart={() => setIsLoadingPdf(true)}
                          onLoadEnd={handlePdfLoadEnd}
                          onError={handlePdfError}
                          scalesPageToFit={true}
                          showsVerticalScrollIndicator={true}
                          javaScriptEnabled={true}
                          domStorageEnabled={true}
                          mixedContentMode="compatibility"
                        />
                      )}
                    </StyledView>
                  )}
                </>
              )}
              {document.documentType === 'image' && (
                <ListItem 
                  label={document.originalFilename || 'View Image'}
                  iconLeft="image"
                  iconLeftColor={colors.accentPrimary}
                  onPress={() => document.documentUri && openImageViewer(document.documentUri)}
                />
              )}
            </Card>
          )}

          <Card title="Extracted Data" tw="mb-6">
            {/* Medications Section */}
            {document.extractedContent?.medications && document.extractedContent.medications.length > 0 && (
              <StyledView className="mb-3">
                <StyledText variant="h4" tw="font-semibold mb-2 text-textPrimary">Medications</StyledText>
                {document.extractedContent.medications.map((med, index) => (
                  <ListItem
                    key={index}
                    label={`${med.name.value}`}
                    subtitle={`${med.dosage.value}${med.dosage.unit || ''} - ${med.frequency.value}`}
                    iconLeft="medication"
                    iconLeftColor={colors.dataColor5}
                    showBottomBorder={index < document.extractedContent!.medications!.length - 1}
                  />
                ))}
              </StyledView>
            )}

            {/* Lab Results Section */}
            {document.extractedContent?.lab_results && document.extractedContent.lab_results.length > 0 && (
              <StyledView className="mb-3">
                <StyledText variant="h4" tw="font-semibold mb-2 text-textPrimary">Lab Results</StyledText>
                {document.extractedContent.lab_results.map((field, index) => (
                  <ListItem
                    key={field.label}
                    label={field.label}
                    value={`${field.value} ${field.unit || ''}`}
                    showBottomBorder={index < document.extractedContent!.lab_results!.length - 1}
                  />
                ))}
              </StyledView>
            )}
            
            {/* Notes Section */}
            {document.extractedContent?.notes && (
              <StyledView className="mt-2">
                <StyledText variant="h4" tw="font-semibold mb-1 text-textPrimary">Notes</StyledText>
                <StyledText variant="body1" color="textSecondary">{document.extractedContent.notes}</StyledText>
              </StyledView>
            )}

            {/* Fallback if no content sections rendered */}
            {!(document.extractedContent?.medications && document.extractedContent.medications.length > 0) &&
             !(document.extractedContent?.lab_results && document.extractedContent.lab_results.length > 0) &&
             !document.extractedContent?.notes && (
                <StyledText color="textMuted" tw="py-3 text-center">No specific data extracted or pending extraction.</StyledText>
            )}

            <StyledButton 
              variant="filledPrimary" 
              tw="mt-4"
              onPress={() => navigation.navigate('DataReview', { documentId })}
              iconNameLeft="check-circle"
            >
              Review & Correct Data
            </StyledButton>
          </Card>
        </StyledView>
      </StyledScrollView>

      {/* Image Viewer Modal */}
      {document.documentType === 'image' && imageUriForModal && (
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