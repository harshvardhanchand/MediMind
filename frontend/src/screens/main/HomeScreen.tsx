import React from 'react';
import { View, ScrollView } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { Card as PaperCard } from 'react-native-paper';
import { Activity, Clipboard, Pill, Upload, Heart, FileText, Calendar, Thermometer, MessageCircle } from 'lucide-react-native';

import ScreenContainer from '../../components/layout/ScreenContainer';
import StyledText from '../../components/common/StyledText';
import StyledButton from '../../components/common/StyledButton';
import { styled } from 'nativewind';

const StyledView = styled(View);
const StyledScrollView = styled(ScrollView);

const HomeScreen = () => {
  const navigation = useNavigation();

  return (
    <ScreenContainer scrollable={false} withPadding={false}>
      <StyledScrollView tw="flex-1 px-4">
        {/* Header */}
        <StyledView tw="pt-4 pb-4">
          <StyledText variant="h1" color="primary">Dashboard</StyledText>
          <StyledText variant="body2" color="textSecondary" tw="mt-1">Welcome to your health insights</StyledText>
        </StyledView>

        {/* Key Metrics Section - Row of small cards */}
        <StyledView tw="flex-row space-x-3 mb-6">
          {/* Blood Pressure Card */}
          <StyledView tw="flex-1 bg-white p-3 rounded-lg shadow-sm">
            <StyledView tw="flex-row justify-between items-center mb-1">
              <StyledText variant="label" tw="text-gray-600">Blood Pressure</StyledText>
              <Activity size={16} color="#0EA5E9" />
            </StyledView>
            <StyledText variant="h3" color="textPrimary">120/80</StyledText>
            <StyledText variant="caption" color="textSecondary">Last checked today</StyledText>
          </StyledView>

          {/* Heart Rate Card */}
          <StyledView tw="flex-1 bg-white p-3 rounded-lg shadow-sm">
            <StyledView tw="flex-row justify-between items-center mb-1">
              <StyledText variant="label" tw="text-gray-600">Heart Rate</StyledText>
              <Heart size={16} color="#ea384c" />
            </StyledView>
            <StyledText variant="h3" color="textPrimary">72 bpm</StyledText>
            <StyledText variant="caption" color="textSecondary">2 hours ago</StyledText>
          </StyledView>

          {/* Glucose Card */}
          <StyledView tw="flex-1 bg-white p-3 rounded-lg shadow-sm">
            <StyledView tw="flex-row justify-between items-center mb-1">
              <StyledText variant="label" tw="text-gray-600">Glucose</StyledText>
              <Thermometer size={16} color="#4ADE80" />
            </StyledView>
            <StyledText variant="h3" color="textPrimary">98</StyledText>
            <StyledText variant="caption" color="textSecondary">Yesterday</StyledText>
          </StyledView>
        </StyledView>

        {/* Section: General Health Insights */}
        <StyledView tw="mb-6">
          <PaperCard mode="elevated" style={{ borderRadius: 12, elevation: 2 }}>
            <PaperCard.Content>
              <StyledView tw="flex-row items-center mb-3">
                <Activity size={20} color="#0EA5E9" />
                <StyledText variant="h3" tw="ml-2 text-primary">Health Insights</StyledText>
              </StyledView>
              
              <StyledView tw="mb-3 p-3 bg-medical-lightblue rounded-lg">
                <StyledText variant="label" tw="font-semibold text-medical-blue mb-1">Sleep Quality Up!</StyledText>
                <StyledText variant="body2" color="textSecondary">Your average sleep quality has improved by 15% this week. Keep it up!</StyledText>
              </StyledView>
              
              <StyledView tw="p-3 bg-medical-lightgreen rounded-lg">
                <StyledText variant="label" tw="font-semibold text-medical-green mb-1">Blood Pressure Reminder</StyledText>
                <StyledText variant="body2" color="textSecondary">Friendly reminder to check your blood pressure today as scheduled.</StyledText>
              </StyledView>
            </PaperCard.Content>
          </PaperCard>
        </StyledView>

        {/* Section: Recently Uploaded Documents */}
        <StyledView tw="mb-6">
          <PaperCard mode="elevated" style={{ borderRadius: 12, elevation: 2 }}>
            <PaperCard.Content>
              <StyledView tw="flex-row items-center mb-3">
                <FileText size={20} color="#0EA5E9" />
                <StyledText variant="h3" tw="ml-2 text-primary">Recent Documents</StyledText>
              </StyledView>
              
              {/* Mock Document 1 */}
              <StyledView tw="mb-2 pb-2 border-b border-gray-200 flex-row items-center">
                <StyledView tw="bg-medical-lightblue p-2 rounded-md mr-3">
                  <Clipboard size={16} color="#0EA5E9" />
                </StyledView>
                <StyledView tw="flex-1">
                  <StyledText variant="label" tw="font-semibold text-gray-800">Lab Report - Blood Test</StyledText>
                  <StyledView tw="flex-row items-center">
                    <Calendar size={12} color="#6B7280" />
                    <StyledText variant="caption" color="textSecondary" tw="ml-1">May 10, 2024</StyledText>
                  </StyledView>
                </StyledView>
              </StyledView>

              {/* Mock Document 2 */}
              <StyledView tw="mb-2 pb-2 border-b border-gray-200 flex-row items-center">
                <StyledView tw="bg-medical-lightgreen p-2 rounded-md mr-3">
                  <Pill size={16} color="#4ADE80" />
                </StyledView>
                <StyledView tw="flex-1">
                  <StyledText variant="label" tw="font-semibold text-gray-800">Prescription - Amoxicillin</StyledText>
                  <StyledView tw="flex-row items-center">
                    <Calendar size={12} color="#6B7280" />
                    <StyledText variant="caption" color="textSecondary" tw="ml-1">May 08, 2024</StyledText>
                  </StyledView>
                </StyledView>
              </StyledView>

              {/* Mock Document 3 */}
              <StyledView tw="mb-3 flex-row items-center">
                <StyledView tw="bg-gray-100 p-2 rounded-md mr-3">
                  <FileText size={16} color="#6B7280" />
                </StyledView>
                <StyledView tw="flex-1">
                  <StyledText variant="label" tw="font-semibold text-gray-800">X-Ray - Chest Scan</StyledText>
                  <StyledView tw="flex-row items-center">
                    <Calendar size={12} color="#6B7280" />
                    <StyledText variant="caption" color="textSecondary" tw="ml-1">May 05, 2024</StyledText>
                  </StyledView>
                </StyledView>
              </StyledView>
            </PaperCard.Content>
            <PaperCard.Actions>
              <StyledButton variant="outline" onPress={() => navigation.navigate('Documents' as never)}>
                View All Documents
              </StyledButton>
            </PaperCard.Actions>
          </PaperCard>
        </StyledView>

        {/* Section: Upcoming Medications */}
        <StyledView tw="mb-6">
          <PaperCard mode="elevated" style={{ borderRadius: 12, elevation: 2 }}>
            <PaperCard.Content>
              <StyledView tw="flex-row items-center mb-3">
                <Pill size={20} color="#0EA5E9" />
                <StyledText variant="h3" tw="ml-2 text-primary">Upcoming Medications</StyledText>
              </StyledView>
              
              {/* Mock Medication 1 */}
              <StyledView tw="mb-2 pb-2 border-b border-gray-200 flex-row items-center">
                <StyledView tw="bg-medical-lightpurple p-2 rounded-md mr-3">
                  <Pill size={16} color="#9b87f5" />
                </StyledView>
                <StyledView tw="flex-1">
                  <StyledText variant="label" tw="font-semibold text-gray-800">Lisinopril - 10mg</StyledText>
                  <StyledText variant="caption" color="textSecondary">Next due: Today, 9:00 AM</StyledText>
                </StyledView>
              </StyledView>

              {/* Mock Medication 2 */}
              <StyledView tw="mb-2 pb-2 border-b border-gray-200 flex-row items-center">
                <StyledView tw="bg-medical-lightpurple p-2 rounded-md mr-3">
                  <Pill size={16} color="#9b87f5" />
                </StyledView>
                <StyledView tw="flex-1">
                  <StyledText variant="label" tw="font-semibold text-gray-800">Metformin - 500mg</StyledText>
                  <StyledText variant="caption" color="textSecondary">Next due: Today, 7:00 PM</StyledText>
                </StyledView>
              </StyledView>

              {/* Mock Medication 3 */}
              <StyledView tw="mb-3 flex-row items-center">
                <StyledView tw="bg-medical-lightpurple p-2 rounded-md mr-3">
                  <Pill size={16} color="#9b87f5" />
                </StyledView>
                <StyledView tw="flex-1">
                  <StyledText variant="label" tw="font-semibold text-gray-800">Atorvastatin - 20mg</StyledText>
                  <StyledText variant="caption" color="textSecondary">Next due: Tomorrow, 8:00 AM</StyledText>
                </StyledView>
              </StyledView>
            </PaperCard.Content>
            <PaperCard.Actions>
              <StyledButton variant="outline" onPress={() => navigation.navigate('Medications' as never)}>
                Manage Medications
              </StyledButton>
            </PaperCard.Actions>
          </PaperCard>
        </StyledView>

        {/* Quick Navigation */}
        <StyledView tw="mb-6">
          <StyledView tw="flex-row items-center mb-3">
            <MessageCircle size={20} color="#0EA5E9" />
            <StyledText variant="h3" tw="ml-2 text-primary">Quick Actions</StyledText>
          </StyledView>
          
          <StyledButton 
            variant="primary" 
            icon={() => <Upload size={18} color="#FFFFFF" />}
            onPress={() => navigation.navigate('Upload' as never)} 
            tw="mb-3 w-full"
          >
            Upload New Document
          </StyledButton>
          
          <StyledView tw="flex-row mb-3 space-x-2">
            <StyledButton 
              variant="outline" 
              icon={() => <Activity size={18} color="#0EA5E9" />}
              onPress={() => navigation.navigate('Vitals' as never)} 
              tw="flex-1"
            >
              Track Vitals
            </StyledButton>
            
            <StyledButton 
              variant="outline" 
              icon={() => <Clipboard size={18} color="#0EA5E9" />}
              onPress={() => navigation.navigate('SymptomTracker' as never)} 
              tw="flex-1"
            >
              Log Symptoms
            </StyledButton>
          </StyledView>
          
          <StyledButton 
            variant="outline"
            icon={() => <MessageCircle size={18} color="#0EA5E9" />}
            onPress={() => navigation.navigate('Assistant' as never)} 
            tw="w-full"
          >
            Ask Assistant
          </StyledButton>
        </StyledView>

        <StyledButton 
          variant="ghost" 
          color="error" 
          onPress={() => navigation.navigate('Onboarding' as never)} 
          tw="mt-2 mb-6 w-full"
        >
          Log Out (Dev)
        </StyledButton>
      </StyledScrollView>
    </ScreenContainer>
  );
};

export default HomeScreen; 