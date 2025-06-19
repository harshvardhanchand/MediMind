import { MedicationStatus, MedicationFrequency, MedicalCondition, DocumentRead, HealthReadingResponse, MedicationResponse, NotificationResponse } from './api';
import { MainAppStackParamList } from '../navigation/types';

// ============================================================================
// HEALTH READINGS & VITALS
// ============================================================================

export type ReadingType = 'all' | 'bloodPressure' | 'bloodGlucose' | 'heartRate';

export interface ReadingData {
  date: string;
  bloodPressureSystolic?: number;
  bloodPressureDiastolic?: number;
  bloodGlucose?: number;
  heartRate?: number;
}

export interface ChartDataset {
  data: number[];
  color: () => string;
  strokeWidth: number;
  label: string;
}

// ============================================================================
// SYMPTOMS
// ============================================================================

export interface SymptomEntry {
  id: string;
  reading_date: string;
  symptom: string;
  severity: number;
  notes?: string;
  color?: string;
}

// ============================================================================
// MEDICATIONS
// ============================================================================

export interface MedicationEntry {
  id: string;
  name: string;
  dosage?: string;
  frequency: string;
  start_date?: string;
  status: MedicationStatus;
  reason?: string;
  prescribing_doctor?: string;
  created_at: string;
}

export interface MedicationDetailData {
  id: string;
  name: string;
  dosage?: string;
  frequency?: string;
  prescribingDoctor?: string;
  startDate?: string;
  endDate?: string;
  notes?: string;
  reason?: string;
}

export interface MedicationFormData {
  id?: string;
  name: string;
  dosageValue: string;
  dosageUnit: string;
  frequency: string;
  prescribingDoctor?: string;
  startDate?: string;
  endDate?: string;
  notes?: string;
}

// ============================================================================
// DOCUMENTS & DATA REVIEW
// ============================================================================

export interface MedicalEvent {
  event_type?: string;
  description?: string;
  [key: string]: any;
}

export interface ExtractedField {
  label: string;
  value: string | number | null;
  unit?: string;
}

export interface MedicationContent {
  name: ExtractedField;
  dosage: ExtractedField;
  frequency: ExtractedField;
}

export interface FormattedExtractedContent {
  lab_results?: ExtractedField[];
  medications?: MedicationContent[];
  notes?: string;
}

export interface ReviewDocument {
  id: string;
  name: string;
  type: string;
  extractedContent: FormattedExtractedContent | null;
}

export interface ChangedField {
  section: 'medications' | 'lab_results' | 'notes';
  index?: number;
  field: string;
  oldValue: any;
  newValue: any;
  context?: string;
}

// ============================================================================
// LAB RESULTS
// ============================================================================

export interface LabResultEntry {
  id: string;
  date: string;
  value: string;
  unit: string;
  referenceRange?: string;
  notes?: string;
}

// ============================================================================
// USER PROFILES
// ============================================================================

export interface UserProfile {
  name: string;
  email?: string;
  dateOfBirth: Date | null;
  weight: string;
  height: string;
  gender: 'male' | 'female' | 'other' | '';
  medicalConditions: MedicalCondition[];
  createdAt?: string | null;
}

// ============================================================================
// SETTINGS
// ============================================================================

export interface SettingItem {
  id: string;
  label: string;
  iconName: string;
  navigateTo?: keyof MainAppStackParamList | null;
  action?: () => void;
  isDestructive?: boolean;
  isToggle?: boolean;
  value?: boolean;
}

// ============================================================================
// NOTIFICATIONS
// ============================================================================

export interface FilterOption {
  label: string;
  value: string | null;
}

// ============================================================================
// ONBOARDING
// ============================================================================

export interface Feature {
  id: number;
  icon: string;
  title: string;
  description: string;
  color: string;
}

// ============================================================================
// HEALTH DATA CATEGORIES
// ============================================================================

export interface HealthCategory {
  id: string;
  label: string;
  iconName: string;
  navigateTo: keyof MainAppStackParamList;
  description?: string;
}

// ============================================================================
// CHAT/ASSISTANT
// ============================================================================

export interface Message {
  id: string;
  text: string;
  sender: 'user' | 'assistant';
  timestamp: Date;
}

// ============================================================================
// DASHBOARD & HOME
// ============================================================================

export interface KeyMetric {
  id: string;
  label: string;
  value: string;
  unit?: string;
  lastChecked: string;
  iconName: string;
  iconColor: string;
}

export interface QuickAction {
  id: string;
  label: string;
  iconNameLeft: string;
  screen: string;
  variant: 'filledPrimary' | 'filledSecondary' | 'textPrimary' | 'textDestructive';
  fullWidth?: boolean;
}

export interface HealthInsight {
  id: string;
  iconName: string;
  iconColor: string;
  title: string;
  description: string;
  onPress: () => void;
}

// ============================================================================
// FORM VALIDATION
// ============================================================================

export interface ValidationError {
  field: string;
  message: string;
}

// ============================================================================
// API RESPONSE WRAPPERS (for screens that extend API types)
// ============================================================================

export interface Document extends DocumentRead {}

// ============================================================================
// UPLOAD & FILE HANDLING
// ============================================================================

export interface FileAsset {
  uri: string;
  name: string;
  mimeType?: string;
  size?: number;
}

// ============================================================================
// CHART & VISUALIZATION
// ============================================================================

export interface ChartDataPoint {
  x: string | number;
  y: number;
  label?: string;
}

export interface ChartConfig {
  backgroundColor: string;
  backgroundGradientFrom: string;
  backgroundGradientTo: string;
  color: (opacity?: number) => string;
  labelColor: (opacity?: number) => string;
  strokeWidth?: number;
  barPercentage?: number;
  useShadowColorFromDataset?: boolean;
  decimalPlaces?: number;
} 