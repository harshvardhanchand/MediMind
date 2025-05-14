import React from 'react';
import { ScrollView } from 'react-native';
import { styled } from 'nativewind';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';

import ScreenContainer from '../../components/layout/ScreenContainer';
import StyledText from '../../components/common/StyledText';
import Card from '../../components/common/Card';
import ListItem from '../../components/common/ListItem';
import { MainAppStackParamList } from '../../navigation/types';
import { useTheme } from '../../theme';

const StyledScrollView = styled(ScrollView);

interface HealthCategory {
  id: string;
  label: string;
  iconName: string;
  navigateTo: keyof MainAppStackParamList;
  description?: string;
}

const healthCategories: HealthCategory[] = [
  { id: 'meds', label: 'Medications', iconName: 'medkit-outline', navigateTo: 'MedicationsScreen', description: 'View prescribed and over-the-counter drugs' },
  { id: 'labs', label: 'Lab Results', iconName: 'flask-outline', navigateTo: 'LabResultsList', description: 'Track and view your test outcomes' },
  { id: 'vitals', label: 'Vitals', iconName: 'pulse-outline', navigateTo: 'Vitals', description: 'Monitor blood pressure, heart rate, etc.' },
  { id: 'symptoms', label: 'Symptoms', iconName: 'thermometer-outline', navigateTo: 'SymptomTracker', description: 'Log and review your symptoms' },
];

type HealthDataScreenNavigationProp = NativeStackNavigationProp<MainAppStackParamList>;

const HealthDataScreen = () => {
  const navigation = useNavigation<HealthDataScreenNavigationProp>();
  const { colors } = useTheme();

  return (
    <ScreenContainer scrollable={false} withPadding={false} backgroundColor={colors.backgroundTertiary}>
      <StyledScrollView className="flex-1">
        <StyledText variant="h1" tw="px-4 pt-6 pb-4 font-bold">Browse Health Data</StyledText>
        
        <Card tw="mx-4 mb-6" noPadding>
          {healthCategories.map((category, index) => (
            <ListItem
              key={category.id}
              label={category.label}
              subtitle={category.description}
              iconLeft={category.iconName}
              iconLeftColor={colors.accentPrimary}
              onPress={() => navigation.navigate(category.navigateTo as any)}
              showBottomBorder={index < healthCategories.length - 1}
            />
          ))}
        </Card>

      </StyledScrollView>
    </ScreenContainer>
  );
};

export default HealthDataScreen; 