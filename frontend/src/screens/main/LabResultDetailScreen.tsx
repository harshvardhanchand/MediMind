import React, { useLayoutEffect, useState, useEffect } from 'react';
import { View, FlatList, ListRenderItem, TouchableOpacity, Dimensions, Platform, ActivityIndicator } from 'react-native';
import { styled } from 'nativewind';
import { useNavigation, useRoute, RouteProp } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { Ionicons } from '@expo/vector-icons';
import { LineChart } from 'react-native-chart-kit';

import ScreenContainer from '../../components/layout/ScreenContainer';
import StyledText from '../../components/common/StyledText';
import ListItem from '../../components/common/ListItem';
import Card from '../../components/common/Card';
import EmptyState from '../../components/common/EmptyState';
import ErrorState from '../../components/common/ErrorState';
import { MainAppStackParamList } from '../../navigation/types'; 
import { useTheme } from '../../theme';
import { ERROR_MESSAGES, LOADING_MESSAGES, EMPTY_STATE_MESSAGES } from '../../constants/messages';

const StyledView = styled(View);
const StyledTouchableOpacity = styled(TouchableOpacity);

interface LabResultEntry {
  id: string;
  date: string;
  value: string; // Keep as string for input, convert for chart
  unit: string;
  referenceRange?: string;
  notes?: string;
}

// Mock data for a specific lab test type's history
const getMockLabHistory = (testTypeId: string, testTypeName: string): LabResultEntry[] => {
  if (testTypeId === 'glucose_fasting') {
    return [
      { id: 'g1', date: '2024-01-10', value: '105', unit: 'mg/dL', referenceRange: '70-100' },
      { id: 'g2', date: '2024-02-15', value: '98', unit: 'mg/dL', referenceRange: '70-100' },
      { id: 'g3', date: '2024-03-20', value: '110', unit: 'mg/dL', referenceRange: '70-100' },
      { id: 'g4', date: '2024-04-25', value: '95', unit: 'mg/dL', referenceRange: '70-100' },
      { id: 'g5', date: '2024-05-10', value: '102', unit: 'mg/dL', referenceRange: '70-100' },
    ];
  }
  if (testTypeId === 'lipid_panel') {
    return [
      { id: 'l1', date: '2024-03-01', value: '190', unit: 'mg/dL', referenceRange: '<200 (Total Cholesterol)' },
      { id: 'l2', date: '2024-05-10', value: '180', unit: 'mg/dL', referenceRange: '<200 (Total Cholesterol)' },
    ];
  }
  return [];
};

type LabResultDetailNavigationProp = NativeStackNavigationProp<any, any>;
type LabResultDetailRouteProp = RouteProp<any, any>;

const LabResultDetailScreen = () => {
  const navigation = useNavigation<LabResultDetailNavigationProp>();
  const route = useRoute<LabResultDetailRouteProp>();
  const { colors } = useTheme();
  const { testTypeId, testTypeName } = route.params as { testTypeId: string; testTypeName: string };

  const [labHistory, setLabHistory] = useState<LabResultEntry[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Simulate fetching data with proper async handling
    const fetchLabHistory = async () => {
      try {
        setIsLoading(true);
        setError(null);
        // Simulate API delay
        await new Promise(resolve => setTimeout(resolve, 500));
        const data = getMockLabHistory(testTypeId, testTypeName);
        setLabHistory(data);
      } catch (e: any) {
        console.error('Error fetching lab history:', e);
        setError('Failed to load lab results. Please try again.');
      } finally {
        setIsLoading(false);
      }
    };

    fetchLabHistory();
  }, [testTypeId, testTypeName]);

  useLayoutEffect(() => {
    navigation.setOptions({
      headerTitle: testTypeName,
      headerLeft: () => (
        <StyledTouchableOpacity onPress={() => navigation.goBack()} className="p-1.5 ml-[-8px]">
            <Ionicons name="chevron-back-outline" size={28} color={colors.accentPrimary} />
        </StyledTouchableOpacity>
      ),
      headerStyle: { backgroundColor: colors.backgroundSecondary },
      headerTitleStyle: { color: colors.textPrimary, fontWeight: '600' },
    });
  }, [navigation, colors, testTypeName]);

  const renderResultItem: ListRenderItem<LabResultEntry> = ({ item }) => (
    <ListItem
      key={item.id}
      label={item.date} // Show date as primary label
      value={`${item.value} ${item.unit}`}
      subtitle={item.referenceRange ? `Ref: ${item.referenceRange}` : undefined}
      tw="px-4" // Add horizontal padding to ListItem itself if Card has noPadding
    />
  );

  const chartLabels = labHistory.length > 0 
    ? labHistory.map(entry => new Date(entry.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })).slice(-7)
    : ['N/A'];
  const chartDatasetData = labHistory.length > 0
    ? labHistory.map(entry => parseFloat(entry.value) || 0).slice(-7)
    : [0];

  const chartData = {
    labels: chartLabels,
    datasets: [
      {
        data: chartDatasetData,
        color: (opacity = 1) => colors.accentPrimary || `rgba(0, 122, 255, ${opacity})`, 
        strokeWidth: 2,
      },
    ],
  };

  const screenWidth = Dimensions.get('window').width;

  return (
    <ScreenContainer scrollable={false} withPadding={false} backgroundColor={colors.backgroundPrimary}>
      {isLoading ? (
        <StyledView className="flex-1 justify-center items-center">
          <ActivityIndicator size="large" color={colors.accentPrimary} />
          <StyledText 
            variant="body1" 
            tw="mt-4 text-center"
            style={{ color: colors.textSecondary }}
          >
            {LOADING_MESSAGES.GENERIC_LOADING}
          </StyledText>
        </StyledView>
      ) : error ? (
        <ErrorState
          title="Unable to Load Lab Results"
          message={error}
          icon="flask-outline"
        />
      ) : labHistory.length === 0 ? (
        <EmptyState
          icon="flask-outline"
          title="No Lab Results"
          description="No lab results are available for this test type."
        />
      ) : (
        <FlatList<LabResultEntry>
          data={labHistory}
          keyExtractor={(item) => item.id}
          renderItem={renderResultItem}
          showsVerticalScrollIndicator={false}
          contentContainerStyle={{ paddingBottom: 20 }}
          ItemSeparatorComponent={() => <StyledView className="h-px bg-borderSubtle ml-4" />}
          ListHeaderComponent={() => (
            <StyledView className="pt-4">
              <StyledText variant="body1" color="textSecondary" tw="text-center mb-4 px-4">Historical Trend</StyledText>
              <Card tw="mx-4 mb-6 items-center justify-center h-60 bg-backgroundSecondary p-0 overflow-hidden rounded-xl">
                {labHistory.length > 1 ? (
                  <LineChart
                    data={chartData}
                    width={screenWidth - 32}
                    height={230}
                    chartConfig={{
                      backgroundColor: colors.backgroundSecondary,
                      backgroundGradientFrom: colors.backgroundSecondary,
                      backgroundGradientTo: colors.backgroundSecondary,
                      decimalPlaces: 1,
                      color: (opacity = 1) => colors.accentPrimary || `rgba(0, 122, 255, ${opacity})`,
                      labelColor: (opacity = 1) => colors.textSecondary || `rgba(0, 0, 0, ${opacity})`,
                      style: { borderRadius: 16 },
                      propsForDots: { r: "5", strokeWidth: "2", stroke: colors.accentPrimary },
                      propsForBackgroundLines: { stroke: colors.borderSubtle, strokeDasharray: "" },
                    }}
                    bezier
                    style={{ borderRadius: 16 }}
                    yAxisLabel={labHistory[0]?.unit ? '' : ''}
                    yAxisSuffix={labHistory[0]?.unit ? ` ${labHistory[0].unit}` : ''}
                    yAxisInterval={1} 
                    segments={Platform.OS === 'android' && chartDatasetData.length > 0 && Math.max(...chartDatasetData) - Math.min(...chartDatasetData) < 4 ? Math.max(...chartDatasetData) - Math.min(...chartDatasetData) +1 : undefined}
                  />
                ) : (
                  <StyledView className="flex-1 items-center justify-center p-4">
                      <Ionicons name="analytics-outline" size={48} color={colors.textMuted} />
                      <StyledText color="textMuted" tw="mt-2 text-center">
                          {labHistory.length === 1 ? 'Not enough data to plot a trend. At least two data points are needed.' : 'No data available for chart.'}
                      </StyledText>
                  </StyledView>
                )}
              </Card>
              {labHistory.length > 0 && <StyledText variant="h4" tw="mb-2 font-semibold px-4">History</StyledText>}
            </StyledView>
          )}
        />
      )}
    </ScreenContainer>
  );
};

export default LabResultDetailScreen; 