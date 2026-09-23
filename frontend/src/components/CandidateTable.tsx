import { useNavigate } from 'react-router-dom';
import { format } from 'date-fns';
import { Eye, FileText, Mail, CheckCircle, Clock, AlertCircle, XCircle } from 'lucide-react';
import type { CandidateListItem } from '../types';

interface CandidateTableProps {
  candidates: CandidateListItem[];
  loading?: boolean;
}

const StatusBadge = ({ status, type }: { status: string; type: 'extraction' | 'document' }) => {
  const configs = {
    extraction: {
      completed: { bg: 'bg-green-100', text: 'text-green-800', icon: CheckCircle },
      processing: { bg: 'bg-violet-100', text: 'text-violet-800', icon: Clock },
      pending: { bg: 'bg-gray-100', text: 'text-gray-800', icon: Clock },
      failed: { bg: 'bg-red-100', text: 'text-red-800', icon: XCircle },
    },
    document: {
      completed: { bg: 'bg-green-100', text: 'text-green-800', icon: CheckCircle },
      partial: { bg: 'bg-yellow-100', text: 'text-yellow-800', icon: AlertCircle },
      requested: { bg: 'bg-violet-100', text: 'text-violet-800', icon: Mail },
      pending: { bg: 'bg-gray-100', text: 'text-gray-800', icon: Clock },
    },
  };

  const config = configs[type][status as keyof typeof configs[typeof type]] || configs[type].pending;
  const Icon = config.icon;

  return (
    <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${config.bg} ${config.text}`}>
      <Icon className="h-3 w-3" />
      {status}
    </span>
  );
};

export default function CandidateTable({ candidates, loading }: CandidateTableProps) {
  const navigate = useNavigate();

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="p-8 text-center text-gray-500">
          <Clock className="h-8 w-8 mx-auto mb-2 animate-spin" />
          Loading candidates...
        </div>
      </div>
    );
  }

  if (candidates.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="p-8 text-center text-gray-500">
          <FileText className="h-12 w-12 mx-auto mb-2 text-gray-300" />
          <p>No candidates yet</p>
          <p className="text-sm">Upload a resume to get started</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Candidate
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Company
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Extraction
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Documents
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Confidence
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Date
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {candidates.map((candidate) => (
              <tr
                key={candidate.id}
                className="hover:bg-gray-50 cursor-pointer"
                onClick={() => navigate(`/candidates/${candidate.id}`)}
              >
                <td className="px-6 py-4 whitespace-nowrap">
                  <div>
                    <div className="text-sm font-medium text-gray-900">
                      {candidate.name || 'Unknown'}
                    </div>
                    <div className="text-sm text-gray-500">
                      {candidate.email || 'No email'}
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-900">
                    {candidate.company || '-'}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <StatusBadge status={candidate.extraction_status} type="extraction" />
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <StatusBadge status={candidate.document_status} type="document" />
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {candidate.overall_confidence !== null ? (
                    <div className="flex items-center gap-2">
                      <div className="w-16 h-2 bg-gray-200 rounded-full overflow-hidden">
                        <div
                          className={`h-full ${
                            candidate.overall_confidence >= 0.8
                              ? 'bg-green-500'
                              : candidate.overall_confidence >= 0.6
                              ? 'bg-yellow-500'
                              : 'bg-red-500'
                          }`}
                          style={{ width: `${candidate.overall_confidence * 100}%` }}
                        />
                      </div>
                      <span className="text-sm text-gray-600">
                        {Math.round(candidate.overall_confidence * 100)}%
                      </span>
                    </div>
                  ) : (
                    <span className="text-sm text-gray-400">-</span>
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {candidate.created_at
                    ? format(new Date(candidate.created_at), 'MMM d, yyyy')
                    : '-'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      navigate(`/candidates/${candidate.id}`);
                    }}
                    className="text-violet-600 hover:text-violet-800"
                  >
                    <Eye className="h-5 w-5" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
