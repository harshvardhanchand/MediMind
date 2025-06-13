import React, { useState, useEffect } from 'react';
import { ScrollView, View, TextInput, TouchableOpacity, Alert, ActivityIndicator } from 'react-native';
import { styled } from 'nativewind';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { Ionicons } from '@expo/vector-icons';
import DateTimePicker from '@react-native-community/datetimepicker';

import { MainAppStackParamList } from '../../navigation/types';
import ScreenContainer from '../../components/layout/ScreenContainer';
import StyledText from '../../components/common/StyledText';
import Card from '../../components/common/Card';
import { useTheme } from '../../theme';
import { useAuth } from '../../context/AuthContext';

const StyledScrollView = styled(ScrollView);
const StyledView = styled(View);
const StyledTextInput = styled(TextInput);
const StyledTouchableOpacity = styled(TouchableOpacity);

type EditProfileScreenNavigationProp = NativeStackNavigationProp<MainAppStackParamList, 'EditProfile'>;

interface UserProfile {
  name: string;
  email: string;
  dateOfBirth: Date | null;
  weight: string;
  height: string;
  gender: 'male' | 'female' | 'other' | '';
}

const EditProfileScreen = () => {
  const navigation = useNavigation<EditProfileScreenNavigationProp>();
  const { colors } = useTheme();
  const { user } = useAuth();
  
  const [profile, setProfile] = useState<UserProfile>({
    name: '',
    email: '',
    dateOfBirth: null,
    weight: '',
    height: '',
    gender: '',
  });
  
  const [loading, setLoading] = useState(false);
  const [showDatePicker, setShowDatePicker] = useState(false);

  useEffect(() => {
    // Load user profile data
    if (user) {
      setProfile({
        name: (user as any).name || '',
        email: user.email || '',
        dateOfBirth: (user as any).date_of_birth ? new Date((user as any).date_of_birth) : null,
        weight: (user as any).weight ? (user as any).weight.toString() : '',
        height: (user as any).height ? (user as any).height.toString() : '',
        gender: (user as any).gender || '',
      });
    }
  }, [user]);

  const handleSave = async () => {
    setLoading(true);
    try {
      // Prepare the data for the API
      const updateData = {
        name: profile.name,
        date_of_birth: profile.dateOfBirth ? profile.dateOfBirth.toISOString().split('T')[0] : null,
        weight: profile.weight ? parseFloat(profile.weight) : null,
        height: profile.height ? parseInt(profile.height) : null,
        gender: profile.gender || null,
      };

      // TODO: Replace with actual API call
      console.log('Saving profile:', updateData);
      
      // Simulate API call for now
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      Alert.alert('Success', 'Profile updated successfully!', [
        { text: 'OK', onPress: () => navigation.goBack() }
      ]);
    } catch (error) {
      console.error('Error updating profile:', error);
      Alert.alert('Error', 'Failed to update profile. Please try again.');
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

        {/* Member Since */}
        <StyledView className="mt-6 mx-4">
          <Card>
            <StyledView className="p-4">
              <StyledText variant="body2" tw="font-semibold mb-2 text-gray-700">
                Member Since
              </StyledText>
              <StyledText variant="body1" tw="text-gray-600">
                {user?.created_at ? new Date(user.created_at).toLocaleDateString('en-US', {
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
    </ScreenContainer>
  );
};

export default EditProfileScreen; 