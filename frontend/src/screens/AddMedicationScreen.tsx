import React, { useState, useEffect } from 'react';
import { View, StyleSheet, ScrollView, Alert, ActivityIndicator } from 'react-native';
import {
  Appbar, Button, TextInput, Title, Paragraph, HelperText, 
  Card, Divider, Switch, Text, ActivityIndicator as PaperActivityIndicator
} from 'react-native-paper';
import { useNavigation, useRoute, RouteProp } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';

import { MainAppStackParamList } from '../navigation/types';
import { medicationServices } from '../api/services';
import { MedicationCreate, MedicationUpdate, MedicationResponse, MedicationFrequency, MedicationStatus } from '../types/api';
import ErrorState from '../components/common/ErrorState';
import { ERROR_MESSAGES, SUCCESS_MESSAGES, LOADING_MESSAGES } from '../constants/messages';

import { MedicationDetailData } from './main/MedicationDetailScreen';

type AddMedicationNavigationProp = NativeStackNavigationProp<MainAppStackParamList, 'AddMedication'>;
type AddMedicationRouteProp = RouteProp<MainAppStackParamList, 'AddMedication'>;

const AddMedicationScreen = () => {
  const navigation = useNavigation<AddMedicationNavigationProp>();
  const route = useRoute<AddMedicationRouteProp>();
  
  const medicationIdToEdit = route.params?.medicationIdToEdit;
  const initialData = route.params?.initialData;
  const isEditMode = !!medicationIdToEdit;

  // Form fields - align more closely with MedicationBase/MedicationResponse where possible
  const [name, setName] = useState(initialData?.name || '');
  const [dosage, setDosage] = useState(initialData?.dosage || '');
  // For frequency, we'll simplify for now and use initialData.frequency (string) for display,
  // but API needs MedicationFrequency enum. This will be improved with a picker.
  const [frequencyDisplay, setFrequencyDisplay] = useState(initialData?.frequency || ''); 
  const [frequencyEnum, setFrequencyEnum] = useState<MedicationFrequency>(MedicationFrequency.ONCE_DAILY); // Default or from initialData if mappable
  const [frequencyDetails, setFrequencyDetails] = useState(''); // For custom text alongside enum

  const [reason, setReason] = useState(initialData?.reason || ''); // Use initialData.reason
  const [notes, setNotes] = useState(initialData?.notes || '');
  const [prescribingDoctor, setPrescribingDoctor] = useState(initialData?.prescribingDoctor || '');
  const [startDate, setStartDate] = useState(initialData?.startDate || '');
  const [endDate, setEndDate] = useState(initialData?.endDate || '');
  const [status, setStatus] = useState<MedicationStatus>(MedicationStatus.ACTIVE);
  const [withFood, setWithFood] = useState(false); // Add more from MedicationBase as needed

  // Reminder settings - keeping UI but not integrating with API payload for now
  const [reminderEnabled, setReminderEnabled] = useState(true);
  const [reminderTime, setReminderTime] = useState('9:00 AM');
  
  const [loading, setLoading] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [criticalError, setCriticalError] = useState<string | null>(null);
  
  // Validation states
  const [nameError, setNameError] = useState('');
  const [dosageError, setDosageError] = useState('');

  useEffect(() => {
    if (isEditMode && initialData) {
      setName(initialData.name || '');
      setDosage(initialData.dosage || '');
      setFrequencyDisplay(initialData.frequency || '');
      setReason(initialData.reason || ''); // Use initialData.reason
      setNotes(initialData.notes || '');
      setPrescribingDoctor(initialData.prescribingDoctor || '');
      setStartDate(initialData.startDate || '');
      setEndDate(initialData.endDate || '');
      // TODO: Properly map status and with_food if richer initialData (MedicationResponse) is passed directly
      // For now, MedicationDetailData is simpler. If initialData were MedicationResponse:
      // if (initialData.status) setStatus(initialData.status);
      // if (initialData.with_food !== undefined) setWithFood(initialData.with_food);
    }
    navigation.setOptions({ title: isEditMode ? 'Edit Medication' : 'Add Medication' });
  }, [isEditMode, initialData, navigation]);
  
  const validateForm = () => {
    let isValid = true;
    setFormError(null);
    if (!name.trim()) { setNameError(ERROR_MESSAGES.REQUIRED_FIELD); isValid = false; } else { setNameError(''); }
    if (!dosage.trim()) { setDosageError(ERROR_MESSAGES.REQUIRED_FIELD); isValid = false; } else { setDosageError(''); }
    // TODO: Add validation for other fields like frequency enum, dates etc.
    return isValid;
  };
  
  const handleSubmit = async () => {
    if (!validateForm()) {
      setFormError(ERROR_MESSAGES.FORM_VALIDATION_ERROR);
      return;
    }
    setLoading(true);
    setFormError(null);
    setCriticalError(null);

    const commonPayload = {
      name: name.trim(),
      dosage: dosage.trim(),
      frequency: frequencyEnum, // Use the enum value
      frequency_details: frequencyDisplay.trim() !== formatFrequencyEnum(frequencyEnum) ? frequencyDisplay.trim() : null, // Store details if different from plain enum text
      reason: reason.trim(),
      notes: notes.trim(),
      prescribing_doctor: prescribingDoctor.trim(),
      start_date: startDate.trim() || null,
      end_date: endDate.trim() || null,
      status: status,
      with_food: withFood, 
      // time_of_day: ... needs dedicated input
    };

    try {
      if (isEditMode && medicationIdToEdit) {
        const payload: MedicationUpdate = commonPayload;
        await medicationServices.updateMedication(medicationIdToEdit, payload);
        Alert.alert('Success', SUCCESS_MESSAGES.MEDICATION_UPDATED, [{ text: 'OK', onPress: () => navigation.goBack() }]);
      } else {
        const payload: MedicationCreate = commonPayload;
        await medicationServices.addMedication(payload);
        Alert.alert('Success', SUCCESS_MESSAGES.MEDICATION_ADDED, [{ text: 'OK', onPress: () => navigation.goBack() }]);
      }
    } catch (err: any) {
      console.error("Failed to save medication:", err);
      const errorMessage = err.response?.data?.detail || err.message || ERROR_MESSAGES.MEDICATION_SAVE_ERROR;
      setFormError(errorMessage);
      Alert.alert("Error", errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const retryOperation = () => {
    setCriticalError(null);
    setFormError(null);
    // Reset form to initial state if needed
  };

  // Helper to format enum for display (can be moved to utils)
  const formatFrequencyEnum = (freq: MedicationFrequency) => {
    return freq.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
  }

  // ✅ Render critical error state using standardized ErrorState component
  if (criticalError) {
    return (
      <View style={styles.container}>
        <Appbar.Header>
          <Appbar.BackAction onPress={() => navigation.goBack()} />
          <Appbar.Content title={isEditMode ? 'Edit Medication' : 'Add New Medication'} />
        </Appbar.Header>
        <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', padding: 16 }}>
          <ErrorState
            title="Unable to Load Medication Form"
            message={criticalError}
            onRetry={retryOperation}
            retryLabel="Try Again"
            icon="medical-outline"
          />
        </View>
      </View>
    );
  }
  
  // TODO: Replace Frequency TextInput with a Picker/Menu for MedicationFrequency enum
  // TODO: Add TextInput for Start Date, End Date (or DatePickers)
  // TODO: Add Switch for With Food

  return (
    <View style={styles.container}>
      <Appbar.Header>
        <Appbar.BackAction onPress={() => navigation.goBack()} />
        <Appbar.Content title={isEditMode ? 'Edit Medication' : 'Add New Medication'} />
      </Appbar.Header>
      
      <ScrollView style={styles.scrollView} contentContainerStyle={styles.scrollContent}>
        {/* <Title style={styles.title}>{isEditMode ? 'Edit Medication' : 'Add New Medication'}</Title> */}
        <Paragraph style={styles.subtitle}>
          {isEditMode ? 'Update the details of your medication.' : 'Enter the details of your new medication.'}
        </Paragraph>

        {formError && <Text style={styles.formErrorText}>{formError}</Text>}
        
        <Card style={styles.card}>
          <Card.Content>
            <Text style={styles.sectionTitle}>Medication Details</Text>
            
            <TextInput label="Medication Name*" value={name} onChangeText={setName} mode="outlined" style={styles.input} error={!!nameError} disabled={loading} />
            {!!nameError && <HelperText type="error">{nameError}</HelperText>}
            
            <TextInput label="Dosage*" value={dosage} onChangeText={setDosage} mode="outlined" placeholder="e.g., 10mg" style={styles.input} error={!!dosageError} disabled={loading} />
            {!!dosageError && <HelperText type="error">{dosageError}</HelperText>}
            
            {/* Placeholder for Frequency Picker - current TextInput is for frequencyDisplay */}
            <TextInput label="Frequency Description (e.g., Once daily with breakfast)" value={frequencyDisplay} onChangeText={setFrequencyDisplay} mode="outlined" placeholder="e.g., Once daily, or specific details" style={styles.input} disabled={loading} />
            {/* TODO: Add Picker here for setFrequencyEnum, mapping to MedicationFrequency enum values */}
            {/* Example: <Picker selectedValue={frequencyEnum} onValueChange={(itemValue) => setFrequencyEnum(itemValue)}> */}
            {/* Object.values(MedicationFrequency).map(f => <Picker.Item key={f} label={formatFrequencyEnum(f)} value={f} />) </Picker> */}
            
            <TextInput label="Reason/Purpose" value={reason} onChangeText={setReason} mode="outlined" placeholder="e.g., Blood pressure management" style={styles.input} disabled={loading} />
            <TextInput label="Instructions/Notes" value={notes} onChangeText={setNotes} mode="outlined" placeholder="e.g., Take with water before meals" multiline numberOfLines={3} style={styles.input} disabled={loading} />
            <TextInput label="Prescriber" value={prescribingDoctor} onChangeText={setPrescribingDoctor} mode="outlined" placeholder="e.g., Dr. Smith" style={styles.input} disabled={loading} />
            <TextInput label="Start Date (YYYY-MM-DD)" value={startDate} onChangeText={setStartDate} mode="outlined" placeholder="Optional" style={styles.input} disabled={loading} />
            <TextInput label="End Date (YYYY-MM-DD)" value={endDate} onChangeText={setEndDate} mode="outlined" placeholder="Optional" style={styles.input} disabled={loading} />
            
            {/* TODO: Add Picker for Status */}
            {/* Example: <Picker selectedValue={status} onValueChange={(itemValue) => setStatus(itemValue)}> */}
            {/* Object.values(MedicationStatus).map(s => <Picker.Item key={s} label={s.replace('_',' ')} value={s} />) </Picker> */}

            <View style={styles.switchContainer}>
              <Text>Take with food?</Text>
              <Switch value={withFood} onValueChange={setWithFood} disabled={loading} />
            </View>

          </Card.Content>
        </Card>
        
        {/* Reminder settings section - kept for UI, not in API payload for now */}
        <Card style={styles.card}>
          <Card.Content>
            <Text style={styles.sectionTitle}>Reminder Settings (UI Only)</Text>
            <View style={styles.switchContainer}>
              <Text>Enable Reminders</Text>
              <Switch value={reminderEnabled} onValueChange={setReminderEnabled} disabled={loading} />
            </View>
            {reminderEnabled && (
              <TextInput label="Reminder Time" value={reminderTime} onChangeText={setReminderTime} mode="outlined" placeholder="9:00 AM" style={styles.input} disabled={loading} />
            )}
          </Card.Content>
        </Card>
        
        <View style={styles.buttonContainer}>
          <Button mode="outlined" onPress={() => navigation.goBack()} style={styles.cancelButton} disabled={loading}>Cancel</Button>
          <Button mode="contained" onPress={handleSubmit} style={styles.submitButton} loading={loading} disabled={loading}>
            {isEditMode ? 'Update Medication' : 'Save Medication'}
          </Button>
        </View>
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F7FA',
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: 16,
    paddingBottom: 40,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#2A6BAC',
    marginTop: 8,
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 16,
    color: '#666',
    marginBottom: 16,
  },
  card: {
    marginBottom: 16,
    borderRadius: 12,
    elevation: 3,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 16,
  },
  input: {
    marginBottom: 14,
  },
  switchContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginVertical: 8,
  },
  buttonContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 16,
  },
  cancelButton: {
    flex: 1,
    marginRight: 8,
  },
  submitButton: {
    flex: 2,
  },
  formErrorText: {
    color: 'red', // or theme.colors.error
    textAlign: 'center',
    marginBottom: 10,
  }
});

export default AddMedicationScreen; 