import axios from 'axios';
import type {
  CandidatesResponse,
  CandidateResponse,
  UploadResponse,
  DocumentRequestResponse,
  AuditLogEntry,
  PortalValidation,
  SubmitResponse,
} from '../types';

// Use proxy in development (vite.config.ts), direct URL in production
const API_BASE = import.meta.env.VITE_API_URL || '/api';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Candidates API
export const candidatesApi = {
  // List candidates with optional filters
  list: async (params?: {
    page?: number;
    per_page?: number;
    status?: string;
    doc_status?: string;
    search?: string;
  }): Promise<CandidatesResponse> => {
    const response = await api.get('/candidates', { params });
    return response.data;
  },

  // Get single candidate
  get: async (id: string): Promise<CandidateResponse> => {
    const response = await api.get(`/candidates/${id}`);
    return response.data;
  },

  // Upload resume
  upload: async (
    file: File,
    onProgress?: (progress: number) => void,
    force?: boolean
  ): Promise<UploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    if (force) {
      formData.append('force', 'true');
    }

    const response = await api.post('/candidates/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      validateStatus: (status) => status < 500, // Don't throw on 409
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total && onProgress) {
          const progress = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          onProgress(progress);
        }
      },
    });
    return response.data;
  },

  // Request documents
  requestDocuments: async (id: string): Promise<DocumentRequestResponse> => {
    const response = await api.post(`/candidates/${id}/request-documents`);
    return response.data;
  },

  // Get audit log
  getAuditLog: async (id: string, limit = 50): Promise<{ logs: AuditLogEntry[] }> => {
    const response = await api.get(`/candidates/${id}/audit-log`, {
      params: { limit },
    });
    return response.data;
  },

  // Reprocess resume
  reprocess: async (id: string): Promise<{ status: string; candidate?: any; error?: string }> => {
    const response = await api.post(`/candidates/${id}/reprocess`);
    return response.data;
  },

  // Update candidate (manual edit)
  update: async (id: string, data: {
    name?: string;
    email?: string;
    phone?: string;
    company?: string;
    designation?: string;
    skills?: string[];
  }): Promise<{ success: boolean; message: string; candidate: any }> => {
    const response = await api.put(`/candidates/${id}`, data);
    return response.data;
  },

  // Delete candidate
  delete: async (id: string): Promise<{ success: boolean; message: string }> => {
    const response = await api.delete(`/candidates/${id}`);
    return response.data;
  },

  // Get resume download URL
  getResumeUrl: (id: string): string => `${API_BASE}/candidates/${id}/resume`,

  // Get document download URL
  getDocumentUrl: (id: string, docType: 'pan' | 'aadhaar'): string =>
    `${API_BASE}/candidates/${id}/documents/${docType}`,
};

// Portal API (for candidates)
export const portalApi = {
  // Validate token
  validate: async (token: string): Promise<PortalValidation> => {
    const response = await api.get(`/portal/${token}`);
    return response.data;
  },

  // Submit documents
  submit: async (
    token: string,
    files: { pan?: File; aadhaar?: File },
    numbers?: { pan_number?: string; aadhaar_number?: string },
    onProgress?: (progress: number) => void
  ): Promise<SubmitResponse> => {
    const formData = new FormData();

    if (files.pan) {
      formData.append('pan', files.pan);
    }
    if (files.aadhaar) {
      formData.append('aadhaar', files.aadhaar);
    }
    if (numbers?.pan_number) {
      formData.append('pan_number', numbers.pan_number);
    }
    if (numbers?.aadhaar_number) {
      formData.append('aadhaar_number', numbers.aadhaar_number);
    }

    const response = await api.post(`/portal/${token}/submit`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total && onProgress) {
          const progress = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          onProgress(progress);
        }
      },
    });
    return response.data;
  },

  // Get submission status
  getStatus: async (token: string) => {
    const response = await api.get(`/portal/${token}/status`);
    return response.data;
  },
};

export default api;
