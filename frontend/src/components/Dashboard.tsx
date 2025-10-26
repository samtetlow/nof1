import React, { useState } from 'react';
import SolicitationForm from './SolicitationForm';
import ResultsDisplay from './ResultsDisplay';
import { apiService, Solicitation, PipelineResponse } from '../services/api';

const Dashboard: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<PipelineResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [solicitationText, setSolicitationText] = useState<string>('');

  const handleAnalyze = async (solicitation: Solicitation, options: {
    enrich: boolean;
    topK: number;
    companyType: 'for-profit' | 'academic-nonprofit';
    companySize: 'all' | 'small' | 'large';
  }) => {
    setLoading(true);
    setError(null);
    setResults(null);

    try {
      // Validate solicitation has content
      if (!solicitation.raw_text || solicitation.raw_text.trim().length < 50) {
        setError('Please upload a valid solicitation document or paste the full text (minimum 50 characters).');
        setLoading(false);
        return;
      }

      // Store solicitation text for confirmation
      setSolicitationText(solicitation.raw_text);

      const response = await apiService.runFullPipeline(
        solicitation,
        undefined,
        options.enrich,
        options.topK,
        options.companyType,
        options.companySize
      );
      
      if (!response || !response.results) {
        setError('Received invalid response from server. Please try again.');
        setLoading(false);
        return;
      }
      
      setResults(response);
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || 'An error occurred while processing your request';
      setError(errorMsg);
      console.error('Pipeline error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div>
        <h2 className="text-3xl font-bold text-gray-900">
          n of 1
        </h2>
        <p className="mt-2 text-sm text-gray-600">
          Your platform to develop target clients based on specific funding solicitations
        </p>
      </div>

      {/* Solicitation Input Form */}
      <SolicitationForm onAnalyze={handleAnalyze} loading={loading} />

      {/* Loading State */}
      {loading && (
        <div className="bg-white rounded-lg shadow-sm p-8">
          <div className="flex items-center justify-center space-x-3">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <div>
              <p className="text-lg font-medium text-gray-900">Sourcing Targeted Companies...</p>
              <p className="text-sm text-gray-500">Running confirmation analysis on all matches</p>
            </div>
          </div>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error</h3>
              <div className="mt-2 text-sm text-red-700">
                {error}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Results Display */}
      {results && !loading && <ResultsDisplay results={results} solicitationText={solicitationText} />}
    </div>
  );
};

export default Dashboard;


