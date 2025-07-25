import Constants from 'expo-constants';

// Base API URL (replace with your actual backend API URL)
export const API_URL = Constants.expoConfig?.extra?.apiUrl;

// Maximum file upload size in bytes (10 MB)
export const MAX_FILE_SIZE = 10 * 1024 * 1024;

// Supported document file types
export const SUPPORTED_FILE_TYPES = ['application/pdf', 'image/jpeg', 'image/png'];

// Document processing states
export const PROCESSING_STATES = {
  PENDING: 'pending',
  PROCESSING: 'processing',
  REVIEW_REQUIRED: 'review_required',
  COMPLETED: 'completed',
  FAILED: 'failed',
};

// Document types
export const DOCUMENT_TYPES = {
  PRESCRIPTION: 'prescription',
  LAB_RESULT: 'lab_result',
  IMAGING_REPORT: 'imaging_report',
  CONSULTATION_NOTE: 'consultation_note',
  DISCHARGE_SUMMARY: 'discharge_summary',
  OTHER: 'other',
}; 