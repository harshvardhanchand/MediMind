import React from 'react';
import { View, ScrollView } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import Ionicons from 'react-native-vector-icons/Ionicons';

import ScreenContainer from '../../components/layout/ScreenContainer';
import StyledText from '../../components/common/StyledText';
import StyledButton from '../../components/common/StyledButton';
import Card from '../../components/common/Card';
import { styled } from 'nativewind';
import { useTheme } from '../../theme';
import ListItem from '../../components/common/ListItem';
import { useAuth } from '../../context/AuthContext';
import { ActivityIndicator } from 'react-native';

const StyledView = styled(View);
const StyledScrollView = styled(ScrollView);

const HomeScreen = () => {
  const navigation = useNavigation<any>();
  const { colors } = useTheme();
  const { signOut, isLoading: authLoading } = useAuth();
  const [isLoggingOut, setIsLoggingOut] = React.useState(false);

  const keyMetrics = [
    {
      id: 'bp',
      label: 'Blood Pressure',
      value: '120/80',
      unit: 'mmHg',
      lastChecked: 'Today',
      iconName: 'heart-outline',
      iconColor: colors.dataColor4,
    },
    {
      id: 'hr',
      label: 'Heart Rate',
      value: '72',
      unit: 'bpm',
      lastChecked: '2 hours ago',
      iconName: 'pulse-outline',
      iconColor: colors.dataColor4,
    },
    {
      id: 'glucose',
      label: 'Glucose',
      value: '98',
      unit: 'mg/dL',
      lastChecked: 'Yesterday',
      iconName: 'thermometer-outline',
      iconColor: colors.dataColor2,
    },
  ];

  // Mock data for Recent Documents - replace with actual data fetching
  const recentDocuments = [
    {
      id: 'doc1',
      name: 'Lab Report - Blood Test',
      type: 'lab_result',
      date: 'May 10, 2024',
    },
    {
      id: 'doc2',
      name: 'Prescription - Amoxicillin',
      type: 'prescription',
      date: 'May 08, 2024',
    },
    {
      id: 'doc3',
      name: 'X-Ray - Chest Scan',
      type: 'imaging',
      date: 'May 05, 2024',
    },
  ];

  const getDocIconName = (docType: string) => {
    switch (docType) {
      case 'lab_result':
        return 'flask-outline';
      case 'prescription':
        return 'medkit-outline';
      case 'imaging':
        return 'images-outline';
      default:
        return 'document-text-outline';
    }
  };
  
  // Updated Mock data for Quick Actions to use iconNameLeft
  const quickActions = [
    { id: 'upload', label: 'Upload Document', iconNameLeft: 'cloud-upload-outline', screen: 'Upload', variant: 'filledPrimary' as const, fullWidth: true },
    { id: 'vitals', label: 'Track Vitals', iconNameLeft: 'pulse-outline', screen: 'Vitals', variant: 'filledSecondary' as const },
    { id: 'symptoms', label: 'Log Symptoms', iconNameLeft: 'clipboard-outline', screen: 'SymptomTracker', variant: 'filledSecondary' as const },
    { id: 'assistant', label: 'Ask Assistant', iconNameLeft: 'chatbubbles-outline', screen: 'AssistantTab' as any, variant: 'filledSecondary' as const, fullWidth: true },
  ];

  // Mock data for Upcoming Medications - replace with actual data fetching
  const upcomingMedications = [
    {
      id: 'med1',
      name: 'Lisinopril - 10mg',
      nextDue: 'Today, 9:00 AM',
      // type: 'cardiovascular' // Optional: for icon color logic if needed
    },
    {
      id: 'med2',
      name: 'Metformin - 500mg',
      nextDue: 'Today, 7:00 PM',
      // type: 'diabetes'
    },
    {
      id: 'med3',
      name: 'Atorvastatin - 20mg',
      nextDue: 'Tomorrow, 8:00 AM',
      // type: 'cholesterol'
    },
  ];

  // Mock data for Health Insights
  const healthInsights = [
    {
      id: 'insight1',
      iconName: 'trending-up-outline',
      iconColor: colors.dataColor2, // Green for positive trends
      title: 'Sleep Quality Up!',
      description: 'Your average sleep quality has improved by 15% this week. Keep it up!',
      onPress: () => console.log('Navigate to sleep details'), // Placeholder action
    },
    {
      id: 'insight2',
      iconName: 'notifications-outline',
      iconColor: colors.info, // Blue for informational reminders
      title: 'Blood Pressure Reminder',
      description: 'Friendly reminder to check your blood pressure today as scheduled.',
      onPress: () => console.log('Navigate to BP tracking'), // Placeholder action
    },
    // Add more insights as needed
  ];

  const handleLogout = async () => {
    setIsLoggingOut(true);
    try {
      await signOut();
      // Navigation to Auth/Onboarding will be handled by AppNavigator due to auth state change
    } catch (error) {
      console.error("Error during sign out:", error);
      // Optionally, show an alert to the user
    } finally {
      setIsLoggingOut(false);
    }
  };

  return (
    <ScreenContainer scrollable={false} withPadding={false}>
      <StyledScrollView className="flex-1 px-4 pt-6 pb-20" showsVerticalScrollIndicator={false}>
        <StyledView className="mb-8">
          <StyledText variant="h1" tw="font-bold text-3xl">Dashboard</StyledText>
          <StyledText variant="body1" color="textSecondary" tw="mt-1">
            Welcome to your health insights.
          </StyledText>
        </StyledView>

        <StyledText variant="h4" tw="mb-3 font-semibold">Highlights</StyledText>
        <StyledView className="flex-row -mx-1.5 mb-8">
          {keyMetrics.map((metric) => (
            <StyledView key={metric.id} className="flex-1 px-1.5">
              <Card withShadow={true} tw="flex-1">
                <StyledView className="flex-row justify-between items-start mb-1">
                  <StyledText variant="label" color="textSecondary" tw="mb-1">
                    {metric.label}
                  </StyledText>
                  <Ionicons name={metric.iconName as any} size={20} color={metric.iconColor} />
                </StyledView>
                <StyledText variant="h3" color="textPrimary" tw="font-bold">
                  {metric.value}
                  {metric.unit && <StyledText variant="body2" color="textSecondary">{metric.unit}</StyledText>}
                </StyledText>
                <StyledText variant="caption" color="textMuted" tw="mt-0.5">
                  {metric.lastChecked}
                </StyledText>
              </Card>
            </StyledView>
          ))}
        </StyledView>

        {/* Section: Recent Documents */}
        <Card title="Recent Activity" withShadow={true} tw="mb-6">
          {recentDocuments.length > 0 ? (
            recentDocuments.slice(0, 3).map((doc, index) => (
              <ListItem
                key={doc.id}
                iconLeft={getDocIconName(doc.type)}
                iconLeftColor={colors.accentPrimary} 
                label={doc.name}
                subtitle={doc.date}
                onPress={() => navigation.navigate('DocumentDetail', { documentId: doc.id })}
                showBottomBorder={index < Math.min(recentDocuments.length, 3) - 1}
              />
            ))
          ) : (
            <StyledText color="textMuted" tw="py-4 text-center">No recent activity.</StyledText>
          )}
          {recentDocuments.length > 3 && (
              <StyledButton
                  variant="textPrimary"
                  onPress={() => navigation.navigate('DocumentsTab' as any)} 
                  tw="mt-3 self-center pb-1"
              >
                  View All Documents
              </StyledButton>
          )}
        </Card>

        {/* Section: Upcoming Medications */}
        <Card title="Upcoming Medications" withShadow={true} tw="mb-6">
          {upcomingMedications.length > 0 ? (
            upcomingMedications.slice(0, 3).map((med, index) => (
              <ListItem
                key={med.id}
                iconLeft="medkit-outline" // Generic medication icon
                iconLeftColor={colors.dataColor5} // Purple for medications
                label={med.name}
                subtitle={med.nextDue}
                // onPress={() => navigation.navigate('MedicationDetail', { medicationId: med.id })} // Example navigation
                onPress={() => navigation.navigate('MedicationsScreen')} // Navigate to a general medications screen for now
                showBottomBorder={index < Math.min(upcomingMedications.length, 3) - 1}
              />
            ))
          ) : (
            <StyledText color="textMuted" tw="py-4 text-center">No upcoming medications.</StyledText>
          )}
          {upcomingMedications.length > 0 && (
              <StyledButton
                  variant="textPrimary"
                  // onPress={() => navigation.navigate('MedicationsTab')} // TODO: Update to correct tab/screen name
                  onPress={() => navigation.navigate('MedicationsScreen')}
                  tw="mt-3 self-center pb-1"
              >
                  Manage Medications
              </StyledButton>
          )}
        </Card>

        {/* Section: Health Insights */}
        <Card title="Health Insights" withShadow={true} tw="mb-6">
          {healthInsights.length > 0 ? (
            healthInsights.map((insight, index) => (
              <ListItem
                key={insight.id}
                iconLeft={insight.iconName}
                iconLeftColor={insight.iconColor}
                label={insight.title}
                subtitle={insight.description}
                onPress={insight.onPress}
                showBottomBorder={index < healthInsights.length - 1}
              />
            ))
          ) : (
            <StyledText color="textMuted" tw="py-4 text-center">No new insights at the moment.</StyledText>
          )}
           {/* Optionally, add a 'View More' if there are many insights */}
        </Card>

        {/* Section: Quick Actions - Using grid-like layout */}
        <Card title="Quick Actions" withShadow={true} tw="mb-6">
            <StyledView className="flex-row flex-wrap -m-1.5">
                {quickActions.map((action) => (
                    <StyledView 
                        key={action.id} 
                        className={`${action.fullWidth ? 'w-full' : 'w-1/2'} p-1.5`}
                    >
                        <StyledButton
                            variant={action.variant}
                            onPress={() => navigation.navigate(action.screen)}
                            tw="w-full" // Button takes full width of its cell
                            iconNameLeft={action.iconNameLeft} // Use new prop
                            // iconSize can be set here if needed, defaults to 18
                        >
                            {action.label} 
                        </StyledButton>
                    </StyledView>
                ))}
            </StyledView>
        </Card>

        <StyledButton 
          variant="textDestructive" 
          onPress={handleLogout}
          tw="mt-4 mb-6 self-center"
          disabled={isLoggingOut || authLoading}
        >
          {isLoggingOut ? <ActivityIndicator size="small" color={colors.error} /> : 'Log Out'}
        </StyledButton>

      </StyledScrollView>
    </ScreenContainer>
  );
};

export default HomeScreen; 