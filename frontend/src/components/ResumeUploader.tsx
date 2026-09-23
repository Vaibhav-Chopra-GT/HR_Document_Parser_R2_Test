import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, X, AlertTriangle, Loader2 } from 'lucide-react';
import { candidatesApi } from '../api/client';
import type { CandidateListItem } from '../types';
import toast from 'react-hot-toast';

interface ResumeUploaderProps {
  onUploadSuccess: (candidateId: string) => void;
}

interface DuplicateInfo {
  matchField: string;
  existingCandidate: CandidateListItem;
  extractedData: Record<string, any>;
  file: File;
}

export default function ResumeUploader({ onUploadSuccess }: ResumeUploaderProps) {
  const [uploading, setUploading] = useState(false);
  const [extracting, setExtracting] = useState(false);
  const [progress, setProgress] = useState(0);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [duplicateInfo, setDuplicateInfo] = useState<DuplicateInfo | null>(null);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      setSelectedFile(acceptedFiles[0]);
      setDuplicateInfo(null);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    },
    maxFiles: 1,
    maxSize: 10 * 1024 * 1024, // 10MB
  });

  const handleUpload = async (force = false) => {
    if (!selectedFile) return;

    setUploading(true);
    setExtracting(false);
    setProgress(0);

    try {
      const result = await candidatesApi.upload(
        selectedFile,
        (p) => {
          setProgress(p);
          // When upload completes, switch to extracting state
          if (p === 100) {
            setExtracting(true);
          }
        },
        force
      );

      // Check for duplicate
      if (result.duplicate && result.existing_candidate) {
        setDuplicateInfo({
          matchField: result.match_field || 'email',
          existingCandidate: result.existing_candidate,
          extractedData: result.extracted_data || {},
          file: selectedFile,
        });
        setUploading(false);
        setExtracting(false);
        return;
      }

      if (result.status === 'completed' && result.id) {
        toast.success('Resume parsed successfully!');
        onUploadSuccess(result.id);
        setSelectedFile(null);
        setDuplicateInfo(null);
      } else if (result.status === 'failed') {
        toast.error(result.error || 'Failed to parse resume');
      }

    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Upload failed');
    } finally {
      setUploading(false);
      setExtracting(false);
      setProgress(0);
    }
  };

  const handleForceCreate = () => {
    handleUpload(true);
  };

  const handleViewExisting = () => {
    if (duplicateInfo?.existingCandidate) {
      onUploadSuccess(duplicateInfo.existingCandidate.id);
      setSelectedFile(null);
      setDuplicateInfo(null);
    }
  };

  const clearFile = () => {
    setSelectedFile(null);
    setDuplicateInfo(null);
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-lg font-semibold mb-4">Upload Resume</h2>

      {!selectedFile ? (
        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors
            ${isDragActive ? 'border-violet-500 bg-violet-50' : 'border-gray-300 hover:border-gray-400'}`}
        >
          <input {...getInputProps()} />
          <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
          {isDragActive ? (
            <p className="text-violet-600">Drop the resume here...</p>
          ) : (
            <>
              <p className="text-gray-600 mb-2">
                Drag & drop a resume here, or click to select
              </p>
              <p className="text-sm text-gray-400">PDF or DOCX, max 10MB</p>
            </>
          )}
        </div>
      ) : (
        <div className="border rounded-lg p-4">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <FileText className="h-8 w-8 text-violet-500" />
              <div>
                <p className="font-medium">{selectedFile.name}</p>
                <p className="text-sm text-gray-500">
                  {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
            </div>
            {!uploading && (
              <button
                onClick={clearFile}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="h-5 w-5" />
              </button>
            )}
          </div>

          {uploading && (
            <div className="mb-4">
              {!extracting ? (
                <>
                  <div className="flex justify-between text-sm text-gray-600 mb-1">
                    <span>Uploading...</span>
                    <span>{progress}%</span>
                  </div>
                  <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-violet-500 transition-all duration-300"
                      style={{ width: `${progress}%` }}
                    />
                  </div>
                </>
              ) : (
                <div className="flex items-center gap-3 text-violet-600">
                  <Loader2 className="h-5 w-5 animate-spin" />
                  <span className="text-sm font-medium">Extracting data with AI...</span>
                </div>
              )}
            </div>
          )}

          {/* Duplicate Warning */}
          {duplicateInfo && (
            <div className="mb-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <div className="flex items-start gap-3">
                <AlertTriangle className="h-5 w-5 text-yellow-600 mt-0.5" />
                <div className="flex-1">
                  <p className="font-medium text-yellow-800">
                    Duplicate Candidate Found
                  </p>
                  <p className="text-sm text-yellow-700 mt-1">
                    A candidate with this <strong>{duplicateInfo.matchField}</strong> already exists:
                  </p>
                  <div className="mt-2 p-3 bg-white rounded border text-sm">
                    <p><strong>Name:</strong> {duplicateInfo.existingCandidate.name || 'N/A'}</p>
                    <p><strong>Email:</strong> {duplicateInfo.existingCandidate.email || 'N/A'}</p>
                    <p><strong>Company:</strong> {duplicateInfo.existingCandidate.company || 'N/A'}</p>
                  </div>
                  <div className="flex gap-2 mt-3">
                    <button
                      onClick={handleViewExisting}
                      className="px-3 py-1.5 text-sm bg-white border border-gray-300 rounded hover:bg-gray-50"
                    >
                      View Existing
                    </button>
                    <button
                      onClick={handleForceCreate}
                      className="px-3 py-1.5 text-sm bg-yellow-600 text-white rounded hover:bg-yellow-700"
                    >
                      Create Anyway
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {!duplicateInfo && (
            <button
              onClick={() => handleUpload(false)}
              disabled={uploading}
              className={`w-full py-2 px-4 rounded-lg font-medium text-white transition-colors
                ${uploading
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-violet-600 hover:bg-violet-700'
                }`}
            >
              {uploading ? 'Processing...' : 'Upload & Parse Resume'}
            </button>
          )}
        </div>
      )}
    </div>
  );
}
