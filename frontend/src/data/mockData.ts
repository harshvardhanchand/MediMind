export interface MockDocument {
  document_id: string;
  original_filename: string;
  document_type: 'prescription' | 'lab_result' | 'other';
  upload_timestamp: string;
  processing_status: 'pending' | 'processing' | 'review_required' | 'completed' | 'failed';
  document_date?: string;
  source_name?: string;
  tags?: string[];
}

export const mockDocuments: MockDocument[] = [
  {
    document_id: 'doc_1',
    original_filename: 'Annual Checkup Results.pdf',
    document_type: 'lab_result',
    upload_timestamp: '2024-05-08T10:00:00Z',
    processing_status: 'completed',
    document_date: '2024-05-01',
    source_name: 'City Clinic Labs',
    tags: ['annual-checkup', 'bloodwork', 'cholesterol'],
  },
  {
    document_id: 'doc_2',
    original_filename: 'Metformin Prescription.jpg',
    document_type: 'prescription',
    upload_timestamp: '2024-04-20T14:30:00Z',
    processing_status: 'completed',
    document_date: '2024-04-18',
    source_name: 'Dr. Emily Carter',
    tags: ['diabetes', 'medication'],
  },
  {
    document_id: 'doc_3',
    original_filename: 'X-Ray Report - Ankle.pdf',
    document_type: 'other',
    upload_timestamp: '2024-03-15T09:15:00Z',
    processing_status: 'review_required',
    document_date: '2024-03-14',
    source_name: 'General Hospital Imaging',
    tags: ['x-ray', 'injury', 'ankle'],
  },
  {
    document_id: 'doc_4',
    original_filename: 'MRI_Brain_Scan_Images.zip',
    document_type: 'other',
    upload_timestamp: '2024-05-10T11:00:00Z',
    processing_status: 'processing',
    document_date: '2024-05-09',
    source_name: 'Neurology Associates',
    tags: ['mri', 'brain', 'neurology'],
  },
];

// Add more mock data for other screens later
export const mockMedications = [];
export const mockHealthReadings = []; 