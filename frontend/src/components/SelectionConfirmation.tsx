import React, { useState } from 'react';
import { apiService } from '../services/api';

interface SelectionConfirmationProps {
  companyName: string;
  companyId: string;
  solicitationText: string;
  solicitationTitle: string;
  onConfirmationComplete: (result: ConfirmationResult) => void;
}

interface ConfirmationResult {
  company_name: string;
  is_confirmed: boolean;
  confidence_score: number;
  reasoning: string;
  findings: {
    company_info: string;
    capability_match: string;
    experience_assessment: string;
    risk_factors: string[];
    strengths: string[];
  };
  recommendation: 'proceed' | 'reconsider' | 'reject';
  chain_of_thought: string[];
}

const SelectionConfirmation: React.FC<SelectionConfirmationProps> = ({
  companyName,
  companyId,
  solicitationText,
  solicitationTitle,
  onConfirmationComplete,
}) => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ConfirmationResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleRunConfirmation = async () => {
    setLoading(true);
    setError(null);

    try {
      const confirmationResult = await apiService.confirmSelection(
        companyName,
        companyId,
        solicitationText,
        solicitationTitle
      );
      setResult(confirmationResult);
      onConfirmationComplete(confirmationResult);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to run confirmation');
      console.error('Confirmation error:', err);
    } finally {
      setLoading(false);
    }
  };

  const getRecommendationColor = (rec: string) => {
    switch (rec) {
      case 'proceed':
        return 'bg-green-50 border-green-200 text-green-800';
      case 'reconsider':
        return 'bg-yellow-50 border-yellow-200 text-yellow-800';
      case 'reject':
        return 'bg-red-50 border-red-200 text-red-800';
      default:
        return 'bg-gray-50 border-gray-200 text-gray-800';
    }
  };

  const getRecommendationIcon = (rec: string) => {
    switch (rec) {
      case 'proceed':
        return '✓';
      case 'reconsider':
        return '⚠';
      case 'reject':
        return '✗';
      default:
        return '?';
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm p-6 border-2 border-indigo-200">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Selection Confirmation</h3>
          <p className="text-sm text-gray-600 mt-1">
            Independent verification of company alignment to solicitation
          </p>
        </div>
        {!result && (
          <button
            onClick={handleRunConfirmation}
            disabled={loading}
            className="px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-md hover:bg-indigo-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            {loading ? 'Verifying...' : 'Run Confirmation'}
          </button>
        )}
      </div>

      {loading && (
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mr-3"></div>
          <div className="text-sm text-gray-600">
            Gathering company information and performing chain-of-thought analysis...
          </div>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      {result && (
        <div className="space-y-4">
          {/* Confirmation Status */}
          <div className={`p-4 rounded-lg border-2 ${getRecommendationColor(result.recommendation)}`}>
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center space-x-2">
                <span className="text-2xl">{getRecommendationIcon(result.recommendation)}</span>
                <div>
                  <h4 className="font-semibold text-lg capitalize">{result.recommendation}</h4>
                  <p className="text-sm opacity-90">
                    Confidence: {(result.confidence_score * 100).toFixed(0)}%
                  </p>
                </div>
              </div>
              <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                result.is_confirmed ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
              }`}>
                {result.is_confirmed ? 'CONFIRMED' : 'NOT CONFIRMED'}
              </span>
            </div>
            <p className="text-sm mt-2">{result.reasoning}</p>
          </div>

          {/* Chain of Thought */}
          <div className="bg-gray-50 rounded-lg p-4">
            <h4 className="text-sm font-semibold text-gray-900 mb-3">Chain of Thought Analysis</h4>
            <div className="space-y-2">
              {result.chain_of_thought.map((thought, idx) => (
                <div key={idx} className="flex items-start space-x-2">
                  <span className="text-indigo-600 font-semibold text-sm mt-0.5">{idx + 1}.</span>
                  <p className="text-sm text-gray-700 flex-1">{thought}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Detailed Findings */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Company Info */}
            <div className="bg-blue-50 rounded-lg p-4">
              <h4 className="text-sm font-semibold text-blue-900 mb-2">Company Information</h4>
              <p className="text-sm text-gray-700">{result.findings.company_info}</p>
            </div>

            {/* Capability Match */}
            <div className="bg-purple-50 rounded-lg p-4">
              <h4 className="text-sm font-semibold text-purple-900 mb-2">Capability Match</h4>
              <p className="text-sm text-gray-700">{result.findings.capability_match}</p>
            </div>

            {/* Experience Assessment */}
            <div className="bg-teal-50 rounded-lg p-4">
              <h4 className="text-sm font-semibold text-teal-900 mb-2">Experience Assessment</h4>
              <p className="text-sm text-gray-700">{result.findings.experience_assessment}</p>
            </div>

            {/* Strengths */}
            <div className="bg-green-50 rounded-lg p-4">
              <h4 className="text-sm font-semibold text-green-900 mb-2">Strengths</h4>
              <ul className="space-y-1">
                {result.findings.strengths.map((strength, idx) => (
                  <li key={idx} className="text-sm text-gray-700 flex items-start">
                    <span className="text-green-600 mr-2">✓</span>
                    <span>{strength}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Risk Factors */}
          {result.findings.risk_factors.length > 0 && (
            <div className="bg-orange-50 rounded-lg p-4 border border-orange-200">
              <h4 className="text-sm font-semibold text-orange-900 mb-2">Risk Factors</h4>
              <ul className="space-y-1">
                {result.findings.risk_factors.map((risk, idx) => (
                  <li key={idx} className="text-sm text-gray-700 flex items-start">
                    <span className="text-orange-600 mr-2">⚠</span>
                    <span>{risk}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default SelectionConfirmation;

