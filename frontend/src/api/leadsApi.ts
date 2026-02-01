import apiClient from './client';
import type {
  Lead,
  LeadListResponse,
  LeadCreate,
  LeadImportResult,
  CopyLeadsResponse,
  LeadStatus,
} from '../types';

export const leadsApi = {
  /**
   * List leads for a campaign
   */
  list: async (
    campaignId: string,
    options?: {
      status?: LeadStatus;
      skip?: number;
      limit?: number;
    }
  ): Promise<LeadListResponse> => {
    const response = await apiClient.get<LeadListResponse>(
      `/campaigns/${campaignId}/leads`,
      { params: options }
    );
    return response.data;
  },

  /**
   * Get a single lead
   */
  get: async (campaignId: string, leadId: string): Promise<Lead> => {
    const response = await apiClient.get<Lead>(
      `/campaigns/${campaignId}/leads/${leadId}`
    );
    return response.data;
  },

  /**
   * Create a single lead
   */
  create: async (campaignId: string, data: LeadCreate): Promise<Lead> => {
    const response = await apiClient.post<Lead>(
      `/campaigns/${campaignId}/leads`,
      data
    );
    return response.data;
  },

  /**
   * Import leads from CSV file
   */
  importCsv: async (campaignId: string, file: File): Promise<LeadImportResult> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiClient.post<LeadImportResult>(
      `/campaigns/${campaignId}/leads/import`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  },

  /**
   * Copy leads from another campaign
   */
  copyFrom: async (
    campaignId: string,
    sourceCampaignId: string
  ): Promise<CopyLeadsResponse> => {
    const response = await apiClient.post<CopyLeadsResponse>(
      `/campaigns/${campaignId}/leads/copy`,
      { source_campaign_id: sourceCampaignId }
    );
    return response.data;
  },

  /**
   * Mark a lead as replied (simulated mode)
   */
  markReplied: async (
    campaignId: string,
    leadId: string
  ): Promise<{ success: boolean; message: string }> => {
    const response = await apiClient.post<{ success: boolean; message: string }>(
      `/campaigns/${campaignId}/leads/${leadId}/mark-replied`,
      {}
    );
    return response.data;
  },
};

export default leadsApi;
