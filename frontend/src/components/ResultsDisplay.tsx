import React, { useState } from 'react';
import { PipelineResponse, MatchResult } from '../services/api';
import ScoreVisualization from './ScoreVisualization';
import SelectionConfirmation from './SelectionConfirmation';

interface ResultsDisplayProps {
  results: PipelineResponse;
  solicitationText?: string;
}

const ResultsDisplay: React.FC<ResultsDisplayProps> = ({ results, solicitationText }) => {
  const [selectedCompany, setSelectedCompany] = useState<MatchResult | null>(
    results.results[0] || null
  );

  return (
    <div className="space-y-6">
      {/* Results List and Details */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Company List - Scrollable */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-lg shadow-sm p-4 sticky top-4">
            <h4 className="text-sm font-semibold text-gray-900 mb-3">Top Matches</h4>
            <div className="space-y-2 max-h-[calc(100vh-200px)] overflow-y-auto pr-2 custom-scrollbar">
              {results.results.map((result, idx) => {
                const isConfirmed = result.confirmation_result?.is_confirmed;
                const confirmationScore = result.confirmation_result?.confidence_score;
                
                return (
                  <button
                    key={result.company_id}
                    onClick={() => setSelectedCompany(result)}
                    className={`w-full text-left p-3 rounded-lg border-2 transition-all ${
                      selectedCompany?.company_id === result.company_id
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-medium text-gray-900">#{idx + 1}</span>
                      {isConfirmed !== null && (
                        <span className={`text-xs px-2 py-0.5 rounded-full ${
                          isConfirmed 
                            ? 'bg-green-100 text-green-700' 
                            : 'bg-yellow-100 text-yellow-700'
                        }`}>
                          {isConfirmed ? '✓ Verified' : '⚠ Review'}
                        </span>
                      )}
                    </div>
                    <p className="text-sm font-medium text-gray-800 mb-1">
                      {result.company_name || 'Unknown Company'}
                    </p>
                    {confirmationScore !== null && confirmationScore !== undefined && (
                      <div className="flex items-center gap-2">
                        <div className="flex-1 bg-gray-200 rounded-full h-1.5">
                          <div 
                            className={`h-1.5 rounded-full ${
                              confirmationScore > 0.7 ? 'bg-green-500' : 
                              confirmationScore > 0.5 ? 'bg-yellow-500' : 'bg-red-500'
                            }`}
                            style={{ width: `${confirmationScore * 100}%` }}
                          />
                        </div>
                        <span className="text-xs text-gray-500">{Math.round(confirmationScore * 100)}%</span>
                      </div>
                    )}
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* Detailed View */}
        {selectedCompany && (
          <div className="lg:col-span-2 space-y-4">
            {/* Company Header */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <div className="mb-4">
                <h3 className="text-xl font-bold text-gray-900">{selectedCompany.company_name || 'Unknown Company'}</h3>
                {selectedCompany.website && (
                  <a 
                    href={selectedCompany.website.startsWith('http') ? selectedCompany.website : `https://${selectedCompany.website}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-blue-600 hover:text-blue-800 hover:underline mt-1 inline-block"
                  >
                    {selectedCompany.website}
                  </a>
                )}
                {!selectedCompany.website && (
                  <p className="text-sm text-gray-500 mt-1">Website not available</p>
                )}
              </div>

              {/* Recommendation */}
              <div className={`p-4 rounded-lg border-2 ${
                selectedCompany.recommendation.startsWith('✓')
                  ? 'bg-green-50 border-green-200'
                  : selectedCompany.recommendation.startsWith('⚠')
                  ? 'bg-yellow-50 border-yellow-200'
                  : 'bg-red-50 border-red-200'
              }`}>
                <p className="font-semibold text-gray-900">{selectedCompany.recommendation}</p>
              </div>
            </div>

            {/* Scores - Compact */}
            <div className="bg-white rounded-lg shadow-sm p-3">
              <h4 className="text-xs font-semibold text-gray-900 mb-2">Score Breakdown</h4>
              <ScoreVisualization result={selectedCompany} />
            </div>

            {/* Confirmation Analysis (if available) */}
            {selectedCompany.confirmation_result && (
              <div className="bg-white rounded-lg shadow-sm p-6">
                <div className="flex items-center justify-between mb-4">
                  <h4 className="text-sm font-semibold text-gray-900">Confirmation Analysis</h4>
                  <span className={`text-xs px-3 py-1 rounded-full font-medium ${
                    selectedCompany.confirmation_result.is_confirmed 
                      ? 'bg-green-100 text-green-700' 
                      : 'bg-yellow-100 text-yellow-700'
                  }`}>
                    {selectedCompany.confirmation_result.is_confirmed ? '✓ Verified Match' : '⚠ Needs Review'}
                  </span>
                </div>

                {/* Confidence Score */}
                {selectedCompany.confirmation_result.confidence_score !== null && (
                  <div className="mb-4">
                    <div className="flex items-center justify-between text-sm mb-1">
                      <span className="text-gray-600">Confidence Score</span>
                      <span className="font-medium">{Math.round(selectedCompany.confirmation_result.confidence_score * 100)}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className={`h-2 rounded-full ${
                          selectedCompany.confirmation_result.confidence_score > 0.7 ? 'bg-green-500' : 
                          selectedCompany.confirmation_result.confidence_score > 0.5 ? 'bg-yellow-500' : 'bg-red-500'
                        }`}
                        style={{ width: `${selectedCompany.confirmation_result.confidence_score * 100}%` }}
                      />
                    </div>
                  </div>
                )}

                {/* Chain of Thought */}
                {selectedCompany.confirmation_result.chain_of_thought && selectedCompany.confirmation_result.chain_of_thought.length > 0 && (
                  <div className="mb-4">
                    <h5 className="text-xs font-semibold text-gray-700 mb-2">Analysis Steps</h5>
                    <ul className="space-y-1">
                      {selectedCompany.confirmation_result.chain_of_thought.map((step: string, idx: number) => (
                        <li key={idx} className="text-xs text-gray-600 flex items-start">
                          <span className="mr-2 text-blue-500">•</span>
                          <span>{step}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Company Info Summary */}
                {selectedCompany.confirmation_result.company_info && (
                  <div className="mt-4 pt-4 border-t border-gray-200">
                    <h5 className="text-xs font-semibold text-gray-700 mb-2">Company Information</h5>
                    <p className="text-xs text-gray-600">{selectedCompany.confirmation_result.company_info}</p>
                  </div>
                )}
              </div>
            )}

            {/* Decision Rationale */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h4 className="text-sm font-semibold text-gray-900 mb-3">Decision Rationale</h4>
              <p className="text-sm text-gray-700 whitespace-pre-wrap">
                {selectedCompany.decision_rationale}
              </p>
            </div>

            {/* Alignment Summary - Client-Facing */}
            {selectedCompany.confirmation_result?.alignment_summary && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg shadow-sm p-6">
                <div className="flex items-start space-x-2">
                  <svg className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <div className="flex-1">
                    <h4 className="text-sm font-semibold text-blue-900 mb-2">Why This Company Aligns</h4>
                    <p className="text-sm text-blue-800 leading-relaxed">
                      {selectedCompany.confirmation_result.alignment_summary}
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Comprehensive Results Table */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Complete Analysis Summary</h3>
        <p className="text-sm text-gray-600 mb-4">Detailed breakdown of all companies analyzed for this solicitation</p>
        
        <div className="overflow-x-auto -mx-6 px-6">
          <table className="min-w-full divide-y divide-gray-200" style={{ minWidth: '1200px' }}>
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider whitespace-nowrap">
                  Company Name
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider whitespace-nowrap">
                  Company URL
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider whitespace-nowrap">
                  Solicitation Name
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider whitespace-nowrap">
                  Why a Match
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider whitespace-nowrap">
                  Analysis Steps
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {results.results.map((result, idx) => {
                const solicitationName = results.solicitation_summary?.title || 'Solicitation';
                const whyMatch = result.confirmation_result?.alignment_summary || 
                                result.decision_rationale?.substring(0, 200) || 
                                'Strong alignment with solicitation requirements based on company capabilities and experience.';
                const analysisSteps = result.confirmation_result?.chain_of_thought || [];
                
                return (
                  <tr key={result.company_id} className={idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                    <td className="px-4 py-4 text-sm font-medium text-gray-900 whitespace-nowrap">
                      <span className="font-semibold">{result.company_name}</span>
                    </td>
                    <td className="px-4 py-4 text-sm text-gray-700">
                      {result.website ? (
                        <a 
                          href={result.website} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:text-blue-800 hover:underline"
                        >
                          {result.website}
                        </a>
                      ) : (
                        <span className="text-gray-400 text-xs">Not available</span>
                      )}
                    </td>
                    <td className="px-4 py-4 text-sm text-gray-700">
                      <div className="max-w-xs">
                        {solicitationName}
                      </div>
                    </td>
                    <td className="px-4 py-4 text-sm text-gray-700">
                      <div className="max-w-lg">
                        {whyMatch.length > 250 ? `${whyMatch.substring(0, 250)}...` : whyMatch}
                      </div>
                    </td>
                    <td className="px-4 py-4 text-sm text-gray-700">
                      <div className="max-w-lg">
                        {analysisSteps.length > 0 ? (
                          <ul className="space-y-1">
                            {analysisSteps.slice(0, 3).map((step, stepIdx) => (
                              <li key={stepIdx} className="text-xs">
                                <span className="font-medium">{stepIdx + 1}.</span> {step.length > 100 ? `${step.substring(0, 100)}...` : step}
                              </li>
                            ))}
                            {analysisSteps.length > 3 && (
                              <li className="text-xs text-gray-500 italic">
                                +{analysisSteps.length - 3} more steps...
                              </li>
                            )}
                          </ul>
                        ) : (
                          <span className="text-xs text-gray-500">Analysis in progress</span>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        
        {/* Table Footer */}
        <div className="mt-4 pt-4 border-t border-gray-200">
          <p className="text-xs text-gray-500">
            Table showing {results.results.length} companies analyzed for "{results.solicitation_summary?.title || 'this solicitation'}"
          </p>
        </div>
      </div>
    </div>
  );
};

export default ResultsDisplay;


