import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { View, FlatList, TouchableOpacity, ListRenderItem, ActivityIndicator } from 'react-native';
import { styled } from 'nativewind';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { Activity, Heart, Calendar, Footprints, Plus, Droplets, ActivitySquare, Thermometer } from 'lucide-react-native';


import { MainAppStackParamList } from '../../navigation/types';
import ScreenContainer from '../../components/layout/ScreenContainer';
import StyledText from '../../components/common/StyledText';
import StyledButton from '../../components/common/StyledButton';
import EmptyState from '../../components/common/EmptyState';
import ErrorState from '../../components/common/ErrorState';
import { HealthReadingResponse, HealthReadingType } from '../../types/api';
import { healthReadingsServices } from '../../api/services';
import { useTheme } from '../../theme';
import { EMPTY_STATE_MESSAGES, ERROR_MESSAGES, LOADING_MESSAGES } from '../../constants/messages';

const StyledView = styled(View);
const StyledTouchableOpacity = styled(TouchableOpacity);

type VitalsScreenNavigationProp = NativeStackNavigationProp<MainAppStackParamList, 'Vitals'>;

const VitalsScreen = () => {
  const navigation = useNavigation<VitalsScreenNavigationProp>();
  const { colors } = useTheme();

  const [displayedReadings, setDisplayedReadings] = useState<HealthReadingResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [usingDummyData, setUsingDummyData] = useState(false);

  // ✅ Memoized dummy data - only created once
  const initialMockHealthReadings = useMemo<HealthReadingResponse[]>(() => [
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
  ], []);

  const loadHealthReadingsFromApi = useCallback(async () => {
    setLoading(true);
    setError(null);
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
      setError(null); // Clear error since we're showing dummy data
    } finally {
      setLoading(false);
    }
  }, [initialMockHealthReadings]);

  useEffect(() => {
    loadHealthReadingsFromApi();
  }, [loadHealthReadingsFromApi]);

  // ✅ Memoized utility functions
  const getVitalIcon = useCallback((type: HealthReadingType, color: string) => {
    switch (type) {
      case HealthReadingType.BLOOD_PRESSURE: return <ActivitySquare size={20} color={color} />;
      case HealthReadingType.HEART_RATE: return <Heart size={20} color={color} />;
      case HealthReadingType.GLUCOSE: return <Droplets size={20} color={color} />;
      case HealthReadingType.STEPS: return <Footprints size={20} color={color} />;
      case HealthReadingType.TEMPERATURE: return <Thermometer size={20} color={color} />;
      default: return <Activity size={20} color={color} />;
    }
  }, []);

  const formatReadingValue = useCallback((reading: HealthReadingResponse): string => {
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
  }, []);

  const renderVitalItem: ListRenderItem<HealthReadingResponse> = ({ item }) => {
    const iconColor = colors.primary;
    const iconBg = 'bg-primary/10';

    return (
      <StyledTouchableOpacity 
        className="p-3 mb-3 bg-white rounded-lg shadow-sm flex-row items-center"
        style={{ borderRadius: 12 }}
      >
        <StyledView tw={`${iconBg} p-2 rounded-md mr-3`}>
          {getVitalIcon(item.reading_type, iconColor)}
        </StyledView>
        <StyledView className="flex-1">
          <StyledView className="flex-row justify-between items-center">
            <StyledText variant="label" className="font-semibold text-gray-800">{item.reading_type.replace('_', ' ').toUpperCase()}</StyledText>
          </StyledView>
          <StyledText variant="h4" className="text-gray-700">{formatReadingValue(item)}</StyledText>
          <StyledView className="flex-row items-center mt-1">
            <Calendar size={12} color="#6B7280" />
            <StyledText variant="caption" color="textSecondary" className="ml-1">
              {new Date(item.reading_date).toLocaleString()}
            </StyledText>
          </StyledView>
          {item.notes && <StyledText variant="caption" color="textMuted" className="mt-1">Notes: {item.notes}</StyledText>}
        </StyledView>
      </StyledTouchableOpacity>
    );
  };

  let mainContent;
  if (loading) {
    return (
      <ScreenContainer>
        <StyledView className="flex-1 justify-center items-center">
          <ActivityIndicator size="large" color={colors.accentPrimary} />
          <StyledText 
            variant="body1" 
            className="mt-4 text-center"
            style={{ color: colors.textSecondary }}
          >
            {LOADING_MESSAGES.GENERIC_LOADING}
          </StyledText>
        </StyledView>
      </ScreenContainer>
    );
  } else if (error && !usingDummyData) {
    return (
      <ScreenContainer>
        <ErrorState
          title="Unable to Load Vitals"
          message={ERROR_MESSAGES.API_ERROR}
          onRetry={loadHealthReadingsFromApi}
          retryLabel="Try Again"
        />
      </ScreenContainer>
    );
  } else if (displayedReadings.length === 0 && !usingDummyData) {
    return (
      <ScreenContainer>
        <EmptyState
          icon="pulse-outline"
          title={EMPTY_STATE_MESSAGES.NO_HEALTH_READINGS.title}
          description={EMPTY_STATE_MESSAGES.NO_HEALTH_READINGS.description}
          actionLabel={EMPTY_STATE_MESSAGES.NO_HEALTH_READINGS.actionLabel}
          onAction={() => navigation.navigate('AddHealthReading')}
        />
      </ScreenContainer>
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
      <StyledView className="pt-2 pb-4 flex-row justify-between items-start">
        <StyledView className="flex-1 pr-2">
          <StyledText variant="h1" color="primary">Vitals</StyledText>
          <StyledText variant="body2" color="textSecondary" className="mt-1">
            Track your health measurements
          </StyledText>
          
          {usingDummyData && (
            <StyledView className="mt-3 p-2 bg-yellow-100 rounded border border-yellow-300">
              <StyledText className="text-yellow-800 text-sm text-center">
                📱 Showing sample data (API not connected)
              </StyledText>
            </StyledView>
          )}
        </StyledView>
        <StyledButton variant="textPrimary" onPress={loadHealthReadingsFromApi} className="px-2 py-1 min-w-0">
            <StyledText variant="caption" color="primary" className="text-xs">
              Show All
            </StyledText>
        </StyledButton>
      </StyledView>
      
      <StyledView className="mb-4 bg-blue-50 p-4 rounded-lg">
        <StyledText variant="label" className="font-semibold text-blue-700 mb-1">
          Vitals Overview
        </StyledText>
        <StyledText variant="body2" color="textSecondary">
          Keep track of your important health numbers here. Add new readings regularly.
        </StyledText>
      </StyledView>
      
      <StyledView className="flex-1">
        {mainContent}
      </StyledView>
      
      <StyledView className="pt-3">
        <StyledButton 
          variant="filledPrimary"
          iconLeft={<Plus size={18} color={colors.onPrimary} />}
          onPress={() => navigation.navigate('AddHealthReading')} 
          className="w-full"
          style={{ borderRadius: 10 }}
        >
          Add New Vital Reading
        </StyledButton>
      </StyledView>
    </ScreenContainer>
  );
};

export default VitalsScreen; 