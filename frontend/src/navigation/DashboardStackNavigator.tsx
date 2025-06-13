import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';


// Screen imports
import HomeScreen from '../screens/main/HomeScreen';
import DocumentUploadScreen from '../screens/DocumentUploadScreen'; // Corrected path and name
import VitalsScreen from '../screens/main/VitalsScreen';
import SymptomTrackerScreen from '../screens/main/SymptomTrackerScreen';
import MedicationsScreen from '../screens/main/MedicationsScreen'; 
import AddMedicationScreen from '../screens/AddMedicationScreen';
import MedicationDetailScreen from '../screens/main/MedicationDetailScreen';
import AddSymptomScreen from '../screens/main/AddSymptomScreen';
import HealthReadingsScreen from '../screens/HealthReadingsScreen'; // Corrected path
import AddHealthReadingScreen from '../screens/AddHealthReadingScreen'; // Corrected path
import QueryScreen from '../screens/QueryScreen'; // Corrected path
import DocumentDetailScreen from '../screens/main/DocumentDetailScreen';
import DataReviewScreen from '../screens/main/DataReviewScreen';
import NotificationScreen from '../screens/main/NotificationScreen';
import EditProfileScreen from '../screens/main/EditProfileScreen';

import { MainAppStackParamList } from './types';

// Placeholder for screens that might not exist yet to avoid import errors
const PlaceholderScreen = () => null; // Or a simple View with Text

// Check actual file names and paths
// For example, UploadScreen might be DocumentUploadScreen.tsx
// MedicationsScreen could be MedicationsListScreen.tsx or MedicationsScreen.tsx itself
// QueryScreen might be in ../screens/QueryScreen.tsx or ../screens/main/QueryScreen.tsx

const Stack = createNativeStackNavigator<MainAppStackParamList>();

const DashboardStackNavigator = () => {
  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      <Stack.Screen name="Home" component={HomeScreen} />
      <Stack.Screen name="Upload" component={DocumentUploadScreen} /> 
      <Stack.Screen name="Vitals" component={VitalsScreen} />
      <Stack.Screen name="SymptomTracker" component={SymptomTrackerScreen} />
      <Stack.Screen name="MedicationsScreen" component={MedicationsScreen} /> 
      <Stack.Screen name="AddMedication" component={AddMedicationScreen} />
      <Stack.Screen name="MedicationDetail" component={MedicationDetailScreen} />
      <Stack.Screen name="AddSymptom" component={AddSymptomScreen} />
      <Stack.Screen name="HealthReadings" component={HealthReadingsScreen} />
      <Stack.Screen name="AddHealthReading" component={AddHealthReadingScreen} />
      <Stack.Screen name="Query" component={QueryScreen} />
      <Stack.Screen name="DocumentDetail" component={DocumentDetailScreen} />
      <Stack.Screen name="DataReview" component={DataReviewScreen} />
      <Stack.Screen name="NotificationScreen" component={NotificationScreen} />
      <Stack.Screen name="EditProfile" component={EditProfileScreen} />
    </Stack.Navigator>
  );
};

export default DashboardStackNavigator; 