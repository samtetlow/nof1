import React from 'react';
import { MatchResult } from '../services/api';

interface ScoreVisualizationProps {
  result: MatchResult;
}

const ScoreVisualization: React.FC<ScoreVisualizationProps> = ({ result }) => {
  return (
    <div className="flex items-center space-x-3">
      {/* Progress bar */}
      <div className="flex-1">
        <div className="overflow-hidden h-2 rounded-full bg-gray-200">
          <div
            style={{ width: `${result.match_score * 100}%`, backgroundColor: '#10b981' }}
            className="h-full rounded-full transition-all duration-300"
          ></div>
        </div>
      </div>
      {/* Score percentage */}
      <span className="text-lg font-bold text-green-600 flex-shrink-0">
        {(result.match_score * 100).toFixed(1)}%
      </span>
    </div>
  );
};

export default ScoreVisualization;


