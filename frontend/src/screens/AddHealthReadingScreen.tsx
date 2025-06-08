import React, { useState, useEffect } from 'react';
import { View, StyleSheet, ScrollView, Alert } from 'react-native';
import {
  Appbar, Button, TextInput, Title, Paragraph, HelperText, 
  Card, Divider, Switch, Text, RadioButton, ActivityIndicator
} from 'react-native-paper';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';

import { RootStackParamList } from '../navigation/types';
import { HealthReadingCreate, HealthReadingType } from '../types/api';
import { healthReadingsServices } from '../api/services';

type AddHealthReadingNavigationProp = NativeStackNavigationProp<RootStackParamList, 'AddHealthReading'>;

// Supported reading types for this screen (subset of HealthReadingType enum)
const supportedReadingTypes = [
  { label: 'Blood Pressure', value: HealthReadingType.BLOOD_PRESSURE },
  { label: 'Blood Glucose', value: HealthReadingType.GLUCOSE },
  { label: 'Heart Rate', value: HealthReadingType.HEART_RATE },
  // Add more here if UI supports them
];

const AddHealthReadingScreen = () => {
  const navigation = useNavigation<AddHealthReadingNavigationProp>();
  
  const [readingType, setReadingType] = useState<HealthReadingType>(HealthReadingType.BLOOD_PRESSURE);
  const [systolic, setSystolic] = useState('');
  const [diastolic, setDiastolic] = useState('');
  const [glucose, setGlucose] = useState('');
  const [heartRate, setHeartRate] = useState('');
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]); // YYYY-MM-DD
  const [time, setTime] = useState(new Date().toLocaleTimeString('en-GB', { hour: '2-digit', minute:'2-digit' })); // HH:MM
  const [notes, setNotes] = useState('');
  
  const [loading, setLoading] = useState(false);
  const [formError, setFormError] = useState<string | null>(null); // For general form errors

  // Specific field errors
  const [systolicError, setSystolicError] = useState('');
  const [diastolicError, setDiastolicError] = useState('');
  const [glucoseError, setGlucoseError] = useState('');
  const [heartRateError, setHeartRateError] = useState('');
  const [dateTimeError, setDateTimeError] = useState('');

  useEffect(() => {
    // Reset specific fields when readingType changes to avoid submitting stale data
    setSystolic(''); setSystolicError('');
    setDiastolic(''); setDiastolicError('');
    setGlucose('');  setGlucoseError('');
    setHeartRate(''); setHeartRateError('');
  }, [readingType]);
  
  const validateForm = () => {
    let isValid = true;
    setSystolicError(''); setDiastolicError(''); setGlucoseError(''); setHeartRateError(''); setDateTimeError(''); setFormError(null);

    if (readingType === HealthReadingType.BLOOD_PRESSURE) {
      if (!systolic.trim()) { setSystolicError('Systolic value is required'); isValid = false; }
      else { const val = parseInt(systolic); if (isNaN(val) || val < 50 || val > 300) { setSystolicError('Range: 50-300'); isValid = false; }}
      if (!diastolic.trim()) { setDiastolicError('Diastolic value is required'); isValid = false; }
      else { const val = parseInt(diastolic); if (isNaN(val) || val < 30 || val > 200) { setDiastolicError('Range: 30-200'); isValid = false; }}
    } else if (readingType === HealthReadingType.GLUCOSE) {
      if (!glucose.trim()) { setGlucoseError('Glucose value is required'); isValid = false; }
      else { const val = parseInt(glucose); if (isNaN(val) || val < 20 || val > 600) { setGlucoseError('Range: 20-600'); isValid = false; }}
    } else if (readingType === HealthReadingType.HEART_RATE) {
      if (!heartRate.trim()) { setHeartRateError('Heart rate is required'); isValid = false; }
      else { const val = parseInt(heartRate); if (isNaN(val) || val < 30 || val > 250) { setHeartRateError('Range: 30-250'); isValid = false; }}
    }
    // Validate date and time format (basic check)
    if (!/^\d{4}-\d{2}-\d{2}$/.test(date) || !/^\d{2}:\d{2}$/.test(time)) {
        setDateTimeError('Invalid date or time format.');
        isValid = false;
    }
    return isValid;
  };
  
  const handleSubmit = async () => {
    if (!validateForm()) {
        setFormError('Please check the form for errors.');
        return;
    }
    setLoading(true);
    setFormError(null);

    // Combine date and time into an ISO string for reading_date
    let reading_date_iso = '';
    try {
        reading_date_iso = new Date(`${date}T${time}:00`).toISOString();
    } catch (e) {
        setDateTimeError('Invalid date/time combination.');
        setLoading(false);
        return;
    }

    const payload: HealthReadingCreate = {
      reading_type: readingType,
      reading_date: reading_date_iso,
      notes: notes.trim() || null,
      source: 'manual_entry', // Default source
      // Values and units based on readingType
      ...(readingType === HealthReadingType.BLOOD_PRESSURE && {
        systolic_value: parseInt(systolic),
        diastolic_value: parseInt(diastolic),
        unit: 'mmHg',
      }),
      ...(readingType === HealthReadingType.GLUCOSE && {
        numeric_value: parseInt(glucose),
        unit: 'mg/dL',
      }),
      ...(readingType === HealthReadingType.HEART_RATE && {
        numeric_value: parseInt(heartRate),
        unit: 'bpm',
      }),
    };

    try {
      await healthReadingsServices.addHealthReading(payload);
      Alert.alert('Success', 'Health reading saved successfully!', [{ text: 'OK', onPress: () => navigation.goBack() }]);
    } catch (err: any) {
      console.error("Failed to save health reading:", err);
      setFormError(err.response?.data?.detail || err.message || 'Failed to save reading.');
      Alert.alert("Error", err.response?.data?.detail || err.message || 'Failed to save reading.');
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <View style={styles.container}>
      <Appbar.Header>
        <Appbar.BackAction onPress={() => navigation.goBack()} />
        <Appbar.Content title="Add Health Reading" />
      </Appbar.Header>
      
      <ScrollView style={styles.scrollView} contentContainerStyle={styles.scrollContent}>
        <Title style={styles.title}>Log New Health Reading</Title>
        <Paragraph style={styles.subtitle}>
          Select the type and enter your measurement.
        </Paragraph>

        {formError && <Text style={styles.formErrorText}>{formError}</Text>}
        
        <Card style={styles.card}>
          <Card.Content>
            <Text style={styles.sectionTitle}>Reading Type</Text>
            <RadioButton.Group
              onValueChange={(value) => setReadingType(value as HealthReadingType)} // Cast to HealthReadingType
              value={readingType}
            >
              {supportedReadingTypes.map(typeInfo => (
                <RadioButton.Item key={typeInfo.value} label={typeInfo.label} value={typeInfo.value} disabled={loading} />
              ))}
            </RadioButton.Group>
          </Card.Content>
        </Card>
        
        <Card style={styles.card}>
          <Card.Content>
            <Text style={styles.sectionTitle}>Reading Details</Text>
            
            {readingType === HealthReadingType.BLOOD_PRESSURE && (
              <>
                <TextInput label="Systolic (mmHg)" value={systolic} onChangeText={setSystolic} mode="outlined" keyboardType="number-pad" style={styles.input} error={!!systolicError} disabled={loading} />
                {!!systolicError && <HelperText type="error">{systolicError}</HelperText>}
                <TextInput label="Diastolic (mmHg)" value={diastolic} onChangeText={setDiastolic} mode="outlined" keyboardType="number-pad" style={styles.input} error={!!diastolicError} disabled={loading} />
                {!!diastolicError && <HelperText type="error">{diastolicError}</HelperText>}
              </>
            )}
            
            {readingType === HealthReadingType.GLUCOSE && (
              <>
                <TextInput label="Blood Glucose (mg/dL)" value={glucose} onChangeText={setGlucose} mode="outlined" keyboardType="number-pad" style={styles.input} error={!!glucoseError} disabled={loading} />
                {!!glucoseError && <HelperText type="error">{glucoseError}</HelperText>}
              </>
            )}
            
            {readingType === HealthReadingType.HEART_RATE && (
              <>
                <TextInput label="Heart Rate (bpm)" value={heartRate} onChangeText={setHeartRate} mode="outlined" keyboardType="number-pad" style={styles.input} error={!!heartRateError} disabled={loading} />
                {!!heartRateError && <HelperText type="error">{heartRateError}</HelperText>}
              </>
            )}
            
            <TextInput label="Date (YYYY-MM-DD)" value={date} onChangeText={setDate} mode="outlined" style={styles.input} disabled={loading} error={!!dateTimeError} />
            <TextInput label="Time (HH:MM)" value={time} onChangeText={setTime} mode="outlined" style={styles.input} disabled={loading} error={!!dateTimeError} />
            {!!dateTimeError && <HelperText type="error">{dateTimeError}</HelperText>}
            
            <TextInput label="Notes (Optional)" value={notes} onChangeText={setNotes} mode="outlined" multiline numberOfLines={3} style={styles.input} disabled={loading} />
          </Card.Content>
        </Card>
        
        <View style={styles.buttonContainer}>
          <Button mode="outlined" onPress={() => navigation.goBack()} style={styles.cancelButton} disabled={loading}>Cancel</Button>
          <Button mode="contained" onPress={handleSubmit} style={styles.submitButton} loading={loading} disabled={loading}>
            Save Reading
          </Button>
        </View>
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F5F7FA' },
  scrollView: { flex: 1 },
  scrollContent: { padding: 16, paddingBottom: 40 },
  title: { fontSize: 24, fontWeight: 'bold', color: '#2A6BAC', marginTop: 8, marginBottom: 4 },
  subtitle: { fontSize: 16, color: '#666', marginBottom: 16 },
  card: { marginBottom: 16, borderRadius: 12, elevation: 3 },
  sectionTitle: { fontSize: 18, fontWeight: 'bold', marginBottom: 16 },
  input: { marginBottom: 12 },
  buttonContainer: { flexDirection: 'row', justifyContent: 'space-between', marginTop: 16 },
  cancelButton: { flex: 1, marginRight: 8 },
  submitButton: { flex: 2 },
  formErrorText: { color: 'red', textAlign: 'center', marginBottom: 10, fontSize: 14 }, // Added style for formError
});

export default AddHealthReadingScreen; 