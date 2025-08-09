import { DocumentType, ProcessingStatus, DocumentFileMetadata } from '../types/api'; // Import enums and types

export interface MockDocument {
  document_id: string;
  user_id: string;
  original_filename: string;
  document_type: DocumentType; 
  upload_timestamp: string;
  processing_status: ProcessingStatus;
  storage_path: string;
  document_date?: string;
  source_name?: string;
  tags?: string[];
  file_metadata?: DocumentFileMetadata;
  file_hash?: string; 
  created_at: string; 
  updated_at: string; 
}

const MOCK_USER_ID = 'user_mock_uuid_12345';

export const mockDocuments: MockDocument[] = [
  {
    document_id: 'doc_1',
    user_id: MOCK_USER_ID,
    original_filename: 'Annual Checkup Results.pdf',
    document_type: DocumentType.LAB_RESULT,
    upload_timestamp: '2024-05-08T10:00:00Z',
    processing_status: ProcessingStatus.COMPLETED,
    storage_path: 'mock/storage/doc_1_annual_checkup.pdf',
    document_date: '2024-05-01',
    source_name: 'City Clinic Labs',
    tags: ['annual-checkup', 'bloodwork', 'cholesterol'],
    file_metadata: { filename: 'Annual Checkup Results.pdf', content_type: 'application/pdf', size: 123456 },
    created_at: '2024-05-08T09:59:00Z',
    updated_at: '2024-05-08T10:01:00Z',
  },
  {
    document_id: 'doc_2',
    user_id: MOCK_USER_ID,
    original_filename: 'Metformin Prescription.jpg',
    document_type: DocumentType.PRESCRIPTION,
    upload_timestamp: '2024-04-20T14:30:00Z',
    processing_status: ProcessingStatus.COMPLETED,
    storage_path: 'mock/storage/doc_2_metformin_prescription.jpg',
    document_date: '2024-04-18',
    source_name: 'Dr. Emily Carter',
    tags: ['diabetes', 'medication'],
    file_metadata: { filename: 'Metformin Prescription.jpg', content_type: 'image/jpeg', size: 78901 },
    created_at: '2024-04-20T14:29:00Z',
    updated_at: '2024-04-20T14:31:00Z',
  },
  {
    document_id: 'doc_3',
    user_id: MOCK_USER_ID,
    original_filename: 'X-Ray Report - Ankle.pdf',
    document_type: DocumentType.IMAGING_REPORT, // Changed from 'other' to a more specific enum if applicable or keep OTHER
    upload_timestamp: '2024-03-15T09:15:00Z',
    processing_status: ProcessingStatus.REVIEW_REQUIRED,
    storage_path: 'mock/storage/doc_3_xray_ankle.pdf',
    document_date: '2024-03-14',
    source_name: 'General Hospital Imaging',
    tags: ['x-ray', 'injury', 'ankle'],
    file_metadata: { filename: 'X-Ray Report - Ankle.pdf', content_type: 'application/pdf', size: 234567 },
    created_at: '2024-03-15T09:14:00Z',
    updated_at: '2024-03-15T09:16:00Z',
  },
  {
    document_id: 'doc_4',
    user_id: MOCK_USER_ID,
    original_filename: 'MRI_Brain_Scan_Images.zip',
    document_type: DocumentType.OTHER,
    upload_timestamp: '2024-05-10T11:00:00Z',
    processing_status: ProcessingStatus.PENDING, 
    storage_path: 'mock/storage/doc_4_mri_brain.zip',
    document_date: '2024-05-09',
    source_name: 'Neurology Associates',
    tags: ['mri', 'brain', 'neurology'],
    file_metadata: { filename: 'MRI_Brain_Scan_Images.zip', content_type: 'application/zip', size: 10241024 },
    created_at: '2024-05-10T10:59:00Z',
    updated_at: '2024-05-10T11:01:00Z',
  },
];


export const mockMedications = [];
export const mockHealthReadings = []; 