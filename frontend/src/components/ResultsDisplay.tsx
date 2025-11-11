import React, { useState } from 'react';
import { PipelineResponse, MatchResult, apiService } from '../services/api';
import ScoreVisualization from './ScoreVisualization';
import SelectionConfirmation from './SelectionConfirmation';
import WebsiteValidationPanel from './WebsiteValidationPanel';

interface ResultsDisplayProps {
  results: PipelineResponse;
  solicitationText?: string;
  uploadedFileName?: string;
}

const ResultsDisplay: React.FC<ResultsDisplayProps> = ({ results, solicitationText, uploadedFileName }) => {
  const [selectedCompany, setSelectedCompany] = useState<MatchResult | null>(
    results.results[0] || null
  );
  const [allResults, setAllResults] = useState<MatchResult[]>(results.results);
  const [pagination, setPagination] = useState(results.pagination);
  const [loadingMore, setLoadingMore] = useState(false);

  const handleLoadNext15 = async () => {
    if (!results.unconfirmed_companies || !results.themes || !pagination) return;
    
    setLoadingMore(true);
    try {
      const response = await apiService.loadNextBatch(
        results.unconfirmed_companies,
        results.themes,
        results.solicitation_title || 'Solicitation',
        pagination.next_index
      );
      
      // Append new results
      setAllResults([...allResults, ...response.results]);
      
      // Update pagination
      setPagination({
        total_matches_above_50: pagination.total_matches_above_50,
        current_batch: pagination.current_batch + 15,
        has_more: response.has_more,
        remaining: response.remaining,
        next_index: response.next_index
      });
      
    } catch (error) {
      console.error('Error loading next batch:', error);
      alert('Failed to load next batch of companies. Please try again.');
    } finally {
      setLoadingMore(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Shortage Notice Banner */}
      {results.shortage_notice && (
        <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 rounded-r-lg shadow-sm">
          <div className="flex items-start">
            <svg className="w-6 h-6 text-yellow-600 mr-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <div className="flex-1">
              <h3 className="text-sm font-semibold text-yellow-800 mb-1">
                ⚠️ Fewer Companies Than Requested
              </h3>
              <p className="text-sm text-yellow-700 mb-2">
                {results.shortage_notice.message}
              </p>
              <div className="flex items-center space-x-4 text-xs text-yellow-600">
                <span>• Requested: <strong>{results.shortage_notice.requested}</strong></span>
                <span>• Delivered: <strong>{results.shortage_notice.delivered}</strong></span>
                <span>• Filtered Out: <strong>{results.shortage_notice.filtered_out}</strong></span>
              </div>
              <p className="text-xs text-yellow-600 mt-2 italic">
                💡 These are all available companies that meet minimum search criteria (accessible website). No additional companies were found matching the solicitation requirements.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Results List and Details */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Company List - Scrollable */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-lg shadow-sm p-4 sticky top-4">
            <h4 className="text-sm font-semibold text-gray-900 mb-3">Top Matches</h4>
            <div className="space-y-2 max-h-[calc(100vh-200px)] overflow-y-auto pr-2 custom-scrollbar">
              {allResults.map((result, idx) => {
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

            {/* Website Validation & Partnering Opportunities */}
            {selectedCompany.website_validation?.available && (
              <WebsiteValidationPanel 
                companyName={selectedCompany.company_name}
                websiteUrl={selectedCompany.website || ''}
                capabilities={selectedCompany.capabilities || []}
                solicitationTitle={results.solicitation_summary?.title || ''}
                preValidatedData={selectedCompany.website_validation.pre_validated ? {
                  validation_score: selectedCompany.website_validation.validation_score,
                  confirmed_capabilities: selectedCompany.website_validation.confirmed_capabilities,
                  website_capabilities: selectedCompany.website_validation.website_capabilities,
                  gaps_count: selectedCompany.website_validation.gaps_count,
                  partnering_opportunities_count: selectedCompany.website_validation.partnering_opportunities_count
                } : undefined}
              />
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
          <table className="w-full divide-y divide-gray-200" style={{ minWidth: '1600px' }}>
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider whitespace-nowrap" style={{ width: '180px' }}>
                  Company Name
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider whitespace-nowrap" style={{ width: '150px' }}>
                  Company URL
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider whitespace-nowrap" style={{ width: '200px' }}>
                  File Name
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider" style={{ width: '1070px' }}>
                  Why a Match
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {allResults.map((result, idx) => {
                const solicitationName = uploadedFileName || results.solicitation_summary?.title || 'Solicitation';
                
                // Clean up company name - remove Inc., LLC, Corp., etc.
                const cleanCompanyName = result.company_name
                  .replace(/,?\s*(Inc\.?|LLC\.?|L\.L\.C\.?|Ltd\.?|Limited|Corp\.?|Corporation|Co\.?|Company|LP\.?|L\.P\.?|LLP\.?|L\.L\.P\.?|PLLC\.?|PC\.?|P\.C\.?|PLC\.?|P\.L\.C\.?|Incorporated|S\.A\.?|AG\.?|GmbH\.?|Pty\.?\s*Ltd\.?|N\.V\.?|B\.V\.?)\s*$/gi, '')
                  .trim();
                
                // Use ONLY the alignment_summary - this is the new 2-paragraph format
                let whyMatchContent = result.confirmation_result?.alignment_summary || 
                                      result.decision_rationale || 
                                      '';
                
                // Fallback if no content (also 2-paragraph format)
                if (!whyMatchContent || whyMatchContent.trim().length < 50) {
                  whyMatchContent = `Based on available information, ${cleanCompanyName} appears to align well with this opportunity based on your sector expertise and capabilities. You appear to specialize in relevant domains and may have operational capacity to address this program's objectives. Your focus suggests potential to support the goals of this solicitation.

Analysis indicates possible alignment between ${cleanCompanyName}'s technology and services and the solicitation's stated needs. Your capabilities appear to address key focus areas. Your experience suggests readiness to meet the program requirements.`;
                }
                
                return (
                  <tr key={result.company_id} className={idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                    <td className="px-4 py-4 text-sm font-medium text-gray-900">
                      <span className="font-semibold">{cleanCompanyName}</span>
                    </td>
                    <td className="px-4 py-4 text-sm text-gray-700">
                      {result.website ? (
                        <a 
                          href={result.website} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:text-blue-800 hover:underline break-all"
                        >
                          {result.website}
                        </a>
                      ) : (
                        <span className="text-gray-400 text-xs">Not available</span>
                      )}
                    </td>
                    <td className="px-4 py-4 text-sm text-gray-700">
                      <div className="break-words">
                        {solicitationName}
                      </div>
                    </td>
                    <td className="px-4 py-4 text-sm text-gray-700">
                      <div className="whitespace-pre-line leading-relaxed space-y-3">
                        {whyMatchContent.split('\n\n').map((paragraph, pIdx) => (
                          <p key={pIdx} className={paragraph.includes(':') && paragraph.split(':')[0].length < 30 ? 'font-semibold text-gray-800 mb-1' : 'text-gray-700'}>
                            {paragraph}
                          </p>
                        ))}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        
        {/* Table Footer with Pagination Info */}
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-900">
                Showing {allResults.length} of {pagination?.total_matches_above_50 || allResults.length} companies
              </p>
              <p className="text-xs text-gray-500 mt-1">
                Complete Analysis Summary provided for "{results.solicitation_summary?.title || 'this solicitation'}"
              </p>
            </div>
            
            {/* Load Next 15 Button */}
            {pagination?.has_more && (
              <button
                onClick={handleLoadNext15}
                disabled={loadingMore}
                className={`px-6 py-3 ${loadingMore ? 'bg-gray-400' : 'bg-blue-600 hover:bg-blue-700'} text-white font-medium rounded-lg transition-colors flex items-center`}
              >
                {loadingMore ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Loading...
                  </>
                ) : (
                  <>
                    Load Next 15
                    <span className="ml-2 text-sm">({pagination.remaining} remaining)</span>
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ResultsDisplay;


