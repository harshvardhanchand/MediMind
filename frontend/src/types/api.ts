// Or use string if UUIDs are handled as strings

// --- Enums based on backend ---
export enum DocumentType {
  PRESCRIPTION = 'prescription',
  LAB_RESULT = 'lab_result',
  IMAGING_REPORT = 'imaging_report',
  CONSULTATION_NOTE = 'consultation_note',
  DISCHARGE_SUMMARY = 'discharge_summary',
  OTHER = 'other',
}

export enum ProcessingStatus {
  PENDING = 'pending',
  OCR_COMPLETED = 'ocr_completed',
  EXTRACTION_COMPLETED = 'extraction_completed',
  REVIEW_REQUIRED = 'review_required',
  COMPLETED = 'completed',
  FAILED = 'failed',
}

export enum ReviewStatus {
  PENDING_REVIEW = 'pending_review',
  REVIEWED_CORRECTED = 'reviewed_corrected',
  REVIEWED_APPROVED = 'reviewed_approved',
}

export enum MedicationFrequency {
  ONCE_DAILY = 'once_daily',
  TWICE_DAILY = 'twice_daily',
  THREE_TIMES_DAILY = 'three_times_daily',
  FOUR_TIMES_DAILY = 'four_times_daily',
  EVERY_OTHER_DAY = 'every_other_day',
  ONCE_WEEKLY = 'once_weekly',
  TWICE_WEEKLY = 'twice_weekly',
  ONCE_MONTHLY = 'once_monthly',
  AS_NEEDED = 'as_needed',
  OTHER = 'other',
}

export enum MedicationStatus {
  ACTIVE = 'active',
  DISCONTINUED = 'discontinued',
  COMPLETED = 'completed',
  ON_HOLD = 'on_hold',
}

// Enum for HealthReadingType based on backend model
export enum HealthReadingType {
  BLOOD_PRESSURE = "blood_pressure",
  GLUCOSE = "glucose",
  HEART_RATE = "heart_rate",
  WEIGHT = "weight",
  HEIGHT = "height",
  BMI = "bmi",
  SPO2 = "spo2",
  TEMPERATURE = "temperature",
  RESPIRATORY_RATE = "respiratory_rate",
  PAIN_LEVEL = "pain_level",
  STEPS = "steps",
  SLEEP = "sleep",
  OTHER = "other",
}

// --- User ---
export interface MedicalCondition {
  condition_name: string;
  diagnosed_date?: string | null; // Date string YYYY-MM-DD
  status?: 'active' | 'resolved' | 'chronic' | 'managed' | 'suspected';
  severity?: 'mild' | 'moderate' | 'severe' | 'critical';
  diagnosing_doctor?: string | null;
  notes?: string | null;
}

export interface UserResponse {
  user_id: string;
  supabase_id?: string | null;
  email: string;
  created_at: string; // ISO DateTime string
  updated_at: string; // ISO DateTime string
  last_login?: string | null; // ISO DateTime string
  
  // Profile fields
  name?: string | null;
  date_of_birth?: string | null; // Date string YYYY-MM-DD
  weight?: number | null; // kg
  height?: number | null; // cm
  gender?: 'male' | 'female' | 'other' | null;
  profile_photo_url?: string | null;
  medical_conditions?: MedicalCondition[];
  
  // Metadata fields
  user_metadata?: any | null;
  app_metadata?: any | null;
}

export interface UserProfileUpdate {
  name?: string | null;
  date_of_birth?: string | null; // Date string YYYY-MM-DD
  weight?: number | null; // kg
  height?: number | null; // cm
  gender?: 'male' | 'female' | 'other' | null;
  profile_photo_url?: string | null;
  medical_conditions?: MedicalCondition[];
}

// --- Document ---
export interface DocumentFileMetadata {
  content_type?: string;
  size?: number;
  filename?: string;
}

export interface DocumentBase {
  original_filename: string;
  document_type: DocumentType;
  file_metadata?: DocumentFileMetadata | null;
  document_date?: string | null; // Date string YYYY-MM-DD
  source_name?: string | null;
  source_location_city?: string | null;
  tags?: string[] | null;
  user_added_tags?: string[] | null;
  related_to_health_goal_or_episode?: string | null;
}

export interface DocumentCreate extends DocumentBase {}

export interface DocumentRead extends DocumentBase {
  document_id: string;
  user_id: string;
  storage_path: string;
  upload_timestamp: string; // ISO DateTime string
  processing_status: ProcessingStatus;
  file_hash?: string | null;
  metadata_overrides?: Partial<DocumentBase> | null; // For fields that can be overridden
}

export interface DocumentMetadataUpdate {
  document_date?: string | null;
  source_name?: string | null;
  source_location_city?: string | null;
  tags?: string[] | null;
  user_added_tags?: string[] | null;
  related_to_health_goal_or_episode?: string | null;
  // Add any other fields that are part of metadata_overrides
}


// --- ExtractedData ---
export interface ExtractedDataResponse {
  extracted_data_id: string;
  document_id: string;
  content?: any | null; // This is JSONB, can be more specific if structure is known
  raw_text?: string | null;
  extraction_timestamp: string; // ISO DateTime string
  review_status: ReviewStatus;
  reviewed_by_user_id?: string | null;
  review_timestamp?: string | null; // ISO DateTime string
}

export interface ExtractedDataUpdate {
  content?: any; // For updating the structured content
  changed_fields?: Array<{
    section: 'medications' | 'lab_results' | 'notes';
    index?: number;
    field: string;
    oldValue: any;
    newValue: any;
    context?: string;
  }>; // For selective reprocessing
  trigger_selective_reprocessing?: boolean; // Whether to start selective reprocessing
}

export interface ExtractedDataStatusUpdate {
  review_status: ReviewStatus;
}

// New interface for combined document and extracted data details
export interface ExtractionDetailsResponse {
  document: {
    document_id: string;
    filename: string; // Corresponds to original_filename
    document_type: DocumentType;
    upload_date: string; // Corresponds to upload_timestamp
    processing_status: ProcessingStatus;
  };
  extracted_data: {
    extracted_data_id: string;
    raw_text?: string | null;
    content?: any | null;
    review_status: ReviewStatus;
    extraction_timestamp: string;
    review_timestamp?: string | null;
  };
}


// --- Medication ---
export interface MedicationBase {
  name: string;
  dosage?: string | null;
  frequency: MedicationFrequency;
  frequency_details?: string | null;
  start_date?: string | null; // Date string YYYY-MM-DD
  end_date?: string | null; // Date string YYYY-MM-DD
  time_of_day?: string[] | null; // e.g., ['08:00', '20:00']
  with_food?: boolean | null;
  reason?: string | null;
  prescribing_doctor?: string | null;
  pharmacy?: string | null;
  notes?: string | null;
  related_document_id?: string | null;
  tags?: string[] | null;
}

export interface MedicationCreate extends MedicationBase {
  status?: MedicationStatus; // Defaults to ACTIVE on backend
}

export interface MedicationUpdate {
  name?: string | null;
  dosage?: string | null;
  frequency?: MedicationFrequency | null;
  frequency_details?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  time_of_day?: string[] | null;
  with_food?: boolean | null;
  reason?: string | null;
  prescribing_doctor?: string | null;
  pharmacy?: string | null;
  notes?: string | null;
  status?: MedicationStatus | null;
  related_document_id?: string | null;
  tags?: string[] | null;
}

export interface MedicationResponse extends MedicationBase {
  medication_id: string;
  user_id: string;
  status: MedicationStatus;
  created_at: string; // ISO DateTime string
  updated_at: string; // ISO DateTime string
}

// --- HealthReading (Placeholder - to be defined with HealthReadings API) ---
export interface HealthReadingBase {
  reading_type: HealthReadingType; // Changed from type: string
  numeric_value?: number | null;    // Added
  unit?: string | null;
  systolic_value?: number | null;   // Added
  diastolic_value?: number | null;  // Added
  text_value?: string | null;       // Added
  json_value?: Record<string, any> | null; // Added, Record<string, any> is equivalent to Dict[str, Any]
  reading_date: string; // ISO DateTime string
  notes?: string | null;
  source?: string | null;           // Added
  related_document_id?: string | null; // Added
  // value: any; // Removed generic value field
}

export interface HealthReadingCreate extends HealthReadingBase {}

export interface HealthReadingUpdate extends Partial<Omit<HealthReadingBase, 'reading_type'>> {
  // reading_type can be optional here if we decide it can be updated.
  // Or make all fields of HealthReadingBase optional manually for more control.
  // For now, making most fields from HealthReadingBase partial. 
  // If reading_type is updatable, it should be Optional<HealthReadingType>
  reading_type?: HealthReadingType;
  numeric_value?: number | null;
  unit?: string | null;
  systolic_value?: number | null;
  diastolic_value?: number | null;
  text_value?: string | null;
  json_value?: Record<string, any> | null;
  reading_date?: string | null;
  notes?: string | null;
  source?: string | null;
  related_document_id?: string | null;
}

export interface HealthReadingResponse extends HealthReadingBase {
  health_reading_id: string;
  user_id: string;
  created_at: string; // ISO DateTime string
  updated_at: string; // ISO DateTime string
}

// --- API Service Function Signatures (Examples) ---

// For paginated responses if any (not explicitly defined in your current services)
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
}

// Query service
export interface QueryRequest {
  query_text: string;
}

export interface QueryResponse {
  query_text: string;
  answer: string;
  relevant_document_ids?: string[];
}

// --- Notification ---
export enum NotificationType {
  INTERACTION_ALERT = 'interaction_alert',
  RISK_ALERT = 'risk_alert',
  MEDICATION_REMINDER = 'medication_reminder',
  LAB_FOLLOWUP = 'lab_followup',
  SYMPTOM_MONITORING = 'symptom_monitoring',
  GENERAL_INFO = 'general_info',
}

export enum NotificationSeverity {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical',
}

export interface NotificationMetadata {
  correlation_type?: string;
  confidence_score?: number;
  entity_type?: string;
  entity_id?: string;
  recommendations?: string[];
  related_entities?: Array<{
    type: string;
    id: string;
    name: string;
  }>;
}

export interface NotificationBase {
  title: string;
  message: string;
  notification_type: NotificationType;
  severity: NotificationSeverity;
  metadata?: NotificationMetadata | null;
}

export interface NotificationCreate extends NotificationBase {}

export interface NotificationResponse extends NotificationBase {
  notification_id: string;
  user_id: string;
  is_read: boolean;
  created_at: string; // ISO DateTime string
  read_at?: string | null; // ISO DateTime string
}

export interface NotificationStatsResponse {
  total_count: number;
  unread_count: number;
  by_severity: Record<NotificationSeverity, number>;
  by_type: Record<NotificationType, number>;
}

export interface NotificationMarkReadRequest {
  notification_ids: string[];
}

// Generic error response from API (example)
export interface ApiErrorResponse {
  detail: string | { message: string; [key: string]: any }; // Backend often sends `detail`
} 