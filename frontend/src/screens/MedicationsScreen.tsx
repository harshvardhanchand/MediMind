import React, { useState, useEffect } from 'react';
import { View, StyleSheet, ScrollView } from 'react-native';
import { Appbar, Button, Card, Divider, FAB, Paragraph, Text, Title, ActivityIndicator } from 'react-native-paper';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';

import { MainAppStackParamList } from '../navigation/types';
import { MedicationResponse, MedicationStatus, MedicationFrequency } from '../types/api';
import { medicationServices } from '../api/services';

type MedicationsScreenNavigationProp = NativeStackNavigationProp<MainAppStackParamList, 'MedicationsScreen'>;

const initialMockMedications: MedicationResponse[] = [
  {
    medication_id: '1',
    user_id: 'mock-user-1',
    name: 'Lisinopril',
    dosage: '10mg',
    frequency: MedicationFrequency.ONCE_DAILY,
    frequency_details: 'Once daily in the morning',
    start_date: '2023-01-15',
    time_of_day: ['09:00'],
    with_food: false,
    reason: 'Blood pressure management',
    prescribing_doctor: 'Dr. Sarah Johnson',
    notes: 'Take with water before breakfast',
    status: MedicationStatus.ACTIVE,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    medication_id: '2',
    user_id: 'mock-user-1',
    name: 'Metformin',
    dosage: '500mg',
    frequency: MedicationFrequency.TWICE_DAILY,
    frequency_details: 'Twice daily with meals',
    start_date: '2023-03-10',
    time_of_day: ['08:00', '18:00'],
    with_food: true,
    reason: 'Diabetes management',
    prescribing_doctor: 'Dr. Michael Chen',
    notes: 'Take with food',
    status: MedicationStatus.ACTIVE,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    medication_id: '3',
    user_id: 'mock-user-1',
    name: 'Atorvastatin',
    dosage: '20mg',
    frequency: MedicationFrequency.ONCE_DAILY,
    frequency_details: 'Once daily in the evening',
    start_date: '2022-11-20',
    time_of_day: ['20:00'],
    reason: 'Cholesterol management',
    prescribing_doctor: 'Dr. Michael Chen',
    notes: 'Take in the evening',
    status: MedicationStatus.ACTIVE,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
];

const MedicationsScreen = () => {
  const navigation = useNavigation<MedicationsScreenNavigationProp>();
  
  const [displayedMedications, setDisplayedMedications] = useState<MedicationResponse[]>(initialMockMedications);
  
  const [apiMedications, setApiMedications] = useState<MedicationResponse[]>([]);
  const [isLoadingApi, setIsLoadingApi] = useState(false);
  const [errorApi, setErrorApi] = useState<string | null>(null);

  const [useApiData, setUseApiData] = useState(false);

  const loadMedicationsFromApi = async () => {
    setIsLoadingApi(true);
    setErrorApi(null);
    try {
      const response = await medicationServices.getMedications();
      setApiMedications(response.data || []);
      if (useApiData) {
        setDisplayedMedications(response.data || []);
      }
    } catch (err: any) {
      console.error("Failed to fetch medications:", err);
      setErrorApi(err.message || 'Failed to load medications.');
    } finally {
      setIsLoadingApi(false);
    }
  };

  useEffect(() => {
    console.log('MedicationsScreen mounted. API call can be triggered by toggle or refresh button.');
  }, []);

  const handleMarkAsTaken = async (medicationId: string) => {
    const medicationToUpdate = displayedMedications.find(m => m.medication_id === medicationId);
    if (!medicationToUpdate) return;

    // Optimistic UI update
    const previousMedications = [...displayedMedications];
    setDisplayedMedications(
      displayedMedications.map((med) =>
        med.medication_id === medicationId
          ? { ...med, status: MedicationStatus.COMPLETED, updated_at: new Date().toISOString() }
          : med
      )
    );

    try {
      const payload: Partial<MedicationResponse> = { // Or use MedicationUpdate if more specific
        status: MedicationStatus.COMPLETED,
      };
      await medicationServices.updateMedication(medicationId, payload as any); // Using 'as any' temporarily if MedicationUpdate is stricter
      // Refresh data from API to ensure consistency
      await loadMedicationsFromApi(); 
      // If not using API data primarily, ensure apiMedications is also updated if it was the source
      if (useApiData) {
         // already handled by loadMedicationsFromApi setting displayedMedications when useApiData is true
      } else {
        // if we were showing mock data, and it got updated, and now we want to ensure apiMedications cache is also updated.
        // This part might be complex if not just re-fetching everything.
        // For simplicity, loadMedicationsFromApi will refresh the source if needed.
      }

    } catch (error) {
      console.error(`Failed to mark medication ${medicationId} as taken:`, error);
      setErrorApi(`Failed to update medication: ${(error as Error).message}`);
      // Revert optimistic update
      setDisplayedMedications(previousMedications);
      // Optionally show an alert or toast to the user
    }
  };

  const formatFrequency = (freq: MedicationFrequency, details?: string | null) => {
    const base = freq.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
    return details ? `${base} (${details})` : base;
  };

  const renderMedicationCard = (medication: MedicationResponse) => {
    const isTakenOrCompleted = medication.status === MedicationStatus.COMPLETED || medication.status === MedicationStatus.DISCONTINUED;
    const nextDoseTimeDisplay = medication.time_of_day && medication.time_of_day.length > 0 
                               ? `Around ${medication.time_of_day[0]}` 
                               : 'As directed';

    return (
      <Card key={medication.medication_id} style={styles.card}>
        <Card.Content>
          <Title style={styles.medicationName}>{medication.name}</Title>
          <Text style={styles.dosage}>{medication.dosage} - {formatFrequency(medication.frequency, medication.frequency_details)}</Text>
          
          <View style={styles.nextDoseContainer}>
            <View style={styles.pillIconContainer}>
              <Text style={styles.pillIcon}>💊</Text>
            </View>
            <View style={styles.doseInfoContainer}>
              <Text style={styles.nextDoseText}>{isTakenOrCompleted ? 'Status:' : 'Next dose approximation:'}</Text>
              <Text style={styles.nextDoseTime}>{isTakenOrCompleted ? medication.status.replace('_',' ') : nextDoseTimeDisplay}</Text>
            </View>
          </View>
          
          <Divider style={styles.divider} />
          
          {medication.reason && (
            <View style={styles.detailsRow}>
              <Text style={styles.detailLabel}>Purpose:</Text>
              <Text style={styles.detailValue}>{medication.reason}</Text>
            </View>
          )}
          
          {medication.notes && (
            <View style={styles.detailsRow}>
              <Text style={styles.detailLabel}>Instructions:</Text>
              <Text style={styles.detailValue}>{medication.notes}</Text>
            </View>
          )}
          
          {medication.prescribing_doctor && (
            <View style={styles.detailsRow}>
              <Text style={styles.detailLabel}>Prescriber:</Text>
              <Text style={styles.detailValue}>{medication.prescribing_doctor}</Text>
            </View>
          )}
           <Text style={styles.detailValue}>Status: {medication.status.replace('_',' ')}</Text>
        </Card.Content>
        
        <Card.Actions style={styles.cardActions}>
          <Button 
            mode="outlined" 
            onPress={() => {
              const initialDataForEdit = {
                id: medication.medication_id,
                name: medication.name,
                dosage: medication.dosage || undefined,
                frequency: medication.frequency_details || formatFrequency(medication.frequency),
                prescribingDoctor: medication.prescribing_doctor || undefined,
                startDate: medication.start_date || undefined,
                endDate: medication.end_date || undefined,
                notes: medication.notes || undefined,
                reason: medication.reason || undefined,
              };
              navigation.navigate('AddMedication', { 
                medicationIdToEdit: medication.medication_id, 
                initialData: initialDataForEdit 
              });
            }}
            style={styles.editButton}
          >
            Edit
          </Button>
          {medication.status === MedicationStatus.ACTIVE && (
            <Button 
              mode="contained" 
              onPress={() => handleMarkAsTaken(medication.medication_id)}
              style={styles.actionButton}
            >
              Mark as Taken/Completed
            </Button>
          )}
        </Card.Actions>
      </Card>
    );
  };

  let content;
  if (isLoadingApi && useApiData) {
    content = <View style={styles.centeredMessage}><ActivityIndicator animating={true} size="large" /><Text style={styles.loadingText}>Loading medications...</Text></View>;
  } else if (errorApi && useApiData) {
    content = <View style={styles.centeredMessage}><Text style={styles.errorText}>{errorApi}</Text><Button onPress={loadMedicationsFromApi}>Retry</Button></View>;
  } else if (displayedMedications.length === 0) {
    content = <View style={styles.centeredMessage}><Text style={styles.emptyText}>No medications found.</Text><Text>Tap the '+' button to add a new medication.</Text></View>;
  } else {
    content = displayedMedications.map(renderMedicationCard);
  }

  return (
    <View style={styles.container}>
      <Appbar.Header>
        <Appbar.BackAction onPress={() => navigation.goBack()} />
        <Appbar.Content title="Medications" />
        <Appbar.Action 
            icon={useApiData ? "database-check" : "database-off"} 
            onPress={() => {
                setUseApiData(!useApiData);
                if (!useApiData && apiMedications.length > 0) setDisplayedMedications(apiMedications);
                else if (useApiData && initialMockMedications.length > 0) setDisplayedMedications(initialMockMedications);
                else if (!useApiData && apiMedications.length === 0) loadMedicationsFromApi();
            }}
        />
        <Appbar.Action icon="reload" onPress={loadMedicationsFromApi} disabled={isLoadingApi} />
      </Appbar.Header>
      
      <View style={styles.headerContainer}>
        <Title style={styles.headerTitle}>Medications</Title>
        <Text style={styles.headerSubtitle}>Manage your medications and schedule</Text>
      </View>
      
      <ScrollView style={styles.scrollView} contentContainerStyle={styles.scrollContent}>
        {content}
      </ScrollView>
      
      <FAB
        style={styles.fab}
        icon="plus"
        onPress={() => navigation.navigate('AddMedication', undefined)}
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
    paddingBottom: 80,
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
  fab: {
    position: 'absolute',
    margin: 16,
    right: 0,
    bottom: 0,
  },
  centeredMessage: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  loadingText: {
    marginTop: 10,
    fontSize: 16,
  },
  errorText: {
    color: 'red',
    fontSize: 16,
    textAlign: 'center',
    marginBottom:10,
  },
  emptyText: {
    fontSize: 18,
    textAlign: 'center',
    marginBottom: 5,
  },
});

export default MedicationsScreen; 