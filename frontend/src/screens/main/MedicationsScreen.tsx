import React from 'react';
import { View, Text, Button, FlatList } from 'react-native';
import { styled } from 'nativewind';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { MainAppStackParamList } from '../../navigation/types';

const StyledView = styled(View);
const StyledText = styled(Text);

// Dummy data for now
const dummyMedications = [
  { id: '1', name: 'Amoxicillin 250mg', dosage: '1 tablet', frequency: 'Every 8 hours', startDate: '2023-10-12' },
  { id: '2', name: 'Lisinopril 10mg', dosage: '1 tablet', frequency: 'Once daily', startDate: '2023-05-01' },
];

type MedicationsScreenNavigationProp = NativeStackNavigationProp<MainAppStackParamList, 'Medications'>;

const MedicationsScreen = () => {
  const navigation = useNavigation<MedicationsScreenNavigationProp>();

  return (
    <StyledView className="flex-1 p-4">
      <StyledText className="text-2xl font-bold mb-4">My Medications</StyledText>
      {/* Add ability to add/edit medications later */}
      <FlatList
        data={dummyMedications}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <StyledView className="p-3 mb-3 bg-white rounded-lg shadow">
            <StyledText className="text-lg font-semibold">{item.name}</StyledText>
            <StyledText className="text-sm text-gray-600">Dosage: {item.dosage}</StyledText>
            <StyledText className="text-sm text-gray-600">Frequency: {item.frequency}</StyledText>
            <StyledText className="text-sm text-gray-500">Start Date: {item.startDate}</StyledText>
            {/* Add reminder or refill options later */}
          </StyledView>
        )}
      />
      <Button title="Back to Home" onPress={() => navigation.navigate('Home')} />
    </StyledView>
  );
};

export default MedicationsScreen; 