import React, { useLayoutEffect } from 'react';
import { ScrollView, View, TouchableOpacity, Alert } from 'react-native';
import { styled } from 'nativewind';
import { useNavigation, useRoute, RouteProp } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';

import ScreenContainer from '../../components/layout/ScreenContainer';
import StyledText from '../../components/common/StyledText';
import StyledButton from '../../components/common/StyledButton'; // For potential Delete button
import Card from '../../components/common/Card';
import ListItem from '../../components/common/ListItem';
import ErrorState from '../../components/common/ErrorState';
import { MainAppStackParamList } from '../../navigation/types'; 
import { useTheme } from '../../theme';
import { MedicationDetailData } from '../../types/interfaces';


const StyledView = styled(View);
const StyledScrollView = styled(ScrollView);
const StyledTouchableOpacity = styled(TouchableOpacity);

// Define navigation props
type MedicationDetailScreenNavigationProp = NativeStackNavigationProp<MainAppStackParamList, 'MedicationDetail'>; 
type MedicationDetailScreenRouteProp = RouteProp<MainAppStackParamList, 'MedicationDetail'>;

const MedicationDetailScreen = () => {
  const navigation = useNavigation<MedicationDetailScreenNavigationProp>();
  const route = useRoute<MedicationDetailScreenRouteProp>();
  const { colors } = useTheme();
  const { medicationId } = route.params; // Assuming medicationId is passed as a route param

  // In a real app, fetch medication details using medicationId
  // For now, using mock data based on the ID. This logic would be replaced by an API call.
  const medication: MedicationDetailData | undefined = [
    { id: 'med101', name: 'Amoxicillin', dosage: '250mg', frequency: 'Twice a day', prescribingDoctor: 'Dr. Anya Sharma', notes: 'Take with food. Finish course.', startDate: '2023-11-01', endDate: '2023-11-07' },
    { id: 'med102', name: 'Ibuprofen', dosage: '200mg', frequency: 'As needed for pain', prescribingDoctor: 'Dr. Anya Sharma', notes: 'Max 3 times a day.', startDate: '2023-11-05' },
    { id: 'med103', name: 'Lisinopril', dosage: '10mg', frequency: 'Once a day', prescribingDoctor: 'Dr. Ken M. Simpleton', notes: 'Monitor blood pressure.', startDate: '2024-01-15' },
    { id: 'med104', name: 'Metformin', dosage: '500mg', frequency: 'Twice daily with meals', prescribingDoctor: 'Dr. Ken M. Simpleton', notes: '', startDate: '2023-09-20' },
  ].find(m => m.id === medicationId);

  // Configure header buttons (Edit)
  useLayoutEffect(() => {
    if (medication) {
      navigation.setOptions({
        headerTitle: medication.name, // Set title to medication name
        headerRight: () => (
          <StyledTouchableOpacity 
            onPress={() => {
              // Pass medicationIdToEdit and the full medication object as initialData
              navigation.navigate('AddMedication', { 
                medicationIdToEdit: medication.id, 
                initialData: medication 
              });
            }}
            className="p-1.5"
          >
            <StyledText style={{ color: colors.accentPrimary, fontSize: 17 }}>Edit</StyledText>
          </StyledTouchableOpacity>
        ),
        headerStyle: { backgroundColor: colors.backgroundSecondary },
        headerTitleStyle: { color: colors.textPrimary },
        headerTintColor: colors.accentPrimary, // For the back button arrow
      });
    }
  }, [navigation, colors, medication]);

  if (!medication) {
    // ✅ Handle case where medication data isn't found using standardized ErrorState
    return (
      <ScreenContainer>
        <ErrorState
          title="Medication Not Found"
          message="The requested medication could not be found. It may have been deleted or moved."
          icon="medical-outline"
        />
      </ScreenContainer>
    );
  }

  const detailItems = [
    { label: 'Dosage', value: medication.dosage, icon: 'eyedrop-outline' },
    { label: 'Frequency', value: medication.frequency, icon: 'repeat-outline' },
    { label: 'Prescribing Doctor', value: medication.prescribingDoctor, icon: 'person-outline' },
    { label: 'Start Date', value: medication.startDate, icon: 'calendar-outline' },
    { label: 'End Date', value: medication.endDate, icon: 'calendar-outline' },
  ];

  return (
    <ScreenContainer scrollable={false} withPadding={false} backgroundColor={colors.backgroundTertiary}>
      <StyledScrollView className="flex-1">
        {/* Main details card */}
        <Card className="mx-4 mt-4 mb-6" noPadding> 
          {detailItems.map((item, index) => (
            item.value && (
              <ListItem
                key={item.label}
                label={item.label}
                value={item.value}
                iconLeft={item.icon}
                iconLeftColor={colors.textSecondary}
                showBottomBorder={index < detailItems.filter(i => i.value).length - 1}
              />
            )
          ))}
        </Card>

        {medication.notes && (
          <Card title="Notes" className="mx-4 mb-6">
            <StyledText variant="body1" color="textSecondary">{medication.notes}</StyledText>
          </Card>
        )}
        
        <StyledView className="mx-4 mb-6">
            <StyledButton 
                variant="textDestructive"
                onPress={() => Alert.alert("Delete Medication?", "This action cannot be undone.", [{text: "Cancel"}, {text: "Delete", style: "destructive", onPress: () => console.log("Deleting medication", medication.id)}])}
                iconNameLeft="trash-outline"
            >
                Delete Medication
            </StyledButton>
        </StyledView>

      </StyledScrollView>
    </ScreenContainer>
  );
};

export default MedicationDetailScreen; 