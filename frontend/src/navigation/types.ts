import { NavigatorScreenParams } from '@react-navigation/native';
import { MedicationDetailData } from '../types/interfaces';

import { MainBottomTabParamList } from './MainTabNavigator';
// Assuming MedicationDetailData might be defined in MedicationDetailScreen or a shared types file
// For now, we'll use a generic object for initialData if needed, or define it if you point me to it.

// Define the parameters for the ResetPassword route
export type ResetPasswordRouteParams = {
  accessToken?: string;
  refreshToken?: string;
  type?: string;
  error_description?: string; // To handle errors passed in URL
};

export type AuthStackParamList = {
  Login: undefined;
  SignUp: undefined;
  ResetPassword: ResetPasswordRouteParams | undefined; // Update to accept params or be undefined
  // Register: undefined; // Removed as SignUpScreen is the primary
  // Add other auth screens here if needed
};

export type OnboardingStackParamList = {
  Welcome: undefined;
  Features: undefined;
  CreateProfile: undefined;
};

export type MainAppStackParamList = {
  Home: undefined;
  Upload: undefined;
  Documents: undefined;
  DocumentDetail: { documentId: string };
  DataReview: { documentId: string };
  Medications: undefined; // This screen might be an alias for MedicationsScreen or a stack root
  MedicationsScreen: undefined; // Lists all medications
  // For AddMedication: allows optional params for editing existing medication
  AddMedication: { 
    medicationIdToEdit?: string; 
    initialData?: MedicationDetailData; // Or Partial<MedicationFormData> if that's the type used in AddMedicationScreen's state
  } | undefined;
  MedicationDetail: { medicationId: string }; // Shows details of one medication
  
  Reports: undefined; // General reports, or could be where LabResultsList is mounted
  Assistant: undefined;
  Settings: undefined;
  EditProfile: undefined;
  Vitals: undefined;
  SymptomTracker: undefined;
  AddSymptom: undefined;
  HealthReadings: undefined;
  Query: undefined;
  AddHealthReading: undefined;
  NotificationScreen: undefined;

  // Tab navigator screen names (usually not navigated to directly like this unless part of a stack)
  DashboardTab: undefined;
  DocumentsTab: undefined;
  DataTab: undefined; 
  AssistantTab: undefined;
  SettingsTab: undefined;
};

// The actual navigation structure in the app seems to be flattened
export type RootStackParamList = {
  Splash: undefined; // Loading/splash screen
  Auth: undefined; // This will nest the AuthStack
  Onboarding: NavigatorScreenParams<OnboardingStackParamList>; // Updated to use OnboardingStack
  Main: NavigatorScreenParams<MainBottomTabParamList>;
  
  // Screens that can be pushed on top of the tab navigator or accessed globally
  DocumentDetail: { documentId: string };
  MedicationDetail: { medicationId: string };
  AddMedication?: { medicationIdToEdit?: string; initialData?: MedicationDetailData; }; // Optional if modal/global
  DataReview?: { documentId: string }; // Optional if modal/global
  AddHealthReading?: undefined;
  // Lab Results List and Detail removed for MVP
  // LabResultsList?: undefined;
  // LabResultDetail?: { testTypeId: string; testTypeName: string };
  
  // Other global screens like a standalone Upload if not part of a tab/stack
  Upload?: undefined; 
  // Query?: undefined; // If Query is a full screen outside tabs
  // HealthReadings?: undefined; // If HealthReadings is a full screen outside tabs
}; 