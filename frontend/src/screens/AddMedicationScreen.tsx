import React, { useState } from 'react';
import { View, StyleSheet, ScrollView, Alert } from 'react-native';
import { Appbar, Button, TextInput, Title, Paragraph, HelperText, Card, Divider, Switch, Text } from 'react-native-paper';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RootStackParamList } from '../navigation/AppNavigator';

type AddMedicationNavigationProp = NativeStackNavigationProp<RootStackParamList, 'AddMedication'>;

const AddMedicationScreen = () => {
  const navigation = useNavigation<AddMedicationNavigationProp>();
  
  // Form fields
  const [medicationName, setMedicationName] = useState('');
  const [dosage, setDosage] = useState('');
  const [frequency, setFrequency] = useState('');
  const [purpose, setPurpose] = useState('');
  const [instructions, setInstructions] = useState('');
  const [prescriber, setPrescriber] = useState('');
  const [reminderEnabled, setReminderEnabled] = useState(true);
  const [reminderTime, setReminderTime] = useState('9:00 AM');
  
  // Validation states
  const [nameError, setNameError] = useState('');
  const [dosageError, setDosageError] = useState('');
  
  const validateForm = () => {
    let isValid = true;
    
    // Validate medication name
    if (!medicationName.trim()) {
      setNameError('Medication name is required');
      isValid = false;
    } else {
      setNameError('');
    }
    
    // Validate dosage
    if (!dosage.trim()) {
      setDosageError('Dosage is required');
      isValid = false;
    } else {
      setDosageError('');
    }
    
    return isValid;
  };
  
  const handleSubmit = () => {
    if (validateForm()) {
      Alert.alert(
        'Success',
        'Medication has been added successfully!',
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
        <Appbar.Content title="Add Medication" />
      </Appbar.Header>
      
      <ScrollView style={styles.scrollView} contentContainerStyle={styles.scrollContent}>
        <Title style={styles.title}>Add New Medication</Title>
        <Paragraph style={styles.subtitle}>
          Enter the details of your medication
        </Paragraph>
        
        <Card style={styles.card}>
          <Card.Content>
            <Text style={styles.sectionTitle}>Medication Details</Text>
            
            <TextInput
              label="Medication Name*"
              value={medicationName}
              onChangeText={setMedicationName}
              mode="outlined"
              style={styles.input}
              error={!!nameError}
            />
            {!!nameError && <HelperText type="error">{nameError}</HelperText>}
            
            <TextInput
              label="Dosage*"
              value={dosage}
              onChangeText={setDosage}
              mode="outlined"
              placeholder="e.g., 10mg"
              style={styles.input}
              error={!!dosageError}
            />
            {!!dosageError && <HelperText type="error">{dosageError}</HelperText>}
            
            <TextInput
              label="Frequency"
              value={frequency}
              onChangeText={setFrequency}
              mode="outlined"
              placeholder="e.g., Once daily, Twice daily"
              style={styles.input}
            />
            
            <TextInput
              label="Purpose"
              value={purpose}
              onChangeText={setPurpose}
              mode="outlined"
              placeholder="e.g., Blood pressure management"
              style={styles.input}
            />
            
            <TextInput
              label="Instructions"
              value={instructions}
              onChangeText={setInstructions}
              mode="outlined"
              placeholder="e.g., Take with water before meals"
              multiline
              numberOfLines={3}
              style={styles.input}
            />
            
            <TextInput
              label="Prescriber"
              value={prescriber}
              onChangeText={setPrescriber}
              mode="outlined"
              placeholder="e.g., Dr. Smith"
              style={styles.input}
            />
          </Card.Content>
        </Card>
        
        <Card style={styles.card}>
          <Card.Content>
            <Text style={styles.sectionTitle}>Reminder Settings</Text>
            
            <View style={styles.switchContainer}>
              <Text>Enable Reminders</Text>
              <Switch
                value={reminderEnabled}
                onValueChange={setReminderEnabled}
              />
            </View>
            
            {reminderEnabled && (
              <TextInput
                label="Reminder Time"
                value={reminderTime}
                onChangeText={setReminderTime}
                mode="outlined"
                placeholder="9:00 AM"
                style={styles.input}
              />
            )}
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
            Save Medication
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
});

export default AddMedicationScreen; 