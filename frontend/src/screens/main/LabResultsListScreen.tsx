import React, { useState } from 'react';
import { View, FlatList, ListRenderItem, TouchableOpacity } from 'react-native';
import { styled } from 'nativewind';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import Ionicons from 'react-native-vector-icons/Ionicons';

import ScreenContainer from '../../components/layout/ScreenContainer';
import StyledText from '../../components/common/StyledText';
import ListItem from '../../components/common/ListItem';
import { MainAppStackParamList } from '../../navigation/types'; 
import { useTheme } from '../../theme';

const StyledView = styled(View);
const StyledTouchableOpacity = styled(TouchableOpacity);

interface LabTestTypeSummary {
  id: string; // e.g., 'glucose_panel', 'cbc'
  name: string; // e.g., "Blood Glucose", "Complete Blood Count"
  iconName: string;
  mostRecentDate?: string;
  resultCount?: number;
}

// Mock data for lab test types/categories
const dummyLabTestTypes: LabTestTypeSummary[] = [
  {
    id: 'glucose_fasting',
    name: 'Fasting Glucose',
    iconName: 'water-outline', // Placeholder, could be more specific
    mostRecentDate: 'May 10, 2024',
    resultCount: 5,
  },
  {
    id: 'lipid_panel',
    name: 'Lipid Panel',
    iconName: 'heart-outline', // Placeholder
    mostRecentDate: 'May 10, 2024',
    resultCount: 3,
  },
  {
    id: 'cbc',
    name: 'Complete Blood Count (CBC)',
    iconName: 'eyedrop-outline', // Placeholder for blood drop or microscope
    mostRecentDate: 'Apr 20, 2024',
    resultCount: 2,
  },
  {
    id: 'thyroid_panel',
    name: 'Thyroid Panel (TSH, T3, T4)',
    iconName: 'analytics-outline',
    mostRecentDate: 'Jan 15, 2024',
    resultCount: 1,
  },
];

// Update navigation prop type to use 'LabResultsList' (assuming you added it to types.ts)
// and define params for LabResultDetail
type LabResultsListNavigationProp = NativeStackNavigationProp<MainAppStackParamList, 'LabResultsList'>;

const LabResultsListScreen = () => {
  const navigation = useNavigation<LabResultsListNavigationProp>();
  const { colors } = useTheme();

  const renderLabTestTypeItem: ListRenderItem<LabTestTypeSummary> = ({ item }) => (
    <ListItem
      key={item.id}
      label={item.name}
      subtitle={item.mostRecentDate ? `Last: ${item.mostRecentDate} (${item.resultCount} results)` : `${item.resultCount || 0} results`}
      iconLeft={item.iconName}
      iconLeftColor={colors.accentPrimary} 
      onPress={() => {
        navigation.navigate('LabResultDetail', { testTypeId: item.id, testTypeName: item.name });
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
        <StyledText variant="h3" tw="font-semibold flex-1 text-center">Lab Results</StyledText>
        <StyledView className="w-8" /> {/* Spacer for balance */}
      </StyledView>

      {/* TODO: Add Search/Filter bar if needed */}

      <FlatList<LabTestTypeSummary>
        data={dummyLabTestTypes}
        keyExtractor={(item) => item.id}
        renderItem={renderLabTestTypeItem}
        showsVerticalScrollIndicator={false}
        contentContainerStyle={{ paddingHorizontal: 16, paddingTop: 12, paddingBottom: 20 }}
        ItemSeparatorComponent={() => <StyledView className="h-px bg-borderSubtle ml-14" />} 
      />
    </ScreenContainer>
  );
};

export default LabResultsListScreen; 