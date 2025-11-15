import axios from 'axios';

// Runtime configuration - LAZY evaluation to ensure config.js has loaded
// Priority: window.APP_CONFIG (runtime) > REACT_APP_API_URL (build-time) > localhost (fallback)
const getApiUrl = (): string => {
  // 1. Check runtime config (from public/config.js) - works in production without rebuild
  if (typeof window !== 'undefined' && (window as any).APP_CONFIG?.API_URL) {
    return (window as any).APP_CONFIG.API_URL;
  }
  
  // 2. Check build-time env variable (for local development)
  if (process.env.REACT_APP_API_URL) {
    return process.env.REACT_APP_API_URL;
  }
  
  // 3. Fallback to localhost for local development
  return 'http://localhost:8000';
};

// Create axios instance with dynamic baseURL that's evaluated on each request
// Create axios instance - baseURL will be set dynamically via interceptor
const api = axios.create({
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 1200000, // 20 minute timeout for long-running operations (100 companies)
  validateStatus: (status) => status < 500, // Don't throw on 4xx errors
});

// Set baseURL dynamically via request interceptor (runs on every request)
// This ensures config.js has loaded before we use the API URL
api.interceptors.request.use((config) => {
  // Get API URL dynamically on each request (ensures config.js has loaded)
  const apiUrl = getApiUrl();
  
  // Log first request only
  if (!(api as any)._urlLogged) {
    console.log('🔍 API Base URL:', apiUrl);
    console.log('🔍 Config source:', 
      typeof window !== 'undefined' && (window as any).APP_CONFIG?.API_URL 
        ? 'runtime (config.js)' 
        : process.env.REACT_APP_API_URL 
          ? 'build-time (env var)' 
          : 'fallback (localhost)'
    );
    console.log('🔍 window.APP_CONFIG:', typeof window !== 'undefined' ? (window as any).APP_CONFIG : 'N/A (SSR)');
    (api as any)._urlLogged = true;
  }
  
  // ALWAYS set baseURL from runtime config (overrides any default)
  config.baseURL = apiUrl;
  
  return config;
});

// Retry logic for network errors
const MAX_RETRIES = 3;
const RETRY_DELAY = 1000; // 1 second

const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

async function retryRequest<T>(
  fn: () => Promise<T>,
  retries: number = MAX_RETRIES,
  delay: number = RETRY_DELAY
): Promise<T> {
  try {
    return await fn();
  } catch (error) {
    if (retries > 0 && axios.isAxiosError(error)) {
      // Retry on network errors or 5xx errors
      if (error.code === 'ECONNABORTED' || 
          error.code === 'ERR_NETWORK' ||
          (error.response && error.response.status >= 500)) {
        console.warn(`Request failed, retrying... (${MAX_RETRIES - retries + 1}/${MAX_RETRIES})`);
        await sleep(delay);
        return retryRequest(fn, retries - 1, delay * 2); // Exponential backoff
      }
    }
    throw error;
  }
}

// Types
export interface Company {
  company_id?: string;
  name: string;
  naics_codes: string[];
  size?: string;
  socioeconomic_status: string[];
  capabilities: string[];
  certifications?: string[];
  security_clearances: string[];
  locations: string[];
  employees?: number;
  annual_revenue?: number;
  description?: string;
  keywords?: string[];
  capability_statement?: string;
  website?: string;
}

export interface Solicitation {
  solicitation_id?: string;
  title?: string;
  agency?: string;
  posting_date?: string;
  due_date?: string;
  contract_type?: string;
  set_asides: string[];
  naics_codes: string[];
  place_of_performance?: string;
  estimated_value?: string;
  technical_requirements?: string[];
  evaluation_criteria?: Record<string, any>;
  keywords?: string[];
  required_capabilities?: string[];
  past_performance_requirements?: Record<string, any>;
  security_clearance?: string;
  raw_text?: string;
}

export interface MatchResult {
  company_id: string;
  company_name: string;
  website?: string;
  description?: string;
  match_score: number;
  confirmation_score: number;
  validation_score: number;
  alignment_percentage: number;
  confidence_percentage: number;
  validation_level: string;
  risk_level: string;
  recommendation: string;
  strengths: string[];
  weaknesses: string[];
  opportunities: string[];
  risks: string[];
  recommended_actions: string[];
  decision_rationale: string;
  confirmation_status: string;
  enrichment_sources: string[];
  data_quality_score: number;
  capabilities?: string[];
  website_validation?: {
    available: boolean;
    website_url: string;
    validation_endpoint: string;
    pre_validated?: boolean;
    validation_score?: number;
    confirmed_capabilities?: string[];
    website_capabilities?: string[];
    gaps_count?: number;
    partnering_opportunities_count?: number;
  };
  confirmation_result?: {
    is_confirmed: boolean;
    confidence_score: number;
    recommendation: string;
    alignment_summary?: string;
    chain_of_thought: string[];
    company_info?: string;
    findings?: {
      company_info?: string;
      capability_match?: string;
      experience_assessment?: string;
      strengths?: string[];
      risk_factors?: string[];
    };
  };
  score_components: Array<{
    component: string;
    score: number;
    weight: number;
    rationale: string;
  }>;
}

export interface PipelineResponse {
  solicitation_summary: {
    title?: string;
    agency?: string;
    naics_codes: string[];
    set_asides: string[];
    security_clearance?: string;
  };
  companies_evaluated: number;
  top_matches_analyzed: number;
  results: MatchResult[];
  pagination?: {
    total_matches_above_50: number;
    current_batch: number;
    has_more: boolean;
    remaining: number;
    next_index: number;
  };
  shortage_notice?: {
    requested: number;
    delivered: number;
    filtered_out: number;
    message: string;
  };
  unconfirmed_companies?: any[];  // For pagination
  themes?: any;
  solicitation_title?: string;
}

// API Methods
export const apiService = {
  // Companies
  async getCompanies(query?: string): Promise<any> {
    const response = await api.get('/api/companies/search', {
      params: query ? { q: query } : {},
    });
    return response.data;
  },

  async getCompany(id: string): Promise<Company> {
    const response = await api.get(`/api/companies/${id}`);
    return response.data;
  },

  async createCompany(company: Company): Promise<Company> {
    const response = await api.post('/api/companies', company);
    return response.data;
  },

  // Solicitations
  async parseSolicitation(rawText: string): Promise<any> {
    const response = await api.post('/api/solicitations/parse', { raw_text: rawText });
    return response.data;
  },

  async uploadAndParseFile(formData: FormData): Promise<any> {
    const response = await api.post('/api/solicitations/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  async fetchSolicitationFromUrl(url: string): Promise<any> {
    const response = await api.post('/api/solicitations/fetch-url', { url });
    return response.data;
  },

  async createSolicitation(solicitation: Solicitation): Promise<any> {
    const response = await api.post('/api/solicitations', solicitation);
    return response.data;
  },

  // Basic Matching
  async matchCompanies(solicitation: Solicitation, topK: number = 25): Promise<any[]> {
    const response = await api.post('/api/match', {
      solicitation,
      top_k: topK,
    });
    return response.data;
  },

  // Enhanced Pipeline
  async runFullPipeline(
    solicitation: Solicitation,
    companyId?: string,
    enrich: boolean = false,
    topK: number = 5,
    companyType: 'for-profit' | 'academic-nonprofit' = 'for-profit',
    companySize: 'all' | 'small' | 'large' = 'all'
  ): Promise<PipelineResponse> {
    return retryRequest(async () => {
      // Log request parameters for debugging
      console.log('🔍 API Request - runFullPipeline:', {
        top_k: topK,
        company_type: companyType,
        company_size: companySize,
        enrich,
        api_url: api.defaults.baseURL || 'not set'
      });
      
      const response = await api.post('/api/full-pipeline', {
        solicitation,
        company_id: companyId,
        enrich,
        top_k: topK,
        company_type: companyType,
        company_size: companySize,
      });
      
      // Log response for debugging
      console.log('🔍 API Response - runFullPipeline:', {
        status: response.status,
        companies_returned: response.data?.results?.length || 0,
        requested: topK,
        companies_evaluated: response.data?.companies_evaluated || 0,
        top_matches_analyzed: response.data?.top_matches_analyzed || 0
      });
      
      if (response.status >= 400) {
        throw new Error(response.data?.detail || 'Pipeline request failed');
      }
      
      return response.data;
    });
  },

  async loadNextBatch(
    companies: any[],
    themes: any,
    solicitationTitle: string,
    startIndex: number
  ): Promise<any> {
    const response = await api.post('/api/load-next-batch', {
      companies,
      themes,
      solicitation_title: solicitationTitle,
      start_index: startIndex
    });
    return response.data;
  },

  async matchWithConfirmation(
    solicitation: Solicitation,
    companyId?: string,
    enrich: boolean = true,
    topK: number = 10
  ): Promise<any> {
    const response = await api.post('/api/match-with-confirmation', {
      solicitation,
      company_id: companyId,
      enrich,
      top_k: topK,
    });
    return response.data;
  },

  async enrichCompany(companyId: string, sources?: string[]): Promise<any> {
    const response = await api.post('/api/enrich-company', {
      company_id: companyId,
      sources,
    });
    return response.data;
  },

  // Seed data
  async seedCompanies(): Promise<any> {
    const response = await api.post('/seed');
    return response.data;
  },

  // Weights
  async getWeights(): Promise<Record<string, number>> {
    const response = await api.get('/api/weights');
    return response.data;
  },

  async updateWeights(weights: Record<string, number>): Promise<any> {
    const response = await api.put('/api/weights', weights);
    return response.data;
  },

  // Selection Confirmation
  async confirmSelection(
    companyName: string,
    companyId: string,
    solicitationText: string,
    solicitationTitle: string
  ): Promise<any> {
    const response = await api.post('/api/confirm-selection', {
      company_name: companyName,
      company_id: companyId,
      solicitation_text: solicitationText,
      solicitation_title: solicitationTitle,
    });
    return response.data;
  },

  // Website Validation
  async validateWebsite(params: {
    company_name: string;
    company_website: string;
    company_capabilities: string[];
    solicitation_title: string;
    required_capabilities: string[];
  }): Promise<any> {
    const response = await api.post('/api/validate-website', params);
    return response.data;
  },
};

export default apiService;

