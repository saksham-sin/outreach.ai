import { useState, useRef, useEffect } from 'react';
import Papa from 'papaparse';
import { useWizard } from './CampaignWizardContext';
import { campaignsApi, leadsApi } from '../api';
import { Button } from '../components';
import type { ParsedLead, Campaign } from '../types';
import toast from 'react-hot-toast';

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

type ImportMethod = 'csv' | 'copy' | 'manual';

export function WizardStep2() {
  const { state, setLeads, nextStep, prevStep } = useWizard();
  const [importMethod, setImportMethod] = useState<ImportMethod>('csv');
  const [isUploading, setIsUploading] = useState(false);
  const [isCopying, setIsCopying] = useState(false);
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [selectedCampaignId, setSelectedCampaignId] = useState<string>('');
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [manualLead, setManualLead] = useState({ email: '', first_name: '', company: '' });
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Fetch existing campaigns for copy option
  useEffect(() => {
    const fetchCampaigns = async () => {
      try {
        const response = await campaignsApi.list();
        // Filter out current campaign
        setCampaigns(
          response.campaigns.filter((c) => c.id !== state.campaignId)
        );
      } catch {
        // Ignore error, optional feature
      }
    };
    fetchCampaigns();
  }, [state.campaignId]);

  const parseCSV = (file: File): Promise<ParsedLead[]> => {
    return new Promise((resolve, reject) => {
      Papa.parse(file, {
        header: true,
        skipEmptyLines: true,
        transformHeader: (header) => header.toLowerCase().trim(),
        complete: (results) => {
          const leads: ParsedLead[] = [];

          for (const row of results.data as Record<string, string>[]) {
            const email = row['email']?.trim() || '';
            const firstName = row['first_name']?.trim() || row['firstname']?.trim() || '';
            const company = row['company']?.trim() || '';

            const lead: ParsedLead = {
              email,
              first_name: firstName || undefined,
              company: company || undefined,
              isValid: true,
            };

            // Validate email
            if (!email) {
              lead.isValid = false;
              lead.error = 'Email is required';
            } else if (!EMAIL_REGEX.test(email)) {
              lead.isValid = false;
              lead.error = 'Invalid email format';
            }

            leads.push(lead);
          }

          resolve(leads);
        },
        error: (error) => {
          reject(new Error(`Failed to parse CSV: ${error.message}`));
        },
      });
    });
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.name.endsWith('.csv')) {
      toast.error('Please select a CSV file');
      return;
    }

    setCsvFile(file);

    try {
      const parsedLeads = await parseCSV(file);
      setLeads(parsedLeads);

      const validCount = parsedLeads.filter((l) => l.isValid).length;
      const invalidCount = parsedLeads.length - validCount;

      if (invalidCount > 0) {
        toast.error(`${invalidCount} leads have errors and will be skipped`);
      } else {
        toast.success(`Parsed ${validCount} leads`);
      }
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Failed to parse CSV');
      setCsvFile(null);
      setLeads([]);
    }
  };

  const handleUploadAndContinue = async () => {
    if (!state.campaignId) return;

    // Only upload CSV if we're using CSV import method and have a file
    if (importMethod === 'csv' && csvFile) {
      setIsUploading(true);

      try {
        const result = await leadsApi.importCsv(state.campaignId, csvFile);
        toast.success(`Imported ${result.imported} leads`);

        if (result.errors.length > 0) {
          console.warn('Import errors:', result.errors);
        }

        nextStep();
      } catch {
        // Error handled by API client
      } finally {
        setIsUploading(false);
      }
    } else if (importMethod === 'manual') {
      // For manual method, save all valid leads to database
      setIsUploading(true);

      try {
        const validLeads = state.leads.filter((l) => l.isValid);
        let savedCount = 0;

        for (const lead of validLeads) {
          try {
            await leadsApi.create(state.campaignId, {
              email: lead.email,
              first_name: lead.first_name,
              company: lead.company,
            });
            savedCount++;
          } catch (err) {
            console.warn(`Failed to save lead ${lead.email}:`, err);
          }
        }

        if (savedCount > 0) {
          toast.success(`Saved ${savedCount} lead${savedCount !== 1 ? 's' : ''}`);
        }
        nextStep();
      } catch {
        // Error handled by API client
        toast.error('Failed to save leads');
      } finally {
        setIsUploading(false);
      }
    } else if (importMethod === 'copy') {
      // For copy method, leads are already in state, just proceed
      nextStep();
    } else if (importMethod === 'csv') {
      toast.error('Please select a CSV file');
    }
  };

  const handleCopyLeads = async () => {
    if (!state.campaignId || !selectedCampaignId) return;

    setIsCopying(true);

    try {
      const result = await leadsApi.copyFrom(state.campaignId, selectedCampaignId);
      toast.success(`Copied ${result.copied} leads`);
      nextStep();
    } catch {
      // Error handled by API client
    } finally {
      setIsCopying(false);
    }
  };

  const handleAddManualLead = () => {
    const { email, first_name, company } = manualLead;
    
    if (!email.trim()) {
      toast.error('Email is required');
      return;
    }

    const lead: ParsedLead = {
      email: email.trim(),
      first_name: first_name.trim() || undefined,
      company: company.trim() || undefined,
      isValid: EMAIL_REGEX.test(email.trim()),
      error: EMAIL_REGEX.test(email.trim()) ? undefined : 'Invalid email format',
    };

    setLeads([...state.leads, lead]);
    setManualLead({ email: '', first_name: '', company: '' });
    toast.success('Lead added');
  };

  const handleRemoveLead = (index: number) => {
    setLeads(state.leads.filter((_, i) => i !== index));
    toast.success('Lead removed');
  };

  const handleAddLeadToPreview = () => {
    const email = prompt('Enter email address:');
    if (!email) return;

    const firstName = prompt('Enter first name (optional):') || '';
    const company = prompt('Enter company (optional):') || '';

    const lead: ParsedLead = {
      email: email.trim(),
      first_name: firstName.trim() || undefined,
      company: company.trim() || undefined,
      isValid: EMAIL_REGEX.test(email.trim()),
      error: EMAIL_REGEX.test(email.trim()) ? undefined : 'Invalid email format',
    };

    setLeads([...state.leads, lead]);
    toast.success('Lead added to preview');
  };

  const validLeads = state.leads.filter((l) => l.isValid);
  const invalidLeads = state.leads.filter((l) => !l.isValid);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-gray-900">Import Leads</h2>
        <p className="mt-1 text-sm text-gray-500">
          Choose how you want to add leads to your campaign.
        </p>
      </div>

      {/* Import Method Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { key: 'csv' as const, label: 'CSV Upload', icon: '📄' },
            { key: 'copy' as const, label: 'Copy from Campaign', icon: '📋' },
            { key: 'manual' as const, label: 'Add Manually', icon: '✍️' },
          ].map((method) => (
            <button
              key={method.key}
              onClick={() => setImportMethod(method.key)}
              className={`
                whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors flex items-center gap-2
                ${
                  importMethod === method.key
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }
              `}
            >
              <span>{method.icon}</span>
              {method.label}
            </button>
          ))}
        </nav>
      </div>

      {/* CSV Upload Method */}
      {importMethod === 'csv' && (
        <div className="space-y-4">
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-6">
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv"
              onChange={handleFileSelect}
              className="hidden"
            />

            <div className="text-center">
              <svg
                className="mx-auto h-12 w-12 text-gray-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                />
              </svg>

              <div className="mt-4">
                <Button
                  variant="secondary"
                  onClick={() => fileInputRef.current?.click()}
                >
                  Select CSV File
                </Button>
              </div>

              {csvFile && (
                <p className="mt-2 text-sm text-gray-600">
                  Selected: <strong>{csvFile.name}</strong>
                </p>
              )}

              <p className="mt-2 text-xs text-gray-500">
                CSV must include <code className="bg-gray-100 px-1">email</code> column.
                Optional: <code className="bg-gray-100 px-1">first_name</code>,{' '}
                <code className="bg-gray-100 px-1">company</code>
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Copy from Campaign Method */}
      {importMethod === 'copy' && (
        <div className="space-y-3">
          {campaigns.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <p>No other campaigns available to copy from.</p>
            </div>
          ) : (
            <>
              <label className="block text-sm font-medium text-gray-700">
                Select a campaign to copy leads from
              </label>
              <div className="flex gap-3">
                <select
                  value={selectedCampaignId}
                  onChange={(e) => setSelectedCampaignId(e.target.value)}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Choose a campaign...</option>
                  {campaigns.map((campaign) => (
                    <option key={campaign.id} value={campaign.id}>
                      {campaign.name}
                    </option>
                  ))}
                </select>
                <Button
                  onClick={handleCopyLeads}
                  disabled={!selectedCampaignId}
                  isLoading={isCopying}
                >
                  Copy Leads
                </Button>
              </div>
            </>
          )}
        </div>
      )}

      {/* Manual Add Method */}
      {importMethod === 'manual' && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Email <span className="text-red-500">*</span>
              </label>
              <input
                type="email"
                value={manualLead.email}
                onChange={(e) => setManualLead({ ...manualLead, email: e.target.value })}
                placeholder="john@example.com"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                First Name
              </label>
              <input
                type="text"
                value={manualLead.first_name}
                onChange={(e) => setManualLead({ ...manualLead, first_name: e.target.value })}
                placeholder="John"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Company
              </label>
              <input
                type="text"
                value={manualLead.company}
                onChange={(e) => setManualLead({ ...manualLead, company: e.target.value })}
                placeholder="Acme Inc"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
          <Button onClick={handleAddManualLead} variant="secondary">
            Add Lead
          </Button>
        </div>
      )}

      {/* Preview Table */}
      {state.leads.length > 0 && (
        <div className="border rounded-lg overflow-hidden">
          <div className="bg-gray-50 px-4 py-3 border-b flex items-center justify-between">
            <span className="text-sm font-medium text-gray-700">
              Preview ({validLeads.length} valid, {invalidLeads.length} invalid)
            </span>
            {importMethod === 'csv' && (
              <button
                onClick={handleAddLeadToPreview}
                className="flex items-center gap-1 text-sm text-blue-600 hover:text-blue-700 font-medium"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                Add Lead
              </button>
            )}
          </div>
          <div className="max-h-96 overflow-y-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50 sticky top-0">
                <tr>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                    Email
                  </th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                    Name
                  </th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                    Company
                  </th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                    Status
                  </th>
                  <th className="px-4 py-2 text-center text-xs font-medium text-gray-500 uppercase">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {state.leads.map((lead, index) => (
                  <tr
                    key={index}
                    className={lead.isValid ? 'bg-white' : 'bg-red-50'}
                  >
                    <td className="px-4 py-2 text-sm text-gray-900">
                      {lead.email || '-'}
                    </td>
                    <td className="px-4 py-2 text-sm text-gray-500">
                      {lead.first_name || '-'}
                    </td>
                    <td className="px-4 py-2 text-sm text-gray-500">
                      {lead.company || '-'}
                    </td>
                    <td className="px-4 py-2 text-sm">
                      {lead.isValid ? (
                        <span className="text-green-600 font-medium">✓ Valid</span>
                      ) : (
                        <span className="text-red-600">{lead.error}</span>
                      )}
                    </td>
                    <td className="px-4 py-2 text-center">
                      <button
                        onClick={() => handleRemoveLead(index)}
                        className="text-red-600 hover:text-red-700 p-1"
                        title="Remove lead"
                      >
                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Navigation */}
      <div className="flex justify-between pt-4 border-t">
        <Button variant="ghost" onClick={prevStep}>
          Back
        </Button>
        <Button
          onClick={handleUploadAndContinue}
          disabled={validLeads.length === 0}
          isLoading={isUploading}
        >
          Next: Email Templates
        </Button>
      </div>
    </div>
  );
}

export default WizardStep2;
