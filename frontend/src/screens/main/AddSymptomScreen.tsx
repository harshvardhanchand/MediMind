import React, { useState } from 'react';
import { View, TouchableOpacity } from 'react-native';
import { styled } from 'nativewind';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { MainAppStackParamList } from '../../navigation/types';
import { ArrowLeft } from 'lucide-react-native';
import { useTheme } from '../../theme';

import ScreenContainer from '../../components/layout/ScreenContainer';
import StyledText from '../../components/common/StyledText';
import StyledButton from '../../components/common/StyledButton';
import StyledInput from '../../components/common/StyledInput';

const StyledView = styled(View);
const StyledTouchableOpacity = styled(TouchableOpacity);

// We'll need a way to pass the new symptom back or trigger a refresh.
// For now, we'll focus on navigation and form structure.
// type AddSymptomScreenProps = {
//   onSymptomAdded: (symptom: SymptomEntry) => void; // Example callback
// };

type AddSymptomNavigationProp = NativeStackNavigationProp<MainAppStackParamList, 'AddSymptom'>;

const AddSymptomScreen = () => {
  const navigation = useNavigation<AddSymptomNavigationProp>();
  const theme = useTheme();
  const [newSymptomText, setNewSymptomText] = useState('');
  const [severity, setSeverity] = useState('3'); // Default severity

  const handleSaveSymptom = () => {
    if (newSymptomText.trim() === '') return;
    // In a real app, you'd save this to your state management/API
    // and then navigate back, possibly passing the new symptom or a flag to refresh.
    console.log('Symptom to save:', { 
      symptom: newSymptomText, 
      severity: parseInt(severity)
    });
    // For now, just navigate back
    if (navigation.canGoBack()) {
        navigation.goBack();
    }
  };

  const getSeverityColor = (level: number, currentSeverity: string) => {
    const isActive = currentSeverity === level.toString();
    if (!isActive) return 'bg-gray-100';
    switch (level) {
      case 1: return 'bg-gray-200'; // Mildest
      case 2: return 'bg-medical-lightblue';
      case 3: return 'bg-medical-lightpurple';
      case 4: return 'bg-yellow-200'; // Using yellow for higher severity
      case 5: return 'bg-medical-lightred'; // Highest
      default: return 'bg-gray-100';
    }
  };

  return (
    <ScreenContainer scrollable withPadding backgroundColor={theme.colors.backgroundScreen}>
      {/* Header */}
      <StyledView tw="flex-row items-center py-2 mb-6">
        <StyledTouchableOpacity onPress={() => navigation.goBack()} tw="p-2">
          <ArrowLeft size={24} color={theme.colors.textPrimary} />
        </StyledTouchableOpacity>
        <StyledText variant="h2" color="primary" tw="ml-2">Add New Symptom</StyledText>
      </StyledView>

      <StyledView tw="bg-white p-5 rounded-lg shadow-sm mb-6" style={{ borderRadius: 12 }}>
        <StyledInput 
          label="Symptom Description"
          placeholder="e.g., Sharp headache in the morning"
          value={newSymptomText}
          onChangeText={setNewSymptomText}
          tw="mb-5"
          multiline
          numberOfLines={3}
          style={{ backgroundColor: theme.colors.gray50, minHeight: 80, textAlignVertical: 'top' }}
        />
        
        <StyledText variant="label" tw="mb-3 text-gray-700">Severity (1-5)</StyledText>
        <StyledView tw="flex-row mb-6 justify-between">
          {[1, 2, 3, 4, 5].map(level => (
            <StyledTouchableOpacity 
              key={level}
              tw={`w-12 h-12 items-center justify-center rounded-full border-2 ${
                severity === level.toString() 
                  ? `${getSeverityColor(level, severity)} border-primary` 
                  : 'border-gray-200 bg-gray-100'
              }`}
              onPress={() => setSeverity(level.toString())}
            >
              <StyledText 
                variant="h4" 
                tw={`${severity === level.toString() ? 'text-primary' : 'text-gray-600'} font-semibold`}
              >
                {level}
              </StyledText>
            </StyledTouchableOpacity>
          ))}
        </StyledView>
        
        <StyledButton 
          variant="primary" 
          onPress={handleSaveSymptom} 
          tw="w-full mb-2" 
          labelStyle={{ fontSize: 16 }}
          disabled={newSymptomText.trim() === ''}
        >
          Save Symptom
        </StyledButton>
        <StyledButton 
          variant="ghost" 
          onPress={() => navigation.goBack()} 
          tw="w-full" 
          labelStyle={{ fontSize: 16 }}
        >
          Cancel
        </StyledButton>
      </StyledView>
    </ScreenContainer>
  );
};

export default AddSymptomScreen; 