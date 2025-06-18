import React, { useState, useEffect } from 'react';
import { ScrollView, View, TextInput, TouchableOpacity, Alert, ActivityIndicator, Modal } from 'react-native';
import { styled } from 'nativewind';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { Ionicons } from '@expo/vector-icons';
import DateTimePicker from '@react-native-community/datetimepicker';

import { MainAppStackParamList } from '../../navigation/types';
import ScreenContainer from '../../components/layout/ScreenContainer';
import StyledText from '../../components/common/StyledText';
import Card from '../../components/common/Card';
import ErrorState from '../../components/common/ErrorState';
import { useTheme } from '../../theme';
import { userServices } from '../../api/services';
import { MedicalCondition, UserProfileUpdate, UserResponse } from '../../types/api';
import { ERROR_MESSAGES, LOADING_MESSAGES, SUCCESS_MESSAGES } from '../../constants/messages';

const StyledScrollView = styled(ScrollView);
const StyledView = styled(View);
const StyledTextInput = styled(TextInput);
const StyledTouchableOpacity = styled(TouchableOpacity);
const StyledModal = styled(Modal);

type EditProfileScreenNavigationProp = NativeStackNavigationProp<MainAppStackParamList, 'EditProfile'>;

interface UserProfile {
  name: string;
  email: string;
  dateOfBirth: Date | null;
  weight: string;
  height: string;
  gender: 'male' | 'female' | 'other' | '';
  medicalConditions: MedicalCondition[];
  createdAt: string | null;
}

const EditProfileScreen = () => {
  const navigation = useNavigation<EditProfileScreenNavigationProp>();
  const { colors } = useTheme();
  
  const [profile, setProfile] = useState<UserProfile>({
    name: '',
    email: '',
    dateOfBirth: null,
    weight: '',
    height: '',
    gender: '',
    medicalConditions: [],
    createdAt: null,
  });
  
  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [showConditionModal, setShowConditionModal] = useState(false);
  const [editingConditionIndex, setEditingConditionIndex] = useState<number | null>(null);
  const [newCondition, setNewCondition] = useState<MedicalCondition>({
    condition_name: '',
    diagnosed_date: null,
    status: 'active',
    severity: undefined,
    diagnosing_doctor: null,
    notes: null,
  });

  useEffect(() => {
    // Load user profile data directly from API
    const fetchUserProfile = async () => {
      try {
        setError(null);
        const response = await userServices.getMe();
        const userData: UserResponse = response.data;
        
        setProfile({
          name: userData.name || '',
          email: userData.email || '',
          dateOfBirth: userData.date_of_birth ? new Date(userData.date_of_birth) : null,
          weight: userData.weight ? userData.weight.toString() : '',
          height: userData.height ? userData.height.toString() : '',
          gender: userData.gender || '',
          medicalConditions: userData.medical_conditions || [],
          createdAt: userData.created_at || null,
        });
      } catch (error: any) {
        console.error('Error fetching user profile:', error);
        setError(error.response?.data?.detail || error.message || ERROR_MESSAGES.PROFILE_LOAD_ERROR);
      } finally {
        setInitialLoading(false);
      }
    };

    fetchUserProfile();
  }, []);

  const handleSave = async () => {
    setLoading(true);
    try {
      // Prepare the data for the API
      const updateData: UserProfileUpdate = {
        name: profile.name || null,
        date_of_birth: profile.dateOfBirth ? profile.dateOfBirth.toISOString().split('T')[0] : null,
        weight: profile.weight ? parseFloat(profile.weight) : null,
        height: profile.height ? parseInt(profile.height) : null,
        gender: profile.gender || null,
        medical_conditions: profile.medicalConditions,
      };

      await userServices.updateProfile(updateData);
      
      Alert.alert('Success', SUCCESS_MESSAGES.PROFILE_UPDATED, [
        { text: 'OK', onPress: () => navigation.goBack() }
      ]);
    } catch (error: any) {
      console.error('Error updating profile:', error);
      Alert.alert('Error', error.response?.data?.detail || error.message || 'Failed to update profile. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const retryLoadProfile = () => {
    setInitialLoading(true);
    setError(null);
    // Re-trigger the useEffect by forcing a re-render
    const fetchUserProfile = async () => {
      try {
        setError(null);
        const response = await userServices.getMe();
        const userData: UserResponse = response.data;
        
        setProfile({
          name: userData.name || '',
          email: userData.email || '',
          dateOfBirth: userData.date_of_birth ? new Date(userData.date_of_birth) : null,
          weight: userData.weight ? userData.weight.toString() : '',
          height: userData.height ? userData.height.toString() : '',
          gender: userData.gender || '',
          medicalConditions: userData.medical_conditions || [],
          createdAt: userData.created_at || null,
        });
      } catch (error: any) {
        console.error('Error fetching user profile:', error);
        setError(error.response?.data?.detail || error.message || ERROR_MESSAGES.PROFILE_LOAD_ERROR);
      } finally {
        setInitialLoading(false);
      }
    };

    fetchUserProfile();
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
    setEditingConditionIndex(null);
    setShowConditionModal(true);
  };

  const handleEditCondition = (index: number) => {
    setNewCondition({ ...profile.medicalConditions[index] });
    setEditingConditionIndex(index);
    setShowConditionModal(true);
  };

  const handleSaveCondition = () => {
    if (!newCondition.condition_name.trim()) {
      Alert.alert('Error', 'Please enter a condition name');
      return;
    }

    const updatedConditions = [...profile.medicalConditions];
    
    if (editingConditionIndex !== null) {
      updatedConditions[editingConditionIndex] = newCondition;
    } else {
      updatedConditions.push(newCondition);
    }

    setProfile(prev => ({ ...prev, medicalConditions: updatedConditions }));
    setShowConditionModal(false);
  };

  const handleDeleteCondition = (index: number) => {
    Alert.alert(
      'Delete Condition',
      'Are you sure you want to delete this medical condition?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: () => {
            const updatedConditions = profile.medicalConditions.filter((_, i) => i !== index);
            setProfile(prev => ({ ...prev, medicalConditions: updatedConditions }));
          }
        }
      ]
    );
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

  // ✅ Render loading state
  if (initialLoading) {
    return (
      <ScreenContainer>
        <StyledView className="flex-1 justify-center items-center">
          <ActivityIndicator size="large" color={colors.accentPrimary} />
          <StyledText 
            variant="body1" 
            tw="mt-4 text-center"
            style={{ color: colors.textSecondary }}
          >
            {LOADING_MESSAGES.LOADING_PROFILE}
          </StyledText>
        </StyledView>
      </ScreenContainer>
    );
  }

  // ✅ Render error state using standardized ErrorState component
  if (error) {
    return (
      <ScreenContainer>
        <ErrorState
          title="Unable to Load Profile"
          message={error}
          onRetry={retryLoadProfile}
          retryLabel="Try Again"
          icon="person-circle-outline"
        />
      </ScreenContainer>
    );
  }

  return (
    <ScreenContainer scrollable={false} withPadding={false}>
      <StyledScrollView className="flex-1 bg-gray-50">
        {/* Header */}
        <StyledView className="flex-row items-center px-4 pt-12 pb-6 bg-white">
          <StyledTouchableOpacity 
            onPress={() => navigation.goBack()}
            className="mr-4"
          >
            <Ionicons name="arrow-back" size={24} color={colors.textPrimary} />
          </StyledTouchableOpacity>
          <StyledText variant="h1" tw="font-bold text-xl flex-1">
            Edit Profile
          </StyledText>
          <StyledTouchableOpacity 
            onPress={handleSave}
            disabled={loading}
            className="px-4 py-2 bg-blue-500 rounded-lg"
          >
            {loading ? (
              <ActivityIndicator size="small" color="white" />
            ) : (
              <StyledText tw="text-white font-semibold">Save</StyledText>
            )}
          </StyledTouchableOpacity>
        </StyledView>

        {/* Profile Form */}
        <StyledView className="mt-6 mx-4">
          <Card>
            <StyledView className="p-4 space-y-4">
              {/* Name */}
              <StyledView>
                <StyledText variant="body2" tw="font-semibold mb-2 text-gray-700">
                  Full Name
                </StyledText>
                <StyledTextInput
                  value={profile.name}
                  onChangeText={(text) => setProfile(prev => ({ ...prev, name: text }))}
                  placeholder="Enter your full name"
                  className="border border-gray-300 rounded-lg px-3 py-3 bg-white"
                  style={{ color: colors.textPrimary }}
                />
              </StyledView>

              {/* Email (Read-only) */}
              <StyledView>
                <StyledText variant="body2" tw="font-semibold mb-2 text-gray-700">
                  Email
                </StyledText>
                <StyledTextInput
                  value={profile.email}
                  editable={false}
                  className="border border-gray-300 rounded-lg px-3 py-3 bg-gray-100"
                  style={{ color: colors.textSecondary }}
                />
                <StyledText variant="caption" tw="text-gray-500 mt-1">
                  Email cannot be changed
                </StyledText>
              </StyledView>

              {/* Date of Birth */}
              <StyledView>
                <StyledText variant="body2" tw="font-semibold mb-2 text-gray-700">
                  Date of Birth
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

              {/* Gender */}
              <StyledView>
                <StyledText variant="body2" tw="font-semibold mb-2 text-gray-700">
                  Gender
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
            </StyledView>
          </Card>
        </StyledView>

        {/* Medical Conditions */}
        <StyledView className="mt-6 mx-4">
          <Card>
            <StyledView className="p-4">
              <StyledView className="flex-row items-center justify-between mb-4">
                <StyledText variant="body2" tw="font-semibold text-gray-700">
                  Medical Conditions
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
                <StyledView className="py-8 items-center">
                  <Ionicons name="medical-outline" size={48} color={colors.textSecondary} />
                  <StyledText tw="text-gray-500 mt-2 text-center">
                    No medical conditions added yet
                  </StyledText>
                  <StyledText tw="text-gray-400 text-sm mt-1 text-center">
                    Tap "Add" to include your medical conditions
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

                          {condition.diagnosed_date && (
                            <StyledText tw="text-sm text-gray-600 mb-1">
                              Diagnosed: {new Date(condition.diagnosed_date).toLocaleDateString()}
                            </StyledText>
                          )}
                          
                          {condition.diagnosing_doctor && (
                            <StyledText tw="text-sm text-gray-600 mb-1">
                              Doctor: {condition.diagnosing_doctor}
                            </StyledText>
                          )}
                          
                          {condition.notes && (
                            <StyledText tw="text-sm text-gray-600 italic">
                              {condition.notes}
                            </StyledText>
                          )}
                        </StyledView>

                        <StyledView className="flex-row items-center space-x-2 ml-3">
                          <StyledTouchableOpacity
                            onPress={() => handleEditCondition(index)}
                            className="p-2"
                          >
                            <Ionicons name="pencil" size={16} color={colors.textSecondary} />
                          </StyledTouchableOpacity>
                          <StyledTouchableOpacity
                            onPress={() => handleDeleteCondition(index)}
                            className="p-2"
                          >
                            <Ionicons name="trash" size={16} color="#ef4444" />
                          </StyledTouchableOpacity>
                        </StyledView>
                      </StyledView>
                    </StyledView>
                  ))}
                </StyledView>
              )}
            </StyledView>
          </Card>
        </StyledView>

        {/* Member Since */}
        <StyledView className="mt-6 mx-4 mb-6">
          <Card>
            <StyledView className="p-4">
              <StyledText variant="body2" tw="font-semibold mb-2 text-gray-700">
                Member Since
              </StyledText>
              <StyledText variant="body1" tw="text-gray-600">
                {profile.createdAt ? new Date(profile.createdAt).toLocaleDateString('en-US', {
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric'
                }) : 'Unknown'}
              </StyledText>
            </StyledView>
          </Card>
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
          {/* Modal Header */}
          <StyledView className="flex-row items-center justify-between px-4 py-4 border-b border-gray-200">
            <StyledTouchableOpacity onPress={() => setShowConditionModal(false)}>
              <StyledText tw="text-blue-500 font-medium">Cancel</StyledText>
            </StyledTouchableOpacity>
            <StyledText tw="font-semibold text-lg">
              {editingConditionIndex !== null ? 'Edit Condition' : 'Add Condition'}
            </StyledText>
            <StyledTouchableOpacity onPress={handleSaveCondition}>
              <StyledText tw="text-blue-500 font-medium">Save</StyledText>
            </StyledTouchableOpacity>
          </StyledView>

          <StyledScrollView className="flex-1 px-4 py-6">
            {/* Condition Name */}
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

            {/* Status */}
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

            {/* Severity */}
            <StyledView className="mb-4">
              <StyledText tw="font-semibold mb-2 text-gray-700">
                Severity (Optional)
              </StyledText>
              <StyledView className="flex-row flex-wrap gap-2">
                {['mild', 'moderate', 'severe', 'critical'].map((severity) => (
                  <StyledTouchableOpacity
                    key={severity}
                    onPress={() => setNewCondition(prev => ({ 
                      ...prev, 
                      severity: prev.severity === severity ? undefined : severity as any 
                    }))}
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

            {/* Diagnosed Date */}
            <StyledView className="mb-4">
              <StyledText tw="font-semibold mb-2 text-gray-700">
                Diagnosed Date (Optional)
              </StyledText>
              <StyledTextInput
                value={newCondition.diagnosed_date || ''}
                onChangeText={(text) => setNewCondition(prev => ({ ...prev, diagnosed_date: text || null }))}
                placeholder="YYYY-MM-DD"
                className="border border-gray-300 rounded-lg px-3 py-3 bg-white"
                style={{ color: colors.textPrimary }}
              />
            </StyledView>

            {/* Diagnosing Doctor */}
            <StyledView className="mb-4">
              <StyledText tw="font-semibold mb-2 text-gray-700">
                Diagnosing Doctor (Optional)
              </StyledText>
              <StyledTextInput
                value={newCondition.diagnosing_doctor || ''}
                onChangeText={(text) => setNewCondition(prev => ({ ...prev, diagnosing_doctor: text || null }))}
                placeholder="Dr. Smith, Cardiologist"
                className="border border-gray-300 rounded-lg px-3 py-3 bg-white"
                style={{ color: colors.textPrimary }}
              />
            </StyledView>

            {/* Notes */}
            <StyledView className="mb-4">
              <StyledText tw="font-semibold mb-2 text-gray-700">
                Notes (Optional)
              </StyledText>
              <StyledTextInput
                value={newCondition.notes || ''}
                onChangeText={(text) => setNewCondition(prev => ({ ...prev, notes: text || null }))}
                placeholder="Additional notes about this condition..."
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

export default EditProfileScreen; 