import React from 'react';
import { View, FlatList, TouchableOpacity, ListRenderItem } from 'react-native';
import { styled } from 'nativewind';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { MainAppStackParamList } from '../../navigation/types';
import { Activity, Heart, Calendar, Footprints, Plus, LineChart } from 'lucide-react-native';

import ScreenContainer from '../../components/layout/ScreenContainer';
import StyledText from '../../components/common/StyledText';
import StyledButton from '../../components/common/StyledButton';

const StyledView = styled(View);
const StyledTouchableOpacity = styled(TouchableOpacity);

// Define vital type
interface Vital {
  id: string;
  type: string;
  value: string;
  date: string;
  iconBg: string;
  iconColor: string;
  icon: 'activity' | 'heart' | 'footprints';
  trend?: 'up' | 'down' | 'stable';
}

// Dummy data with enhanced properties
const dummyVitals: Vital[] = [
  { 
    id: '1', 
    type: 'Blood Pressure', 
    value: '120/80 mmHg', 
    date: 'Today, 8:00 AM',
    iconBg: 'bg-medical-lightblue',
    iconColor: '#0EA5E9',
    icon: 'activity',
    trend: 'stable'
  },
  { 
    id: '2', 
    type: 'Blood Sugar', 
    value: '95 mg/dL', 
    date: 'Today, 7:30 AM',
    iconBg: 'bg-medical-lightgreen',
    iconColor: '#4ADE80',
    icon: 'activity',
    trend: 'down'
  },
  { 
    id: '3', 
    type: 'Heart Rate', 
    value: '72 bpm', 
    date: 'Yesterday, 9:15 PM',
    iconBg: 'bg-medical-lightred',
    iconColor: '#ea384c',
    icon: 'heart',
    trend: 'up'
  },
  { 
    id: '4', 
    type: 'Steps', 
    value: '3,450 steps', 
    date: 'Yesterday',
    iconBg: 'bg-medical-lightgray',
    iconColor: '#6B7280',
    icon: 'footprints',
    trend: 'up'
  }
];

type VitalsScreenNavigationProp = NativeStackNavigationProp<MainAppStackParamList, 'Vitals'>;

const VitalsScreen = () => {
  const navigation = useNavigation<VitalsScreenNavigationProp>();

  const getVitalIcon = (icon: string, color: string) => {
    switch (icon) {
      case 'activity':
        return <Activity size={20} color={color} />;
      case 'heart':
        return <Heart size={20} color={color} />;
      case 'footprints':
        return <Footprints size={20} color={color} />;
      default:
        return <Activity size={20} color={color} />;
    }
  };

  const renderVitalItem: ListRenderItem<Vital> = ({ item }) => (
    <StyledTouchableOpacity 
      tw="p-3 mb-3 bg-white rounded-lg shadow-sm flex-row items-center"
      onPress={() => {/* Navigate to detail or show chart */}}
      style={{ borderRadius: 12 }}
    >
      <StyledView tw={`${item.iconBg} p-2 rounded-md mr-3`}>
        {getVitalIcon(item.icon, item.iconColor)}
      </StyledView>
      <StyledView tw="flex-1">
        <StyledView tw="flex-row justify-between items-center">
          <StyledText variant="label" tw="font-semibold text-gray-800">{item.type}</StyledText>
          <StyledView tw="flex-row items-center">
            {item.trend === 'up' && <StyledView tw="w-0 h-0 border-l-4 border-r-4 border-b-8 border-l-transparent border-r-transparent border-b-green-500 mr-1" />}
            {item.trend === 'down' && <StyledView tw="w-0 h-0 border-l-4 border-r-4 border-t-8 border-l-transparent border-r-transparent border-t-red-500 mr-1" />}
            {item.trend === 'stable' && <StyledView tw="w-4 h-1 bg-gray-400 mr-1" />}
            <LineChart size={16} color="#6B7280" />
          </StyledView>
        </StyledView>
        <StyledText variant="h4" tw="text-gray-700">{item.value}</StyledText>
        <StyledView tw="flex-row items-center mt-1">
          <Calendar size={12} color="#6B7280" />
          <StyledText variant="caption" color="textSecondary" tw="ml-1">{item.date}</StyledText>
        </StyledView>
      </StyledView>
    </StyledTouchableOpacity>
  );

  return (
    <ScreenContainer scrollable={false} withPadding>
      {/* Header */}
      <StyledView tw="pt-2 pb-4">
        <StyledText variant="h1" color="primary">Vitals</StyledText>
        <StyledText variant="body2" color="textSecondary" tw="mt-1">
          Track your health measurements and see trends
        </StyledText>
      </StyledView>
      
      {/* Summary Section */}
      <StyledView tw="mb-4 bg-medical-lightgray p-4 rounded-lg">
        <StyledText variant="label" tw="font-semibold text-gray-700 mb-1">
          Last 7 Days Summary
        </StyledText>
        <StyledText variant="body2" color="textSecondary">
          Your blood pressure readings are improving. Keep monitoring your heart rate.
        </StyledText>
      </StyledView>
      
      {/* Vitals List */}
      <StyledView tw="flex-1">
        <FlatList<Vital>
          data={dummyVitals}
          keyExtractor={(item) => item.id}
          renderItem={renderVitalItem}
          showsVerticalScrollIndicator={false}
        />
      </StyledView>
      
      {/* Add Button */}
      <StyledView tw="pt-3">
        <StyledButton 
          variant="primary"
          icon={() => <Plus size={18} color="#FFFFFF" />}
          onPress={() => {/* Navigate to add vital screen */}} 
          tw="w-full"
          style={{ borderRadius: 10 }}
        >
          Add New Vital Reading
        </StyledButton>
      </StyledView>
    </ScreenContainer>
  );
};

export default VitalsScreen; 