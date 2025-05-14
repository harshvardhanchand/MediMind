import React, { useState } from 'react';
import { View, FlatList, ListRenderItem, TouchableOpacity } from 'react-native';
import { styled } from 'nativewind';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import Ionicons from 'react-native-vector-icons/Ionicons';

import ScreenContainer from '../../components/layout/ScreenContainer';
import StyledText from '../../components/common/StyledText';
import ListItem from '../../components/common/ListItem';
// import StyledButton from '../../components/common/StyledButton'; // Removed unused import
import { MainAppStackParamList } from '../../navigation/types'; 
import { useTheme } from '../../theme';

const StyledView = styled(View);
const StyledTouchableOpacity = styled(TouchableOpacity);

interface MedicationListItem {
  id: string;
  name: string;
  dosage?: string;
  frequency?: string;
  prescribingDoctor?: string;
  lastUpdated: string; // Or a date for sorting
  // Potentially add source document link/name
}

// Mock data for medications list
const dummyMedications: MedicationListItem[] = [
  {
    id: 'med101',
    name: 'Amoxicillin',
    dosage: '250mg',
    frequency: 'Twice a day',
    prescribingDoctor: 'Dr. Anya Sharma',
    lastUpdated: 'Nov 05, 2023',
  },
  {
    id: 'med102',
    name: 'Ibuprofen',
    dosage: '200mg',
    frequency: 'As needed for pain',
    prescribingDoctor: 'Dr. Anya Sharma',
    lastUpdated: 'Nov 05, 2023',
  },
  {
    id: 'med103',
    name: 'Lisinopril',
    dosage: '10mg',
    frequency: 'Once a day',
    prescribingDoctor: 'Dr. Ken M. Simpleton',
    lastUpdated: 'May 10, 2024',
  },
  {
    id: 'med104',
    name: 'Metformin',
    dosage: '500mg',
    frequency: 'Twice daily with meals',
    prescribingDoctor: 'Dr. Ken M. Simpleton',
    lastUpdated: 'May 10, 2024',
  },
];

// Define navigation prop type
type MedicationsListScreenNavigationProp = NativeStackNavigationProp<MainAppStackParamList, 'MedicationsScreen'>; // Assuming 'MedicationsScreen' is the route name for this

const MedicationsListScreen = () => {
  const navigation = useNavigation<MedicationsListScreenNavigationProp>();
  const { colors } = useTheme();
  // const [searchTerm, setSearchTerm] = useState(''); // For future search

  const renderMedicationItem: ListRenderItem<MedicationListItem> = ({ item }) => (
    <ListItem
      key={item.id}
      label={item.name}
      subtitle={`${item.dosage || ''}${item.dosage && item.frequency ? ' - ' : ''}${item.frequency || ''}${item.prescribingDoctor ? `\nPrescribed by: ${item.prescribingDoctor}` : ''}`}
      iconLeft="medkit-outline"
      iconLeftColor={colors.dataColor5} // Purple for medications
      onPress={() => {
        navigation.navigate('MedicationDetail', { medicationId: item.id }); // Correctly navigate
      }}
    />
  );

  return (
    <ScreenContainer scrollable={false} withPadding={false} backgroundColor={colors.backgroundPrimary}>
      {/* Custom Header */}
      <StyledView className="flex-row items-center px-3 py-3 border-b border-borderSubtle bg-backgroundSecondary">
        <StyledTouchableOpacity onPress={() => navigation.goBack()} className="p-1 mr-2">
          <Ionicons name="chevron-back-outline" size={28} color={colors.accentPrimary} />
        </StyledTouchableOpacity>
        <StyledText variant="h3" tw="font-semibold flex-1 text-center">Medications</StyledText>
        <StyledTouchableOpacity 
            onPress={() => navigation.navigate('AddMedication')}
            className="p-1 ml-2"
        >
          <Ionicons name="add-circle-outline" size={28} color={colors.accentPrimary} />
        </StyledTouchableOpacity>
      </StyledView>

      {/* TODO: Add Search/Filter bar if needed, similar to DocumentsScreen */}
      {/* <StyledView className="px-4 py-2 border-b border-borderSubtle"> ... </StyledView> */}

      <FlatList<MedicationListItem>
        data={dummyMedications}
        keyExtractor={(item) => item.id}
        renderItem={renderMedicationItem}
        showsVerticalScrollIndicator={false}
        contentContainerStyle={{ paddingHorizontal: 16, paddingTop: 12, paddingBottom: 20 }}
        ItemSeparatorComponent={() => <StyledView className="h-px bg-borderSubtle ml-14" />} // Offset by icon width + margin
      />
      
      {/* Alternative for Add Button if not in header - FAB style */}
      {/* <StyledTouchableOpacity
        className="absolute bottom-6 right-6 bg-accentPrimary rounded-full p-4 shadow-lg"
        onPress={() => alert('TODO: Navigate to Add New Medication Screen')}
        activeOpacity={0.8}
      >
        <Ionicons name="add-outline" size={28} color={colors.textOnPrimaryColor} />
      </StyledTouchableOpacity> */}
    </ScreenContainer>
  );
};

export default MedicationsListScreen; 