import apiClient from './client';
import type {
  Campaign,
  CampaignWithStats,
  CampaignListResponse,
  CampaignCreate,
  CampaignUpdate,
} from '../types';

export const campaignsApi = {
  /**
   * List all campaigns for the current user
   */
  list: async (skip = 0, limit = 50): Promise<CampaignListResponse> => {
    const response = await apiClient.get<CampaignListResponse>('/campaigns', {
      params: { skip, limit },
    });
    return response.data;
  },

  /**
   * Get a single campaign with stats
   */
  get: async (campaignId: string): Promise<CampaignWithStats> => {
    const response = await apiClient.get<CampaignWithStats>(`/campaigns/${campaignId}`);
    return response.data;
  },

  /**
   * Create a new campaign (starts in DRAFT status)
   */
  create: async (data: CampaignCreate): Promise<Campaign> => {
    const response = await apiClient.post<Campaign>('/campaigns', data);
    return response.data;
  },

  /**
   * Update a campaign (only in DRAFT status)
   */
  update: async (campaignId: string, data: CampaignUpdate): Promise<Campaign> => {
    const response = await apiClient.patch<Campaign>(`/campaigns/${campaignId}`, data);
    return response.data;
  },

  /**
   * Enhance a campaign pitch using AI
   */
  enhancePitch: async (name: string, pitch: string): Promise<{ pitch: string }> => {
    const response = await apiClient.post<{ pitch: string }>(
      '/campaigns/enhance-pitch',
      { name, pitch }
    );
    return response.data;
  },

  /**
   * Launch a campaign (DRAFT -> ACTIVE)
   */
  launch: async (campaignId: string, startTime?: string | null): Promise<Campaign> => {
    const response = await apiClient.post<Campaign>(`/campaigns/${campaignId}/launch`, {
      start_time: startTime || null,
    });
    return response.data;
  },

  /**
   * Pause a campaign (ACTIVE -> PAUSED)
   */
  pause: async (campaignId: string): Promise<Campaign> => {
    const response = await apiClient.post<Campaign>(`/campaigns/${campaignId}/pause`);
    return response.data;
  },

  /**
   * Resume a campaign (PAUSED -> ACTIVE)
   */
  resume: async (campaignId: string): Promise<Campaign> => {
    const response = await apiClient.post<Campaign>(`/campaigns/${campaignId}/resume`);
    return response.data;
  },

  /**
   * Duplicate a campaign with its templates
   */
  duplicate: async (campaignId: string, newName: string): Promise<Campaign> => {
    const response = await apiClient.post<Campaign>(`/campaigns/${campaignId}/duplicate`, {
      new_name: newName,
    });
    return response.data;
  },

  /**
   * Get the next scheduled send time
   */
  getNextSend: async (campaignId: string): Promise<{ next_send_at: string | null; job_id: string | null }> => {
    const response = await apiClient.get<{ next_send_at: string | null; job_id: string | null }>(
      `/campaigns/${campaignId}/next-send`
    );
    return response.data;
  },

  /**
   * Trigger immediate send of the next pending email
   */
  sendNow: async (campaignId: string): Promise<{ success: boolean; message: string }> => {
    const response = await apiClient.post<{ success: boolean; message: string }>(
      `/campaigns/${campaignId}/send-now`
    );
    return response.data;
  },

  /**
   * Delete a campaign (only DRAFT campaigns can be deleted)
   */
  delete: async (campaignId: string): Promise<void> => {
    await apiClient.delete(`/campaigns/${campaignId}`);
  },

  /**
   * Add a tag to a campaign
   */
  addTag: async (campaignId: string, tag: string): Promise<{ success: boolean; message: string }> => {
    const response = await apiClient.post<{ success: boolean; message: string }>(
      `/campaigns/${campaignId}/tags`,
      { tag }
    );
    return response.data;
  },

  /**
   * Remove a tag from a campaign
   */
  removeTag: async (campaignId: string, tag: string): Promise<void> => {
    await apiClient.delete(`/campaigns/${campaignId}/tags/${encodeURIComponent(tag)}`);
  },
};

export default campaignsApi;
