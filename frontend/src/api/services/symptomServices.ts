/**
 * Symptom API Services
 * Frontend services for symptom tracking and management
 */

import { AxiosResponse } from 'axios';
import apiClient from '../client';

// Types for symptom data
export interface SymptomSeverity {
  MILD: 'mild';
  MODERATE: 'moderate';
  SEVERE: 'severe';
  CRITICAL: 'critical';
}

export interface SymptomCreate {
  symptom: string;
  severity: 'mild' | 'moderate' | 'severe' | 'critical';
  duration?: string;
  location?: string;
  notes?: string;
  reported_date?: string;
  related_medication_id?: string;
  related_document_id?: string;
}

export interface SymptomUpdate {
  symptom?: string;
  severity?: 'mild' | 'moderate' | 'severe' | 'critical';
  duration?: string;
  location?: string;
  notes?: string;
  reported_date?: string;
  related_medication_id?: string;
  related_document_id?: string;
}

export interface SymptomResponse {
  symptom_id: string;
  user_id: string;
  symptom: string;
  severity: 'mild' | 'moderate' | 'severe' | 'critical';
  duration?: string;
  location?: string;
  notes?: string;
  reported_date?: string;
  related_medication_id?: string;
  related_document_id?: string;
  created_at: string;
  updated_at: string;
}

export interface SymptomListResponse {
  symptoms: SymptomResponse[];
  total: number;
  skip: number;
  limit: number;
}

export interface SymptomStatsResponse {
  total_symptoms: number;
  recent_symptoms: number;
  severity_breakdown: {
    [key: string]: number;
  };
}

export interface SymptomSearchParams {
  skip?: number;
  limit?: number;
  severity?: 'mild' | 'moderate' | 'severe' | 'critical';
  start_date?: string;
  end_date?: string;
  search?: string;
}

export interface SymptomBulkCreateRequest {
  symptoms: SymptomCreate[];
}

export interface SymptomBulkCreateResponse {
  created_symptoms: SymptomResponse[];
  failed_symptoms: Array<{
    index: number;
    symptom_data: SymptomCreate;
    error: string;
  }>;
  total_created: number;
  total_failed: number;
}

class SymptomServices {
  private readonly baseUrl = '/symptoms';

  /**
   * Get symptoms for the current user
   */
  async getSymptoms(params?: SymptomSearchParams): Promise<AxiosResponse<SymptomListResponse>> {
    const searchParams = new URLSearchParams();
    
    if (params?.skip !== undefined) searchParams.append('skip', params.skip.toString());
    if (params?.limit !== undefined) searchParams.append('limit', params.limit.toString());
    if (params?.severity) searchParams.append('severity', params.severity);
    if (params?.start_date) searchParams.append('start_date', params.start_date);
    if (params?.end_date) searchParams.append('end_date', params.end_date);
    if (params?.search) searchParams.append('search', params.search);

    const url = `${this.baseUrl}${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;
    return apiClient.get<SymptomListResponse>(url);
  }

  /**
   * Create a new symptom
   */
  async createSymptom(symptom: SymptomCreate): Promise<AxiosResponse<SymptomResponse>> {
    return apiClient.post<SymptomResponse>(this.baseUrl, symptom);
  }

  /**
   * Get a specific symptom by ID
   */
  async getSymptom(symptomId: string): Promise<AxiosResponse<SymptomResponse>> {
    return apiClient.get<SymptomResponse>(`${this.baseUrl}/${symptomId}`);
  }

  /**
   * Update a symptom
   */
  async updateSymptom(symptomId: string, updates: SymptomUpdate): Promise<AxiosResponse<SymptomResponse>> {
    return apiClient.put<SymptomResponse>(`${this.baseUrl}/${symptomId}`, updates);
  }

  /**
   * Delete a symptom
   */
  async deleteSymptom(symptomId: string): Promise<AxiosResponse<void>> {
    return apiClient.delete<void>(`${this.baseUrl}/${symptomId}`);
  }

  /**
   * Get symptom statistics
   */
  async getSymptomStats(): Promise<AxiosResponse<SymptomStatsResponse>> {
    return apiClient.get<SymptomStatsResponse>(`${this.baseUrl}/stats/overview`);
  }

  /**
   * Get recent symptoms
   */
  async getRecentSymptoms(days: number = 30, limit: number = 50): Promise<AxiosResponse<SymptomResponse[]>> {
    return apiClient.get<SymptomResponse[]>(`${this.baseUrl}/recent/${days}?limit=${limit}`);
  }

  /**
   * Get symptoms by severity
   */
  async getSymptomsBySeverity(
    severity: 'mild' | 'moderate' | 'severe' | 'critical',
    limit: number = 50
  ): Promise<AxiosResponse<SymptomResponse[]>> {
    return apiClient.get<SymptomResponse[]>(`${this.baseUrl}/by-severity/${severity}?limit=${limit}`);
  }

  /**
   * Get symptom patterns for a specific symptom name
   */
  async getSymptomPatterns(symptomName: string, limit: number = 20): Promise<AxiosResponse<SymptomResponse[]>> {
    return apiClient.get<SymptomResponse[]>(`${this.baseUrl}/patterns/${encodeURIComponent(symptomName)}?limit=${limit}`);
  }

  /**
   * Create multiple symptoms at once
   */
  async createSymptomsBulk(request: SymptomBulkCreateRequest): Promise<AxiosResponse<SymptomBulkCreateResponse>> {
    return apiClient.post<SymptomBulkCreateResponse>(`${this.baseUrl}/bulk`, request);
  }

  /**
   * Search symptoms with advanced filters
   */
  async searchSymptoms(
    query: string,
    filters?: {
      severity?: 'mild' | 'moderate' | 'severe' | 'critical';
      start_date?: string;
      end_date?: string;
      skip?: number;
      limit?: number;
    }
  ): Promise<AxiosResponse<SymptomListResponse>> {
    const params: SymptomSearchParams = {
      search: query,
      ...filters
    };
    return this.getSymptoms(params);
  }

  /**
   * Get symptoms for a specific date range
   */
  async getSymptomsInDateRange(
    startDate: string,
    endDate: string,
    limit: number = 100
  ): Promise<AxiosResponse<SymptomListResponse>> {
    return this.getSymptoms({
      start_date: startDate,
      end_date: endDate,
      limit
    });
  }

  /**
   * Get today's symptoms
   */
  async getTodaysSymptoms(): Promise<AxiosResponse<SymptomResponse[]>> {
    const today = new Date().toISOString().split('T')[0];
    return this.getRecentSymptoms(1);
  }

  /**
   * Get this week's symptoms
   */
  async getWeeklySymptoms(): Promise<AxiosResponse<SymptomResponse[]>> {
    return this.getRecentSymptoms(7);
  }

  /**
   * Get this month's symptoms
   */
  async getMonthlySymptoms(): Promise<AxiosResponse<SymptomResponse[]>> {
    return this.getRecentSymptoms(30);
  }

  /**
   * Helper method to format symptom data for display
   */
  formatSymptomForDisplay(symptom: SymptomResponse): {
    id: string;
    name: string;
    severity: string;
    severityLevel: number;
    date: string;
    time: string;
    duration?: string;
    location?: string;
    notes?: string;
    color: string;
  } {
    const date = new Date(symptom.reported_date || symptom.created_at);
    
    // Map severity to display values
    const severityMap = {
      mild: { level: 1, color: '#10B981' },      // Green
      moderate: { level: 2, color: '#F59E0B' },  // Yellow
      severe: { level: 3, color: '#EF4444' },    // Red
      critical: { level: 4, color: '#DC2626' }   // Dark Red
    };

    const severityInfo = severityMap[symptom.severity] || severityMap.mild;

    return {
      id: symptom.symptom_id,
      name: symptom.symptom,
      severity: symptom.severity.charAt(0).toUpperCase() + symptom.severity.slice(1),
      severityLevel: severityInfo.level,
      date: date.toLocaleDateString(),
      time: date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      duration: symptom.duration,
      location: symptom.location,
      notes: symptom.notes,
      color: severityInfo.color
    };
  }

  /**
   * Helper method to validate symptom data before submission
   */
  validateSymptomData(symptom: SymptomCreate): { isValid: boolean; errors: string[] } {
    const errors: string[] = [];

    if (!symptom.symptom || symptom.symptom.trim().length === 0) {
      errors.push('Symptom description is required');
    }

    if (symptom.symptom && symptom.symptom.length > 200) {
      errors.push('Symptom description must be less than 200 characters');
    }

    if (!symptom.severity) {
      errors.push('Severity level is required');
    }

    if (symptom.severity && !['mild', 'moderate', 'severe', 'critical'].includes(symptom.severity)) {
      errors.push('Invalid severity level');
    }

    if (symptom.duration && symptom.duration.length > 100) {
      errors.push('Duration must be less than 100 characters');
    }

    if (symptom.location && symptom.location.length > 100) {
      errors.push('Location must be less than 100 characters');
    }

    if (symptom.notes && symptom.notes.length > 1000) {
      errors.push('Notes must be less than 1000 characters');
    }

    return {
      isValid: errors.length === 0,
      errors
    };
  }
}

// Export singleton instance
export const symptomServices = new SymptomServices(); 