import React, { useState, useEffect } from 'react';
import { View, FlatList, TouchableOpacity, ListRenderItem, ActivityIndicator } from 'react-native';
import { styled } from 'nativewind';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { Clipboard, Calendar, Plus, AlertCircle, ArrowLeft, ChevronRight } from 'lucide-react-native';

import { MainAppStackParamList } from '../../navigation/types';
import ScreenContainer from '../../components/layout/ScreenContainer';
import StyledText from '../../components/common/StyledText';
import StyledButton from '../../components/common/StyledButton';
import StyledInput from '../../components/common/StyledInput';
import { useTheme } from '../../theme';

const StyledView = styled(View);
const StyledTouchableOpacity = styled(TouchableOpacity);

interface SymptomEntry {
  id: string;
  reading_date: string;
  symptom: string;
  severity: number;
  notes?: string;
  color?: string;
}

type SymptomTrackerScreenNavigationProp = NativeStackNavigationProp<MainAppStackParamList, 'SymptomTracker'>;

const SymptomTrackerScreen = () => {
  const navigation = useNavigation<SymptomTrackerScreenNavigationProp>();
  const { colors } = useTheme();

  // Data states
  const [symptoms, setSymptoms] = useState<SymptomEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [usingDummyData, setUsingDummyData] = useState(false);
  
  const [newSymptom, setNewSymptom] = useState('');
  const [severity, setSeverity] = useState('3');
  const [showForm, setShowForm] = useState(false);

  // Dummy data fallback
  const dummySymptoms: SymptomEntry[] = [
    { 
      id: '1', 
      reading_date: new Date(Date.now() - 3600000 * 1).toISOString(),
      symptom: 'Headache', 
      severity: 3, 
      notes: 'Mild, in the morning.', 
      color: colors.info
    },
    { 
      id: '2', 
      reading_date: new Date(Date.now() - 3600000 * 24).toISOString(),
      symptom: 'Fatigue', 
      severity: 4, 
      notes: 'All day long.', 
      color: colors.warning
    },
    { 
      id: '3', 
      reading_date: new Date(Date.now() - 3600000 * 25).toISOString(),
      symptom: 'Sore Throat', 
      severity: 2, 
      notes: 'Mild irritation when swallowing.', 
      color: '#4ADE80'
    },
    { 
      id: '4', 
      reading_date: new Date(Date.now() - 3600000 * 26).toISOString(),
      symptom: 'Muscle Pain', 
      severity: 3, 
      notes: 'After exercise, right shoulder.', 
      color: '#ea384c'
    }
  ];

  useEffect(() => {
    fetchSymptoms();
  }, []);

  const fetchSymptoms = async () => {
    try {
      setLoading(true);
      setUsingDummyData(false);
      
      console.log('Trying to fetch real symptoms from API...');
      // TODO: Replace with actual symptom API call when available
      // const response = await symptomServices.getSymptoms();
      
      // Simulate API call that might fail
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // For now, always use dummy data since symptom API doesn't exist yet
      console.log('Using dummy symptoms (API not implemented yet)');
      setSymptoms(dummySymptoms);
      setUsingDummyData(true);
      
    } catch (err: any) {
      console.log('API call failed, falling back to dummy data:', err.message);
      setSymptoms(dummySymptoms);
      setUsingDummyData(true);
    } finally {
      setLoading(false);
    }
  };

  const handleAddSymptom = () => {
    if (newSymptom.trim() === '') return;
    const newSeverity = parseInt(severity) || 3;
    const entry: SymptomEntry = {
      id: Date.now().toString(),
      reading_date: new Date().toISOString(),
      symptom: newSymptom.trim(),
      severity: newSeverity,
      notes: undefined,
      color: newSeverity >= 4 ? colors.error : (newSeverity === 3 ? colors.warning : colors.info)
    };
    
    console.log("TODO: API Call - Add symptom to backend", entry);

    setSymptoms(prev => [entry, ...prev]);
    setNewSymptom('');
    setSeverity('3');
    setShowForm(false);
  };

  const getSeverityColor = (severityValue: number) => {
    switch (severityValue) {
      case 1: return 'bg-green-100';
      case 2: return 'bg-blue-100';
      case 3: return 'bg-yellow-100';
      case 4: return 'bg-orange-100';
      case 5: return 'bg-red-100';
      default: return 'bg-gray-100';
    }
  };

  const renderSymptomItem: ListRenderItem<SymptomEntry> = ({ item }) => (
    <StyledTouchableOpacity 
      tw="p-4 mb-3 bg-white rounded-lg shadow-sm flex-row"
      style={{ borderRadius: 12 }}
    >
      <StyledView tw={`${getSeverityColor(item.severity)} p-2 rounded-md self-start mr-3`}>
        <AlertCircle size={20} color={item.severity >=4 ? colors.error : (item.severity === 3 ? colors.warning : colors.info)} />
      </StyledView>
      <StyledView tw="flex-1">
        <StyledView tw="flex-row justify-between items-center">
          <StyledText variant="label" tw="font-semibold text-gray-800">{item.symptom}</StyledText>
          <StyledView tw="flex-row items-center">
            <StyledView tw="flex-row">
              {Array.from({ length: 5 }).map((_, i) => (
                <StyledView 
                  key={i} 
                  style={{
                    width: 10, height: 10, borderRadius: 5, marginHorizontal: 1,
                    backgroundColor: i < item.severity ? (item.color || colors.primary) : colors.legacyGray200
                  }}
                />
              ))}
            </StyledView>
          </StyledView>
        </StyledView>
        {item.notes && (
          <StyledText variant="body2" color="textSecondary" tw="mt-1">{item.notes}</StyledText>
        )}
        <StyledView tw="flex-row items-center mt-1">
          <Calendar size={12} color={colors.textMuted} />
          <StyledText variant="caption" color="textSecondary" tw="ml-1">
            {new Date(item.reading_date).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: 'numeric', minute: 'numeric', hour12: true })}
          </StyledText>
        </StyledView>
      </StyledView>
    </StyledTouchableOpacity>
  );

  if (loading) {
    return (
      <ScreenContainer scrollable={false} withPadding>
        <StyledView tw="flex-1 justify-center items-center">
          <ActivityIndicator size="large" />
          <StyledText tw="mt-2 text-gray-600">Loading symptoms...</StyledText>
        </StyledView>
      </ScreenContainer>
    );
  }

  return (
    <ScreenContainer scrollable={false} withPadding>
      <StyledView tw="pt-2 pb-4 flex-row items-center justify-between">
        <StyledView>
          <StyledText variant="h1" color="primary">Symptom Tracker</StyledText>
          <StyledText variant="body2" color="textSecondary" tw="mt-1">
            Record and monitor your symptoms over time
          </StyledText>
          
          {usingDummyData && (
            <StyledView tw="mt-3 p-2 bg-yellow-100 rounded border border-yellow-300">
              <StyledText tw="text-yellow-800 text-sm text-center">
                📱 Showing sample data (API not connected)
              </StyledText>
            </StyledView>
          )}
        </StyledView>
      </StyledView>
      
      {showForm ? (
        <StyledView tw="mb-4 p-5 bg-white rounded-lg shadow-sm" style={{ borderRadius: 12 }}>
          <StyledView tw="flex-row justify-between items-center mb-4">
            <StyledText variant="h3" tw="text-gray-800">Log New Symptom</StyledText>
            <TouchableOpacity onPress={() => setShowForm(false)}>
              <ArrowLeft size={20} color={colors.textSecondary} />
            </TouchableOpacity>
          </StyledView>
          
          <StyledInput 
            placeholder="Describe your symptom (e.g., Headache, Nausea)"
            value={newSymptom}
            onChangeText={setNewSymptom}
            tw="mb-4 bg-gray-50"
          />
          
          <StyledText variant="label" tw="mb-1 text-gray-700">Severity</StyledText>
          <StyledText variant="caption" tw="mb-3 text-gray-500">(1 - Very Mild, 5 - Very Severe)</StyledText>
          <StyledView tw="flex-row mb-4 justify-between">
            {[1, 2, 3, 4, 5].map(level => (
              <StyledTouchableOpacity 
                key={level}
                tw={`w-12 h-12 items-center justify-center rounded-full border-2 ${severity === level.toString() ? getSeverityColor(level) + ' border-primary' : 'bg-gray-100 border-gray-300'}`}
                onPress={() => setSeverity(level.toString())}
              >
                <StyledText variant="body1" tw={`font-semibold ${severity === level.toString() ? 'text-primary' : 'text-gray-600'}`}>{level}</StyledText>
              </StyledTouchableOpacity>
            ))}
          </StyledView>
          
          <StyledButton 
            variant="filledPrimary" 
            onPress={handleAddSymptom} 
            tw="w-full mb-2 mt-2"
            style={{ borderRadius: 10 }}
          >
            Save Symptom
          </StyledButton>
          <StyledButton 
            variant="textPrimary" 
            onPress={() => setShowForm(false)} 
            tw="w-full"
          >
            Cancel
          </StyledButton>
        </StyledView>
      ) : (
        <StyledButton 
          variant="filledPrimary"
          iconLeft={<Plus size={18} color={colors.onPrimary} />}
          onPress={() => setShowForm(true)} 
          tw="mb-4"
          style={{ borderRadius: 10 }}
        >
          Log New Symptom
        </StyledButton>
      )}
      
      <StyledView tw="flex-1">
        <FlatList<SymptomEntry>
          data={symptoms}
          keyExtractor={(item) => item.id}
          renderItem={renderSymptomItem}
          showsVerticalScrollIndicator={false}
          ListEmptyComponent={
            <StyledView tw="flex items-center justify-center p-6 mt-10">
              <AlertCircle size={40} color={colors.textMuted} />
              <StyledText variant="h4" tw="mt-3 text-gray-700">No Symptoms Logged Yet</StyledText>
              <StyledText variant="body2" color="textSecondary" tw="text-center mt-1">
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