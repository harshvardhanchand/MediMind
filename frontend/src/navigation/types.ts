export type AuthStackParamList = {
  Login: undefined;
  SignUp: undefined;
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
  // Add other main app screens here
};

export type RootStackParamList = {
  Auth: undefined; // This will nest the AuthStack
  Main: undefined; // This will nest the MainAppStack (or a TabNavigator)
  Onboarding: undefined;
}; 