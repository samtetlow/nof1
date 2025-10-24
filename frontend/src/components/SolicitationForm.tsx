import React, { useState } from 'react';
import { Solicitation, apiService } from '../services/api';

interface SolicitationFormProps {
  onAnalyze: (solicitation: Solicitation, options: { enrich: boolean; topK: number; companyType: 'for-profit' | 'academic-nonprofit'; companySize: 'all' | 'small' | 'large' }) => void;
  loading: boolean;
}

const SolicitationForm: React.FC<SolicitationFormProps> = ({ onAnalyze, loading }) => {
  const [rawText, setRawText] = useState('');
  const [parsedData, setParsedData] = useState<any>(null);
  const [parsing, setParsing] = useState(false);
  const [fileName, setFileName] = useState('');
  const [dragActive, setDragActive] = useState(false);
  
  const [formData, setFormData] = useState<Solicitation>({
    title: '',
    agency: '',
    naics_codes: [],
    set_asides: [],
    security_clearance: '',
    required_capabilities: [],
    keywords: [],
    raw_text: '',
  });

  const [enrich, setEnrich] = useState(false);
  const [topK, setTopK] = useState(5);
  const [companyType, setCompanyType] = useState<'for-profit' | 'academic-nonprofit'>('for-profit');
  const [companySize, setCompanySize] = useState<'all' | 'small' | 'large'>('all');

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      await handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileInput = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      await handleFile(e.target.files[0]);
    }
  };

  const handleFile = async (file: File) => {
    setFileName(file.name);
    setParsing(true);
    
    try {
      const isPDF = file.name.toLowerCase().endsWith('.pdf');
      const isDoc = file.name.toLowerCase().endsWith('.doc') || file.name.toLowerCase().endsWith('.docx');
      
      if (isPDF || isDoc) {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await apiService.uploadAndParseFile(formData);
        const text = response.text || response.content || '';
        
        if (!text || text.length < 50) {
          alert('Could not extract text from file. Please try copying and pasting the text directly.');
          setParsing(false);
          return;
        }
        
        setRawText(text);
        const parsed = response.parsed || {};
        setParsedData(parsed);
        
        setFormData(prev => ({
          ...prev,
          raw_text: text,
          solicitation_id: parsed.solicitation_id || '',
          title: parsed.title || text.split('\n')[0].substring(0, 100) || 'Solicitation',
          agency: parsed.agency || '',
          naics_codes: parsed.naics_codes || [],
          set_asides: parsed.set_asides || [],
          security_clearance: parsed.security_clearance || '',
          required_capabilities: parsed.required_capabilities || [],
          keywords: parsed.keywords || [],
        }));
        
        setParsing(false);
      } else {
        const reader = new FileReader();
        
        reader.onload = async (event) => {
          const text = event.target?.result as string;
          setRawText(text);
          await parseAndExtract(text);
        };
        
        reader.onerror = () => {
          alert('Error reading file. Please try again.');
          setParsing(false);
        };
        
        reader.readAsText(file);
      }
    } catch (error: any) {
      console.error('Error handling file:', error);
      alert(`Error reading file: ${error.response?.data?.detail || error.message || 'Unknown error'}. Please try again or copy/paste the text directly.`);
      setParsing(false);
    }
  };

  const parseAndExtract = async (text: string) => {
    setParsing(true);
    try {
      const parsed = await apiService.parseSolicitation(text);
      setParsedData(parsed);
      
      setFormData(prev => ({
        ...prev,
        raw_text: text,
        solicitation_id: parsed.solicitation_id || '',
        title: parsed.title || text.split('\n')[0].substring(0, 100) || 'Solicitation',
        agency: parsed.agency || '',
        naics_codes: parsed.naics_codes || [],
        set_asides: parsed.set_asides || [],
        security_clearance: parsed.security_clearance || '',
        required_capabilities: parsed.required_capabilities || [],
        keywords: parsed.keywords || [],
      }));
    } catch (error) {
      console.error('Error parsing solicitation:', error);
      alert('Error parsing solicitation. You can still manually fill in the details.');
      setFormData(prev => ({
        ...prev,
        raw_text: text,
      }));
    } finally {
      setParsing(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.raw_text && !formData.title) {
      alert('Please upload a solicitation or enter a URL first');
      return;
    }
    
    onAnalyze(formData, { enrich, topK, companyType, companySize });
  };

  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Input Solicitation</h3>
      
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* File Upload */}
        <div className="border-b pb-4">
          <label className="block text-sm font-medium text-gray-700 mb-3">
            Upload Solicitation
          </label>
          
          <div 
            className={`relative flex items-center justify-center w-full ${
              dragActive ? 'bg-blue-50 border-blue-400' : 'bg-gray-50 hover:bg-gray-100'
            }`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <label className="flex flex-col items-center justify-center w-full h-48 border-2 border-gray-300 border-dashed rounded-lg cursor-pointer transition-colors">
              <div className="flex flex-col items-center justify-center pt-5 pb-6">
                <svg className="w-12 h-12 mb-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
                <p className="mb-2 text-base text-gray-600">
                  <span className="font-semibold">Drag and drop solicitation file here</span>
                </p>
                <p className="text-sm text-gray-500 mb-3">or</p>
                <div className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700">
                  Browse Files
                </div>
                <p className="text-xs text-gray-400 mt-3">Supports: TXT, PDF, DOC, DOCX (MAX. 10MB)</p>
              </div>
              <input
                type="file"
                className="hidden"
                accept=".txt,.pdf,.doc,.docx"
                onChange={handleFileInput}
              />
            </label>
          </div>
          
          {fileName && (
            <div className="mt-3 p-3 bg-blue-50 rounded-md flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <span className="text-sm text-blue-900 font-medium">{fileName}</span>
                {parsing && <span className="text-xs text-blue-600">Parsing...</span>}
              </div>
            </div>
          )}
        </div>

        {/* Parsed Results */}
        {parsedData && (
          <div className="border-b pb-4">
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Review Extracted Information
            </label>
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="flex items-start space-x-2">
                <svg className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div className="flex-1">
                  <p className="text-sm font-semibold text-green-900 mb-2">Successfully Extracted</p>
                  <div className="space-y-1 text-sm text-green-800">
                    {parsedData.title && <p><span className="font-medium">Title:</span> {parsedData.title}</p>}
                    {parsedData.agency && <p><span className="font-medium">Agency:</span> {parsedData.agency}</p>}
                  </div>
                  <p className="text-xs text-green-700 mt-2">✓ Ready to analyze!</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Analysis Options */}
        <div className="border-t pt-4">
          <h4 className="text-sm font-semibold text-gray-900 mb-4">Analysis Options</h4>
          
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={() => setEnrich(!enrich)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors flex-shrink-0 ${
                  enrich ? 'bg-blue-600' : 'bg-gray-200'
                }`}
              >
                <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${enrich ? 'translate-x-6' : 'translate-x-1'}`} />
              </button>
              <div>
                <label className="text-sm font-medium text-gray-700">Enable External Data Enrichment</label>
                <p className="text-xs text-gray-500">Fetch data from USASpending, NIH, SBIR, USPTO, and AI sources</p>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Top Companies to Analyze: {topK}
              </label>
              <input type="range" min="1" max="20" value={topK} onChange={(e) => setTopK(parseInt(e.target.value))} className="w-full" />
              <div className="flex justify-between text-xs text-gray-500">
                <span>1 (fastest)</span>
                <span>20 (most comprehensive)</span>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Company Type
              </label>
              <div className="flex space-x-2 mb-4">
                <button
                  type="button"
                  onClick={() => setCompanyType('for-profit')}
                  className={`flex-1 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                    companyType === 'for-profit'
                      ? 'bg-indigo-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  For-Profit Company
                </button>
                <button
                  type="button"
                  onClick={() => setCompanyType('academic-nonprofit')}
                  className={`flex-1 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                    companyType === 'academic-nonprofit'
                      ? 'bg-teal-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  Academic / Non-Profit
                </button>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Company Size Preference
              </label>
              <div className="flex space-x-2">
                <button
                  type="button"
                  onClick={() => setCompanySize('all')}
                  className={`flex-1 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                    companySize === 'all'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  All Sizes
                </button>
                <button
                  type="button"
                  onClick={() => setCompanySize('small')}
                  className={`flex-1 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                    companySize === 'small'
                      ? 'bg-green-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                  title="Companies with 500 employees or fewer"
                >
                  <div>Small Business</div>
                  <div className="text-xs opacity-90">≤500 employees</div>
                </button>
                <button
                  type="button"
                  onClick={() => setCompanySize('large')}
                  className={`flex-1 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                    companySize === 'large'
                      ? 'bg-purple-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                  title="Companies with more than 500 employees"
                >
                  <div>Large Business</div>
                  <div className="text-xs opacity-90">&gt;500 employees</div>
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Submit Button */}
        <div className="flex justify-end">
          <button
            type="submit"
            disabled={loading || (!formData.raw_text && !formData.title)}
            className="px-6 py-3 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            {loading ? 'Searching...' : 'Search for Targeted Companies'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default SolicitationForm;
