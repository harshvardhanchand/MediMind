import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { withScreenErrorBoundary } from '../utils/withErrorBoundary';
import HomeScreen from '../screens/main/HomeScreen';
import DocumentUploadScreen from '../screens/DocumentUploadScreen';
import VitalsScreen from '../screens/main/VitalsScreen';
import SymptomTrackerScreen from '../screens/main/SymptomTrackerScreen';
import MedicationsScreen from '../screens/main/MedicationsScreen';
import AddMedicationScreen from '../screens/AddMedicationScreen';
import MedicationDetailScreen from '../screens/main/MedicationDetailScreen';
import AddSymptomScreen from '../screens/main/AddSymptomScreen';
import HealthReadingsScreen from '../screens/HealthReadingsScreen';
import AddHealthReadingScreen from '../screens/AddHealthReadingScreen';
import QueryScreen from '../screens/QueryScreen';
import DocumentDetailScreen from '../screens/main/DocumentDetailScreen';
import DataReviewScreen from '../screens/main/DataReviewScreen';
import NotificationScreen from '../screens/main/NotificationScreen';
import EditProfileScreen from '../screens/main/EditProfileScreen';

import { MainAppStackParamList } from './types';

const HomeScreenWithErrorBoundary = withScreenErrorBoundary(HomeScreen, 'HomeScreen');
const QueryScreenWithErrorBoundary = withScreenErrorBoundary(QueryScreen, 'QueryScreen');
const DocumentDetailScreenWithErrorBoundary = withScreenErrorBoundary(DocumentDetailScreen, 'DocumentDetailScreen');
const NotificationScreenWithErrorBoundary = withScreenErrorBoundary(NotificationScreen, 'NotificationScreen');
const EditProfileScreenWithErrorBoundary = withScreenErrorBoundary(EditProfileScreen, 'EditProfileScreen');

const Stack = createNativeStackNavigator<MainAppStackParamList>();

const DashboardStackNavigator = () => {
  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      <Stack.Screen name="Home" component={HomeScreenWithErrorBoundary} />
      <Stack.Screen name="Upload" component={DocumentUploadScreen} />
      <Stack.Screen name="Vitals" component={VitalsScreen} />
      <Stack.Screen name="SymptomTracker" component={SymptomTrackerScreen} />
      <Stack.Screen name="MedicationsScreen" component={MedicationsScreen} />
      <Stack.Screen name="AddMedication" component={AddMedicationScreen} />
      <Stack.Screen name="MedicationDetail" component={MedicationDetailScreen} />
      <Stack.Screen name="AddSymptom" component={AddSymptomScreen} />
      <Stack.Screen name="HealthReadings" component={HealthReadingsScreen} />
      <Stack.Screen name="AddHealthReading" component={AddHealthReadingScreen} />
      <Stack.Screen name="Query" component={QueryScreenWithErrorBoundary} />
      <Stack.Screen name="DocumentDetail" component={DocumentDetailScreenWithErrorBoundary} />
      <Stack.Screen name="DataReview" component={DataReviewScreen} />
      <Stack.Screen name="NotificationScreen" component={NotificationScreenWithErrorBoundary} />
      <Stack.Screen name="EditProfile" component={EditProfileScreenWithErrorBoundary} />
    </Stack.Navigator>
  );
};

export default DashboardStackNavigator; 