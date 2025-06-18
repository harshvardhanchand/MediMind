// Standardized messages for consistent UX across the app

export const ERROR_MESSAGES = {
  // Network & API errors
  NETWORK_ERROR: 'Unable to connect to the server. Please check your internet connection and try again.',
  API_ERROR: 'We encountered an error while loading your data. Please try again.',
  TIMEOUT_ERROR: 'The request took too long to complete. Please try again.',
  UNAUTHORIZED: 'Your session has expired. Please log in again.',
  
  // Data loading errors
  DOCUMENTS_LOAD_ERROR: 'Unable to load your documents. Please try again.',
  MEDICATIONS_LOAD_ERROR: 'Unable to load your medications. Please try again.',
  NOTIFICATIONS_LOAD_ERROR: 'Unable to load your notifications. Please try again.',
  PROFILE_LOAD_ERROR: 'Unable to load your profile information. Please try again.',
  
  // Form validation errors
  REQUIRED_FIELD: 'This field is required.',
  INVALID_EMAIL: 'Please enter a valid email address.',
  INVALID_PASSWORD: 'Password must be at least 8 characters long.',
  PASSWORDS_DONT_MATCH: 'Passwords do not match.',
  INVALID_DATE: 'Please enter a valid date.',
  INVALID_PHONE: 'Please enter a valid phone number.',
  FORM_VALIDATION_ERROR: 'Please correct the errors in the form.',
  
  // Save/Update errors
  MEDICATION_SAVE_ERROR: 'Failed to save medication. Please try again.',
  HEALTH_READING_SAVE_ERROR: 'Failed to save health reading. Please try again.',
  SYMPTOM_SAVE_ERROR: 'Failed to save symptom. Please try again.',
  
  // Upload errors
  UPLOAD_ERROR: 'Failed to upload file. Please try again.',
  FILE_TOO_LARGE: 'File size is too large. Please choose a smaller file.',
  INVALID_FILE_TYPE: 'Invalid file type. Please choose a PDF, JPG, or PNG file.',
  
  // Authentication errors
  LOGIN_ERROR: 'Invalid email or password. Please try again.',
  SIGNUP_ERROR: 'Unable to create account. Please try again.',
  LOGOUT_ERROR: 'Unable to sign out. Please try again.',
  
  // Generic fallback
  GENERIC_ERROR: 'Something went wrong. Please try again.',
} as const;

export const EMPTY_STATE_MESSAGES = {
  // Documents
  NO_DOCUMENTS: {
    title: 'No Documents Yet',
    description: 'Upload your first medical document to get started with AI-powered health insights.',
    actionLabel: 'Upload Document'
  },
  
  // Medications
  NO_MEDICATIONS: {
    title: 'No Medications Added',
    description: 'Add your medications to track dosages, set reminders, and monitor interactions.',
    actionLabel: 'Add Medication'
  },
  
  // Notifications
  NO_NOTIFICATIONS: {
    title: 'All Caught Up!',
    description: 'You have no new notifications. We\'ll notify you of important health insights and reminders.',
    actionLabel: undefined
  },
  
  // Health readings
  NO_HEALTH_READINGS: {
    title: 'No Health Data Yet',
    description: 'Start tracking your vital signs and health metrics to monitor your wellness journey.',
    actionLabel: 'Add Reading'
  },
  
  // Search results
  NO_SEARCH_RESULTS: {
    title: 'No Results Found',
    description: 'Try adjusting your search terms or filters to find what you\'re looking for.',
    actionLabel: 'Clear Filters'
  },
  
  // Filtered results
  NO_FILTERED_RESULTS: {
    title: 'No Items Match Your Filters',
    description: 'Try adjusting your filters to see more results.',
    actionLabel: 'Clear Filters'
  },
  
  // Generic empty state
  GENERIC_EMPTY: {
    title: 'Nothing Here Yet',
    description: 'This section will populate as you add more data to your health profile.',
    actionLabel: undefined
  }
} as const;

export const SUCCESS_MESSAGES = {
  // Profile & Account
  PROFILE_UPDATED: 'Profile updated successfully!',
  PASSWORD_CHANGED: 'Password changed successfully!',
  ACCOUNT_CREATED: 'Account created successfully! Welcome to MediMind.',
  
  // Documents
  DOCUMENT_UPLOADED: 'Document uploaded successfully!',
  DOCUMENT_DELETED: 'Document deleted successfully.',
  
  // Medications
  MEDICATION_ADDED: 'Medication added successfully!',
  MEDICATION_UPDATED: 'Medication updated successfully!',
  MEDICATION_DELETED: 'Medication removed successfully.',
  
  // Health readings
  READING_ADDED: 'Health reading added successfully!',
  READING_UPDATED: 'Health reading updated successfully!',
  
  // Notifications
  NOTIFICATION_MARKED_READ: 'Notification marked as read.',
  ALL_NOTIFICATIONS_READ: 'All notifications marked as read.',
  
  // Generic success
  CHANGES_SAVED: 'Changes saved successfully!',
} as const;

export const LOADING_MESSAGES = {
  LOADING_DOCUMENTS: 'Loading your documents...',
  LOADING_MEDICATIONS: 'Loading your medications...',
  LOADING_NOTIFICATIONS: 'Loading notifications...',
  LOADING_PROFILE: 'Loading profile...',
  UPLOADING_DOCUMENT: 'Uploading document...',
  SAVING_CHANGES: 'Saving changes...',
  PROCESSING: 'Processing...',
  GENERIC_LOADING: 'Loading...',
} as const; 