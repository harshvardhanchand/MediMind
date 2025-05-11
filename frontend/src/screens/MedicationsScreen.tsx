import React, { useState } from 'react';
import { View, StyleSheet, ScrollView } from 'react-native';
import { Appbar, Button, Card, Chip, Divider, FAB, Paragraph, Text, Title } from 'react-native-paper';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RootStackParamList } from '../navigation/AppNavigator';

type MedicationsScreenNavigationProp = NativeStackNavigationProp<RootStackParamList, 'Medications'>;

// Mock medication data
interface Medication {
  id: string;
  name: string;
  dosage: string;
  frequency: string;
  nextDose: {
    time: string;
    taken: boolean;
  };
  purpose: string;
  instructions: string;
  prescriber: string;
}

const mockMedications: Medication[] = [
  {
    id: '1',
    name: 'Lisinopril',
    dosage: '10mg - Once daily',
    frequency: 'Once daily',
    nextDose: {
      time: '9:00 AM',
      taken: false,
    },
    purpose: 'Blood pressure management',
    instructions: 'Take with water before breakfast',
    prescriber: 'Dr. Sarah Johnson',
  },
  {
    id: '2',
    name: 'Metformin',
    dosage: '500mg - Twice daily',
    frequency: 'Twice daily',
    nextDose: {
      time: '1:30 PM',
      taken: false,
    },
    purpose: 'Diabetes management',
    instructions: 'Take with food',
    prescriber: 'Dr. Michael Chen',
  },
  {
    id: '3',
    name: 'Atorvastatin',
    dosage: '20mg - Once daily',
    frequency: 'Once daily',
    nextDose: {
      time: '8:00 PM',
      taken: false,
    },
    purpose: 'Cholesterol management',
    instructions: 'Take in the evening',
    prescriber: 'Dr. Michael Chen',
  },
];

const MedicationsScreen = () => {
  const navigation = useNavigation<MedicationsScreenNavigationProp>();
  const [medications, setMedications] = useState<Medication[]>(mockMedications);

  const handleMarkAsTaken = (id: string) => {
    setMedications(
      medications.map((med) =>
        med.id === id
          ? {
              ...med,
              nextDose: {
                ...med.nextDose,
                taken: true,
              },
            }
          : med
      )
    );
  };

  const renderMedicationCard = (medication: Medication) => {
    return (
      <Card key={medication.id} style={styles.card}>
        <Card.Content>
          <Title style={styles.medicationName}>{medication.name}</Title>
          <Text style={styles.dosage}>{medication.dosage}</Text>
          
          <View style={styles.nextDoseContainer}>
            <View style={styles.pillIconContainer}>
              <Text style={styles.pillIcon}>💊</Text>
            </View>
            <View style={styles.doseInfoContainer}>
              <Text style={styles.nextDoseText}>Next dose:</Text>
              <Text style={styles.nextDoseTime}>Today, {medication.nextDose.time}</Text>
            </View>
          </View>
          
          <Divider style={styles.divider} />
          
          <View style={styles.detailsRow}>
            <Text style={styles.detailLabel}>Purpose:</Text>
            <Text style={styles.detailValue}>{medication.purpose}</Text>
          </View>
          
          <View style={styles.detailsRow}>
            <Text style={styles.detailLabel}>Instructions:</Text>
            <Text style={styles.detailValue}>{medication.instructions}</Text>
          </View>
          
          <View style={styles.detailsRow}>
            <Text style={styles.detailLabel}>Prescriber:</Text>
            <Text style={styles.detailValue}>{medication.prescriber}</Text>
          </View>
        </Card.Content>
        
        <Card.Actions style={styles.cardActions}>
          <Button 
            mode="outlined" 
            onPress={() => {}} 
            style={styles.editButton}
          >
            Edit
          </Button>
          <Button 
            mode="contained" 
            onPress={() => handleMarkAsTaken(medication.id)}
            disabled={medication.nextDose.taken}
            style={medication.nextDose.taken ? styles.takenButton : styles.actionButton}
          >
            {medication.nextDose.taken ? 'Marked as Taken' : 'Mark as Taken'}
          </Button>
        </Card.Actions>
      </Card>
    );
  };

  return (
    <View style={styles.container}>
      <Appbar.Header>
        <Appbar.BackAction onPress={() => navigation.goBack()} />
        <Appbar.Content title="Medications" />
      </Appbar.Header>
      
      <View style={styles.headerContainer}>
        <Title style={styles.headerTitle}>Medications</Title>
        <Text style={styles.headerSubtitle}>Manage your medications and schedule</Text>
      </View>
      
      <ScrollView style={styles.scrollView} contentContainerStyle={styles.scrollContent}>
        {medications.map(renderMedicationCard)}
      </ScrollView>
      
      <FAB
        style={styles.fab}
        icon="plus"
        onPress={() => navigation.navigate('AddMedication')}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F7FA',
  },
  headerContainer: {
    paddingHorizontal: 16,
    paddingTop: 16,
    paddingBottom: 8,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
  },
  headerSubtitle: {
    fontSize: 16,
    color: '#666',
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: 16,
    paddingBottom: 80, // Extra padding for FAB
  },
  card: {
    marginBottom: 16,
    borderRadius: 12,
    elevation: 3,
  },
  medicationName: {
    fontSize: 22,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  dosage: {
    fontSize: 16,
    color: '#555',
    marginBottom: 16,
  },
  nextDoseContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  pillIconContainer: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#E3F2FD',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  pillIcon: {
    fontSize: 24,
  },
  doseInfoContainer: {
    flex: 1,
  },
  nextDoseText: {
    fontSize: 14,
    color: '#777',
  },
  nextDoseTime: {
    fontSize: 16,
    fontWeight: 'bold',
  },
  divider: {
    marginVertical: 12,
  },
  detailsRow: {
    flexDirection: 'row',
    marginBottom: 8,
  },
  detailLabel: {
    width: 100,
    fontWeight: 'bold',
    fontSize: 14,
  },
  detailValue: {
    flex: 1,
    fontSize: 14,
  },
  cardActions: {
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingBottom: 16,
  },
  editButton: {
    minWidth: 100,
  },
  actionButton: {
    minWidth: 160,
  },
  takenButton: {
    minWidth: 160,
    backgroundColor: '#4CAF50',
  },
  fab: {
    position: 'absolute',
    margin: 16,
    right: 0,
    bottom: 0,
  },
});

export default MedicationsScreen; 