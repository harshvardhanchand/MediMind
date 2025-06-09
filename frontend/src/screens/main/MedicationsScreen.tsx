import React, { useState, useEffect } from 'react';
import { View, Text, Button, FlatList, ActivityIndicator } from 'react-native';
import { styled } from 'nativewind';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';

import { MainAppStackParamList } from '../../navigation/types';
import { medicationServices } from '../../api/services';
import { MedicationResponse, MedicationStatus, MedicationFrequency } from '../../types/api';

const StyledView = styled(View);
const StyledText = styled(Text);

// Dummy data as fallback
const dummyMedications: MedicationResponse[] = [
  {
    medication_id: 'dummy-1',
    name: 'Amoxicillin',
    dosage: '250mg',
    frequency: MedicationFrequency.OTHER,
    frequency_details: 'Every 8 hours',
    start_date: '2023-10-12',
    status: MedicationStatus.ACTIVE,
    reason: 'Bacterial infection',
    prescribing_doctor: 'Dr. Smith',
    user_id: 'dummy-user',
    created_at: '2023-10-12T00:00:00Z',
    updated_at: '2023-10-12T00:00:00Z'
  },
  {
    medication_id: 'dummy-2',
    name: 'Lisinopril',
    dosage: '10mg',
    frequency: MedicationFrequency.ONCE_DAILY,
    start_date: '2023-05-01',
    status: MedicationStatus.ACTIVE,
    reason: 'High blood pressure',
    prescribing_doctor: 'Dr. Johnson',
    user_id: 'dummy-user',
    created_at: '2023-05-01T00:00:00Z',
    updated_at: '2023-05-01T00:00:00Z'
  },
  {
    medication_id: 'dummy-3',
    name: 'Metformin',
    dosage: '500mg',
    frequency: MedicationFrequency.TWICE_DAILY,
    frequency_details: 'With meals',
    start_date: '2023-03-15',
    status: MedicationStatus.ACTIVE,
    reason: 'Type 2 diabetes',
    prescribing_doctor: 'Dr. Williams',
    user_id: 'dummy-user',
    created_at: '2023-03-15T00:00:00Z',
    updated_at: '2023-03-15T00:00:00Z'
  }
];

type MedicationsScreenNavigationProp = NativeStackNavigationProp<MainAppStackParamList, 'Medications'>;

const MedicationsScreen = () => {
  const navigation = useNavigation<MedicationsScreenNavigationProp>();
  const [medications, setMedications] = useState<MedicationResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [usingDummyData, setUsingDummyData] = useState(false);

  useEffect(() => {
    fetchMedications();
  }, []);

  const fetchMedications = async () => {
    try {
      setLoading(true);
      setUsingDummyData(false);
      
      console.log('Trying to fetch real medications from API...');
      const response = await medicationServices.getMedications({
        limit: 100,
      });
      
      if (response.data && response.data.length > 0) {
        console.log(`Loaded ${response.data.length} real medications from API`);
        setMedications(response.data);
      } else {
        console.log('API returned empty data, using dummy medications');
        setMedications(dummyMedications);
        setUsingDummyData(true);
      }
    } catch (err: any) {
      console.log('API call failed, falling back to dummy data:', err.message);
      setMedications(dummyMedications);
      setUsingDummyData(true);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleDateString();
    } catch {
      return dateString;
    }
  };

  const formatFrequency = (frequency: MedicationFrequency, frequencyDetails?: string | null) => {
    // Convert enum to readable text
    const frequencyMap: Record<MedicationFrequency, string> = {
      [MedicationFrequency.ONCE_DAILY]: 'Once daily',
      [MedicationFrequency.TWICE_DAILY]: 'Twice daily',
      [MedicationFrequency.THREE_TIMES_DAILY]: 'Three times daily',
      [MedicationFrequency.FOUR_TIMES_DAILY]: 'Four times daily',
      [MedicationFrequency.EVERY_OTHER_DAY]: 'Every other day',
      [MedicationFrequency.ONCE_WEEKLY]: 'Once weekly',
      [MedicationFrequency.TWICE_WEEKLY]: 'Twice weekly',
      [MedicationFrequency.ONCE_MONTHLY]: 'Once monthly',
      [MedicationFrequency.AS_NEEDED]: 'As needed',
      [MedicationFrequency.OTHER]: 'Other',
    };

    const baseText = frequencyMap[frequency] || frequency;
    return frequencyDetails ? `${baseText} (${frequencyDetails})` : baseText;
  };

  if (loading) {
    return (
      <StyledView className="flex-1 justify-center items-center">
        <ActivityIndicator size="large" />
        <StyledText className="mt-2 text-gray-600">Loading medications...</StyledText>
      </StyledView>
    );
  }

  return (
    <StyledView className="flex-1 p-4">
      <StyledText className="text-2xl font-bold mb-4">My Medications</StyledText>
      
      {usingDummyData && (
        <StyledView className="mb-3 p-2 bg-yellow-100 rounded border border-yellow-300">
          <StyledText className="text-yellow-800 text-sm text-center">
            📱 Showing sample data (API not connected)
          </StyledText>
        </StyledView>
      )}
      
      <FlatList
        data={medications}
        keyExtractor={(item) => item.medication_id}
        renderItem={({ item }) => (
          <StyledView className="p-3 mb-3 bg-white rounded-lg shadow">
            <StyledText className="text-lg font-semibold">{item.name}</StyledText>
            {item.dosage && (
              <StyledText className="text-sm text-gray-600">Dosage: {item.dosage}</StyledText>
            )}
            <StyledText className="text-sm text-gray-600">
              Frequency: {formatFrequency(item.frequency, item.frequency_details)}
            </StyledText>
            {item.start_date && (
              <StyledText className="text-sm text-gray-500">
                Start Date: {formatDate(item.start_date)}
              </StyledText>
            )}
            {item.reason && (
              <StyledText className="text-sm text-gray-600">Reason: {item.reason}</StyledText>
            )}
            {item.prescribing_doctor && (
              <StyledText className="text-sm text-gray-600">
                Prescribed by: {item.prescribing_doctor}
              </StyledText>
            )}
            <StyledText className="text-xs text-gray-400 mt-1">
              Status: {item.status}
            </StyledText>
          </StyledView>
        )}
        onRefresh={fetchMedications}
        refreshing={loading}
      />
      
      <Button title="Back to Home" onPress={() => navigation.navigate('Home')} />
    </StyledView>
  );
};

export default MedicationsScreen; 