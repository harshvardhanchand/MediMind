import React, { useState, useEffect } from 'react';
import { View, StyleSheet, ScrollView, Dimensions, ActivityIndicator } from 'react-native';
import { Appbar, Button, Card, Text, Chip, FAB, Divider, TouchableRipple } from 'react-native-paper';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { LineChart } from 'react-native-chart-kit';

import { MainAppStackParamList } from '../navigation/types';
import { healthReadingsServices } from '../api/services';
import { HealthReadingResponse } from '../types/api';
import { ReadingType, ReadingData, ChartDataset } from '../types/interfaces';

type HealthReadingsScreenNavigationProp = NativeStackNavigationProp<MainAppStackParamList, 'HealthReadings'>;

// Dummy health reading data for fallback
const dummyReadings: ReadingData[] = [
  {
    date: 'May 3',
    bloodPressureSystolic: 128,
    bloodPressureDiastolic: 82,
    bloodGlucose: 95,
    heartRate: 72,
  },
  {
    date: 'May 4',
    bloodPressureSystolic: 130,
    bloodPressureDiastolic: 84,
    bloodGlucose: 98,
    heartRate: 74,
  },
  {
    date: 'May 5',
    bloodPressureSystolic: 125,
    bloodPressureDiastolic: 80,
    bloodGlucose: 92,
    heartRate: 75,
  },
  {
    date: 'May 6',
    bloodPressureSystolic: 127,
    bloodPressureDiastolic: 81,
    bloodGlucose: 94,
    heartRate: 76,
  },
  {
    date: 'May 7',
    bloodPressureSystolic: 126,
    bloodPressureDiastolic: 80,
    bloodGlucose: 93,
    heartRate: 73,
  },
  {
    date: 'May 8',
    bloodPressureSystolic: 129,
    bloodPressureDiastolic: 83,
    bloodGlucose: 105,
    heartRate: 72,
  },
  {
    date: 'May 9',
    bloodPressureSystolic: 128,
    bloodPressureDiastolic: 82,
    bloodGlucose: 96,
    heartRate: 71,
  },
];

const HealthReadingsScreen = () => {
  const navigation = useNavigation<HealthReadingsScreenNavigationProp>();
  const [selectedReadingType, setSelectedReadingType] = useState<ReadingType>('all');
  const [viewMode, setViewMode] = useState<'chart' | 'table'>('chart');

  // Data states
  const [readings, setReadings] = useState<ReadingData[]>([]);
  const [loading, setLoading] = useState(true);
  const [usingDummyData, setUsingDummyData] = useState(false);

  const screenWidth = Dimensions.get('window').width - 32; // Adjust for padding

  useEffect(() => {
    fetchHealthReadings();
  }, []);

  const fetchHealthReadings = async () => {
    try {
      setLoading(true);
      setUsingDummyData(false);

      console.log('Trying to fetch real health readings from API...');
      const response = await healthReadingsServices.getHealthReadings();

      if (response.data && response.data.length > 0) {
        console.log(`Loaded ${response.data.length} real health readings from API`);
        const convertedReadings = convertApiReadingsToDisplayFormat(response.data);
        setReadings(convertedReadings);
        setUsingDummyData(false);
      } else {
        console.log('API returned empty data, using dummy health readings');
        setReadings(dummyReadings);
        setUsingDummyData(true);
      }
    } catch (err: any) {
      console.log('API call failed, falling back to dummy data:', err.message);
      setReadings(dummyReadings);
      setUsingDummyData(true);
    } finally {
      setLoading(false);
    }
  };

  const convertApiReadingsToDisplayFormat = (apiReadings: HealthReadingResponse[]): ReadingData[] => {
    // Group readings by date
    const groupedByDate = apiReadings.reduce((acc: any, reading) => {
      const date = new Date(reading.reading_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
      if (!acc[date]) {
        acc[date] = {
          date,
          bloodPressureSystolic: undefined,
          bloodPressureDiastolic: undefined,
          bloodGlucose: undefined,
          heartRate: undefined,
        };
      }

      // Map reading types to display format
      if (reading.reading_type === 'blood_pressure') {
        acc[date].bloodPressureSystolic = reading.systolic_value;
        acc[date].bloodPressureDiastolic = reading.diastolic_value;
      } else if (reading.reading_type === 'glucose') {
        acc[date].bloodGlucose = reading.numeric_value;
      } else if (reading.reading_type === 'heart_rate') {
        acc[date].heartRate = reading.numeric_value;
      }

      return acc;
    }, {});

    return Object.values(groupedByDate) as ReadingData[];
  };

  const handleReadingTypeChange = (value: ReadingType) => {
    setSelectedReadingType(value);
  };

  // Get chart data based on reading type
  const getChartData = () => {
    const labels = readings.map(reading => reading.date);

    const datasets: ChartDataset[] = [];

    if (selectedReadingType === 'all' || selectedReadingType === 'bloodPressure') {
      datasets.push({
        data: readings.map(reading => reading.bloodPressureSystolic || 0),
        color: () => '#2196F3', // blue
        strokeWidth: 2,
        label: 'Blood Pressure (systolic)',
      });
    }

    if (selectedReadingType === 'all' || selectedReadingType === 'bloodGlucose') {
      datasets.push({
        data: readings.map(reading => reading.bloodGlucose || 0),
        color: () => '#4CAF50', // green
        strokeWidth: 2,
        label: 'Blood Glucose (mg/dL)',
      });
    }

    if (selectedReadingType === 'all' || selectedReadingType === 'heartRate') {
      datasets.push({
        data: readings.map(reading => reading.heartRate || 0),
        color: () => '#F44336', // red
        strokeWidth: 2,
        label: 'Heart Rate (bpm)',
      });
    }

    return {
      labels,
      datasets,
    };
  };

  if (loading) {
    return (
      <View style={[styles.container, styles.loadingContainer]}>
        <ActivityIndicator size="large" />
        <Text style={styles.loadingText}>Loading health readings...</Text>
      </View>
    );
  }

  // Render the chart view
  const renderChartView = () => {
    const chartData = getChartData();

    return (
      <View style={styles.chartContainer}>
        <LineChart
          data={chartData}
          width={screenWidth}
          height={300}
          chartConfig={{
            backgroundColor: '#FFFFFF',
            backgroundGradientFrom: '#FFFFFF',
            backgroundGradientTo: '#FFFFFF',
            decimalPlaces: 0,
            color: (opacity = 1) => `rgba(0, 0, 0, ${opacity})`,
            labelColor: (opacity = 1) => `rgba(0, 0, 0, ${opacity})`,
            style: {
              borderRadius: 16,
            },
            propsForDots: {
              r: '4',
              strokeWidth: '1',
              stroke: '#FFFFFF',
            },
          }}
          bezier
          style={styles.chart}
          fromZero
        />
        <View style={styles.legendContainer}>
          {selectedReadingType === 'all' || selectedReadingType === 'bloodPressure' ? (
            <Chip style={[styles.legendChip, { backgroundColor: '#E3F2FD' }]} textStyle={{ color: '#2196F3' }}>Blood Pressure (systolic)</Chip>
          ) : null}
          {selectedReadingType === 'all' || selectedReadingType === 'bloodGlucose' ? (
            <Chip style={[styles.legendChip, { backgroundColor: '#E8F5E9' }]} textStyle={{ color: '#4CAF50' }}>Blood Glucose (mg/dL)</Chip>
          ) : null}
          {selectedReadingType === 'all' || selectedReadingType === 'heartRate' ? (
            <Chip style={[styles.legendChip, { backgroundColor: '#FFEBEE' }]} textStyle={{ color: '#F44336' }}>Heart Rate (bpm)</Chip>
          ) : null}
        </View>
      </View>
    );
  };

  // Render the table view
  const renderTableView = () => {
    return (
      <View style={styles.tableContainer}>
        <View style={styles.tableHeader}>
          <Text style={[styles.tableHeaderCell, { flex: 1.5 }]}>Date</Text>
          {selectedReadingType === 'all' || selectedReadingType === 'bloodPressure' ? (
            <Text style={styles.tableHeaderCell}>Blood Pressure (mmHg)</Text>
          ) : null}
          {selectedReadingType === 'all' || selectedReadingType === 'bloodGlucose' ? (
            <Text style={styles.tableHeaderCell}>Blood Glucose (mg/dL)</Text>
          ) : null}
          {selectedReadingType === 'all' || selectedReadingType === 'heartRate' ? (
            <Text style={styles.tableHeaderCell}>Heart Rate (bpm)</Text>
          ) : null}
        </View>
        {readings.map((reading, index) => (
          <View key={index} style={styles.tableRow}>
            <Text style={[styles.tableCell, { flex: 1.5 }]}>{reading.date}</Text>
            {selectedReadingType === 'all' || selectedReadingType === 'bloodPressure' ? (
              <Text style={styles.tableCell}>
                {reading.bloodPressureSystolic}/{reading.bloodPressureDiastolic}
              </Text>
            ) : null}
            {selectedReadingType === 'all' || selectedReadingType === 'bloodGlucose' ? (
              <Text style={styles.tableCell}>{reading.bloodGlucose}</Text>
            ) : null}
            {selectedReadingType === 'all' || selectedReadingType === 'heartRate' ? (
              <Text style={styles.tableCell}>{reading.heartRate}</Text>
            ) : null}
          </View>
        ))}
      </View>
    );
  };

  return (
    <View style={styles.container}>
      <Appbar.Header>
        <Appbar.BackAction onPress={() => navigation.goBack()} />
        <Appbar.Content title="Health Readings" />
      </Appbar.Header>

      <View style={styles.headerContainer}>
        <Text style={styles.headerTitle}>Health Readings</Text>
        <Text style={styles.headerSubtitle}>Track and monitor your health metrics</Text>

        {usingDummyData && (
          <View style={styles.dummyDataBanner}>
            <Text style={styles.dummyDataText}>
              Showing sample data (API not connected)
            </Text>
          </View>
        )}
      </View>

      <View style={styles.filterContainer}>
        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
          <Button
            mode={selectedReadingType === 'all' ? 'contained' : 'outlined'}
            onPress={() => handleReadingTypeChange('all')}
            style={styles.filterButton}
          >
            All Readings
          </Button>
          <Button
            mode={selectedReadingType === 'bloodPressure' ? 'contained' : 'outlined'}
            onPress={() => handleReadingTypeChange('bloodPressure')}
            style={styles.filterButton}
          >
            Blood Pressure
          </Button>
          <Button
            mode={selectedReadingType === 'bloodGlucose' ? 'contained' : 'outlined'}
            onPress={() => handleReadingTypeChange('bloodGlucose')}
            style={styles.filterButton}
          >
            Blood Glucose
          </Button>
          <Button
            mode={selectedReadingType === 'heartRate' ? 'contained' : 'outlined'}
            onPress={() => handleReadingTypeChange('heartRate')}
            style={styles.filterButton}
          >
            Heart Rate
          </Button>
        </ScrollView>
      </View>

      <Card style={styles.card}>
        <Card.Content>
          <View style={styles.cardHeader}>
            <Text style={styles.cardTitle}>Health Readings Overview</Text>
            <View style={styles.viewToggleContainer}>
              <TouchableRipple onPress={() => setViewMode('table')} style={viewMode === 'table' ? styles.activeViewToggle : styles.viewToggle}>
                <Text style={viewMode === 'table' ? styles.activeViewToggleText : styles.viewToggleText}>Table View</Text>
              </TouchableRipple>
              <TouchableRipple onPress={() => setViewMode('chart')} style={viewMode === 'chart' ? styles.activeViewToggle : styles.viewToggle}>
                <Text style={viewMode === 'chart' ? styles.activeViewToggleText : styles.viewToggleText}>Chart View</Text>
              </TouchableRipple>
            </View>
          </View>
          <Text style={styles.cardSubtitle}>View and analyze your health metrics</Text>
          <Divider style={styles.divider} />

          {viewMode === 'chart' ? renderChartView() : renderTableView()}
        </Card.Content>
      </Card>

      <FAB
        style={styles.fab}
        icon="plus"
        onPress={() => navigation.navigate('AddHealthReading')}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F7FA',
  },
  headerContainer: {
    paddingHorizontal: 16,
    paddingTop: 16,
    paddingBottom: 8,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
  },
  headerSubtitle: {
    fontSize: 16,
    color: '#666',
  },
  filterContainer: {
    paddingHorizontal: 16,
    paddingVertical: 8,
  },
  filterButton: {
    marginRight: 8,
  },
  card: {
    margin: 16,
    flex: 1,
    borderRadius: 12,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  cardSubtitle: {
    fontSize: 14,
    color: '#666',
  },
  divider: {
    marginVertical: 16,
  },
  chartContainer: {
    alignItems: 'center',
  },
  chart: {
    borderRadius: 16,
    paddingRight: 16,
  },
  legendContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'center',
    marginTop: 16,
  },
  legendChip: {
    marginRight: 8,
    marginBottom: 8,
  },
  tableContainer: {
    marginTop: 8,
  },
  tableHeader: {
    flexDirection: 'row',
    backgroundColor: '#ECEFF1',
    paddingVertical: 12,
    paddingHorizontal: 8,
    borderRadius: 8,
  },
  tableHeaderCell: {
    fontWeight: 'bold',
    flex: 1,
    fontSize: 13,
  },
  tableRow: {
    flexDirection: 'row',
    paddingVertical: 12,
    paddingHorizontal: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#ECEFF1',
  },
  tableCell: {
    flex: 1,
    fontSize: 13,
  },
  fab: {
    position: 'absolute',
    margin: 16,
    right: 0,
    bottom: 0,
  },
  viewToggleContainer: {
    flexDirection: 'row',
    backgroundColor: '#ECEFF1',
    borderRadius: 8,
    overflow: 'hidden',
  },
  viewToggle: {
    paddingHorizontal: 12,
    paddingVertical: 6,
  },
  activeViewToggle: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    backgroundColor: '#2A6BAC',
  },
  viewToggleText: {
    fontSize: 12,
    color: '#555',
  },
  activeViewToggleText: {
    fontSize: 12,
    color: '#FFF',
    fontWeight: 'bold',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    fontSize: 16,
    color: '#666',
    marginTop: 16,
  },
  dummyDataBanner: {
    backgroundColor: '#FFEBEE',
    padding: 8,
    borderRadius: 4,
    marginTop: 8,
  },
  dummyDataText: {
    fontSize: 12,
    color: '#F44336',
    fontWeight: 'bold',
  },
});

export default HealthReadingsScreen; 