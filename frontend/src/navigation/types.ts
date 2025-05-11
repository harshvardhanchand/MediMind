export type AuthStackParamList = {
  Login: undefined;
  SignUp: undefined;
  Register: undefined;
  // Add other auth screens here if needed
};

export type MainAppStackParamList = {
  Home: undefined;
  Upload: undefined;
  Documents: undefined;
  DocumentDetail: { documentId: string };
  DataReview: { documentId: string };
  Medications: undefined;
  Reports: undefined;
  Assistant: undefined;
  Settings: undefined;
  Vitals: undefined;
  SymptomTracker: undefined;
  AddSymptom: undefined;
  DocumentUpload: undefined;
  HealthReadings: undefined;
  Query: undefined;
  AddHealthReading: undefined;
  AddMedication: undefined;
  MedicationsScreen: undefined;
  // Add other main app screens here
};

// The actual navigation structure in the app seems to be flattened
export type RootStackParamList = {
  Auth: undefined; // This will nest the AuthStack
  Main: undefined; // This will nest the MainAppStack (or a TabNavigator)
  Onboarding: undefined;
  Login: undefined;
  Home: undefined;
  DocumentDetail: { documentId: string };
  Medications: undefined;
  HealthReadings: undefined;
  Query: undefined;
  DocumentUpload: undefined;
}; 