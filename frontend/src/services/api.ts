import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

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
  confirmation_result?: {
    is_confirmed: boolean;
    confidence_score: number;
    recommendation: string;
    chain_of_thought: string[];
    company_info?: string;
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
    const response = await api.post('/api/full-pipeline', {
      solicitation,
      company_id: companyId,
      enrich,
      top_k: topK,
      company_type: companyType,
      company_size: companySize,
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
};

export default apiService;

