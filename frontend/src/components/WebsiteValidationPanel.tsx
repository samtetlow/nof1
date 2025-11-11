import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';

interface WebsiteValidationPanelProps {
  companyName: string;
  websiteUrl: string;
  capabilities: string[];
  solicitationTitle: string;
  preValidatedData?: {
    validation_score?: number;
    confirmed_capabilities?: string[];
    website_capabilities?: string[];
    gaps_count?: number;
    partnering_opportunities_count?: number;
  };
}

interface Gap {
  type: string;
  description: string;
  claimed: string;
  website: string;
  severity: number;
}

interface PartneringOpportunity {
  gap: string;
  opportunity_type: string;
  suggestion: string;
  priority: string;
}

interface ValidationData {
  company_name: string;
  website_url: string;
  website_accessible: boolean;
  validation_score: number;
  confirmed_capabilities: string[];
  website_capabilities: string[];
  gaps: Gap[];
  partnering_opportunities: PartneringOpportunity[];
  summary: string;
}

const WebsiteValidationPanel: React.FC<WebsiteValidationPanelProps> = ({
  companyName,
  websiteUrl,
  capabilities,
  solicitationTitle,
  preValidatedData
}) => {
  const [loading, setLoading] = useState(false);
  const [validationData, setValidationData] = useState<ValidationData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(true); // Auto-expand since we have data
  const [showPreValidatedSummary, setShowPreValidatedSummary] = useState(!!preValidatedData);

  // Load full validation data on mount if we only have pre-validated summary
  useEffect(() => {
    if (preValidatedData && !validationData) {
      // Auto-load full data since we know the website is accessible
      loadValidation();
    }
  }, [preValidatedData]);

  const loadValidation = async () => {
    if (!websiteUrl) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const data = await apiService.validateWebsite({
        company_name: companyName,
        company_website: websiteUrl,
        company_capabilities: capabilities,
        solicitation_title: solicitationTitle,
        required_capabilities: []
      });
      
      setValidationData(data);
      setExpanded(true);
    } catch (err) {
      console.error('Website validation failed:', err);
      setError('Failed to validate website. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const getSeverityColor = (severity: number): string => {
    if (severity >= 0.7) return 'text-red-600 bg-red-50';
    if (severity >= 0.5) return 'text-orange-600 bg-orange-50';
    return 'text-yellow-600 bg-yellow-50';
  };

  const getPriorityColor = (priority: string): string => {
    const p = priority.toLowerCase();
    if (p === 'critical' || p === 'high') return 'bg-red-100 text-red-700';
    if (p === 'medium') return 'bg-yellow-100 text-yellow-700';
    return 'bg-blue-100 text-blue-700';
  };

  return (
    <div className="bg-gradient-to-br from-purple-50 to-pink-50 border border-purple-200 rounded-lg shadow-sm p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
          </svg>
          <h4 className="text-sm font-semibold text-purple-900">Website Validation & Partnering Opportunities</h4>
          {validationData && (
            <span className="text-xs px-2 py-1 bg-green-100 text-green-700 rounded-full font-medium">
              ✓ Pre-Validated
            </span>
          )}
        </div>
        
        {!validationData && !loading && (
          <button
            onClick={loadValidation}
            className="px-4 py-2 bg-purple-600 text-white text-sm font-medium rounded-lg hover:bg-purple-700 transition-colors"
          >
            Re-analyze Website
          </button>
        )}
      </div>

      {loading && (
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
          <span className="ml-3 text-sm text-purple-700">Analyzing website...</span>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {validationData && (
        <div className="space-y-4">
          {/* Validation Score */}
          <div className="bg-white rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700">Website Validation Score</span>
              <span className="text-lg font-bold text-purple-600">
                {Math.round(validationData.validation_score * 100)}%
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className={`h-2 rounded-full ${
                  validationData.validation_score >= 0.8 ? 'bg-green-500' :
                  validationData.validation_score >= 0.6 ? 'bg-yellow-500' : 'bg-red-500'
                }`}
                style={{ width: `${validationData.validation_score * 100}%` }}
              />
            </div>
            <p className="text-xs text-gray-600 mt-2">
              Measures how well the website confirms claimed capabilities
            </p>
          </div>

          {/* Summary */}
          <div className="bg-white rounded-lg p-4">
            <h5 className="text-xs font-semibold text-gray-700 mb-2">Summary</h5>
            <p className="text-sm text-gray-800 whitespace-pre-wrap">{validationData.summary}</p>
          </div>

          {/* Confirmed Capabilities */}
          {validationData.confirmed_capabilities.length > 0 && (
            <div className="bg-white rounded-lg p-4">
              <h5 className="text-xs font-semibold text-gray-700 mb-2">
                ✓ Confirmed on Website ({validationData.confirmed_capabilities.length})
              </h5>
              <div className="flex flex-wrap gap-2">
                {validationData.confirmed_capabilities.map((cap, idx) => (
                  <span key={idx} className="text-xs px-2 py-1 bg-green-100 text-green-700 rounded">
                    {cap}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Website Capabilities */}
          {validationData.website_capabilities.length > 0 && (
            <div className="bg-white rounded-lg p-4">
              <h5 className="text-xs font-semibold text-gray-700 mb-2">
                Found on Website ({validationData.website_capabilities.length})
              </h5>
              <div className="flex flex-wrap gap-2">
                {validationData.website_capabilities.map((cap, idx) => (
                  <span key={idx} className="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded">
                    {cap}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Gaps Found */}
          {validationData.gaps.length > 0 && (
            <div className="bg-white rounded-lg p-4">
              <h5 className="text-xs font-semibold text-gray-700 mb-3">
                ⚠️ Gaps Identified ({validationData.gaps.length})
              </h5>
              <div className="space-y-3">
                {validationData.gaps.map((gap, idx) => (
                  <div key={idx} className={`p-3 rounded-lg border ${getSeverityColor(gap.severity)}`}>
                    <div className="flex items-start justify-between mb-1">
                      <p className="text-sm font-medium">{gap.description}</p>
                      <span className="text-xs px-2 py-0.5 rounded bg-white bg-opacity-50">
                        {Math.round(gap.severity * 100)}% severity
                      </span>
                    </div>
                    <div className="text-xs mt-2 space-y-1">
                      <div><strong>Claimed:</strong> {gap.claimed}</div>
                      <div><strong>On Website:</strong> {gap.website}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Partnering Opportunities */}
          {validationData.partnering_opportunities.length > 0 && (
            <div className="bg-gradient-to-r from-purple-100 to-pink-100 rounded-lg p-4 border-2 border-purple-300">
              <div className="flex items-center space-x-2 mb-3">
                <svg className="w-5 h-5 text-purple-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
                <h5 className="text-sm font-bold text-purple-900">
                  🤝 Partnering Opportunities ({validationData.partnering_opportunities.length})
                </h5>
              </div>
              
              <div className="space-y-3">
                {validationData.partnering_opportunities.map((opp, idx) => (
                  <div key={idx} className="bg-white rounded-lg p-4 shadow-sm">
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <span className={`text-xs px-2 py-1 rounded font-medium ${getPriorityColor(opp.priority)}`}>
                          {opp.priority} Priority
                        </span>
                      </div>
                    </div>
                    
                    <h6 className="text-sm font-semibold text-gray-900 mb-1">
                      {opp.opportunity_type}
                    </h6>
                    
                    <p className="text-sm text-gray-700 mb-2">{opp.suggestion}</p>
                    
                    {opp.gap && (
                      <p className="text-xs text-gray-600">
                        <strong>Gap:</strong> {opp.gap}
                      </p>
                    )}
                  </div>
                ))}
              </div>

              <div className="mt-4 pt-4 border-t border-purple-200">
                <p className="text-xs text-purple-800 italic">
                  💡 These partnering opportunities could strengthen your bid by addressing identified gaps.
                </p>
              </div>
            </div>
          )}

          {/* No Gaps - Success Message */}
          {validationData.gaps.length === 0 && validationData.partnering_opportunities.length === 0 && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="flex items-center space-x-2">
                <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <p className="text-sm text-green-800 font-medium">
                  ✓ Website strongly validates all claimed capabilities. No significant gaps identified.
                </p>
              </div>
            </div>
          )}
        </div>
      )}

      {!validationData && !loading && !error && (
        <div className="text-center py-4">
          <p className="text-sm text-purple-700">
            Click "Analyze Website" to validate capabilities and identify partnering opportunities
          </p>
        </div>
      )}
    </div>
  );
};

export default WebsiteValidationPanel;

