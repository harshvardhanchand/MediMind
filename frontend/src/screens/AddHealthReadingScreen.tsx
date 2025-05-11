import React, { useState } from 'react';
import { View, StyleSheet, ScrollView, Alert } from 'react-native';
import { Appbar, Button, TextInput, Title, Paragraph, HelperText, Card, Divider, Switch, Text, RadioButton } from 'react-native-paper';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RootStackParamList } from '../navigation/AppNavigator';

type AddHealthReadingNavigationProp = NativeStackNavigationProp<RootStackParamList, 'AddHealthReading'>;

type ReadingType = 'bloodPressure' | 'bloodGlucose' | 'heartRate';

const AddHealthReadingScreen = () => {
  const navigation = useNavigation<AddHealthReadingNavigationProp>();
  
  // Form fields
  const [readingType, setReadingType] = useState<ReadingType>('bloodPressure');
  const [systolic, setSystolic] = useState('');
  const [diastolic, setDiastolic] = useState('');
  const [glucose, setGlucose] = useState('');
  const [heartRate, setHeartRate] = useState('');
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
  const [time, setTime] = useState(
    new Date().toTimeString().split(' ')[0].substring(0, 5)
  );
  const [notes, setNotes] = useState('');
  
  // Validation states
  const [systolicError, setSystolicError] = useState('');
  const [diastolicError, setDiastolicError] = useState('');
  const [glucoseError, setGlucoseError] = useState('');
  const [heartRateError, setHeartRateError] = useState('');
  
  const validateForm = () => {
    let isValid = true;
    
    // Reset all errors
    setSystolicError('');
    setDiastolicError('');
    setGlucoseError('');
    setHeartRateError('');
    
    if (readingType === 'bloodPressure') {
      // Validate systolic
      if (!systolic.trim()) {
        setSystolicError('Systolic value is required');
        isValid = false;
      } else {
        const systolicValue = parseInt(systolic);
        if (isNaN(systolicValue) || systolicValue < 50 || systolicValue > 250) {
          setSystolicError('Systolic value should be between 50 and 250');
          isValid = false;
        }
      }
      
      // Validate diastolic
      if (!diastolic.trim()) {
        setDiastolicError('Diastolic value is required');
        isValid = false;
      } else {
        const diastolicValue = parseInt(diastolic);
        if (isNaN(diastolicValue) || diastolicValue < 30 || diastolicValue > 150) {
          setDiastolicError('Diastolic value should be between 30 and 150');
          isValid = false;
        }
      }
    } 
    else if (readingType === 'bloodGlucose') {
      // Validate glucose
      if (!glucose.trim()) {
        setGlucoseError('Blood glucose value is required');
        isValid = false;
      } else {
        const glucoseValue = parseInt(glucose);
        if (isNaN(glucoseValue) || glucoseValue < 20 || glucoseValue > 600) {
          setGlucoseError('Blood glucose value should be between 20 and 600 mg/dL');
          isValid = false;
        }
      }
    } 
    else if (readingType === 'heartRate') {
      // Validate heart rate
      if (!heartRate.trim()) {
        setHeartRateError('Heart rate value is required');
        isValid = false;
      } else {
        const heartRateValue = parseInt(heartRate);
        if (isNaN(heartRateValue) || heartRateValue < 30 || heartRateValue > 220) {
          setHeartRateError('Heart rate value should be between 30 and 220 bpm');
          isValid = false;
        }
      }
    }
    
    return isValid;
  };
  
  const handleSubmit = () => {
    if (validateForm()) {
      Alert.alert(
        'Success',
        'Health reading has been added successfully!',
        [
          {
            text: 'OK',
            onPress: () => navigation.goBack(),
          },
        ]
      );
    }
  };
  
  return (
    <View style={styles.container}>
      <Appbar.Header>
        <Appbar.BackAction onPress={() => navigation.goBack()} />
        <Appbar.Content title="Add Health Reading" />
      </Appbar.Header>
      
      <ScrollView style={styles.scrollView} contentContainerStyle={styles.scrollContent}>
        <Title style={styles.title}>Add New Health Reading</Title>
        <Paragraph style={styles.subtitle}>
          Enter your health measurement details
        </Paragraph>
        
        <Card style={styles.card}>
          <Card.Content>
            <Text style={styles.sectionTitle}>Reading Type</Text>
            <RadioButton.Group
              onValueChange={(value) => setReadingType(value as ReadingType)}
              value={readingType}
            >
              <RadioButton.Item label="Blood Pressure" value="bloodPressure" />
              <RadioButton.Item label="Blood Glucose" value="bloodGlucose" />
              <RadioButton.Item label="Heart Rate" value="heartRate" />
            </RadioButton.Group>
          </Card.Content>
        </Card>
        
        <Card style={styles.card}>
          <Card.Content>
            <Text style={styles.sectionTitle}>Reading Details</Text>
            
            {readingType === 'bloodPressure' && (
              <>
                <TextInput
                  label="Systolic (mmHg)"
                  value={systolic}
                  onChangeText={setSystolic}
                  mode="outlined"
                  keyboardType="number-pad"
                  placeholder="e.g., 120"
                  style={styles.input}
                  error={!!systolicError}
                />
                {!!systolicError && <HelperText type="error">{systolicError}</HelperText>}
                
                <TextInput
                  label="Diastolic (mmHg)"
                  value={diastolic}
                  onChangeText={setDiastolic}
                  mode="outlined"
                  keyboardType="number-pad"
                  placeholder="e.g., 80"
                  style={styles.input}
                  error={!!diastolicError}
                />
                {!!diastolicError && <HelperText type="error">{diastolicError}</HelperText>}
              </>
            )}
            
            {readingType === 'bloodGlucose' && (
              <>
                <TextInput
                  label="Blood Glucose (mg/dL)"
                  value={glucose}
                  onChangeText={setGlucose}
                  mode="outlined"
                  keyboardType="number-pad"
                  placeholder="e.g., 100"
                  style={styles.input}
                  error={!!glucoseError}
                />
                {!!glucoseError && <HelperText type="error">{glucoseError}</HelperText>}
              </>
            )}
            
            {readingType === 'heartRate' && (
              <>
                <TextInput
                  label="Heart Rate (bpm)"
                  value={heartRate}
                  onChangeText={setHeartRate}
                  mode="outlined"
                  keyboardType="number-pad"
                  placeholder="e.g., 70"
                  style={styles.input}
                  error={!!heartRateError}
                />
                {!!heartRateError && <HelperText type="error">{heartRateError}</HelperText>}
              </>
            )}
            
            <TextInput
              label="Date"
              value={date}
              onChangeText={setDate}
              mode="outlined"
              placeholder="YYYY-MM-DD"
              style={styles.input}
            />
            
            <TextInput
              label="Time"
              value={time}
              onChangeText={setTime}
              mode="outlined"
              placeholder="HH:MM"
              style={styles.input}
            />
            
            <TextInput
              label="Notes"
              value={notes}
              onChangeText={setNotes}
              mode="outlined"
              placeholder="Optional notes about this reading"
              multiline
              numberOfLines={3}
              style={styles.input}
            />
          </Card.Content>
        </Card>
        
        <View style={styles.buttonContainer}>
          <Button
            mode="outlined"
            onPress={() => navigation.goBack()}
            style={styles.cancelButton}
          >
            Cancel
          </Button>
          <Button
            mode="contained"
            onPress={handleSubmit}
            style={styles.submitButton}
          >
            Save Reading
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
    marginBottom: 12,
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
});

export default AddHealthReadingScreen; 