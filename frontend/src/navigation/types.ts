import { NavigatorScreenParams } from '@react-navigation/native';
import { MedicationDetailData } from '../types/interfaces';

import { MainBottomTabParamList } from './MainTabNavigator';

export type ResetPasswordRouteParams = {
  type?: string;
  error_description?: string;
};

export type ConfirmRouteParams = {
  token_hash?: string;
  type?: string;
  error_description?: string;
};

export type AuthStackParamList = {
  Login: undefined;
  SignUp: undefined;
  ResetPassword: ResetPasswordRouteParams | undefined;
  Confirm: ConfirmRouteParams | undefined;
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
  Medications: undefined; 
  MedicationsScreen: undefined; 
 
  AddMedication: { 
    medicationIdToEdit?: string; 
    initialData?: MedicationDetailData; 
  } | undefined;
  MedicationDetail: { medicationId: string }; 
  
  Reports: undefined; 
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
  DashboardTab: undefined;
  DocumentsTab: undefined;
  DataTab: undefined; 
  AssistantTab: undefined;
  SettingsTab: undefined;
};


export type RootStackParamList = {
  Splash: undefined; 
  Auth: undefined; 
  Onboarding: NavigatorScreenParams<OnboardingStackParamList>; 
  Main: NavigatorScreenParams<MainBottomTabParamList>;
  
  
  DocumentDetail: { documentId: string };
  MedicationDetail: { medicationId: string };
  AddMedication?: { medicationIdToEdit?: string; initialData?: MedicationDetailData; }; // Optional if modal/global
  DataReview?: { documentId: string }; 
  AddHealthReading?: undefined;
  
  
 
  Upload?: undefined; 
  
}; 