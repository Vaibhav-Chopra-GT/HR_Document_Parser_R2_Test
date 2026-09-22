// Candidate types
export interface ConfidenceScores {
  name: number | null;
  email: number | null;
  phone: number | null;
  company: number | null;
  designation: number | null;
  skills: number | null;
  overall: number | null;
}

export interface Candidate {
  id: string;
  name: string | null;
  email: string | null;
  phone: string | null;
  company: string | null;
  designation: string | null;
  skills: string[] | string | null;
  confidence_scores: ConfidenceScores;
  extraction_status: 'pending' | 'processing' | 'completed' | 'failed';
  extraction_error: string | null;
  document_status: 'pending' | 'requested' | 'partial' | 'completed';
  has_pan: boolean;
  has_aadhaar: boolean;
  pan_validated: boolean;
  aadhaar_validated: boolean;
  resume_original_name: string | null;
  created_at: string | null;
  updated_at: string | null;
  documents_requested_at: string | null;
  documents_submitted_at: string | null;
}

export interface CandidateListItem {
  id: string;
  name: string | null;
  email: string | null;
  company: string | null;
  extraction_status: string;
  document_status: string;
  overall_confidence: number | null;
  created_at: string | null;
}

export interface PaginationInfo {
  page: number;
  per_page: number;
  total: number;
  pages: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface CandidatesResponse {
  candidates: CandidateListItem[];
  pagination: PaginationInfo;
}

export interface CandidateResponse {
  candidate: Candidate;
}

export interface UploadResponse {
  id?: string;
  status?: string;
  candidate?: Candidate;
  error?: string;
  message: string;
  // Duplicate detection fields
  duplicate?: boolean;
  match_field?: 'email' | 'phone';
  existing_candidate?: CandidateListItem;
  extracted_data?: Record<string, any>;
  hint?: string;
}

export interface DocumentRequestResponse {
  success: boolean;
  message: string;
  email_sent: boolean;
  submission_link: string;
  subject: string;
  body: string;
}

export interface AuditLogEntry {
  id: number;
  action: string;
  actor: string;
  details: string | null;
  created_at: string;
}

// Portal types
export interface PortalValidation {
  valid: boolean;
  already_submitted: boolean;
  name: string;
  documents_submitted: {
    pan: boolean;
    aadhaar: boolean;
  };
  submitted_at: string | null;
}

export interface SubmitResult {
  uploaded: boolean;
  filename: string;
  validated?: boolean;
  holder_type?: string;
  masked?: string;
}

export interface SubmitResponse {
  success: boolean;
  results: {
    pan: SubmitResult | null;
    aadhaar: SubmitResult | null;
    errors: string[];
  };
  document_status: string;
  message: string;
}
