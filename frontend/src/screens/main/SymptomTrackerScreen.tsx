import React, { useState } from 'react';
import { View, FlatList, TouchableOpacity, ListRenderItem } from 'react-native';
import { styled } from 'nativewind';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { MainAppStackParamList } from '../../navigation/types';
import { Clipboard, Calendar, Plus, AlertCircle, ArrowLeft, ChevronRight } from 'lucide-react-native';

import ScreenContainer from '../../components/layout/ScreenContainer';
import StyledText from '../../components/common/StyledText';
import StyledButton from '../../components/common/StyledButton';
import StyledInput from '../../components/common/StyledInput';

const StyledView = styled(View);
const StyledTouchableOpacity = styled(TouchableOpacity);

interface SymptomEntry {
  id: string;
  date: string;
  symptom: string;
  severity: number; // e.g., 1-5 or 1-10
  notes?: string;
  color?: string;
}

type SymptomTrackerScreenNavigationProp = NativeStackNavigationProp<MainAppStackParamList, 'SymptomTracker'>;

const SymptomTrackerScreen = () => {
  const navigation = useNavigation<SymptomTrackerScreenNavigationProp>();

  const [symptoms, setSymptoms] = useState<SymptomEntry[]>([
    { 
      id: '1', 
      date: 'Today, 10:30 AM', 
      symptom: 'Headache', 
      severity: 3, 
      notes: 'Mild, in the morning.', 
      color: '#0EA5E9'
    },
    { 
      id: '2', 
      date: 'Yesterday, 2:15 PM', 
      symptom: 'Fatigue', 
      severity: 4, 
      notes: 'All day long.', 
      color: '#F59E0B'
    },
    { 
      id: '3', 
      date: 'Oct 25, 8:45 AM', 
      symptom: 'Sore Throat', 
      severity: 2, 
      notes: 'Mild irritation when swallowing.', 
      color: '#4ADE80'
    },
    { 
      id: '4', 
      date: 'Oct 24, 6:20 PM', 
      symptom: 'Muscle Pain', 
      severity: 3, 
      notes: 'After exercise, right shoulder.', 
      color: '#ea384c'
    }
  ]);
  
  const [newSymptom, setNewSymptom] = useState('');
  const [severity, setSeverity] = useState('3');
  const [showForm, setShowForm] = useState(false);

  const handleAddSymptom = () => {
    if (newSymptom.trim() === '') return;
    const entry: SymptomEntry = {
      id: Date.now().toString(),
      date: new Date().toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: 'numeric',
        minute: 'numeric',
        hour12: true
      }),
      symptom: newSymptom,
      severity: parseInt(severity) || 3,
      color: '#0EA5E9'
    };
    setSymptoms(prev => [entry, ...prev]);
    setNewSymptom('');
    setSeverity('3');
    setShowForm(false);
  };

  const getSeverityColor = (severity: number) => {
    switch (severity) {
      case 1: return 'bg-gray-100';
      case 2: return 'bg-medical-lightblue';
      case 3: return 'bg-medical-lightpurple';
      case 4: return 'bg-medical-lightgreen';
      case 5: return 'bg-medical-lightred';
      default: return 'bg-gray-100';
    }
  };

  const renderSymptomItem: ListRenderItem<SymptomEntry> = ({ item }) => (
    <StyledTouchableOpacity 
      tw="p-4 mb-3 bg-white rounded-lg shadow-sm flex-row"
      onPress={() => {/* Navigate to detail view */}}
      style={{ borderRadius: 12 }}
    >
      <StyledView tw={`${getSeverityColor(item.severity)} p-2 rounded-md self-start mr-3`}>
        <AlertCircle size={20} color={item.color || '#0EA5E9'} />
      </StyledView>
      <StyledView tw="flex-1">
        <StyledView tw="flex-row justify-between items-center">
          <StyledText variant="label" tw="font-semibold text-gray-800">{item.symptom}</StyledText>
          <StyledView tw="flex-row items-center">
            <StyledView tw="flex-row">
              {Array.from({ length: 5 }).map((_, i) => (
                <StyledView 
                  key={i} 
                  tw={`w-2.5 h-2.5 rounded-full mx-0.5 ${i < item.severity ? 'bg-medical-red' : 'bg-gray-200'}`} 
                />
              ))}
            </StyledView>
          </StyledView>
        </StyledView>
        {item.notes && (
          <StyledText variant="body2" color="textSecondary" tw="mt-1">{item.notes}</StyledText>
        )}
        <StyledView tw="flex-row items-center mt-1">
          <Calendar size={12} color="#6B7280" />
          <StyledText variant="caption" color="textSecondary" tw="ml-1">{item.date}</StyledText>
        </StyledView>
      </StyledView>
      <ChevronRight size={16} color="#6B7280" />
    </StyledTouchableOpacity>
  );

  return (
    <ScreenContainer scrollable={false} withPadding>
      {/* Header */}
      <StyledView tw="pt-2 pb-4 flex-row items-center justify-between">
        <StyledView>
          <StyledText variant="h1" color="primary">Symptom Tracker</StyledText>
          <StyledText variant="body2" color="textSecondary" tw="mt-1">
            Record and monitor your symptoms over time
          </StyledText>
        </StyledView>
      </StyledView>
      
      {/* Add Symptom Form */}
      {showForm ? (
        <StyledView tw="mb-4 p-5 bg-white rounded-lg shadow-sm" style={{ borderRadius: 12 }}>
          <StyledView tw="flex-row justify-between items-center mb-4">
            <StyledText variant="h3" tw="text-gray-800">Add New Symptom</StyledText>
            <TouchableOpacity onPress={() => setShowForm(false)}>
              <ArrowLeft size={20} color="#6B7280" />
            </TouchableOpacity>
          </StyledView>
          
          <StyledInput 
            placeholder="Describe your symptom..."
            value={newSymptom}
            onChangeText={setNewSymptom}
            tw="mb-4"
            style={{ backgroundColor: "#F9FAFB" }}
          />
          
          <StyledText variant="label" tw="mb-3 text-gray-700">Severity (1-5)</StyledText>
          <StyledView tw="flex-row mb-4 justify-between">
            {[1, 2, 3, 4, 5].map(level => (
              <StyledTouchableOpacity 
                key={level}
                tw={`w-12 h-12 items-center justify-center rounded-full ${severity === level.toString() ? getSeverityColor(level) : 'bg-gray-100'}`}
                onPress={() => setSeverity(level.toString())}
              >
                <StyledText variant="body1" tw="font-semibold">{level}</StyledText>
              </StyledTouchableOpacity>
            ))}
          </StyledView>
          
          <StyledButton 
            variant="primary" 
            onPress={handleAddSymptom} 
            tw="w-full mb-2" 
            labelStyle={{ fontSize: 16 }}
            style={{ borderRadius: 10 }}
          >
            Save Symptom
          </StyledButton>
          <StyledButton 
            variant="ghost" 
            onPress={() => setShowForm(false)} 
            tw="w-full" 
            labelStyle={{ fontSize: 16 }}
          >
            Cancel
          </StyledButton>
        </StyledView>
      ) : (
        <StyledButton 
          variant="primary"
          icon={() => <Plus size={18} color="#FFFFFF" />}
          onPress={() => setShowForm(true)} 
          tw="mb-4"
          style={{ borderRadius: 10 }}
        >
          Log New Symptom
        </StyledButton>
      )}
      
      {/* Symptoms List */}
      <StyledView tw="flex-1">
        <FlatList<SymptomEntry>
          data={symptoms}
          keyExtractor={(item) => item.id}
          renderItem={renderSymptomItem}
          showsVerticalScrollIndicator={false}
          ListEmptyComponent={
            <StyledView tw="flex items-center justify-center p-6">
              <AlertCircle size={40} color="#6B7280" />
              <StyledText variant="h4" tw="mt-2 text-gray-700">No symptoms logged</StyledText>
              <StyledText variant="body2" color="textSecondary" tw="text-center mt-1">
                Tap the button above to log a new symptom.
              </StyledText>
            </StyledView>
          }
        />
      </StyledView>
    </ScreenContainer>
  );
};

export default SymptomTrackerScreen; 