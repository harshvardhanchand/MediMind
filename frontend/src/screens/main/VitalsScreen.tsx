import React, { useState, useEffect } from 'react';
import { View, FlatList, TouchableOpacity, ListRenderItem } from 'react-native';
import { styled } from 'nativewind';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { Activity, Heart, Calendar, Footprints, Plus, LineChart, Droplets, ActivitySquare, Thermometer } from 'lucide-react-native';
import { Ionicons } from '@expo/vector-icons';
import { ActivityIndicator as PaperActivityIndicator } from 'react-native-paper';

import { MainAppStackParamList } from '../../navigation/types';
import ScreenContainer from '../../components/layout/ScreenContainer';
import StyledText from '../../components/common/StyledText';
import StyledButton from '../../components/common/StyledButton';
import { HealthReadingResponse, HealthReadingType } from '../../types/api';
import { healthReadingsServices } from '../../api/services';
import { useTheme } from '../../theme';

const StyledView = styled(View);
const StyledTouchableOpacity = styled(TouchableOpacity);

const initialMockHealthReadings: HealthReadingResponse[] = [
  {
    health_reading_id: '1',
    user_id: 'mock-user-1',
    reading_type: HealthReadingType.BLOOD_PRESSURE,
    systolic_value: 120,
    diastolic_value: 80,
    unit: 'mmHg',
    reading_date: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString(),
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    health_reading_id: '2',
    user_id: 'mock-user-1',
    reading_type: HealthReadingType.GLUCOSE,
    numeric_value: 95,
    unit: 'mg/dL',
    reading_date: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    notes: 'Fasting',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    health_reading_id: '3',
    user_id: 'mock-user-1',
    reading_type: HealthReadingType.HEART_RATE,
    numeric_value: 72,
    unit: 'bpm',
    reading_date: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    health_reading_id: '4',
    user_id: 'mock-user-1',
    reading_type: HealthReadingType.STEPS,
    numeric_value: 3450,
    unit: 'steps',
    reading_date: new Date(Date.now() - 25 * 60 * 60 * 1000).toISOString(),
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
];

type VitalsScreenNavigationProp = NativeStackNavigationProp<MainAppStackParamList, 'Vitals'>;

const VitalsScreen = () => {
  const navigation = useNavigation<VitalsScreenNavigationProp>();
  const { colors } = useTheme();

  const [displayedReadings, setDisplayedReadings] = useState<HealthReadingResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [usingDummyData, setUsingDummyData] = useState(false);

  const loadHealthReadingsFromApi = async () => {
    setLoading(true);
    setUsingDummyData(false);
    
    try {
      console.log('Trying to fetch real health readings from API...');
      const response = await healthReadingsServices.getHealthReadings();
      
      if (response.data && response.data.length > 0) {
        console.log(`Loaded ${response.data.length} real health readings from API`);
        setDisplayedReadings(response.data);
        setUsingDummyData(false);
      } else {
        console.log('API returned empty data, using dummy health readings');
        setDisplayedReadings(initialMockHealthReadings);
        setUsingDummyData(true);
      }
    } catch (err: any) {
      console.log('API call failed, falling back to dummy data:', err.message);
      setDisplayedReadings(initialMockHealthReadings);
      setUsingDummyData(true);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHealthReadingsFromApi();
  }, []);

  const getVitalIcon = (type: HealthReadingType, color: string) => {
    switch (type) {
      case HealthReadingType.BLOOD_PRESSURE: return <ActivitySquare size={20} color={color} />;
      case HealthReadingType.HEART_RATE: return <Heart size={20} color={color} />;
      case HealthReadingType.GLUCOSE: return <Droplets size={20} color={color} />;
      case HealthReadingType.STEPS: return <Footprints size={20} color={color} />;
      case HealthReadingType.TEMPERATURE: return <Thermometer size={20} color={color} />;
      default: return <Activity size={20} color={color} />;
    }
  };

  const formatReadingValue = (reading: HealthReadingResponse): string => {
    switch (reading.reading_type) {
      case HealthReadingType.BLOOD_PRESSURE:
        return `${reading.systolic_value || 'N/A'}/${reading.diastolic_value || 'N/A'} ${reading.unit || ''}`;
      case HealthReadingType.GLUCOSE:
      case HealthReadingType.HEART_RATE:
      case HealthReadingType.STEPS:
      case HealthReadingType.WEIGHT:
      case HealthReadingType.HEIGHT:
      case HealthReadingType.BMI:
      case HealthReadingType.SPO2:
      case HealthReadingType.TEMPERATURE:
      case HealthReadingType.RESPIRATORY_RATE:
      case HealthReadingType.PAIN_LEVEL:
        return `${reading.numeric_value || 'N/A'} ${reading.unit || ''}`;
      case HealthReadingType.SLEEP:
        return reading.text_value || (reading.numeric_value ? `${reading.numeric_value} hours` : 'N/A');
      case HealthReadingType.OTHER:
        return reading.text_value || JSON.stringify(reading.json_value) || 'N/A';
      default:
        return 'N/A';
    }
  };

  const renderVitalItem: ListRenderItem<HealthReadingResponse> = ({ item }) => {
    const iconColor = colors.primary;
    const iconBg = 'bg-primary/10';

    return (
      <StyledTouchableOpacity 
        tw="p-3 mb-3 bg-white rounded-lg shadow-sm flex-row items-center"
        style={{ borderRadius: 12 }}
      >
        <StyledView tw={`${iconBg} p-2 rounded-md mr-3`}>
          {getVitalIcon(item.reading_type, iconColor)}
        </StyledView>
        <StyledView tw="flex-1">
          <StyledView tw="flex-row justify-between items-center">
            <StyledText variant="label" tw="font-semibold text-gray-800">{item.reading_type.replace('_', ' ').toUpperCase()}</StyledText>
          </StyledView>
          <StyledText variant="h4" tw="text-gray-700">{formatReadingValue(item)}</StyledText>
          <StyledView tw="flex-row items-center mt-1">
            <Calendar size={12} color="#6B7280" />
            <StyledText variant="caption" color="textSecondary" tw="ml-1">
              {new Date(item.reading_date).toLocaleString()}
            </StyledText>
          </StyledView>
          {item.notes && <StyledText variant="caption" color="textMuted" tw="mt-1">Notes: {item.notes}</StyledText>}
        </StyledView>
      </StyledTouchableOpacity>
    );
  };

  let mainContent;
  if (loading && usingDummyData) {
    mainContent = (
        <StyledView className="flex-1 items-center justify-center">
            <PaperActivityIndicator animating={true} size="large" />
            <StyledText variant="body1" color="textSecondary" tw="mt-2">Loading vitals...</StyledText>
        </StyledView>
    );
  } else if (displayedReadings.length === 0) {
    mainContent = (
        <StyledView className="flex-1 items-center justify-center">
            <Ionicons name="cloud-offline-outline" size={64} color={colors.textMuted} />
            <StyledText variant="h4" color="textMuted" tw="mt-4">No Vitals Recorded</StyledText>
            <StyledText color="textMuted" tw="text-center mt-1 mx-8">
                Tap 'Add New Vital Reading' to get started.
            </StyledText>
        </StyledView>
    );
  } else {
    mainContent = (
        <FlatList<HealthReadingResponse>
            data={displayedReadings}
            keyExtractor={(item) => item.health_reading_id}
            renderItem={renderVitalItem}
            showsVerticalScrollIndicator={false}
        />
    );
  }

  return (
    <ScreenContainer scrollable={false} withPadding>
      <StyledView tw="pt-2 pb-4 flex-row justify-between items-center">
        <View>
          <StyledText variant="h1" color="primary">Vitals</StyledText>
          <StyledText variant="body2" color="textSecondary" tw="mt-1">
            Track your health measurements
          </StyledText>
          
          {usingDummyData && (
            <StyledView tw="mt-3 p-2 bg-yellow-100 rounded border border-yellow-300">
              <StyledText tw="text-yellow-800 text-sm text-center">
                📱 Showing sample data (API not connected)
              </StyledText>
            </StyledView>
          )}
        </View>
        <StyledButton variant="textPrimary" onPress={loadHealthReadingsFromApi} tw="px-2 py-1">
            {usingDummyData ? "Show API" : "Show Mock"}
        </StyledButton>
      </StyledView>
      
      <StyledView tw="mb-4 bg-blue-50 p-4 rounded-lg">
        <StyledText variant="label" tw="font-semibold text-blue-700 mb-1">
          Vitals Overview
        </StyledText>
        <StyledText variant="body2" color="textSecondary">
          Keep track of your important health numbers here. Add new readings regularly.
        </StyledText>
      </StyledView>
      
      <StyledView tw="flex-1">
        {mainContent}
      </StyledView>
      
      <StyledView tw="pt-3">
        <StyledButton 
          variant="filledPrimary"
          iconLeft={<Plus size={18} color={colors.onPrimary} />}
          onPress={() => navigation.navigate('AddHealthReading')} 
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