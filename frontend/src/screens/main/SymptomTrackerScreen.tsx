import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { View, FlatList, TouchableOpacity, ListRenderItem, ActivityIndicator } from 'react-native';
import { styled } from 'nativewind';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { Plus, AlertCircle, ChevronRight } from 'lucide-react-native';

import { MainAppStackParamList } from '../../navigation/types';
import ScreenContainer from '../../components/layout/ScreenContainer';
import StyledText from '../../components/common/StyledText';
import StyledButton from '../../components/common/StyledButton';
import StyledInput from '../../components/common/StyledInput';
import EmptyState from '../../components/common/EmptyState';
import ErrorState from '../../components/common/ErrorState';
import { useTheme } from '../../theme';
import { symptomServices, SymptomCreate } from '../../api/services/symptomServices';
import { ERROR_MESSAGES, LOADING_MESSAGES } from '../../constants/messages';
import { SymptomEntry } from '../../types/interfaces';

const StyledView = styled(View);
const StyledTouchableOpacity = styled(TouchableOpacity);

type SymptomTrackerScreenNavigationProp = NativeStackNavigationProp<MainAppStackParamList, 'SymptomTracker'>;

const SymptomTrackerScreen = () => {
  const navigation = useNavigation<SymptomTrackerScreenNavigationProp>();
  const { colors } = useTheme();

  // Data states
  const [symptoms, setSymptoms] = useState<SymptomEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [usingDummyData, setUsingDummyData] = useState(false);
  const [apiConnected, setApiConnected] = useState(false);

  const [newSymptom, setNewSymptom] = useState('');
  const [severity, setSeverity] = useState('3');
  const [showForm, setShowForm] = useState(false);

  // ✅ Memoized dummy data - only created once
  const dummySymptoms = useMemo<SymptomEntry[]>(() => [
    {
      id: 'dummy-1',
      reading_date: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
      symptom: 'Headache',
      severity: 3,
      notes: 'Mild tension headache after work',
      color: colors.warning
    },
    {
      id: 'dummy-2',
      reading_date: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
      symptom: 'Fatigue',
      severity: 2,
      notes: 'Feeling tired after lunch',
      color: colors.info
    },
    {
      id: 'dummy-3',
      reading_date: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
      symptom: 'Nausea',
      severity: 4,
      notes: 'Feeling sick after medication',
      color: colors.error
    }
  ], [colors]);

  useEffect(() => {
    fetchSymptoms();
  }, []);

  const fetchSymptoms = async () => {
    try {
      setLoading(true);
      setError(null);
      setUsingDummyData(false);
      setApiConnected(false);

      console.log('Fetching symptoms from API...');

      // Call the real API
      const response = await symptomServices.getSymptoms({ limit: 50 });

      if (response.data && response.data.symptoms) {
        setApiConnected(true);

        // Convert API response to display format
        const formattedSymptoms: SymptomEntry[] = response.data.symptoms.map(symptom => {
          const formatted = symptomServices.formatSymptomForDisplay(symptom);
          return {
            id: formatted.id,
            reading_date: symptom.reported_date || symptom.created_at,
            symptom: formatted.name,
            severity: formatted.severityLevel,
            notes: formatted.notes,
            color: formatted.color
          };
        });

        // If API returns empty list, show mock data instead of empty state
        if (formattedSymptoms.length === 0) {
          console.log('✅ API connected but no symptoms found - showing mock data');
          setSymptoms(dummySymptoms);
          setUsingDummyData(true);
        } else {
          setSymptoms(formattedSymptoms);
          console.log(`✅ Loaded ${formattedSymptoms.length} symptoms from API`);
        }
      } else {
        throw new Error('Invalid response format');
      }

    } catch (err: any) {
      console.log('API call failed, falling back to dummy data:', err.message);
      setSymptoms(dummySymptoms);
      setUsingDummyData(true);
      setApiConnected(false);
      setError(null); // Clear error since we're showing dummy data
    } finally {
      setLoading(false);
    }
  };

  const handleAddSymptom = async () => {
    if (newSymptom.trim() === '') return;

    const newSeverity = parseInt(severity) || 3;

    // Map numeric severity to API severity
    const severityMap: { [key: number]: 'mild' | 'moderate' | 'severe' | 'critical' } = {
      1: 'mild',
      2: 'mild',
      3: 'moderate',
      4: 'severe',
      5: 'critical'
    };

    const apiSeverity = severityMap[newSeverity] || 'moderate';

    const symptomData: SymptomCreate = {
      symptom: newSymptom.trim(),
      severity: apiSeverity,
      reported_date: new Date().toISOString()
    };

    try {
      if (apiConnected) {
        console.log("Adding symptom via API:", symptomData);
        const response = await symptomServices.createSymptom(symptomData);

        if (response.data) {
          // Refresh the list to get the new symptom
          await fetchSymptoms();
          console.log("✅ Symptom added successfully");
        }
      } else {
        // Fallback to local state update when API is not connected
        const entry: SymptomEntry = {
          id: Date.now().toString(),
          reading_date: new Date().toISOString(),
          symptom: newSymptom.trim(),
          severity: newSeverity,
          notes: undefined,
          color: newSeverity >= 4 ? colors.error : (newSeverity === 3 ? colors.warning : colors.info)
        };

        console.log("Adding symptom locally (API not connected):", entry);
        setSymptoms(prev => [entry, ...prev]);
      }

      setNewSymptom('');
      setSeverity('3');
      setShowForm(false);

    } catch (error: any) {
      console.error("Failed to add symptom:", error.message);
      // Fallback to local addition on error
      const entry: SymptomEntry = {
        id: Date.now().toString(),
        reading_date: new Date().toISOString(),
        symptom: newSymptom.trim(),
        severity: newSeverity,
        notes: undefined,
        color: newSeverity >= 4 ? colors.error : (newSeverity === 3 ? colors.warning : colors.info)
      };

      setSymptoms(prev => [entry, ...prev]);
      setNewSymptom('');
      setSeverity('3');
      setShowForm(false);
    }
  };

  // ✅ Memoized utility functions
  const getSeverityColor = useCallback((severityValue: number) => {
    switch (severityValue) {
      case 1: return 'bg-green-100';
      case 2: return 'bg-blue-100';
      case 3: return 'bg-yellow-100';
      case 4: return 'bg-orange-100';
      case 5: return 'bg-red-100';
      default: return 'bg-gray-100';
    }
  }, []);

  const getSeverityTextColor = useCallback((severityValue: number) => {
    switch (severityValue) {
      case 1: return 'text-green-800';
      case 2: return 'text-blue-800';
      case 3: return 'text-yellow-800';
      case 4: return 'text-orange-800';
      case 5: return 'text-red-800';
      default: return 'text-gray-800';
    }
  }, []);

  const renderSymptomItem: ListRenderItem<SymptomEntry> = ({ item }) => (
    <StyledTouchableOpacity className="bg-white rounded-lg p-4 mb-3 shadow-sm border border-gray-100">
      <StyledView className="flex-row justify-between items-start">
        <StyledView className="flex-1">
          <StyledText variant="h4" className="text-gray-900 mb-1">{item.symptom}</StyledText>
          <StyledView className="flex-row items-center mb-2">
            <StyledView tw={`px-2 py-1 rounded-full ${getSeverityColor(item.severity)} mr-2`}>
              <StyledText className={`text-xs font-medium ${getSeverityTextColor(item.severity)}`}>
                Severity {item.severity}
              </StyledText>
            </StyledView>
            <StyledText variant="caption" color="textSecondary">
              {new Date(item.reading_date).toLocaleDateString()} at {new Date(item.reading_date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </StyledText>
          </StyledView>
          {item.notes && (
            <StyledText variant="body2" color="textSecondary" className="mt-1">
              {item.notes}
            </StyledText>
          )}
        </StyledView>
        <ChevronRight size={20} color={colors.textMuted} />
      </StyledView>
    </StyledTouchableOpacity>
  );

  // ✅ Render loading state
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
  }

  // ✅ Render error state (only if we have a real error and no fallback data)
  if (error && !usingDummyData) {
    return (
      <ScreenContainer>
        <ErrorState
          title="Unable to Load Symptoms"
          message={ERROR_MESSAGES.API_ERROR}
          onRetry={fetchSymptoms}
          retryLabel="Try Again"
        />
      </ScreenContainer>
    );
  }

  // ✅ Render empty state for no symptoms
  if (symptoms.length === 0 && !usingDummyData) {
    return (
      <ScreenContainer>
        <EmptyState
          icon="medical-outline"
          title="No Symptoms Logged Yet"
          description="Start tracking your symptoms to monitor your health patterns and share insights with your healthcare provider."
          actionLabel="Log First Symptom"
          onAction={() => setShowForm(true)}
        />
      </ScreenContainer>
    );
  }

  return (
    <ScreenContainer scrollable={false} withPadding>
      <StyledView className="pt-2 pb-4 flex-row items-center justify-beclassNameeen">
        <StyledView>
          <StyledText variant="h1" color="primary">Symptom Tracker</StyledText>
          <StyledText variant="body2" color="textSecondary" className="mt-1">
            Record and monitor your symptoms over time
          </StyledText>

          {usingDummyData && !apiConnected && (
            <StyledView className="mt-3 p-2 bg-yellow-100 rounded border border-yellow-300">
              <StyledText className="text-yellow-800 text-sm text-center">
                API connection failed - Showing sample data
              </StyledText>
            </StyledView>
          )}

          {usingDummyData && apiConnected && (
            <StyledView className="mt-3 p-2 bg-blue-100 rounded border border-blue-300">
              <StyledText className="text-blue-800 text-sm text-center">
                No symptoms logged yet - Showing sample data
              </StyledText>
            </StyledView>
          )}

          {!usingDummyData && apiConnected && symptoms.length > 0 && (
            <StyledView className="mt-3 p-2 bg-green-100 rounded border border-green-300">
              <StyledText className="text-green-800 text-sm text-center">
                Connected to API - Real data loaded
              </StyledText>
            </StyledView>
          )}
        </StyledView>
      </StyledView>

      {showForm ? (
        <StyledView className="bg-gray-50 p-4 rounded-lg mb-4">
          <StyledText variant="h4" className="mb-3">Log New Symptom</StyledText>

          <StyledInput
            placeholder="Describe your symptom..."
            value={newSymptom}
            onChangeText={setNewSymptom}
            className="mb-3"
          />

          <StyledText variant="body2" className="mb-2 text-gray-700">Severity Level (1-5)</StyledText>
          <StyledView className="flex-row justify-between mb-4">
            {[1, 2, 3, 4, 5].map((level) => (
              <StyledTouchableOpacity
                key={level}
                tw={`flex-1 mx-1 py-2 rounded ${severity === level.toString() ? getSeverityColor(level) : 'bg-gray-200'}`}
                onPress={() => setSeverity(level.toString())}
              >
                <StyledText className={`text-center font-medium ${severity === level.toString() ? getSeverityTextColor(level) : 'text-gray-600'}`}>
                  {level}
                </StyledText>
              </StyledTouchableOpacity>
            ))}
          </StyledView>

          <StyledView className="flex-row space-x-2">
            <StyledButton
              variant="filledPrimary"
              onPress={handleAddSymptom}
              className="flex-1"
              disabled={!newSymptom.trim()}
            >
              Add Symptom
            </StyledButton>
            <StyledButton
              variant="textPrimary"
              onPress={() => setShowForm(false)}
              className="flex-1"
            >
              Cancel
            </StyledButton>
          </StyledView>
        </StyledView>
      ) : (
        <StyledButton
          variant="filledPrimary"
          iconLeft={<Plus size={18} color={colors.onPrimary} />}
          onPress={() => setShowForm(true)}
          className="mb-4"
          style={{ borderRadius: 10 }}
        >
          Log New Symptom
        </StyledButton>
      )}

      <StyledView className="flex-1">
        <FlatList<SymptomEntry>
          data={symptoms}
          keyExtractor={(item) => item.id}
          renderItem={renderSymptomItem}
          showsVerticalScrollIndicator={false}
          ListEmptyComponent={
            <StyledView className="flex items-center justify-center p-6 mt-10">
              <AlertCircle size={40} color={colors.textMuted} />
              <StyledText variant="h4" className="mt-3 text-gray-700">No Symptoms Logged Yet</StyledText>
              <StyledText variant="body2" color="textSecondary" className="text-center mt-1">
                Tap the button above to log your first symptom.
              </StyledText>
            </StyledView>
          }
        />
      </StyledView>
    </ScreenContainer>
  );
};

export default SymptomTrackerScreen; 