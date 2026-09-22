import { useState, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { useDropzone } from 'react-dropzone';
import {
  Upload,
  FileText,
  CheckCircle,
  XCircle,
  AlertCircle,
  Shield,
  X,
} from 'lucide-react';
import { portalApi } from '../api/client';
import toast from 'react-hot-toast';

export default function SubmitDocuments() {
  const { token } = useParams<{ token: string }>();

  const [validating, setValidating] = useState(true);
  const [valid, setValid] = useState(false);
  const [alreadySubmitted, setAlreadySubmitted] = useState(false);
  const [submittedAt, setSubmittedAt] = useState<string | null>(null);
  const [candidateName, setCandidateName] = useState('');
  const [existingDocs, setExistingDocs] = useState({ pan: false, aadhaar: false });
  const [hrEmail, setHrEmail] = useState<string | null>(null);

  const [panFile, setPanFile] = useState<File | null>(null);
  const [aadhaarFile, setAadhaarFile] = useState<File | null>(null);

  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [errors, setErrors] = useState<string[]>([]);

  useEffect(() => {
    const validateToken = async () => {
      if (!token) {
        setValid(false);
        setValidating(false);
        return;
      }

      try {
        const result = await portalApi.validate(token);
        setValid(result.valid);
        setCandidateName(result.name);
        setExistingDocs(result.documents_submitted);
        setAlreadySubmitted(result.already_submitted || false);
        setSubmittedAt(result.submitted_at || null);
        setHrEmail(result.hr_email || null);
      } catch (error: any) {
        setValid(false);
        if (error.response?.status === 410) {
          toast.error('This link has expired');
        }
      } finally {
        setValidating(false);
      }
    };

    validateToken();
  }, [token]);

  const onDropPan = useCallback((files: File[]) => {
    if (files.length > 0) setPanFile(files[0]);
  }, []);

  const onDropAadhaar = useCallback((files: File[]) => {
    if (files.length > 0) setAadhaarFile(files[0]);
  }, []);

  const panDropzone = useDropzone({
    onDrop: onDropPan,
    accept: {
      'image/*': ['.png', '.jpg', '.jpeg'],
      'application/pdf': ['.pdf'],
    },
    maxFiles: 1,
    maxSize: 5 * 1024 * 1024,
  });

  const aadhaarDropzone = useDropzone({
    onDrop: onDropAadhaar,
    accept: {
      'image/*': ['.png', '.jpg', '.jpeg'],
      'application/pdf': ['.pdf'],
    },
    maxFiles: 1,
    maxSize: 5 * 1024 * 1024,
  });

  const handleSubmit = async () => {
    if (!token) return;
    if (!panFile && !aadhaarFile) {
      toast.error('Please upload at least one document');
      return;
    }

    setSubmitting(true);
    setErrors([]);

    try {
      const result = await portalApi.submit(
        token,
        { pan: panFile || undefined, aadhaar: aadhaarFile || undefined }
      );

      if (result.success) {
        setSubmitted(true);
        toast.success('Documents submitted successfully!');
      } else {
        setErrors(result.results.errors);
      }
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Submission failed');
    } finally {
      setSubmitting(false);
    }
  };

  if (validating) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-4"></div>
          <p className="text-gray-600">Validating your link...</p>
        </div>
      </div>
    );
  }

  if (!valid) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
        <div className="bg-white rounded-lg shadow-lg p-8 max-w-md w-full text-center">
          <XCircle className="h-16 w-16 text-red-500 mx-auto mb-4" />
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Invalid Link</h1>
          <p className="text-gray-600">
            This link is invalid or has expired. Please contact{' '}
            {hrEmail ? (
              <a href={`mailto:${hrEmail}`} className="text-blue-600 hover:underline">{hrEmail}</a>
            ) : (
              'the HR team'
            )}{' '}
            for a new link.
          </p>
        </div>
      </div>
    );
  }

  if (alreadySubmitted) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
        <div className="bg-white rounded-lg shadow-lg p-8 max-w-md w-full text-center">
          <CheckCircle className="h-16 w-16 text-green-500 mx-auto mb-4" />
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Already Submitted</h1>
          <p className="text-gray-600 mb-4">
            You have already submitted your documents using this link.
          </p>
          {submittedAt && (
            <p className="text-sm text-gray-500 mb-4">
              Submitted on: {new Date(submittedAt).toLocaleString()}
            </p>
          )}
          <p className="text-sm text-gray-500">
            If you need to update your documents, please contact{' '}
            {hrEmail ? (
              <a href={`mailto:${hrEmail}`} className="text-blue-600 hover:underline">{hrEmail}</a>
            ) : (
              'the HR team'
            )}{' '}
            for a new submission link.
          </p>
        </div>
      </div>
    );
  }

  if (submitted) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
        <div className="bg-white rounded-lg shadow-lg p-8 max-w-md w-full text-center">
          <CheckCircle className="h-16 w-16 text-green-500 mx-auto mb-4" />
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Thank You!</h1>
          <p className="text-gray-600 mb-4">
            Your documents have been submitted successfully. Our team will review them shortly.
          </p>
          <p className="text-sm text-gray-500">
            You can close this page now.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            Document Submission
          </h1>
          <p className="text-gray-600">
            Welcome{candidateName ? `, ${candidateName}` : ''}! Please upload your documents below.
          </p>
        </div>

        {/* Security Notice */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6 flex items-start gap-3">
          <Shield className="h-5 w-5 text-blue-500 mt-0.5" />
          <div>
            <p className="text-sm text-blue-800 font-medium">Secure Upload</p>
            <p className="text-sm text-blue-700">
              Your documents are encrypted and will only be used for verification purposes.
            </p>
          </div>
        </div>

        {/* Error Messages */}
        {errors.length > 0 && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <div className="flex items-start gap-3">
              <AlertCircle className="h-5 w-5 text-red-500 mt-0.5" />
              <div>
                <p className="text-sm text-red-800 font-medium">Please fix the following:</p>
                <ul className="text-sm text-red-700 list-disc list-inside mt-1">
                  {errors.map((error, i) => (
                    <li key={i}>{error}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}

        {/* PAN Card Upload */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            PAN Card
            {existingDocs.pan && (
              <span className="text-sm font-normal text-green-600 flex items-center gap-1">
                <CheckCircle className="h-4 w-4" /> Already submitted
              </span>
            )}
          </h2>

          {!panFile ? (
            <div
              {...panDropzone.getRootProps()}
              className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${
                panDropzone.isDragActive
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-300 hover:border-gray-400'
              }`}
            >
              <input {...panDropzone.getInputProps()} />
              <Upload className="h-8 w-8 text-gray-400 mx-auto mb-2" />
              <p className="text-gray-600 text-sm">
                Drag & drop your PAN card, or click to select
              </p>
              <p className="text-xs text-gray-400 mt-1">PNG, JPG, or PDF (max 5MB)</p>
            </div>
          ) : (
            <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-3">
                <FileText className="h-8 w-8 text-blue-500" />
                <div>
                  <p className="font-medium">{panFile.name}</p>
                  <p className="text-sm text-gray-500">
                    {(panFile.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
              </div>
              <button
                onClick={() => setPanFile(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
          )}
        </div>

        {/* Aadhaar Card Upload */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            Aadhaar Card
            {existingDocs.aadhaar && (
              <span className="text-sm font-normal text-green-600 flex items-center gap-1">
                <CheckCircle className="h-4 w-4" /> Already submitted
              </span>
            )}
          </h2>

          {!aadhaarFile ? (
            <div
              {...aadhaarDropzone.getRootProps()}
              className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${
                aadhaarDropzone.isDragActive
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-300 hover:border-gray-400'
              }`}
            >
              <input {...aadhaarDropzone.getInputProps()} />
              <Upload className="h-8 w-8 text-gray-400 mx-auto mb-2" />
              <p className="text-gray-600 text-sm">
                Drag & drop your Aadhaar card, or click to select
              </p>
              <p className="text-xs text-gray-400 mt-1">PNG, JPG, or PDF (max 5MB)</p>
            </div>
          ) : (
            <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-3">
                <FileText className="h-8 w-8 text-blue-500" />
                <div>
                  <p className="font-medium">{aadhaarFile.name}</p>
                  <p className="text-sm text-gray-500">
                    {(aadhaarFile.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
              </div>
              <button
                onClick={() => setAadhaarFile(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
          )}
        </div>

        {/* Submit Button */}
        <button
          onClick={handleSubmit}
          disabled={submitting || (!panFile && !aadhaarFile)}
          className={`w-full py-3 px-4 rounded-lg font-medium text-white transition-colors ${
            submitting || (!panFile && !aadhaarFile)
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-blue-600 hover:bg-blue-700'
          }`}
        >
          {submitting ? 'Submitting...' : 'Submit Documents'}
        </button>

        <p className="text-center text-sm text-gray-500 mt-4">
          Having trouble? Contact{' '}
          {hrEmail ? (
            <a href={`mailto:${hrEmail}`} className="text-blue-600 hover:underline">{hrEmail}</a>
          ) : (
            'the HR team'
          )}{' '}
          for assistance.
        </p>
      </div>
    </div>
  );
}
