import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { format } from 'date-fns';
import {
  ArrowLeft,
  Mail,
  Phone,
  Building,
  Briefcase,
  FileText,
  Send,
  Download,
  RefreshCw,
  CheckCircle,
  XCircle,
  Trash2,
  Edit3,
  Save,
  X,
  ChevronDown,
  ChevronUp,
  AlertTriangle,
} from 'lucide-react';
import ConfidenceBar from '../components/ConfidenceBar';
import { candidatesApi } from '../api/client';
import type { Candidate, AuditLogEntry } from '../types';
import toast from 'react-hot-toast';

export default function CandidateDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [candidate, setCandidate] = useState<Candidate | null>(null);
  const [auditLogs, setAuditLogs] = useState<AuditLogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [requesting, setRequesting] = useState(false);
  const [reprocessing, setReprocessing] = useState(false);
  const [showEmailPreview, setShowEmailPreview] = useState(false);
  const [emailContent, setEmailContent] = useState<{ subject: string; body: string } | null>(null);

  // Edit mode state
  const [isEditing, setIsEditing] = useState(false);
  const [editData, setEditData] = useState({
    name: '',
    email: '',
    phone: '',
    company: '',
    designation: '',
    skills: [] as string[],
  });
  const [saving, setSaving] = useState(false);
  const [newSkill, setNewSkill] = useState('');

  // Confirmation modal state
  const [showConfirmModal, setShowConfirmModal] = useState(false);

  // Skills display state
  const [showAllSkills, setShowAllSkills] = useState(false);
  const SKILLS_PREVIEW_COUNT = 6;

  const fetchCandidate = async () => {
    if (!id) return;

    try {
      const [candidateRes, logsRes] = await Promise.all([
        candidatesApi.get(id),
        candidatesApi.getAuditLog(id),
      ]);

      setCandidate(candidateRes.candidate);
      setAuditLogs(logsRes.logs);

      // Initialize edit data
      const c = candidateRes.candidate;
      const skills = typeof c.skills === 'string'
        ? JSON.parse(c.skills || '[]')
        : c.skills || [];
      setEditData({
        name: c.name || '',
        email: c.email || '',
        phone: c.phone || '',
        company: c.company || '',
        designation: c.designation || '',
        skills: skills,
      });
    } catch (error) {
      toast.error('Failed to load candidate');
      navigate('/');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCandidate();
  }, [id]);

  const handleRequestDocuments = async () => {
    if (!candidate?.email) {
      toast.error('No email address available');
      return;
    }

    // Show confirmation modal if documents already submitted
    if (candidate.has_pan || candidate.has_aadhaar) {
      setShowConfirmModal(true);
      return;
    }

    await sendDocumentRequest();
  };

  const sendDocumentRequest = async () => {
    if (!candidate) return;

    setShowConfirmModal(false);
    setRequesting(true);
    try {
      const result = await candidatesApi.requestDocuments(candidate.id);
      toast.success(result.message);
      setEmailContent({ subject: result.subject, body: result.body });
      setShowEmailPreview(true);
      fetchCandidate();
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Failed to send request');
    } finally {
      setRequesting(false);
    }
  };

  const handleReprocess = async () => {
    if (!candidate) return;

    setReprocessing(true);
    try {
      const result = await candidatesApi.reprocess(candidate.id);
      if (result.status === 'completed') {
        toast.success('Resume reprocessed successfully');
        fetchCandidate();
      } else {
        toast.error(result.error || 'Reprocessing failed');
      }
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Reprocessing failed');
    } finally {
      setReprocessing(false);
    }
  };

  const handleDelete = async () => {
    if (!candidate) return;

    if (!confirm('Are you sure you want to delete this candidate?')) return;

    try {
      await candidatesApi.delete(candidate.id);
      toast.success('Candidate deleted');
      navigate('/');
    } catch (error) {
      toast.error('Failed to delete candidate');
    }
  };

  const handleStartEdit = () => {
    if (!candidate) return;
    const skills = typeof candidate.skills === 'string'
      ? JSON.parse(candidate.skills || '[]')
      : candidate.skills || [];
    setEditData({
      name: candidate.name || '',
      email: candidate.email || '',
      phone: candidate.phone || '',
      company: candidate.company || '',
      designation: candidate.designation || '',
      skills: skills,
    });
    setIsEditing(true);
  };

  const handleCancelEdit = () => {
    setIsEditing(false);
    setNewSkill('');
  };

  const handleSaveEdit = async () => {
    if (!candidate) return;

    setSaving(true);
    try {
      const result = await candidatesApi.update(candidate.id, editData);
      toast.success(result.message);
      setIsEditing(false);
      fetchCandidate();
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Failed to save changes');
    } finally {
      setSaving(false);
    }
  };

  const handleAddSkill = () => {
    if (newSkill.trim() && !editData.skills.includes(newSkill.trim())) {
      setEditData({
        ...editData,
        skills: [...editData.skills, newSkill.trim()]
      });
      setNewSkill('');
    }
  };

  const handleRemoveSkill = (skillToRemove: string) => {
    setEditData({
      ...editData,
      skills: editData.skills.filter(s => s !== skillToRemove)
    });
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  if (!candidate) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8 text-center">
        <p className="text-gray-500">Candidate not found</p>
      </div>
    );
  }

  const skills = typeof candidate.skills === 'string'
    ? JSON.parse(candidate.skills || '[]')
    : candidate.skills || [];

  const displayedSkills = showAllSkills ? skills : skills.slice(0, SKILLS_PREVIEW_COUNT);
  const hasMoreSkills = skills.length > SKILLS_PREVIEW_COUNT;

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <button
          onClick={() => navigate('/')}
          className="p-2 hover:bg-gray-100 rounded-lg"
        >
          <ArrowLeft className="h-5 w-5" />
        </button>
        <div className="flex-1">
          <h1 className="text-2xl font-bold text-gray-900">
            {candidate.name || 'Unknown Candidate'}
          </h1>
          <p className="text-gray-500">
            {candidate.designation} {candidate.company && `at ${candidate.company}`}
          </p>
        </div>
        <button
          onClick={handleDelete}
          className="p-2 text-red-500 hover:bg-red-50 rounded-lg"
          title="Delete candidate"
        >
          <Trash2 className="h-5 w-5" />
        </button>
      </div>

      {/* Status Badges */}
      <div className="flex gap-2 mb-6">
        <span className={`px-3 py-1 rounded-full text-sm font-medium ${
          candidate.extraction_status === 'completed'
            ? 'bg-green-100 text-green-800'
            : candidate.extraction_status === 'failed'
            ? 'bg-red-100 text-red-800'
            : 'bg-yellow-100 text-yellow-800'
        }`}>
          Extraction: {candidate.extraction_status}
        </span>
        <span className={`px-3 py-1 rounded-full text-sm font-medium ${
          candidate.document_status === 'completed'
            ? 'bg-green-100 text-green-800'
            : candidate.document_status === 'partial'
            ? 'bg-yellow-100 text-yellow-800'
            : 'bg-gray-100 text-gray-800'
        }`}>
          Documents: {candidate.document_status}
        </span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Extracted Information */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">Extracted Information</h2>
            {!isEditing ? (
              <button
                onClick={handleStartEdit}
                className="flex items-center gap-1 px-3 py-1.5 text-sm text-blue-600 hover:bg-blue-50 rounded-lg"
              >
                <Edit3 className="h-4 w-4" />
                Edit
              </button>
            ) : (
              <div className="flex gap-2">
                <button
                  onClick={handleCancelEdit}
                  disabled={saving}
                  className="flex items-center gap-1 px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-100 rounded-lg"
                >
                  <X className="h-4 w-4" />
                  Cancel
                </button>
                <button
                  onClick={handleSaveEdit}
                  disabled={saving}
                  className="flex items-center gap-1 px-3 py-1.5 text-sm text-white bg-blue-600 hover:bg-blue-700 rounded-lg"
                >
                  <Save className="h-4 w-4" />
                  {saving ? 'Saving...' : 'Save'}
                </button>
              </div>
            )}
          </div>

          {candidate.extraction_status === 'failed' && (
            <div className="mb-4 p-4 bg-red-50 rounded-lg">
              <p className="text-red-700 text-sm">{candidate.extraction_error}</p>
              <button
                onClick={handleReprocess}
                disabled={reprocessing}
                className="mt-2 text-sm text-red-600 hover:text-red-800 flex items-center gap-1"
              >
                <RefreshCw className={`h-4 w-4 ${reprocessing ? 'animate-spin' : ''}`} />
                {reprocessing ? 'Reprocessing...' : 'Retry Extraction'}
              </button>
            </div>
          )}

          <div className="space-y-4">
            {/* Email Field */}
            <div className="flex items-start gap-3">
              <Mail className="h-5 w-5 text-gray-400 mt-0.5" />
              <div className="flex-1">
                <p className="text-sm text-gray-500">Email</p>
                {isEditing ? (
                  <input
                    type="email"
                    value={editData.email}
                    onChange={(e) => setEditData({...editData, email: e.target.value})}
                    className="w-full px-2 py-1 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                ) : (
                  <p className="font-medium">{candidate.email || 'Not found'}</p>
                )}
                {!isEditing && <ConfidenceBar score={candidate.confidence_scores.email} label="" showLabel={false} />}
              </div>
            </div>

            {/* Phone Field */}
            <div className="flex items-start gap-3">
              <Phone className="h-5 w-5 text-gray-400 mt-0.5" />
              <div className="flex-1">
                <p className="text-sm text-gray-500">Phone</p>
                {isEditing ? (
                  <input
                    type="tel"
                    value={editData.phone}
                    onChange={(e) => setEditData({...editData, phone: e.target.value})}
                    className="w-full px-2 py-1 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                ) : (
                  <p className="font-medium">{candidate.phone || 'Not found'}</p>
                )}
                {!isEditing && <ConfidenceBar score={candidate.confidence_scores.phone} label="" showLabel={false} />}
              </div>
            </div>

            {/* Company Field */}
            <div className="flex items-start gap-3">
              <Building className="h-5 w-5 text-gray-400 mt-0.5" />
              <div className="flex-1">
                <p className="text-sm text-gray-500">Company</p>
                {isEditing ? (
                  <input
                    type="text"
                    value={editData.company}
                    onChange={(e) => setEditData({...editData, company: e.target.value})}
                    className="w-full px-2 py-1 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                ) : (
                  <p className="font-medium">{candidate.company || 'Not found'}</p>
                )}
                {!isEditing && <ConfidenceBar score={candidate.confidence_scores.company} label="" showLabel={false} />}
              </div>
            </div>

            {/* Designation Field */}
            <div className="flex items-start gap-3">
              <Briefcase className="h-5 w-5 text-gray-400 mt-0.5" />
              <div className="flex-1">
                <p className="text-sm text-gray-500">Designation</p>
                {isEditing ? (
                  <input
                    type="text"
                    value={editData.designation}
                    onChange={(e) => setEditData({...editData, designation: e.target.value})}
                    className="w-full px-2 py-1 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                ) : (
                  <p className="font-medium">{candidate.designation || 'Not found'}</p>
                )}
                {!isEditing && <ConfidenceBar score={candidate.confidence_scores.designation} label="" showLabel={false} />}
              </div>
            </div>

            {/* Skills Field */}
            <div>
              <p className="text-sm text-gray-500 mb-2">Skills</p>
              {isEditing ? (
                <div>
                  <div className="flex flex-wrap gap-2 mb-2">
                    {editData.skills.map((skill, i) => (
                      <span
                        key={i}
                        className="inline-flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-800 rounded text-sm"
                      >
                        {skill}
                        <button
                          onClick={() => handleRemoveSkill(skill)}
                          className="hover:text-blue-600"
                        >
                          <X className="h-3 w-3" />
                        </button>
                      </span>
                    ))}
                  </div>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={newSkill}
                      onChange={(e) => setNewSkill(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && handleAddSkill()}
                      placeholder="Add skill..."
                      className="flex-1 px-2 py-1 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                    <button
                      onClick={handleAddSkill}
                      className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
                    >
                      Add
                    </button>
                  </div>
                </div>
              ) : (
                <>
                  <div className="flex flex-wrap gap-2">
                    {displayedSkills.length > 0 ? (
                      displayedSkills.map((skill: string, i: number) => (
                        <span
                          key={i}
                          className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-sm"
                        >
                          {skill}
                        </span>
                      ))
                    ) : (
                      <span className="text-gray-400">No skills extracted</span>
                    )}
                  </div>
                  {hasMoreSkills && (
                    <button
                      onClick={() => setShowAllSkills(!showAllSkills)}
                      className="mt-2 flex items-center gap-1 text-sm text-blue-600 hover:text-blue-800"
                    >
                      {showAllSkills ? (
                        <>
                          <ChevronUp className="h-4 w-4" />
                          Show less
                        </>
                      ) : (
                        <>
                          <ChevronDown className="h-4 w-4" />
                          Show {skills.length - SKILLS_PREVIEW_COUNT} more skills
                        </>
                      )}
                    </button>
                  )}
                  <div className="mt-2">
                    <ConfidenceBar score={candidate.confidence_scores.skills} label="" showLabel={false} />
                  </div>
                </>
              )}
            </div>
          </div>

          {/* Overall Confidence */}
          {!isEditing && (
            <div className="mt-6 pt-4 border-t">
              <div className="flex justify-between items-center">
                <span className="font-medium">Overall Confidence</span>
                <span className={`text-lg font-bold ${
                  (candidate.confidence_scores.overall || 0) >= 0.8
                    ? 'text-green-600'
                    : (candidate.confidence_scores.overall || 0) >= 0.6
                    ? 'text-yellow-600'
                    : 'text-red-600'
                }`}>
                  {Math.round((candidate.confidence_scores.overall || 0) * 100)}%
                </span>
              </div>
              {(candidate.confidence_scores.overall || 0) < 0.7 && (
                <p className="text-sm text-amber-600 mt-2">
                  ⚠️ Low confidence - consider reviewing and editing the extracted data
                </p>
              )}
            </div>
          )}
        </div>

        {/* Documents & Actions */}
        <div className="space-y-6">
          {/* Document Request */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">Document Request</h2>

            <button
              onClick={handleRequestDocuments}
              disabled={requesting || !candidate.email}
              className={`w-full flex items-center justify-center gap-2 py-3 px-4 rounded-lg font-medium text-white transition-colors ${
                requesting || !candidate.email
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-700'
              }`}
            >
              <Send className="h-5 w-5" />
              {requesting ? 'Sending...' : 'Request PAN & Aadhaar'}
            </button>

            {!candidate.email && (
              <p className="mt-2 text-sm text-red-500">
                No email address available
              </p>
            )}

            {candidate.documents_requested_at && (
              <p className="mt-2 text-sm text-gray-500">
                Last requested: {format(new Date(candidate.documents_requested_at), 'MMM d, yyyy h:mm a')}
              </p>
            )}
          </div>

          {/* Submitted Documents */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">Submitted Documents</h2>

            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  {candidate.has_pan ? (
                    <CheckCircle className="h-5 w-5 text-green-500" />
                  ) : (
                    <XCircle className="h-5 w-5 text-gray-300" />
                  )}
                  <div>
                    <p className="font-medium">PAN Card</p>
                    <p className="text-sm text-gray-500">
                      {candidate.has_pan
                        ? 'Submitted'
                        : 'Not submitted'}
                    </p>
                  </div>
                </div>
                {candidate.has_pan && (
                  <a
                    href={candidatesApi.getDocumentUrl(candidate.id, 'pan')}
                    download
                    className="text-blue-600 hover:text-blue-800"
                  >
                    <Download className="h-5 w-5" />
                  </a>
                )}
              </div>

              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  {candidate.has_aadhaar ? (
                    <CheckCircle className="h-5 w-5 text-green-500" />
                  ) : (
                    <XCircle className="h-5 w-5 text-gray-300" />
                  )}
                  <div>
                    <p className="font-medium">Aadhaar Card</p>
                    <p className="text-sm text-gray-500">
                      {candidate.has_aadhaar
                        ? 'Submitted'
                        : 'Not submitted'}
                    </p>
                  </div>
                </div>
                {candidate.has_aadhaar && (
                  <a
                    href={candidatesApi.getDocumentUrl(candidate.id, 'aadhaar')}
                    download
                    className="text-blue-600 hover:text-blue-800"
                  >
                    <Download className="h-5 w-5" />
                  </a>
                )}
              </div>
            </div>

            {candidate.documents_submitted_at && (
              <p className="mt-4 text-sm text-gray-500">
                Submitted: {format(new Date(candidate.documents_submitted_at), 'MMM d, yyyy h:mm a')}
              </p>
            )}
          </div>

          {/* Resume Download */}
          {candidate.resume_original_name && (
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold mb-4">Resume</h2>
              <a
                href={candidatesApi.getResumeUrl(candidate.id)}
                download
                className="flex items-center gap-3 p-4 bg-gray-50 rounded-lg hover:bg-gray-100"
              >
                <FileText className="h-8 w-8 text-blue-500" />
                <div className="flex-1">
                  <p className="font-medium">{candidate.resume_original_name}</p>
                  <p className="text-sm text-gray-500">Click to download</p>
                </div>
                <Download className="h-5 w-5 text-gray-400" />
              </a>
            </div>
          )}
        </div>
      </div>

      {/* Audit Log */}
      <div className="mt-6 bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold mb-4">Activity Log</h2>
        <div className="space-y-3">
          {auditLogs.map((log) => (
            <div key={log.id} className="flex items-start gap-3 text-sm">
              <div className="w-2 h-2 mt-2 rounded-full bg-blue-500"></div>
              <div className="flex-1">
                <p className="text-gray-900">
                  <span className="font-medium">{log.action.replace(/_/g, ' ')}</span>
                  <span className="text-gray-500"> by {log.actor}</span>
                </p>
                <p className="text-gray-400 text-xs">
                  {format(new Date(log.created_at), 'MMM d, yyyy h:mm a')}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Confirmation Modal */}
      {showConfirmModal && (
        <div className="fixed inset-0 bg-black/30 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
            <div className="p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 bg-amber-100 rounded-full">
                  <AlertTriangle className="h-6 w-6 text-amber-600" />
                </div>
                <h3 className="text-lg font-semibold">Documents Already Submitted</h3>
              </div>

              <p className="text-gray-600 mb-4">
                This candidate has already submitted their documents. Sending a new request will:
              </p>

              <ul className="text-sm text-gray-600 mb-6 space-y-2">
                <li className="flex items-start gap-2">
                  <span className="text-amber-500 mt-0.5">•</span>
                  Generate a new submission link
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-amber-500 mt-0.5">•</span>
                  Invalidate the previous link
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-amber-500 mt-0.5">•</span>
                  Allow them to replace existing documents
                </li>
              </ul>

              <div className="flex gap-3">
                <button
                  onClick={() => setShowConfirmModal(false)}
                  className="flex-1 py-2 px-4 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  onClick={sendDocumentRequest}
                  className="flex-1 py-2 px-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Send Request
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Email Preview Modal */}
      {showEmailPreview && emailContent && (
        <div className="fixed inset-0 bg-black/30 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[80vh] overflow-auto">
            <div className="p-6">
              <h3 className="text-lg font-semibold mb-4">Email Sent</h3>
              <div className="mb-4">
                <p className="text-sm text-gray-500">Subject:</p>
                <p className="font-medium">{emailContent.subject}</p>
              </div>
              <div className="mb-4">
                <p className="text-sm text-gray-500">Body:</p>
                <pre className="whitespace-pre-wrap text-sm bg-gray-50 p-4 rounded-lg">
                  {emailContent.body}
                </pre>
              </div>
              <button
                onClick={() => setShowEmailPreview(false)}
                className="w-full py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
