import { AxiosResponse } from 'axios'; // To type the full response

import {
  UserResponse, // Assuming you might have a /me endpoint returning this
  UserProfileUpdate, // Added for profile updates
  DocumentRead,
  // DocumentCreate, // FormData handled directly
  ExtractedDataResponse,
  ExtractedDataUpdate,
  ExtractedDataStatusUpdate,
  MedicationResponse,
  MedicationCreate,
  MedicationUpdate,
  MedicationStatus,
  HealthReadingResponse, // Placeholder
  HealthReadingCreate,   // Placeholder
  QueryRequest,
  QueryResponse,
  DocumentMetadataUpdate,
  ExtractionDetailsResponse, // Added new response type
  DocumentType, // Make sure DocumentType is imported if used in params, it was missing here
  NotificationResponse,
  NotificationCreate,
  NotificationStatsResponse,
  NotificationMarkReadRequest,
  NotificationType,
  NotificationSeverity,
  // UUID, // No longer directly needed here if types handle it
} from '../types/api';

import apiClient from './client';

// Authentication services
// Authentication is handled directly by Supabase client SDK


// Document services
export const documentServices = {
  getDocuments: (params?: { skip?: number; limit?: number }): Promise<AxiosResponse<DocumentRead[]>> => 
    apiClient.get('/api/documents', { params }),
    
  getDocumentById: (id: string): Promise<AxiosResponse<DocumentRead>> => 
    apiClient.get(`/api/documents/${id}`),

  updateDocumentMetadata: (id: string, metadata: DocumentMetadataUpdate): Promise<AxiosResponse<DocumentRead>> =>
    apiClient.patch(`/api/documents/${id}/metadata`, metadata),
    
  deleteDocument: (id: string): Promise<AxiosResponse<void>> => 
    apiClient.delete(`/api/documents/${id}`),
    
  uploadDocument: (documentData: FormData): Promise<AxiosResponse<DocumentRead[]>> => 
    apiClient.post('/api/documents/upload', documentData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }),
    
  searchDocuments: (params: { query: string; document_type?: DocumentType; skip?: number; limit?: number }): Promise<AxiosResponse<DocumentRead[]>> =>
    apiClient.get('/api/documents/search', { params }),
    
  // getPresignedUrl remains misaligned if direct uploads are the strategy.
  // Commenting out for now as per decision to use direct backend uploads.
  // getPresignedUrl: (filename: string, contentType: string): Promise<AxiosResponse<{ upload_url: string, document_id: string }>> => 
  //   apiClient.post('/api/documents/presigned-url', { filename, contentType }),
};

// Extracted data services
export const extractedDataServices = {
  getExtractedData: (documentId: string): Promise<AxiosResponse<ExtractedDataResponse>> => 
    apiClient.get(`/api/extracted_data/${documentId}`),
    
  // Assuming this endpoint returns combined Document and ExtractedData details
  // The response type might need a custom interface if it's a mix.
  // For now, using ExtractedDataResponse, but it might be more like DocumentRead & ExtractedDataResponse nested.
  getAllExtractedData: (documentId: string): Promise<AxiosResponse<ExtractionDetailsResponse>> =>
    apiClient.get(`/api/extracted_data/all/${documentId}`),
    
  // Aligning with backend specific routes for status and content update
  updateExtractedDataStatus: (documentId: string, statusUpdate: ExtractedDataStatusUpdate): Promise<AxiosResponse<ExtractedDataResponse>> =>
    apiClient.put(`/api/extracted_data/${documentId}/status`, statusUpdate),

  updateExtractedDataContent: (documentId: string, contentUpdate: ExtractedDataUpdate): Promise<AxiosResponse<ExtractedDataResponse>> =>
    apiClient.put(`/api/extracted_data/${documentId}/content`, contentUpdate),
};

// Health readings services (using placeholder types for now)
export const healthReadingsServices = {
  getHealthReadings: (): Promise<AxiosResponse<HealthReadingResponse[]>> => 
    apiClient.get('/api/health_readings'),
    
  addHealthReading: (readingData: HealthReadingCreate): Promise<AxiosResponse<HealthReadingResponse>> => 
    apiClient.post('/api/health_readings', readingData),
  // Add update/delete if needed, e.g.:
  // updateHealthReading: (id: string, data: HealthReadingUpdate): Promise<AxiosResponse<HealthReadingResponse>> =>
  //   apiClient.put(`/api/health_readings/${id}`, data),
  // deleteHealthReading: (id: string): Promise<AxiosResponse<void>> =>
  //   apiClient.delete(`/api/health_readings/${id}`),
};

// Medication services
export const medicationServices = {
  // Add filter parameters to getMedications
  getMedications: (params?: { skip?: number; limit?: number; status?: MedicationStatus; search?: string; active_only?: boolean }): Promise<AxiosResponse<MedicationResponse[]>> => 
    apiClient.get('/api/medications', { params }),
    
  addMedication: (medicationData: MedicationCreate): Promise<AxiosResponse<MedicationResponse>> => 
    apiClient.post('/api/medications', medicationData),

  getMedicationById: (medicationId: string): Promise<AxiosResponse<MedicationResponse>> =>
    apiClient.get(`/api/medications/${medicationId}`),

  updateMedication: (medicationId: string, medicationData: MedicationUpdate): Promise<AxiosResponse<MedicationResponse>> =>
    apiClient.put(`/api/medications/${medicationId}`, medicationData),

  deleteMedication: (medicationId: string): Promise<AxiosResponse<void>> =>
    apiClient.delete(`/api/medications/${medicationId}`),
};

// Query services
export const queryServices = {
  askQuestion: (request: QueryRequest): Promise<AxiosResponse<QueryResponse>> => 
    apiClient.post('/api/query', request),
};

// User services
export const userServices = {
  getMe: (): Promise<AxiosResponse<UserResponse>> => 
    apiClient.get('/api/users/me'),
    
  updateProfile: (profileData: UserProfileUpdate): Promise<AxiosResponse<UserResponse>> => 
    apiClient.patch('/api/users/me/profile', profileData),
};

// Notification services
export const notificationServices = {
  getNotifications: (params?: { 
    skip?: number; 
    limit?: number; 
    unread_only?: boolean;
    notification_type?: NotificationType;
    severity?: NotificationSeverity;
  }): Promise<AxiosResponse<NotificationResponse[]>> => 
    apiClient.get('/api/notifications', { params }),
    
  getNotificationStats: (): Promise<AxiosResponse<NotificationStatsResponse>> => 
    apiClient.get('/api/notifications/stats'),
    
  markNotificationsAsRead: (request: NotificationMarkReadRequest): Promise<AxiosResponse<void>> => 
    apiClient.post('/api/notifications/mark-read', request),
    
  markAllNotificationsAsRead: (): Promise<AxiosResponse<void>> => 
    apiClient.post('/api/notifications/mark-all-read'),
    
  deleteNotification: (notificationId: string): Promise<AxiosResponse<void>> => 
    apiClient.delete(`/api/notifications/${notificationId}`),
    
  createNotification: (notificationData: NotificationCreate): Promise<AxiosResponse<NotificationResponse>> => 
    apiClient.post('/api/notifications', notificationData),
}; 