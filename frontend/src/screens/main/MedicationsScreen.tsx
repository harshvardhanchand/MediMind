import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { View, FlatList, TouchableOpacity, ListRenderItem, ActivityIndicator } from 'react-native';
import { styled } from 'nativewind';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { Pill,Plus,ChevronRight } from 'lucide-react-native';

import { MainAppStackParamList } from '../../navigation/types';
import ScreenContainer from '../../components/layout/ScreenContainer';
import StyledText from '../../components/common/StyledText';
import StyledButton from '../../components/common/StyledButton';
import { medicationServices } from '../../api/services';
import { MedicationStatus, MedicationFrequency } from '../../types/api';
import { useTheme } from '../../theme';
import { MedicationEntry } from '../../types/interfaces';

const StyledView = styled(View);
const StyledTouchableOpacity = styled(TouchableOpacity);

type MedicationsScreenNavigationProp = NativeStackNavigationProp<MainAppStackParamList, 'Medications'>;

const MedicationsScreen = () => {
  const navigation = useNavigation<MedicationsScreenNavigationProp>();
  const { colors } = useTheme();

  // Data states
  const [medications, setMedications] = useState<MedicationEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [usingDummyData, setUsingDummyData] = useState(false);
  const [apiConnected, setApiConnected] = useState(false);

  // ✅ Memoized dummy data - only created once
  const dummyMedications = useMemo<MedicationEntry[]>(() => [
    {
      id: 'dummy-1',
      name: 'Amoxicillin',
      dosage: '250mg',
      frequency: 'Every 8 hours',
      start_date: '2023-10-12',
      status: MedicationStatus.ACTIVE,
      reason: 'Bacterial infection',
      prescribing_doctor: 'Dr. Smith',
      created_at: '2023-10-12T00:00:00Z'
    },
    {
      id: 'dummy-2',
      name: 'Lisinopril',
      dosage: '10mg',
      frequency: 'Once daily',
      start_date: '2023-05-01',
      status: MedicationStatus.ACTIVE,
      reason: 'High blood pressure',
      prescribing_doctor: 'Dr. Johnson',
      created_at: '2023-05-01T00:00:00Z'
    },
    {
      id: 'dummy-3',
      name: 'Metformin',
      dosage: '500mg',
      frequency: 'Twice daily with meals',
      start_date: '2023-03-15',
      status: MedicationStatus.ACTIVE,
      reason: 'Type 2 diabetes',
      prescribing_doctor: 'Dr. Williams',
      created_at: '2023-03-15T00:00:00Z'
    }
  ], []);

  useEffect(() => {
    fetchMedications();
  }, []);

  const fetchMedications = async () => {
    try {
      setLoading(true);
      setUsingDummyData(false);
      setApiConnected(false);
      
      console.log('Fetching medications from API...');
      
      // Call the real API
      const response = await medicationServices.getMedications({ limit: 100 });
      
      if (response.data) {
        setApiConnected(true);
        
        // Convert API response to display format
        const formattedMedications: MedicationEntry[] = response.data.map(med => ({
          id: med.medication_id,
          name: med.name,
          dosage: med.dosage,
          frequency: formatFrequency(med.frequency, med.frequency_details),
          start_date: med.start_date,
          status: med.status,
          reason: med.reason,
          prescribing_doctor: med.prescribing_doctor,
          created_at: med.created_at
        }));
        
        // If API returns empty list, show mock data instead of empty state
        if (formattedMedications.length === 0) {
          console.log('✅ API connected but no medications found - showing mock data');
          setMedications(dummyMedications);
          setUsingDummyData(true);
        } else {
          setMedications(formattedMedications);
          console.log(`✅ Loaded ${formattedMedications.length} medications from API`);
        }
      } else {
        throw new Error('Invalid response format');
      }
      
    } catch (err: any) {
      console.log('API call failed, falling back to dummy data:', err.message);
      setMedications(dummyMedications);
      setUsingDummyData(true);
      setApiConnected(false);
    } finally {
      setLoading(false);
    }
  };

  // ✅ Memoized frequency formatting function
  const formatFrequency = useCallback((frequency: MedicationFrequency, frequencyDetails?: string | null) => {
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
  }, []);

  // ✅ Memoized status color functions
  const getStatusColor = useCallback((status: MedicationStatus) => {
    switch (status) {
      case MedicationStatus.ACTIVE: return 'bg-green-100';
      case MedicationStatus.COMPLETED: return 'bg-blue-100';
      case MedicationStatus.DISCONTINUED: return 'bg-red-100';
      case MedicationStatus.ON_HOLD: return 'bg-yellow-100';
      default: return 'bg-gray-100';
    }
  }, []);

  const getStatusTextColor = useCallback((status: MedicationStatus) => {
    switch (status) {
      case MedicationStatus.ACTIVE: return 'text-green-800';
      case MedicationStatus.COMPLETED: return 'text-blue-800';
      case MedicationStatus.DISCONTINUED: return 'text-red-800';
      case MedicationStatus.ON_HOLD: return 'text-yellow-800';
      default: return 'text-gray-800';
    }
  }, []);

  const renderMedicationItem: ListRenderItem<MedicationEntry> = ({ item }) => (
    <StyledTouchableOpacity tw="bg-white rounded-lg p-4 mb-3 shadow-sm border border-gray-100">
      <StyledView tw="flex-row justify-between items-start">
        <StyledView tw="flex-1">
          <StyledText variant="h4" tw="text-gray-900 mb-1">{item.name}</StyledText>
          <StyledView tw="flex-row items-center mb-2">
            <StyledView tw={`px-2 py-1 rounded-full ${getStatusColor(item.status)} mr-2`}>
              <StyledText tw={`text-xs font-medium ${getStatusTextColor(item.status)}`}>
                {item.status}
              </StyledText>
            </StyledView>
            {item.dosage && (
              <StyledText variant="caption" color="textSecondary" tw="mr-2">
                {item.dosage}
              </StyledText>
            )}
          </StyledView>
          <StyledText variant="body2" color="textSecondary" tw="mb-1">
            {item.frequency}
          </StyledText>
          {item.reason && (
            <StyledText variant="body2" color="textSecondary" tw="mb-1">
              Reason: {item.reason}
            </StyledText>
          )}
          {item.prescribing_doctor && (
            <StyledText variant="caption" color="textMuted">
              Prescribed by: {item.prescribing_doctor}
            </StyledText>
          )}
        </StyledView>
        <ChevronRight size={20} color={colors.textMuted} />
      </StyledView>
    </StyledTouchableOpacity>
  );

  if (loading) {
    return (
      <ScreenContainer scrollable={false} withPadding>
        <StyledView tw="flex-1 justify-center items-center">
          <ActivityIndicator size="large" />
          <StyledText tw="mt-2 text-gray-600">Loading medications...</StyledText>
        </StyledView>
      </ScreenContainer>
    );
  }

  return (
    <ScreenContainer scrollable={false} withPadding>
      <StyledView tw="pt-2 pb-4 flex-row items-center justify-between">
        <StyledView>
          <StyledText variant="h1" color="primary">Medications</StyledText>
          <StyledText variant="body2" color="textSecondary" tw="mt-1">
            Track your medications and schedule
          </StyledText>
          
          {usingDummyData && !apiConnected && (
            <StyledView tw="mt-3 p-2 bg-yellow-100 rounded border border-yellow-300">
              <StyledText tw="text-yellow-800 text-sm text-center">
                📱 API connection failed - Showing sample data
              </StyledText>
            </StyledView>
          )}
          
          {usingDummyData && apiConnected && (
            <StyledView tw="mt-3 p-2 bg-blue-100 rounded border border-blue-300">
              <StyledText tw="text-blue-800 text-sm text-center">
                📋 No medications added yet - Showing sample data
              </StyledText>
            </StyledView>
          )}
          
          {!usingDummyData && apiConnected && medications.length > 0 && (
            <StyledView tw="mt-3 p-2 bg-green-100 rounded border border-green-300">
              <StyledText tw="text-green-800 text-sm text-center">
                ✅ Connected to API - Real data loaded
              </StyledText>
            </StyledView>
          )}
        </StyledView>
      </StyledView>

      <StyledButton 
        variant="filledPrimary"
        iconLeft={<Plus size={18} color={colors.onPrimary} />}
        onPress={() => navigation.navigate('AddMedication')} 
        tw="mb-4"
        style={{ borderRadius: 10 }}
      >
        Add New Medication
      </StyledButton>
      
      <StyledView tw="flex-1">
        <FlatList<MedicationEntry>
          data={medications}
          keyExtractor={(item) => item.id}
          renderItem={renderMedicationItem}
          showsVerticalScrollIndicator={false}
          onRefresh={fetchMedications}
          refreshing={loading}
          ListEmptyComponent={
            <StyledView tw="flex items-center justify-center p-6 mt-10">
              <Pill size={40} color={colors.textMuted} />
              <StyledText variant="h4" tw="mt-3 text-gray-700">No Medications Added Yet</StyledText>
              <StyledText variant="body2" color="textSecondary" tw="text-center mt-1">
                Tap the button above to add your first medication.
              </StyledText>
            </StyledView>
          }
        />
      </StyledView>
    </ScreenContainer>
  );
};

export default MedicationsScreen; 