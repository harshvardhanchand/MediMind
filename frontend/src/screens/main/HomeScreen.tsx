import React, { useState, useEffect } from 'react';
import { View, ScrollView, ActivityIndicator } from 'react-native';
import { styled } from 'nativewind';
import { useNavigation } from '@react-navigation/native';
import Ionicons from '@expo/vector-icons/Ionicons';

import ScreenContainer from '../../components/layout/ScreenContainer';
import StyledText from '../../components/common/StyledText';
import StyledButton from '../../components/common/StyledButton';
import Card from '../../components/common/Card';
import ListItem from '../../components/common/ListItem';
import { useTheme } from '../../theme';
import { documentServices, medicationServices, healthReadingsServices } from '../../api/services';
import { DocumentRead, MedicationResponse, HealthReadingResponse } from '../../types/api';
import { useNotifications } from '../../context/NotificationContext';

const StyledView = styled(View);
const StyledScrollView = styled(ScrollView);

const HomeScreen = () => {
  const navigation = useNavigation<any>();
  const { colors } = useTheme();
  
  // Data states
  const [documents, setDocuments] = useState<DocumentRead[]>([]);
  const [medications, setMedications] = useState<MedicationResponse[]>([]);
  const [healthReadings, setHealthReadings] = useState<HealthReadingResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [usingDummyData, setUsingDummyData] = useState(false);

  // Dummy data fallbacks
  const dummyDocuments: DocumentRead[] = [
    {
      document_id: 'dummy-doc1',
      user_id: 'dummy-user',
      original_filename: 'Lab Report - Blood Test.pdf',
      document_type: 'lab_result' as any,
      storage_path: 'dummy/path',
      upload_timestamp: '2024-05-10T00:00:00Z',
      processing_status: 'completed' as any,
      document_date: '2024-05-10',
      source_name: 'Central Lab',
    },
    {
      document_id: 'dummy-doc2',
      user_id: 'dummy-user',
      original_filename: 'Prescription - Amoxicillin.pdf',
      document_type: 'prescription' as any,
      storage_path: 'dummy/path',
      upload_timestamp: '2024-05-08T00:00:00Z',
      processing_status: 'completed' as any,
      document_date: '2024-05-08',
      source_name: 'Dr. Smith',
    },
    {
      document_id: 'dummy-doc3',
      user_id: 'dummy-user',
      original_filename: 'X-Ray - Chest Scan.pdf',
      document_type: 'imaging_report' as any,
      storage_path: 'dummy/path',
      upload_timestamp: '2024-05-05T00:00:00Z',
      processing_status: 'completed' as any,
      document_date: '2024-05-05',
      source_name: 'Radiology Center',
    },
  ];

  const dummyMedications: MedicationResponse[] = [
    {
      medication_id: 'dummy-med1',
      user_id: 'dummy-user',
      name: 'Lisinopril',
      dosage: '10mg',
      frequency: 'once_daily' as any,
      status: 'active' as any,
      created_at: '2024-05-01T09:00:00Z',
      updated_at: '2024-05-01T09:00:00Z',
    },
    {
      medication_id: 'dummy-med2',
      user_id: 'dummy-user',
      name: 'Metformin',
      dosage: '500mg',
      frequency: 'twice_daily' as any,
      status: 'active' as any,
      created_at: '2024-05-01T19:00:00Z',
      updated_at: '2024-05-01T19:00:00Z',
    },
  ];

  const dummyHealthReadings: any[] = [
    { reading_type: 'blood_pressure', systolic_value: 120, diastolic_value: 80, unit: 'mmHg', reading_date: new Date().toISOString() },
    { reading_type: 'heart_rate', numeric_value: 72, unit: 'bpm', reading_date: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString() },
    { reading_type: 'glucose', numeric_value: 98, unit: 'mg/dL', reading_date: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString() },
  ];

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setUsingDummyData(false);
      
      console.log('Fetching dashboard data...');
      
      // Fetch all data in parallel
      const [docsResult, medsResult, healthResult] = await Promise.allSettled([
        documentServices.getDocuments({ limit: 5 }),
        medicationServices.getMedications({ limit: 5, active_only: true }),
        healthReadingsServices.getHealthReadings().catch(() => ({ data: [] })) // Graceful fallback for health readings
      ]);

      let hasRealData = false;

      // Process documents
      if (docsResult.status === 'fulfilled' && docsResult.value.data?.length > 0) {
        setDocuments(docsResult.value.data);
        hasRealData = true;
        console.log(`Loaded ${docsResult.value.data.length} real documents`);
      } else {
        setDocuments(dummyDocuments);
        console.log('Using dummy documents');
      }

      // Process medications
      if (medsResult.status === 'fulfilled' && medsResult.value.data?.length > 0) {
        setMedications(medsResult.value.data);
        hasRealData = true;
        console.log(`Loaded ${medsResult.value.data.length} real medications`);
      } else {
        setMedications(dummyMedications);
        console.log('Using dummy medications');
      }

      // Process health readings
      if (healthResult.status === 'fulfilled' && healthResult.value.data?.length > 0) {
        setHealthReadings(healthResult.value.data);
        hasRealData = true;
        console.log(`Loaded ${healthResult.value.data.length} real health readings`);
      } else {
        setHealthReadings(dummyHealthReadings);
        console.log('Using dummy health readings');
      }

      setUsingDummyData(!hasRealData);
      
    } catch (err: any) {
      console.log('Dashboard API calls failed, using dummy data:', err.message);
      setDocuments(dummyDocuments);
      setMedications(dummyMedications);
      setHealthReadings(dummyHealthReadings);
      setUsingDummyData(true);
    } finally {
      setLoading(false);
    }
  };

  // Generate key metrics from health readings
  const getKeyMetrics = () => {
    const metrics = [];
    
    // Find latest readings
    const latestBP = healthReadings.find(r => r.reading_type === 'blood_pressure' || (r as any).reading_type === 'blood_pressure');
    const latestHR = healthReadings.find(r => r.reading_type === 'heart_rate' || (r as any).reading_type === 'heart_rate');
    const latestGlucose = healthReadings.find(r => r.reading_type === 'glucose' || (r as any).reading_type === 'glucose');

    if (latestBP) {
      const bp = latestBP as any;
      metrics.push({
        id: 'bp',
        label: 'Blood Pressure',
        value: `${bp.systolic_value || 120}/${bp.diastolic_value || 80}`,
        unit: 'mmHg',
        lastChecked: 'Today',
        iconName: 'heart-outline',
        iconColor: colors.dataColor4,
      });
    }

    if (latestHR) {
      const hr = latestHR as any;
      metrics.push({
        id: 'hr',
        label: 'Heart Rate',
        value: (hr.numeric_value || 72).toString(),
        unit: 'bpm',
        lastChecked: '2 hours ago',
        iconName: 'pulse-outline',
        iconColor: colors.dataColor4,
      });
    }

    if (latestGlucose) {
      const glucose = latestGlucose as any;
      metrics.push({
        id: 'glucose',
        label: 'Glucose',
        value: (glucose.numeric_value || 98).toString(),
        unit: 'mg/dL',
        lastChecked: 'Yesterday',
        iconName: 'thermometer-outline',
        iconColor: colors.dataColor2,
      });
    }

    return metrics;
  };

  const keyMetrics = getKeyMetrics();

  // Convert documents to display format
  const recentDocuments = documents.slice(0, 3).map(doc => ({
    id: doc.document_id,
    name: doc.original_filename.replace(/\.[^/.]+$/, ''), // Remove file extension
    type: doc.document_type,
    date: doc.document_date ? new Date(doc.document_date).toLocaleDateString() : 'Unknown date',
  }));

  // Convert medications to upcoming format
  const upcomingMedications = medications.slice(0, 3).map(med => ({
    id: med.medication_id,
    name: `${med.name}${med.dosage ? ` - ${med.dosage}` : ''}`,
    nextDue: 'Today', // Would calculate from frequency in real app
  }));

  const getDocIconName = (docType: string) => {
    switch (docType) {
      case 'lab_result':
        return 'flask-outline';
      case 'prescription':
        return 'medkit-outline';
      case 'imaging_report':
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

  // Mock data for Health Insights - now using real notification data
  const { stats: notificationStats } = useNotifications();
  
  const healthInsights = React.useMemo(() => {
    const insights = [];
    
    // Add notification-based insights
    if (notificationStats && notificationStats.unread_count > 0) {
      insights.push({
        id: 'notifications',
        iconName: 'notifications-outline',
        iconColor: notificationStats.by_severity?.critical > 0 ? colors.error : 
                   notificationStats.by_severity?.high > 0 ? colors.warning : colors.info,
        title: `${notificationStats.unread_count} New Alert${notificationStats.unread_count > 1 ? 's' : ''}`,
        description: notificationStats.by_severity?.critical > 0 
          ? 'You have critical health alerts that need attention.'
          : notificationStats.by_severity?.high > 0
          ? 'You have important health notifications to review.'
          : 'New health insights and reminders are available.',
        onPress: () => navigation.navigate('NotificationsTab' as any),
      });
    }

    // Add other insights
    insights.push({
      id: 'insight1',
      iconName: 'trending-up-outline',
      iconColor: colors.dataColor2, // Green for positive trends
      title: 'Sleep Quality Up!',
      description: 'Your average sleep quality has improved by 15% this week. Keep it up!',
      onPress: () => console.log('Navigate to sleep details'), // Placeholder action
    });

    return insights;
  }, [notificationStats, colors, navigation]);

  if (loading) {
    return (
      <ScreenContainer scrollable={false} withPadding={false}>
        <StyledView className="flex-1 justify-center items-center">
          <ActivityIndicator size="large" />
          <StyledText tw="mt-2 text-gray-600">Loading dashboard...</StyledText>
        </StyledView>
      </ScreenContainer>
    );
  }

  return (
    <ScreenContainer scrollable={false} withPadding={false}>
      <StyledScrollView className="flex-1 px-4 pt-6 pb-20" showsVerticalScrollIndicator={false}>
        <StyledView className="mb-8">
          <StyledText variant="h1" tw="font-bold text-3xl">Dashboard</StyledText>
          <StyledText variant="body1" color="textSecondary" tw="mt-1">
            Welcome to your health insights.
          </StyledText>
          
          {usingDummyData && (
            <StyledView className="mt-3 p-2 bg-yellow-100 rounded border border-yellow-300">
              <StyledText tw="text-yellow-800 text-sm text-center">
                📱 Showing sample data (API not connected)
              </StyledText>
            </StyledView>
          )}
        </StyledView>

        {keyMetrics.length > 0 && (
          <>
            <StyledText variant="h4" tw="mb-3 font-semibold">Highlights</StyledText>
            <StyledView className="flex-row -mx-1 mb-8">
              {keyMetrics.map((metric) => (
                <StyledView key={metric.id} className="flex-1 px-1">
                  <Card withShadow={true} tw="flex-1 min-h-[120]">
                    <StyledView className="flex-row justify-between items-center mb-3">
                      <StyledText variant="label" color="textSecondary" tw="text-xs font-medium flex-1 mr-2">
                        {metric.label === 'Blood Pressure' ? 'Blood Pressure' : metric.label}
                      </StyledText>
                      <Ionicons name={metric.iconName as any} size={20} color={metric.iconColor} style={{ marginRight: -2 }} />
                    </StyledView>
                    <StyledView className="mb-2">
                      <StyledText variant="h3" color="textPrimary" tw="font-bold text-2xl" numberOfLines={1} adjustsFontSizeToFit>
                        {metric.value}
                        {metric.unit && (
                          <StyledText variant="body2" color="textSecondary" tw="text-base">
                            {metric.unit}
                          </StyledText>
                        )}
                      </StyledText>
                    </StyledView>
                    <StyledText variant="caption" color="textMuted" tw="mt-auto text-xs">
                      {metric.lastChecked}
                    </StyledText>
                  </Card>
                </StyledView>
              ))}
            </StyledView>
          </>
        )}

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

      </StyledScrollView>
    </ScreenContainer>
  );
};

export default HomeScreen; 