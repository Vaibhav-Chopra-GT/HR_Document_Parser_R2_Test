import axios from 'axios';
import type {
  CandidatesResponse,
  CandidateResponse,
  UploadResponse,
  DocumentRequestResponse,
  AuditLogEntry,
  PortalValidation,
  SubmitResponse,
  AuthResponse,
  User,
} from '../types';

// Use proxy in development (vite.config.ts), direct URL in production
const API_BASE = import.meta.env.VITE_API_URL || '/api';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 errors (token expired)
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401 && error.response?.data?.code === 'token_expired') {
      // Try to refresh token
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const response = await axios.post(`${API_BASE}/auth/refresh`, {}, {
            headers: { Authorization: `Bearer ${refreshToken}` }
          });
          localStorage.setItem('access_token', response.data.access_token);
          // Retry original request
          error.config.headers.Authorization = `Bearer ${response.data.access_token}`;
          return api.request(error.config);
        } catch {
          // Refresh failed, clear tokens
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authApi = {
  signup: async (name: string, email: string, password: string, company?: string): Promise<AuthResponse> => {
    const response = await api.post('/auth/signup', { name, email, password, company });
    return response.data;
  },

  login: async (email: string, password: string): Promise<AuthResponse> => {
    const response = await api.post('/auth/login', { email, password });
    return response.data;
  },

  me: async (): Promise<{ user: User }> => {
    const response = await api.get('/auth/me');
    return response.data;
  },

  refresh: async (): Promise<{ access_token: string }> => {
    const refreshToken = localStorage.getItem('refresh_token');
    const response = await axios.post(`${API_BASE}/auth/refresh`, {}, {
      headers: { Authorization: `Bearer ${refreshToken}` }
    });
    return response.data;
  },
};

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

  // Download resume (authenticated)
  downloadResume: async (id: string, filename?: string): Promise<void> => {
    const response = await api.get(`/candidates/${id}/resume`, {
      responseType: 'blob',
    });

    // Get filename from Content-Disposition header or use provided filename
    const contentDisposition = response.headers['content-disposition'];
    let downloadFilename = filename || 'resume';
    if (contentDisposition) {
      const match = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
      if (match && match[1]) {
        downloadFilename = match[1].replace(/['"]/g, '');
      }
    }

    // Create blob with correct MIME type from response headers
    const contentType = response.headers['content-type'] || 'application/octet-stream';
    const blob = new Blob([response.data], { type: contentType });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = downloadFilename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  },

  // Download document (authenticated)
  downloadDocument: async (id: string, docType: 'pan' | 'aadhaar', filename?: string): Promise<void> => {
    const response = await api.get(`/candidates/${id}/documents/${docType}`, {
      responseType: 'blob',
    });

    // Get filename from Content-Disposition header or use provided filename
    const contentDisposition = response.headers['content-disposition'];
    let downloadFilename = filename || `${docType}_document`;
    if (contentDisposition) {
      const match = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
      if (match && match[1]) {
        downloadFilename = match[1].replace(/['"]/g, '');
      }
    }

    // Create blob with correct MIME type from response headers
    const contentType = response.headers['content-type'] || 'application/octet-stream';
    const blob = new Blob([response.data], { type: contentType });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = downloadFilename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  },
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
