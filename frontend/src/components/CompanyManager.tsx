import React, { useState, useEffect } from 'react';
import { apiService, Company } from '../services/api';

const CompanyManager: React.FC = () => {
  const [companies, setCompanies] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState<Company>({
    name: '',
    naics_codes: [],
    size: '',
    socioeconomic_status: [],
    capabilities: [],
    security_clearances: [],
    locations: [],
    keywords: [],
  });

  useEffect(() => {
    loadCompanies();
  }, []);

  const loadCompanies = async () => {
    setLoading(true);
    try{
      const data = await apiService.getCompanies();
      setCompanies(data);
    } catch (err) {
      console.error('Error loading companies:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSeedData = async () => {
    try {
      await apiService.seedCompanies();
      await loadCompanies();
      alert('Sample companies added successfully!');
    } catch (err) {
      console.error('Error seeding companies:', err);
      alert('Error adding sample companies');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiService.createCompany(formData);
      setShowForm(false);
      setFormData({
        name: '',
        naics_codes: [],
        size: '',
        socioeconomic_status: [],
        capabilities: [],
        security_clearances: [],
        locations: [],
        keywords: [],
      });
      await loadCompanies();
      alert('Company added successfully!');
    } catch (err: any) {
      console.error('Error creating company:', err);
      alert(`Error: ${err.response?.data?.detail || err.message}`);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold text-gray-900">Company Management</h2>
          <p className="mt-2 text-sm text-gray-600">
            Manage your company database for pipeline analysis
          </p>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={handleSeedData}
            className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700"
          >
            Seed Sample Data
          </button>
          <button
            onClick={() => setShowForm(!showForm)}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            {showForm ? 'Cancel' : '+ Add Company'}
          </button>
        </div>
      </div>

      {/* Add Company Form */}
      {showForm && (
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Add New Company</h3>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Company Name *
                </label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Size
                </label>
                <select
                  value={formData.size}
                  onChange={(e) => setFormData({ ...formData, size: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="">Select size...</option>
                  <option value="Small">Small</option>
                  <option value="Medium">Medium</option>
                  <option value="Large">Large</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  NAICS Codes (comma-separated)
                </label>
                <input
                  type="text"
                  placeholder="541512, 541519"
                  onChange={(e) => setFormData({ 
                    ...formData, 
                    naics_codes: e.target.value.split(',').map(s => s.trim()).filter(Boolean)
                  })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Capabilities (comma-separated)
                </label>
                <input
                  type="text"
                  placeholder="cybersecurity, cloud computing"
                  onChange={(e) => setFormData({ 
                    ...formData, 
                    capabilities: e.target.value.split(',').map(s => s.trim()).filter(Boolean)
                  })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Employees
                </label>
                <input
                  type="number"
                  value={formData.employees || ''}
                  onChange={(e) => setFormData({ ...formData, employees: parseInt(e.target.value) || undefined })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Annual Revenue
                </label>
                <input
                  type="number"
                  value={formData.annual_revenue || ''}
                  onChange={(e) => setFormData({ ...formData, annual_revenue: parseFloat(e.target.value) || undefined })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Description
              </label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            <div className="flex justify-end space-x-3">
              <button
                type="button"
                onClick={() => setShowForm(false)}
                className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Add Company
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Companies List */}
      <div className="bg-white rounded-lg shadow-sm">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Companies ({companies.length})</h3>
        </div>
        
        {loading ? (
          <div className="p-8 text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            <p className="text-gray-500 mt-2">Loading companies...</p>
          </div>
        ) : companies.length === 0 ? (
          <div className="p-8 text-center">
            <p className="text-gray-500">No companies found. Add your first company or seed sample data.</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {companies.map((company) => (
              <div key={company.company_id} className="p-6 hover:bg-gray-50">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h4 className="text-lg font-semibold text-gray-900">{company.name}</h4>
                    {company.description && (
                      <p className="text-sm text-gray-600 mt-1">{company.description}</p>
                    )}
                    
                    <div className="mt-3 flex flex-wrap gap-2">
                      {company.naics_codes && company.naics_codes.length > 0 && (
                        <div className="flex items-center space-x-1">
                          <span className="text-xs font-medium text-gray-500">NAICS:</span>
                          {company.naics_codes.map((code: string, idx: number) => (
                            <span key={idx} className="text-xs px-2 py-1 bg-blue-100 text-blue-800 rounded">
                              {code}
                            </span>
                          ))}
                        </div>
                      )}
                      
                      {company.capabilities && company.capabilities.length > 0 && (
                        <div className="flex items-center space-x-1">
                          <span className="text-xs font-medium text-gray-500">Capabilities:</span>
                          {company.capabilities.slice(0, 3).map((cap: string, idx: number) => (
                            <span key={idx} className="text-xs px-2 py-1 bg-purple-100 text-purple-800 rounded">
                              {cap}
                            </span>
                          ))}
                          {company.capabilities.length > 3 && (
                            <span className="text-xs text-gray-500">+{company.capabilities.length - 3} more</span>
                          )}
                        </div>
                      )}

                      {company.security_clearances && company.security_clearances.length > 0 && (
                        <div className="flex items-center space-x-1">
                          <span className="text-xs font-medium text-gray-500">Clearances:</span>
                          {company.security_clearances.map((clearance: string, idx: number) => (
                            <span key={idx} className="text-xs px-2 py-1 bg-green-100 text-green-800 rounded">
                              {clearance}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>

                  {company.size && (
                    <span className="ml-4 px-3 py-1 text-xs font-semibold text-gray-700 bg-gray-100 rounded-full">
                      {company.size}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default CompanyManager;


