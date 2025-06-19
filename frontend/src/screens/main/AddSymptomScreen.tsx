import React, { useState } from 'react';
import { View, TouchableOpacity, Alert } from 'react-native';
import { styled } from 'nativewind';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { ArrowLeft } from 'lucide-react-native';

import { MainAppStackParamList } from '../../navigation/types';
import { useTheme } from '../../theme';
import ScreenContainer from '../../components/layout/ScreenContainer';
import StyledText from '../../components/common/StyledText';
import StyledButton from '../../components/common/StyledButton';
import StyledInput from '../../components/common/StyledInput';
import ErrorState from '../../components/common/ErrorState';
import { ERROR_MESSAGES} from '../../constants/messages';

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
  const [loading, setLoading] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [criticalError, setCriticalError] = useState<string | null>(null);

  const validateForm = () => {
    setFormError(null);
    if (!newSymptomText.trim()) {
      setFormError(ERROR_MESSAGES.REQUIRED_FIELD);
      return false;
    }
    return true;
  };

  const handleSaveSymptom = async () => {
    if (!validateForm()) {
      return;
    }

    setLoading(true);
    setFormError(null);
    setCriticalError(null);

    try {
      // In a real app, you'd save this to your state management/API
      // For now, simulate API call with delay
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      console.log('Symptom to save:', { 
        symptom: newSymptomText, 
        severity: parseInt(severity)
      });

      Alert.alert('Success', 'Symptom logged successfully!', [
        { text: 'OK', onPress: () => navigation.goBack() }
      ]);
    } catch (err: any) {
      console.error('Failed to save symptom:', err);
      const errorMessage = err.response?.data?.detail || err.message || ERROR_MESSAGES.SYMPTOM_SAVE_ERROR;
      setFormError(errorMessage);
      Alert.alert('Error', errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const retryOperation = () => {
    setCriticalError(null);
    setFormError(null);
    // Reset form to initial state if needed
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

  // ✅ Render critical error state using standardized ErrorState component
  if (criticalError) {
    return (
      <ScreenContainer scrollable withPadding backgroundColor={theme.colors.backgroundPrimary}>
        <StyledView tw="flex-row items-center py-2 mb-6">
          <StyledTouchableOpacity onPress={() => navigation.goBack()} tw="p-2">
            <ArrowLeft size={24} color={theme.colors.textPrimary} />
          </StyledTouchableOpacity>
          <StyledText variant="h2" color="primary" tw="ml-2">Add New Symptom</StyledText>
        </StyledView>
        <ErrorState
          title="Unable to Load Symptom Form"
          message={criticalError}
          onRetry={retryOperation}
          retryLabel="Try Again"
          icon="thermometer-outline"
        />
      </ScreenContainer>
    );
  }

  return (
    <ScreenContainer scrollable withPadding backgroundColor={theme.colors.backgroundPrimary}>
      {/* Header */}
      <StyledView tw="flex-row items-center py-2 mb-6">
        <StyledTouchableOpacity onPress={() => navigation.goBack()} tw="p-2">
          <ArrowLeft size={24} color={theme.colors.textPrimary} />
        </StyledTouchableOpacity>
        <StyledText variant="h2" color="primary" tw="ml-2">Add New Symptom</StyledText>
      </StyledView>

      <StyledView tw="bg-white p-5 rounded-lg shadow-sm mb-6" style={{ borderRadius: 12 }}>
        {formError && (
          <StyledView tw="mb-4 p-3 bg-red-50 rounded-lg border border-red-200">
            <StyledText tw="text-red-700 text-sm">{formError}</StyledText>
          </StyledView>
        )}

        <StyledInput 
          label="Symptom Description"
          placeholder="e.g., Sharp headache in the morning"
          value={newSymptomText}
          onChangeText={setNewSymptomText}
          tw="mb-5"
          multiline
          numberOfLines={3}
          inputStyle={{ backgroundColor: theme.colors.backgroundSecondary, minHeight: 80, textAlignVertical: 'top' }}
          editable={!loading}
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
              disabled={loading}
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
          variant="filledPrimary" 
          onPress={handleSaveSymptom} 
          tw="w-full mb-2" 
          disabled={loading || newSymptomText.trim() === ''}
          loading={loading}
        >
          {loading ? 'Saving...' : 'Save Symptom'}
        </StyledButton>
        <StyledButton 
          variant="textPrimary" 
          onPress={() => navigation.goBack()} 
          tw="w-full" 
          disabled={loading}
        >
          Cancel
        </StyledButton>
      </StyledView>
    </ScreenContainer>
  );
};

export default AddSymptomScreen; 