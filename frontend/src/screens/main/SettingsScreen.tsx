import React from 'react';
import { View, Text, Button, ScrollView } from 'react-native';
import { styled } from 'nativewind';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { MainAppStackParamList } from '../../navigation/types';

const StyledView = styled(View);
const StyledText = styled(Text);
const StyledScrollView = styled(ScrollView);

type SettingsScreenNavigationProp = NativeStackNavigationProp<MainAppStackParamList, 'Settings'>;

const SettingsScreen = () => {
  const navigation = useNavigation<SettingsScreenNavigationProp>();

  const handleLogout = () => {
    // Perform actual logout logic here (e.g., clear token, reset Zustand store)
    console.log("Logging out...");
    navigation.getParent()?.navigate('Auth' as never); // Navigate to Auth stack, assuming RootNavigator is parent
  };

  const handleExportData = () => {
    console.log("Initiating data export...");
    // Implement data export functionality
    alert("Data Export Initiated! (Placeholder)");
  };

  return (
    <StyledScrollView className="flex-1 p-4 bg-gray-50">
      <StyledText className="text-2xl font-bold mb-6">Settings</StyledText>

      <StyledView className="mb-6 p-4 bg-white rounded-lg shadow">
        <StyledText className="text-lg font-semibold mb-2">Account</StyledText>
        {/* <Button title="Edit Profile" onPress={() => {}} /> */} 
        <Button title="Logout" onPress={handleLogout} color="red"/>
      </StyledView>

      <StyledView className="mb-6 p-4 bg-white rounded-lg shadow">
        <StyledText className="text-lg font-semibold mb-2">Data Management</StyledText>
        <Button title="Export My Data" onPress={handleExportData} />
      </StyledView>
      
      <StyledView className="mb-6 p-4 bg-white rounded-lg shadow">
        <StyledText className="text-lg font-semibold mb-2">Support</StyledText>
        <Button title="Help Center" onPress={() => {alert('Navigate to Help Center')}} />
        <Button title="Contact Support" onPress={() => {alert('Open email to support')}} />
      </StyledView>
      
      <StyledView className="mb-6 p-4 bg-white rounded-lg shadow">
        <StyledText className="text-lg font-semibold mb-2">About</StyledText>
        <StyledText className="text-gray-600">App Version: 1.0.0</StyledText>
        {/* <Button title="Terms of Service" onPress={() => {}} /> */} 
        {/* <Button title="Privacy Policy" onPress={() => {}} /> */} 
      </StyledView>

      <Button title="Back to Home" onPress={() => navigation.navigate('Home')} />
    </StyledScrollView>
  );
};

export default SettingsScreen; 