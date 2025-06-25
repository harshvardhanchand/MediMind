import React, { useState, useLayoutEffect } from 'react';
import { ScrollView, View, TouchableOpacity, Alert } from 'react-native';
import { styled } from 'nativewind';
import { useNavigation, useRoute, RouteProp } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';

import ScreenContainer from '../../components/layout/ScreenContainer';
import StyledText from '../../components/common/StyledText';
import StyledInput from '../../components/common/StyledInput';
import Card from '../../components/common/Card'; // For grouping form elements if needed
import { MainAppStackParamList } from '../../navigation/types'; 
import { useTheme } from '../../theme';
import { MedicationFormData } from '../../types/interfaces';

const StyledView = styled(View);
const StyledScrollView = styled(ScrollView);
const StyledTouchableOpacity = styled(TouchableOpacity);

// Update navigation and route prop types for AddMedication route
type AddMedicationScreenNavigationProp = NativeStackNavigationProp<MainAppStackParamList, 'AddMedication'>; 
// Define route prop to accept optional params for editing
type AddMedicationScreenRouteProp = RouteProp<MainAppStackParamList, 'AddMedication'>;

const AddMedicationScreen = () => {
  const navigation = useNavigation<AddMedicationScreenNavigationProp>();
  const route = useRoute<AddMedicationScreenRouteProp>();
  const { colors } = useTheme();

  const medicationToEdit = route.params?.initialData;
  const medicationIdToEdit = route.params?.medicationIdToEdit;
  const isEditMode = !!(medicationToEdit || medicationIdToEdit);
  
  const [formData, setFormData] = useState<MedicationFormData>(() => {
    if (medicationToEdit) {
      return {
        id: medicationIdToEdit || medicationToEdit.id, // Ensure ID is included if available
        name: medicationToEdit.name || '',
        dosageValue: medicationToEdit.dosage?.replace(/[^0-9.]/g, '') || '', // Extract numeric part
        dosageUnit: medicationToEdit.dosage?.replace(/[0-9.]/g, '') || '', // Extract unit part
        frequency: medicationToEdit.frequency || '',
        prescribingDoctor: medicationToEdit.prescribingDoctor || '',
        startDate: medicationToEdit.startDate || '',
        endDate: medicationToEdit.endDate || '',
        notes: medicationToEdit.notes || '',
      };
    }
    return {
      name: '',
      dosageValue: '',
      dosageUnit: '',
      frequency: '',
      prescribingDoctor: '',
      startDate: '',
      endDate: '',
      notes: '',
    };
  });

  // TODO: If only medicationIdToEdit is passed, fetch data in useEffect
  // useEffect(() => {
  //   if (medicationIdToEdit && !medicationToEdit) {
  //     // Fetch medication data by ID and setFormData
  //     console.log("Fetching medication data for ID:", medicationIdToEdit);
  //   }
  // }, [medicationIdToEdit, medicationToEdit]);

  const handleInputChange = (field: keyof MedicationFormData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleSaveOrUpdate = () => {
    if (!formData.name.trim() || !formData.dosageValue.trim() || !formData.dosageUnit.trim()) {
      Alert.alert("Missing Information", "Please fill in at least Name, Dosage, and Unit.");
      return;
    }

    if (isEditMode) {
      console.log("Updating Medication:", formData.id, formData);
      // TODO: Implement API call to update medication
      Alert.alert("Medication Updated", "Changes have been saved.", [
        { text: "OK", onPress: () => navigation.goBack() } // Or navigate to detail screen
      ]);
    } else {
      console.log("Saving New Medication:", formData);
      // TODO: Implement API call to save new medication
      Alert.alert("Medication Added", "New medication has been added successfully.", [
        { text: "OK", onPress: () => navigation.goBack() }
      ]);
    }
  };

  useLayoutEffect(() => {
    navigation.setOptions({
      headerTitle: isEditMode ? 'Edit Medication' : 'Add New Medication',
      headerLeft: () => (
        <StyledTouchableOpacity onPress={() => navigation.goBack()} className="ml-[-8px] p-1.5">
          <StyledText style={{ color: colors.accentPrimary, fontSize: 17 }}>Cancel</StyledText>
        </StyledTouchableOpacity>
      ),
      headerRight: () => (
        <StyledTouchableOpacity onPress={handleSaveOrUpdate} className="p-1.5">
          <StyledText style={{ color: colors.accentPrimary, fontSize: 17, fontWeight: '600' }}>
            {isEditMode ? 'Update' : 'Save'}
          </StyledText>
        </StyledTouchableOpacity>
      ),
      headerStyle: { backgroundColor: colors.backgroundSecondary },
      headerTitleStyle: { color: colors.textPrimary },
    });
  }, [navigation, colors, formData, isEditMode, handleSaveOrUpdate]);

  return (
    // Using backgroundTertiary for iOS-like grouped form feel
    <ScreenContainer scrollable={false} withPadding={false} backgroundColor={colors.backgroundTertiary}>
      <StyledScrollView 
        className="flex-1"
        contentContainerStyle={{ paddingVertical: 16, paddingHorizontal: 0 }} // No horizontal padding for full-width cards
        keyboardShouldPersistTaps="handled"
      >
        <Card className="mx-4 mb-5" noPadding> 
          <StyledInput
            variant="formListItem"
            label="Medication Name"
            value={formData.name}
            onChangeText={(text) => handleInputChange('name', text)}
            placeholder="e.g., Amoxicillin, Ibuprofen"
          />
          <StyledView className="flex-row items-center border-b border-borderSubtle px-4">
            <StyledInput
              variant="formListItem"
              label="Dosage"
              value={formData.dosageValue}
              onChangeText={(text) => handleInputChange('dosageValue', text)}
              placeholder="e.g., 250"
              keyboardType="numeric"
              className="flex-2 py-3.5 pr-2"
              showBottomBorder={false}
            />
            <StyledInput
              variant="formListItem"
              label="Unit"
              value={formData.dosageUnit}
              onChangeText={(text) => handleInputChange('dosageUnit', text)}
              placeholder="e.g., mg, mL"
              className="flex-1 py-3.5 pl-2"
              showBottomBorder={false}
            />
          </StyledView>
          <StyledInput
            variant="formListItem"
            label="Frequency"
            value={formData.frequency}
            onChangeText={(text) => handleInputChange('frequency', text)}
            placeholder="e.g., Twice a day, As needed"
          />
        </Card>

        <Card className="mx-4 mb-5" noPadding>
          <StyledInput
            variant="formListItem"
            label="Prescribing Doctor (Optional)"
            value={formData.prescribingDoctor}
            onChangeText={(text) => handleInputChange('prescribingDoctor', text)}
            placeholder="e.g., Dr. Anya Sharma"
          />
          <StyledInput 
            variant="formListItem"
            label="Start Date (Optional)"
            value={formData.startDate}
            onChangeText={(text) => handleInputChange('startDate', text)}
            placeholder="YYYY-MM-DD"
          />
          <StyledInput 
            variant="formListItem"
            label="End Date (Optional)"
            value={formData.endDate}
            onChangeText={(text) => handleInputChange('endDate', text)}
            placeholder="YYYY-MM-DD"
            showBottomBorder={false}
          />
        </Card>

        <Card className="mx-4 mb-5" noPadding>
          <StyledInput
            variant="formListItem"
            label="Notes (Optional)"
            value={formData.notes}
            onChangeText={(text) => handleInputChange('notes', text)}
            placeholder="e.g., Take with food, For headache only"
            multiline
            inputStyle={{ height: 100, textAlignVertical: 'top' }}
            showBottomBorder={false}
          />
        </Card>
      </StyledScrollView>
    </ScreenContainer>
  );
};

export default AddMedicationScreen; 