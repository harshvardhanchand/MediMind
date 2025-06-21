import React, { useState, useEffect } from 'react';
import { ScrollView, View, TouchableOpacity, Alert, RefreshControl, ActivityIndicator } from 'react-native';
import { styled } from 'nativewind';
import { useNavigation, useRoute, RouteProp } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import MaterialIcons from 'react-native-vector-icons/MaterialIcons';

import { MainAppStackParamList } from '../../navigation/types';
import ScreenContainer from '../../components/layout/ScreenContainer';
import StyledText from '../../components/common/StyledText';
import StyledButton from '../../components/common/StyledButton';
import StyledInput from '../../components/common/StyledInput';
import Card from '../../components/common/Card';
import EmptyState from '../../components/common/EmptyState';
import ErrorState from '../../components/common/ErrorState';
import { useTheme } from '../../theme';
import {ExtractedDataResponse } from '../../types/api';
import { documentServices, extractedDataServices } from '../../api/services';
import {  LOADING_MESSAGES} from '../../constants/messages';
import { 
  ExtractedField, 
  MedicationContent, 
  FormattedExtractedContent, 
  ReviewDocument, 
  ChangedField 
} from '../../types/interfaces';

const StyledView = styled(View);
const StyledScrollView = styled(ScrollView);
const StyledTouchableOpacity = styled(TouchableOpacity);

type DataReviewScreenNavigationProp = NativeStackNavigationProp<MainAppStackParamList, 'DataReview'>;
type DataReviewScreenRouteProp = RouteProp<MainAppStackParamList, 'DataReview'>;

const DataReviewScreen = () => {
  const navigation = useNavigation<DataReviewScreenNavigationProp>();
  const route = useRoute<DataReviewScreenRouteProp>();
  const { colors } = useTheme();
  const { documentId } = route.params;

  const [document, setDocument] = useState<ReviewDocument | null>(null);
  const [extractedData, setExtractedData] = useState<ExtractedDataResponse | null>(null);
  const [editedData, setEditedData] = useState<FormattedExtractedContent | null>(null);
  const [originalData, setOriginalData] = useState<FormattedExtractedContent | null>(null);
  const [changedFields, setChangedFields] = useState<ChangedField[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadDocumentData();
  }, [documentId]);

  const loadDocumentData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      // Fetch document details
      const documentResponse = await documentServices.getDocumentById(documentId);
      const docData = documentResponse.data;

      // Fetch extracted data
      const extractedResponse = await extractedDataServices.getExtractedData(documentId);
      const extractedData = extractedResponse.data;
      setExtractedData(extractedData);

      // Convert extracted data to form-friendly format
      const formattedContent = convertToFormFormat(extractedData);

      const reviewDoc: ReviewDocument = {
        id: documentId,
        name: docData.original_filename || 'Document',
        type: docData.document_type || 'Unknown',
        extractedContent: formattedContent
      };

      setDocument(reviewDoc);
      setEditedData(formattedContent ? JSON.parse(JSON.stringify(formattedContent)) : null);
      setOriginalData(formattedContent ? JSON.parse(JSON.stringify(formattedContent)) : null);
    } catch (err: any) {
      console.error('Failed to load document data:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to load document data');
    } finally {
      setIsLoading(false);
    }
  };

  // Convert the array-based extracted data to form-friendly structure
  const convertToFormFormat = (extractedData: ExtractedDataResponse): FormattedExtractedContent | null => {
    if (!extractedData.content || !Array.isArray(extractedData.content)) {
      return null;
    }

    const medications: MedicationContent[] = [];
    const lab_results: ExtractedField[] = [];
    const notesList: string[] = [];

    extractedData.content.forEach((event: any) => {
      if (event.event_type === 'Medication') {
        medications.push({
          name: { label: 'Medication Name', value: event.description || '' },
          dosage: { label: 'Dosage', value: event.value || '', unit: event.units || 'mg' },
          frequency: { label: 'Frequency', value: event.frequency || 'As needed' }
        });
      } else if (event.event_type === 'LabResult' || (event.value && event.units && event.event_type !== 'Medication')) {
        lab_results.push({
          label: event.description || event.test_name || 'Lab Test',
          value: event.value || '',
          unit: event.units || ''
        });
      } else if (event.event_type === 'PatientInstruction' || event.event_type === 'Note') {
        notesList.push(event.description);
      }
    });

    return {
      medications: medications.length > 0 ? medications : undefined,
      lab_results: lab_results.length > 0 ? lab_results : undefined,
      notes: notesList.length > 0 ? notesList.join('. ') : undefined
    };
  };

  const handleInputChange = (
    section: 'medications' | 'lab_results' | 'notes',
    index: number | null, 
    fieldKey: string, 
    subFieldKeyOrValueType: 'value' | 'unit' | null,
    text: string
  ) => {
    setEditedData(prevData => {
      if (!prevData) return null;
      const newData = JSON.parse(JSON.stringify(prevData)) as FormattedExtractedContent;

      // Get the old value for change tracking
      let oldValue: any;
      let fieldPath: string;

      if (section === 'medications' && newData.medications && typeof index === 'number') {
        const medication = newData.medications[index];
        if (medication && medication[fieldKey as keyof MedicationContent] && subFieldKeyOrValueType) {
          oldValue = (medication[fieldKey as keyof MedicationContent] as ExtractedField)[subFieldKeyOrValueType];
          (medication[fieldKey as keyof MedicationContent] as ExtractedField)[subFieldKeyOrValueType] = text;
          fieldPath = `medications[${index}].${fieldKey}.${subFieldKeyOrValueType}`;
        }
      } else if (section === 'lab_results' && newData.lab_results && typeof index === 'number') {
        const labResultItem = newData.lab_results[index];
        if (labResultItem) {
          if (fieldKey === 'value') {
            oldValue = labResultItem.value;
            labResultItem.value = text;
            fieldPath = `lab_results[${index}].value`;
          } else if (fieldKey === 'unit') {
            oldValue = labResultItem.unit;
            labResultItem.unit = text;
            fieldPath = `lab_results[${index}].unit`;
          }
        }
      } else if (section === 'notes' && fieldKey === 'notesText') {
        oldValue = newData.notes;
        newData.notes = text;
        fieldPath = 'notes';
      }

      // Track the change if the value actually changed
      if (oldValue !== text && originalData) {
        setChangedFields(prevChanges => {
          // Remove existing change for this field path
          const filteredChanges = prevChanges.filter(change => {
            if (section === 'medications' && change.section === 'medications' && change.index === index && change.field === `${fieldKey}.${subFieldKeyOrValueType}`) {
              return false;
            }
            if (section === 'lab_results' && change.section === 'lab_results' && change.index === index && change.field === fieldKey) {
              return false;
            }
            if (section === 'notes' && change.section === 'notes' && change.field === fieldKey) {
              return false;
            }
            return true;
          });

          // Add new change record
          const newChange: ChangedField = {
            section,
            index: typeof index === 'number' ? index : undefined,
            field: subFieldKeyOrValueType ? `${fieldKey}.${subFieldKeyOrValueType}` : fieldKey,
            oldValue,
            newValue: text,
            context: generateContextForField(section, index, fieldKey, newData)
          };

          return [...filteredChanges, newChange];
        });
      }

      return newData;
    });
  };

  // Generate context for AI processing
  const generateContextForField = (
    section: 'medications' | 'lab_results' | 'notes',
    index: number | null,
    fieldKey: string,
    data: FormattedExtractedContent
  ): string => {
    if (section === 'medications' && typeof index === 'number' && data.medications?.[index]) {
      const med = data.medications[index];
      return `Medication: ${med.name.value} ${med.dosage.value}${med.dosage.unit} ${med.frequency.value}`;
    }
    
    if (section === 'lab_results' && typeof index === 'number' && data.lab_results?.[index]) {
      const lab = data.lab_results[index];
      return `Lab Result: ${lab.label} ${lab.value} ${lab.unit}`;
    }
    
    if (section === 'notes') {
      return `Patient Instructions: ${data.notes || ''}`;
    }
    
    return '';
  };
  
  const handleSave = async () => {
    if (!editedData || !extractedData) {
      Alert.alert("Error", "No data available to save.");
      return;
    }

    try {
      setIsSaving(true);

      // Convert the form data back to the API format (array of medical events)
      const apiContent = convertFromFormFormat(editedData);

      // Update the extracted data content with selective reprocessing information
      await extractedDataServices.updateExtractedDataContent(documentId, {
        content: apiContent,
        changed_fields: changedFields, // Include changed fields for selective reprocessing
        trigger_selective_reprocessing: changedFields.length > 0 // Only trigger if there are changes
      });

      Alert.alert(
        "Success", 
        changedFields.length > 0 
          ? "Your corrections have been saved and selective AI reprocessing has started for changed fields." 
          : "Your corrections have been saved and the review status has been updated.", 
        [{ text: "OK", onPress: () => navigation.goBack() }]
      );
    } catch (err: any) {
      console.error('Failed to save corrections:', err);
      Alert.alert(
        "Error", 
        err.response?.data?.detail || err.message || "Failed to save corrections. Please try again."
      );
    } finally {
      setIsSaving(false);
    }
  };

  // Convert form-friendly format back to API format (array of medical events)
  const convertFromFormFormat = (formData: FormattedExtractedContent): any[] => {
    const events: any[] = [];

    // Add medications
    if (formData.medications) {
      formData.medications.forEach(med => {
        events.push({
          event_type: 'Medication',
          description: med.name.value,
          value: med.dosage.value,
          units: med.dosage.unit,
          frequency: med.frequency.value
        });
      });
    }

    // Add lab results
    if (formData.lab_results) {
      formData.lab_results.forEach(lab => {
        events.push({
          event_type: 'LabResult',
          description: lab.label,
          value: lab.value,
          units: lab.unit
        });
      });
    }

    // Add notes
    if (formData.notes) {
      events.push({
        event_type: 'PatientInstruction',
        description: formData.notes
      });
    }

    return events;
  };

  if (isLoading) {
    return (
      <ScreenContainer>
        <StyledView className="flex-1 justify-center items-center">
          <ActivityIndicator size="large" color={colors.accentPrimary} />
          <StyledText 
            variant="body1" 
            tw="mt-4 text-center"
            style={{ color: colors.textSecondary }}
          >
            {LOADING_MESSAGES.LOADING_DOCUMENTS}
          </StyledText>
        </StyledView>
      </ScreenContainer>
    );
  }

  if (error) {
    return (
      <ScreenContainer>
        <ErrorState
          title="Unable to Load Review Data"
          message={error}
          onRetry={loadDocumentData}
          retryLabel="Try Again"
          icon="document-text-outline"
        />
      </ScreenContainer>
    );
  }

  if (!document || !editedData) {
    return (
      <ScreenContainer>
        <EmptyState
          icon="document-text-outline"
          title="No Data to Review"
          description="No extracted data is available for review. The document may not have been processed yet."
          actionLabel="Go Back"
          onAction={() => navigation.goBack()}
        />
      </ScreenContainer>
    );
  }

  const renderMedicationInputs = (med: MedicationContent, medIndex: number) => {
    const medicationName = String(editedData?.medications?.[medIndex]?.name.value || med.name.value || 'Unnamed');
    return (
      <Card key={`med-${medIndex}`} title={`Medication: ${medicationName}`} tw="mb-4">
        <StyledInput
          label={med.name.label}
          value={String(editedData?.medications?.[medIndex]?.name.value || '')}
          onChangeText={(text) => handleInputChange('medications', medIndex, 'name', 'value', text)}
          tw="mb-3"
        />
        <StyledView className="flex-row mb-3">
            <StyledInput
                label={med.dosage.label}
                value={String(editedData?.medications?.[medIndex]?.dosage.value || '')}
                onChangeText={(text) => handleInputChange('medications', medIndex, 'dosage', 'value', text)}
                tw="flex-1 mr-2"
                keyboardType="numeric"
            />
            <StyledInput
                label="Unit"
                value={String(editedData?.medications?.[medIndex]?.dosage.unit || '')}
                onChangeText={(text) => handleInputChange('medications', medIndex, 'dosage', 'unit', text)}
                tw="w-1/3"
            />
        </StyledView>
        <StyledInput
          label={med.frequency.label}
          value={String(editedData?.medications?.[medIndex]?.frequency.value || '')}
          onChangeText={(text) => handleInputChange('medications', medIndex, 'frequency', 'value', text)}
          tw="mb-1"
        />
      </Card>
    );
  };

  return (
    <ScreenContainer scrollable={false} withPadding={false} backgroundColor={colors.backgroundPrimary}>
      {/* Custom Header */}
      <StyledView className="flex-row items-center px-3 py-3 border-b border-borderSubtle bg-backgroundSecondary">
        <StyledTouchableOpacity onPress={() => navigation.goBack()} className="p-1 mr-2">
          <MaterialIcons name="chevron-left" size={28} color={colors.accentPrimary} />
        </StyledTouchableOpacity>
        <StyledText variant="h3" tw="font-semibold flex-1 text-center" numberOfLines={1} ellipsizeMode="tail">
          Review: {String(document?.name || 'Document')}
        </StyledText>
        <StyledView className="w-8" /> 
      </StyledView>

      <StyledScrollView 
        className="flex-1" 
        contentContainerStyle={{ padding: 16 }}
        refreshControl={
          <RefreshControl 
            refreshing={isLoading} 
            onRefresh={loadDocumentData} 
            tintColor={colors.accentPrimary}
          />
        }
      >
        {editedData.medications && editedData.medications.length > 0 && (
          editedData.medications.map((med, index) => renderMedicationInputs(med, index))
        )}

        {editedData.lab_results && editedData.lab_results.length > 0 && (
            <Card title="Lab Results" tw="mb-4">
                {editedData.lab_results.map((labField, labIndex) => (
                    <StyledView key={`lab-${labIndex}-${String(labField.label || 'lab')}`} className="mb-3">
                        <StyledText variant="label" color="textSecondary" tw="mb-1">{String(labField.label || 'Lab Test')}</StyledText>
                        <StyledView className="flex-row items-center">
                            <StyledInput
                                value={String(labField.value || '')}
                                onChangeText={(text) => handleInputChange('lab_results', labIndex, 'value', null, text)}
                                tw="flex-2 mr-2"
                                keyboardType="numeric"
                                placeholder={`Value for ${String(labField.label || 'test')}`}
                            />
                            <StyledInput
                                value={String(labField.unit || '')}
                                onChangeText={(text) => handleInputChange('lab_results', labIndex, 'unit', null, text)}
                                tw="flex-1"
                                placeholder="Unit"
                            />
                        </StyledView>
                    </StyledView>
                ))}
            </Card>
        )}

        {editedData.notes !== undefined && (
          <Card title="General Notes" tw="mb-4">
            <StyledInput
              label="Notes"
              value={editedData.notes || ''}
              onChangeText={(text) => handleInputChange('notes', null, 'notesText', 'value', text)} 
              multiline
              inputStyle={{ height: 120, textAlignVertical: 'top' }}
              tw="h-auto"
            />
          </Card>
        )}
        
        <StyledView className="mt-6 flex-row justify-between">
            <StyledButton variant="textDestructive" onPress={() => navigation.goBack()} tw="flex-1 mr-2" disabled={isSaving}>
                <StyledText>Discard Changes</StyledText>
            </StyledButton>
            <StyledButton 
              variant="filledPrimary" 
              onPress={handleSave} 
              tw="flex-1 ml-2"
              disabled={isSaving}
              loading={isSaving}
            >
                {isSaving ? 'Saving...' : 'Save Corrections'}
            </StyledButton>
        </StyledView>
      </StyledScrollView>
    </ScreenContainer>
  );
};

export default DataReviewScreen; 