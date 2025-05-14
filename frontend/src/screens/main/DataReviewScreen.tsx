import React, { useState, useEffect } from 'react';
import { ScrollView, View, TouchableOpacity, Alert, Platform } from 'react-native';
import { styled } from 'nativewind';
import { useNavigation, useRoute, RouteProp } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { MainAppStackParamList } from '../../navigation/types';
import Ionicons from 'react-native-vector-icons/Ionicons';

import ScreenContainer from '../../components/layout/ScreenContainer';
import StyledText from '../../components/common/StyledText';
import StyledButton from '../../components/common/StyledButton';
import StyledInput from '../../components/common/StyledInput';
import Card from '../../components/common/Card';
import { useTheme } from '../../theme';

// Assuming a similar MockDocument structure as in DocumentDetailScreen for now
// In a real app, this would come from a shared types definition
interface ExtractedField {
  label: string;
  value: string | number | null;
  unit?: string;
}
interface MedicationContent {
    name: ExtractedField;
    dosage: ExtractedField;
    frequency: ExtractedField;
    // Add any other medication-specific fields that are extractable/editable
}
interface MockExtractedContent {
  lab_results?: ExtractedField[];
  medications?: MedicationContent[];
  notes?: string;
}
interface MockReviewDocument {
  id: string;
  name: string;
  type: string; // e.g. 'Prescription', 'Lab Result'
  extractedContent: MockExtractedContent | null;
}

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

  const [document, setDocument] = useState<MockReviewDocument | null>(null);
  const [editedData, setEditedData] = useState<MockExtractedContent | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    setIsLoading(true);
    setTimeout(() => {
      const mockDoc: MockReviewDocument = {
        id: documentId,
        name: documentId.includes('lab') ? `Lab Report - Blood Panel` : `Prescription - Dr. Smith`, 
        type: documentId.includes('lab') ? 'Lab Result' : 'Prescription',
        extractedContent: {
          medications: documentId.includes('lab') ? [] : [
            { 
              name: { label: 'Medication Name', value: 'Amoxicillin' }, 
              dosage: { label: 'Dosage', value: '250', unit: 'mg' }, 
              frequency: { label: 'Frequency', value: 'Twice a day' } 
            },
            { 
              name: { label: 'Medication Name', value: 'Ibuprofen' }, 
              dosage: { label: 'Dosage', value: '200', unit: 'mg' }, 
              frequency: { label: 'Frequency', value: 'As needed for pain' } 
            },
          ],
          lab_results: documentId.includes('lab') ? [
            { label: 'Hemoglobin', value: '14.5', unit: 'g/dL' }, // Store values as strings for inputs
            { label: 'WBC Count', value: '7.2', unit: 'x10^9/L' },
            { label: 'Platelets', value: '250', unit: 'x10^9/L' },
          ] : [],
          notes: documentId.includes('lab') ? 'All results within normal limits.' : 'Take Amoxicillin with food. Finish the entire course. Avoid alcohol with Ibuprofen if taken regularly.'
        }
      };
      setDocument(mockDoc);
      setEditedData(mockDoc.extractedContent ? JSON.parse(JSON.stringify(mockDoc.extractedContent)) : null);
      setIsLoading(false);
    }, 300);
  }, [documentId]);

  const handleInputChange = (
    section: 'medications' | 'lab_results' | 'notes',
    index: number | null, 
    fieldKey: string, 
    subFieldKeyOrValueType: 'value' | 'unit' | null,
    text: string
  ) => {
    setEditedData(prevData => {
      if (!prevData) return null;
      const newData = JSON.parse(JSON.stringify(prevData)) as MockExtractedContent;

      if (section === 'medications' && newData.medications && typeof index === 'number') {
        const medication = newData.medications[index];
        if (medication && medication[fieldKey as keyof MedicationContent] && subFieldKeyOrValueType) {
          (medication[fieldKey as keyof MedicationContent] as ExtractedField)[subFieldKeyOrValueType] = text;
        }
      } else if (section === 'lab_results' && newData.lab_results && typeof index === 'number') {
        const labResultItem = newData.lab_results[index];
        if (labResultItem) {
          if (fieldKey === 'value') {
            labResultItem.value = text;
          } else if (fieldKey === 'unit') {
            labResultItem.unit = text;
          }
        }
      } else if (section === 'notes' && fieldKey === 'notesText') {
        newData.notes = text;
      }
      return newData;
    });
  };
  
  const handleSave = () => {
    console.log("Saving corrected data:", editedData);
    Alert.alert("Data Saved", "Your corrections have been saved.", [{ text: "OK", onPress: () => navigation.goBack() }]);
  };

  if (isLoading) {
    return <ScreenContainer><StyledView className="flex-1 justify-center items-center"><StyledText>Loading review data...</StyledText></StyledView></ScreenContainer>;
  }

  if (!document || !editedData) {
    return <ScreenContainer><StyledView className="flex-1 justify-center items-center"><StyledText>Could not load document data.</StyledText></StyledView></ScreenContainer>;
  }

  const renderMedicationInputs = (med: MedicationContent, medIndex: number) => {
    return (
      <Card key={`med-${medIndex}`} title={`Medication: ${editedData?.medications?.[medIndex]?.name.value || med.name.value || 'Unnamed'}`} tw="mb-4">
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
          <Ionicons name="chevron-back-outline" size={28} color={colors.accentPrimary} />
        </StyledTouchableOpacity>
        <StyledText variant="h3" tw="font-semibold flex-1 text-center" numberOfLines={1} ellipsizeMode="tail">
          Review: {document.name}
        </StyledText>
        <StyledView className="w-8" /> 
      </StyledView>

      <StyledScrollView className="flex-1" contentContainerStyle={{ padding: 16 }}>
        {editedData.medications && editedData.medications.length > 0 && (
          editedData.medications.map((med, index) => renderMedicationInputs(med, index))
        )}

        {editedData.lab_results && editedData.lab_results.length > 0 && (
            <Card title="Lab Results" tw="mb-4">
                {editedData.lab_results.map((labField, labIndex) => (
                    <StyledView key={`lab-${labIndex}-${labField.label}`} className="mb-3">
                        <StyledText variant="label" color="textSecondary" tw="mb-1">{labField.label}</StyledText>
                        <StyledView className="flex-row items-center">
                            <StyledInput
                                value={String(labField.value || '')}
                                onChangeText={(text) => handleInputChange('lab_results', labIndex, 'value', null, text)}
                                tw="flex-2 mr-2"
                                keyboardType="numeric"
                                placeholder={`Value for ${labField.label}`}
                            />
                            <StyledInput
                                value={String(labField.unit || '')}
                                onChangeText={(text) => handleInputChange('lab_results', labIndex, 'unit', null, text)}
                                tw="flex-1"
                                placeholder={`Unit`}
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
            <StyledButton variant="textDestructive" onPress={() => navigation.goBack()} tw="flex-1 mr-2">
                Discard Changes
            </StyledButton>
            <StyledButton variant="filledPrimary" onPress={handleSave} tw="flex-1 ml-2">
                Save Corrections
            </StyledButton>
        </StyledView>
      </StyledScrollView>
    </ScreenContainer>
  );
};

export default DataReviewScreen; 