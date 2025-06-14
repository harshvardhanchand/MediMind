import React, { useState } from 'react';
import { ScrollView, View, TextInput, TouchableOpacity, Alert, ActivityIndicator, Modal } from 'react-native';
import { styled } from 'nativewind';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { Ionicons } from '@expo/vector-icons';
import DateTimePicker from '@react-native-community/datetimepicker';

import { OnboardingStackParamList } from '../../navigation/types';
import ScreenContainer from '../../components/layout/ScreenContainer';
import StyledText from '../../components/common/StyledText';
import Card from '../../components/common/Card';
import { useTheme } from '../../theme';
import { userServices } from '../../api/services';
import { MedicalCondition, UserProfileUpdate } from '../../types/api';

const StyledScrollView = styled(ScrollView);
const StyledView = styled(View);
const StyledTextInput = styled(TextInput);
const StyledTouchableOpacity = styled(TouchableOpacity);
const StyledModal = styled(Modal);

type CreateProfileScreenNavigationProp = NativeStackNavigationProp<OnboardingStackParamList, 'CreateProfile'>;

interface UserProfile {
  name: string;
  dateOfBirth: Date | null;
  weight: string;
  height: string;
  gender: 'male' | 'female' | 'other' | '';
  medicalConditions: MedicalCondition[];
}

const CreateProfileScreen = () => {
  const navigation = useNavigation<CreateProfileScreenNavigationProp>();
  const { colors } = useTheme();
  
  const [profile, setProfile] = useState<UserProfile>({
    name: '',
    dateOfBirth: null,
    weight: '',
    height: '',
    gender: '',
    medicalConditions: [],
  });
  
  const [loading, setLoading] = useState(false);
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [showConditionModal, setShowConditionModal] = useState(false);
  const [newCondition, setNewCondition] = useState<MedicalCondition>({
    condition_name: '',
    diagnosed_date: null,
    status: 'active',
    severity: undefined,
    diagnosing_doctor: null,
    notes: null,
  });

  const handleCreateProfile = async () => {
    if (!profile.name.trim()) {
      Alert.alert('Required Field', 'Please enter your name to continue.');
      return;
    }

    setLoading(true);
    try {
      const updateData: UserProfileUpdate = {
        name: profile.name || null,
        date_of_birth: profile.dateOfBirth ? profile.dateOfBirth.toISOString().split('T')[0] : null,
        weight: profile.weight ? parseFloat(profile.weight) : null,
        height: profile.height ? parseInt(profile.height) : null,
        gender: profile.gender || null,
        medical_conditions: profile.medicalConditions,
      };

      await userServices.updateProfile(updateData);
      
      // Navigate to main app
      navigation.reset({
        index: 0,
        routes: [{ name: 'Main' as any }],
      });
    } catch (error) {
      console.error('Error creating profile:', error);
      Alert.alert('Error', 'Failed to create profile. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleDateChange = (event: any, selectedDate?: Date) => {
    setShowDatePicker(false);
    if (selectedDate) {
      setProfile(prev => ({ ...prev, dateOfBirth: selectedDate }));
    }
  };

  const formatDate = (date: Date | null) => {
    if (!date) return 'Select date';
    return date.toLocaleDateString();
  };

  const calculateAge = (birthDate: Date | null) => {
    if (!birthDate) return '';
    const today = new Date();
    const age = today.getFullYear() - birthDate.getFullYear();
    const monthDiff = today.getMonth() - birthDate.getMonth();
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
      return age - 1;
    }
    return age;
  };

  const handleAddCondition = () => {
    setNewCondition({
      condition_name: '',
      diagnosed_date: null,
      status: 'active',
      severity: undefined,
      diagnosing_doctor: null,
      notes: null,
    });
    setShowConditionModal(true);
  };

  const handleSaveCondition = () => {
    if (!newCondition.condition_name.trim()) {
      Alert.alert('Error', 'Please enter a condition name');
      return;
    }

    setProfile(prev => ({ 
      ...prev, 
      medicalConditions: [...prev.medicalConditions, newCondition] 
    }));
    setShowConditionModal(false);
  };

  const handleDeleteCondition = (index: number) => {
    const updatedConditions = profile.medicalConditions.filter((_, i) => i !== index);
    setProfile(prev => ({ ...prev, medicalConditions: updatedConditions }));
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-red-100 text-red-800';
      case 'chronic': return 'bg-orange-100 text-orange-800';
      case 'managed': return 'bg-blue-100 text-blue-800';
      case 'resolved': return 'bg-green-100 text-green-800';
      case 'suspected': return 'bg-yellow-100 text-yellow-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getSeverityColor = (severity?: string) => {
    switch (severity) {
      case 'mild': return 'bg-green-100 text-green-800';
      case 'moderate': return 'bg-yellow-100 text-yellow-800';
      case 'severe': return 'bg-orange-100 text-orange-800';
      case 'critical': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <ScreenContainer scrollable={false} withPadding={false}>
      <StyledScrollView className="flex-1 bg-gray-50">
        {/* Header */}
        <StyledView className="px-6 pt-12 pb-6 bg-white">
          <StyledText variant="h1" tw="font-bold text-2xl text-center mb-2">
            Create Your Profile
          </StyledText>
          <StyledText variant="body1" tw="text-gray-600 text-center">
            Help us personalize your health experience
          </StyledText>
        </StyledView>

        {/* Profile Form */}
        <StyledView className="mt-6 mx-4">
          <Card>
            <StyledView className="p-4 space-y-4">
              {/* Name */}
              <StyledView>
                <StyledText variant="body2" tw="font-semibold mb-2 text-gray-700">
                  Full Name *
                </StyledText>
                <StyledTextInput
                  value={profile.name}
                  onChangeText={(text) => setProfile(prev => ({ ...prev, name: text }))}
                  placeholder="Enter your full name"
                  className="border border-gray-300 rounded-lg px-3 py-3 bg-white"
                  style={{ color: colors.textPrimary }}
                />
              </StyledView>

              {/* Date of Birth */}
              <StyledView>
                <StyledText variant="body2" tw="font-semibold mb-2 text-gray-700">
                  Date of Birth (Optional)
                </StyledText>
                <StyledTouchableOpacity
                  onPress={() => setShowDatePicker(true)}
                  className="border border-gray-300 rounded-lg px-3 py-3 bg-white flex-row items-center justify-between"
                >
                  <StyledText style={{ color: profile.dateOfBirth ? colors.textPrimary : colors.textSecondary }}>
                    {formatDate(profile.dateOfBirth)}
                  </StyledText>
                  <Ionicons name="calendar-outline" size={20} color={colors.textSecondary} />
                </StyledTouchableOpacity>
                {profile.dateOfBirth && (
                  <StyledText variant="caption" tw="text-gray-500 mt-1">
                    Age: {calculateAge(profile.dateOfBirth)} years
                  </StyledText>
                )}
              </StyledView>

              {/* Gender */}
              <StyledView>
                <StyledText variant="body2" tw="font-semibold mb-2 text-gray-700">
                  Gender (Optional)
                </StyledText>
                <StyledView className="flex-row space-x-2">
                  {['male', 'female', 'other'].map((genderOption) => (
                    <StyledTouchableOpacity
                      key={genderOption}
                      onPress={() => setProfile(prev => ({ ...prev, gender: genderOption as any }))}
                      className={`flex-1 py-3 px-4 rounded-lg border ${
                        profile.gender === genderOption 
                          ? 'bg-blue-500 border-blue-500' 
                          : 'bg-white border-gray-300'
                      }`}
                    >
                      <StyledText 
                        tw={`text-center font-medium capitalize ${
                          profile.gender === genderOption ? 'text-white' : 'text-gray-700'
                        }`}
                      >
                        {genderOption}
                      </StyledText>
                    </StyledTouchableOpacity>
                  ))}
                </StyledView>
              </StyledView>

              {/* Weight */}
              <StyledView>
                <StyledText variant="body2" tw="font-semibold mb-2 text-gray-700">
                  Weight (kg)
                </StyledText>
                <StyledTextInput
                  value={profile.weight}
                  onChangeText={(text) => setProfile(prev => ({ ...prev, weight: text }))}
                  placeholder="Enter weight in kg"
                  keyboardType="numeric"
                  className="border border-gray-300 rounded-lg px-3 py-3 bg-white"
                  style={{ color: colors.textPrimary }}
                />
              </StyledView>

              {/* Height */}
              <StyledView>
                <StyledText variant="body2" tw="font-semibold mb-2 text-gray-700">
                  Height (cm)
                </StyledText>
                <StyledTextInput
                  value={profile.height}
                  onChangeText={(text) => setProfile(prev => ({ ...prev, height: text }))}
                  placeholder="Enter height in cm"
                  keyboardType="numeric"
                  className="border border-gray-300 rounded-lg px-3 py-3 bg-white"
                  style={{ color: colors.textPrimary }}
                />
              </StyledView>
            </StyledView>
          </Card>
        </StyledView>

        {/* Medical Conditions */}
        <StyledView className="mt-6 mx-4">
          <Card>
            <StyledView className="p-4">
              <StyledView className="flex-row items-center justify-between mb-4">
                <StyledText variant="body2" tw="font-semibold text-gray-700">
                  Medical Conditions (Optional)
                </StyledText>
                <StyledTouchableOpacity
                  onPress={handleAddCondition}
                  className="bg-blue-500 px-3 py-2 rounded-lg flex-row items-center"
                >
                  <Ionicons name="add" size={16} color="white" />
                  <StyledText tw="text-white font-medium ml-1">Add</StyledText>
                </StyledTouchableOpacity>
              </StyledView>

              {profile.medicalConditions.length === 0 ? (
                <StyledView className="py-6 items-center">
                  <Ionicons name="medical-outline" size={32} color={colors.textSecondary} />
                  <StyledText tw="text-gray-500 mt-2 text-center text-sm">
                    Add any current medical conditions to get personalized health insights
                  </StyledText>
                </StyledView>
              ) : (
                <StyledView className="space-y-3">
                  {profile.medicalConditions.map((condition, index) => (
                    <StyledView key={index} className="bg-gray-50 rounded-lg p-3">
                      <StyledView className="flex-row items-start justify-between">
                        <StyledView className="flex-1">
                          <StyledText tw="font-semibold text-gray-900 mb-1">
                            {condition.condition_name}
                          </StyledText>
                          
                          <StyledView className="flex-row items-center space-x-2 mb-2">
                            <StyledView className={`px-2 py-1 rounded-full ${getStatusColor(condition.status || 'active')}`}>
                              <StyledText tw="text-xs font-medium capitalize">
                                {condition.status || 'active'}
                              </StyledText>
                            </StyledView>
                            {condition.severity && (
                              <StyledView className={`px-2 py-1 rounded-full ${getSeverityColor(condition.severity)}`}>
                                <StyledText tw="text-xs font-medium capitalize">
                                  {condition.severity}
                                </StyledText>
                              </StyledView>
                            )}
                          </StyledView>

                          {condition.diagnosing_doctor && (
                            <StyledText tw="text-sm text-gray-600 mb-1">
                              Doctor: {condition.diagnosing_doctor}
                            </StyledText>
                          )}
                          
                          {condition.notes && (
                            <StyledText tw="text-sm text-gray-600">
                              {condition.notes}
                            </StyledText>
                          )}
                        </StyledView>
                        
                        <StyledTouchableOpacity
                          onPress={() => handleDeleteCondition(index)}
                          className="p-2"
                        >
                          <Ionicons name="trash" size={16} color="#ef4444" />
                        </StyledTouchableOpacity>
                      </StyledView>
                    </StyledView>
                  ))}
                </StyledView>
              )}
            </StyledView>
          </Card>
        </StyledView>

        {/* Action Buttons */}
        <StyledView className="mt-8 mx-4 mb-8">
          <StyledTouchableOpacity
            onPress={handleCreateProfile}
            disabled={loading || !profile.name.trim()}
            className={`rounded-lg py-4 shadow-lg ${
              !profile.name.trim() ? 'bg-gray-400' : 'bg-blue-500'
            }`}
            style={{ elevation: 3 }}
          >
            {loading ? (
              <ActivityIndicator size="small" color="white" />
            ) : (
              <StyledText tw="text-white font-bold text-lg text-center">
                Complete Profile & Continue
              </StyledText>
            )}
          </StyledTouchableOpacity>

          <StyledView className="mt-4 px-4">
            <StyledText tw="text-gray-500 text-center text-sm leading-relaxed">
              Your profile helps us provide personalized health insights and ensure medication safety. All information is securely encrypted.
            </StyledText>
          </StyledView>
        </StyledView>
      </StyledScrollView>

      {/* Date Picker Modal */}
      {showDatePicker && (
        <DateTimePicker
          value={profile.dateOfBirth || new Date()}
          mode="date"
          display="default"
          onChange={handleDateChange}
          maximumDate={new Date()}
        />
      )}

      {/* Medical Condition Modal */}
      <StyledModal
        visible={showConditionModal}
        animationType="slide"
        presentationStyle="pageSheet"
      >
        <StyledView className="flex-1 bg-white">
          <StyledView className="flex-row items-center justify-between px-4 py-4 border-b border-gray-200">
            <StyledTouchableOpacity onPress={() => setShowConditionModal(false)}>
              <StyledText tw="text-blue-500 font-medium">Cancel</StyledText>
            </StyledTouchableOpacity>
            <StyledText tw="font-semibold text-lg">Add Condition</StyledText>
            <StyledTouchableOpacity onPress={handleSaveCondition}>
              <StyledText tw="text-blue-500 font-medium">Save</StyledText>
            </StyledTouchableOpacity>
          </StyledView>

          <StyledScrollView className="flex-1 px-4 py-6">
            <StyledView className="mb-4">
              <StyledText tw="font-semibold mb-2 text-gray-700">
                Condition Name *
              </StyledText>
              <StyledTextInput
                value={newCondition.condition_name}
                onChangeText={(text) => setNewCondition(prev => ({ ...prev, condition_name: text }))}
                placeholder="e.g., Diabetes Type 2, Hypertension"
                className="border border-gray-300 rounded-lg px-3 py-3 bg-white"
                style={{ color: colors.textPrimary }}
              />
            </StyledView>

            <StyledView className="mb-4">
              <StyledText tw="font-semibold mb-2 text-gray-700">
                Status
              </StyledText>
              <StyledView className="flex-row flex-wrap gap-2">
                {['active', 'chronic', 'managed', 'resolved', 'suspected'].map((status) => (
                  <StyledTouchableOpacity
                    key={status}
                    onPress={() => setNewCondition(prev => ({ ...prev, status: status as any }))}
                    className={`px-3 py-2 rounded-lg border ${
                      newCondition.status === status 
                        ? 'bg-blue-500 border-blue-500' 
                        : 'bg-white border-gray-300'
                    }`}
                  >
                    <StyledText 
                      tw={`font-medium capitalize ${
                        newCondition.status === status ? 'text-white' : 'text-gray-700'
                      }`}
                    >
                      {status}
                    </StyledText>
                  </StyledTouchableOpacity>
                ))}
              </StyledView>
            </StyledView>

            <StyledView className="mb-4">
              <StyledText tw="font-semibold mb-2 text-gray-700">
                Severity (Optional)
              </StyledText>
              <StyledView className="flex-row flex-wrap gap-2">
                {['mild', 'moderate', 'severe', 'critical'].map((severity) => (
                  <StyledTouchableOpacity
                    key={severity}
                    onPress={() => setNewCondition(prev => ({ ...prev, severity: severity as any }))}
                    className={`px-3 py-2 rounded-lg border ${
                      newCondition.severity === severity 
                        ? 'bg-blue-500 border-blue-500' 
                        : 'bg-white border-gray-300'
                    }`}
                  >
                    <StyledText 
                      tw={`font-medium capitalize ${
                        newCondition.severity === severity ? 'text-white' : 'text-gray-700'
                      }`}
                    >
                      {severity}
                    </StyledText>
                  </StyledTouchableOpacity>
                ))}
              </StyledView>
            </StyledView>

            <StyledView className="mb-4">
              <StyledText tw="font-semibold mb-2 text-gray-700">
                Diagnosing Doctor (Optional)
              </StyledText>
              <StyledTextInput
                value={newCondition.diagnosing_doctor || ''}
                onChangeText={(text) => setNewCondition(prev => ({ ...prev, diagnosing_doctor: text || null }))}
                placeholder="Dr. Smith"
                className="border border-gray-300 rounded-lg px-3 py-3 bg-white"
                style={{ color: colors.textPrimary }}
              />
            </StyledView>

            <StyledView className="mb-4">
              <StyledText tw="font-semibold mb-2 text-gray-700">
                Notes (Optional)
              </StyledText>
              <StyledTextInput
                value={newCondition.notes || ''}
                onChangeText={(text) => setNewCondition(prev => ({ ...prev, notes: text || null }))}
                placeholder="Additional notes about this condition"
                multiline
                numberOfLines={3}
                className="border border-gray-300 rounded-lg px-3 py-3 bg-white"
                style={{ color: colors.textPrimary, textAlignVertical: 'top' }}
              />
            </StyledView>
          </StyledScrollView>
        </StyledView>
      </StyledModal>
    </ScreenContainer>
  );
};

export default CreateProfileScreen;