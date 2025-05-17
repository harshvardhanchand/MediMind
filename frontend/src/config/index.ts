import { API_URL as ENV_API_URL } from '@env';

// Base API URL (replace with your actual backend API URL)
export const API_URL = ENV_API_URL;

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
  OTHER: 'other',
}; 