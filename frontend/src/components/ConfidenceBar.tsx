interface ConfidenceBarProps {
  score: number | null;
  label: string;
  showLabel?: boolean;
}

export default function ConfidenceBar({ score, label, showLabel = true }: ConfidenceBarProps) {
  if (score === null || score === undefined) {
    return (
      <div className="flex items-center gap-2">
        {showLabel && <span className="text-sm text-gray-600 w-24">{label}</span>}
        <span className="text-sm text-gray-400">N/A</span>
      </div>
    );
  }

  const percentage = Math.round(score * 100);

  const getColor = () => {
    if (score >= 0.8) return 'bg-green-500';
    if (score >= 0.6) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const getTextColor = () => {
    if (score >= 0.8) return 'text-green-700';
    if (score >= 0.6) return 'text-yellow-700';
    return 'text-red-700';
  };

  return (
    <div className="flex items-center gap-2">
      {showLabel && <span className="text-sm text-gray-600 w-24">{label}</span>}
      <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden max-w-32">
        <div
          className={`h-full ${getColor()} transition-all duration-300`}
          style={{ width: `${percentage}%` }}
        />
      </div>
      <span className={`text-sm font-medium w-12 text-right ${getTextColor()}`}>
        {percentage}%
      </span>
    </div>
  );
}
