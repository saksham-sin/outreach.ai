import apiClient from './client';

interface FailedJobInfo {
  job_id: string;
  lead_id: string;
}

export const jobsApi = {
  /**
   * Retry a single failed job
   */
  retry: async (jobId: string): Promise<{ success: boolean; message: string }> => {
    const response = await apiClient.post<{ success: boolean; message: string }>(
      `/jobs/${jobId}/retry`
    );
    return response.data;
  },

  /**
   * Retry all failed jobs for a campaign
   */
  retryAllFailed: async (
    campaignId: string
  ): Promise<{ success: boolean; message: string }> => {
    const response = await apiClient.post<{ success: boolean; message: string }>(
      `/jobs/campaigns/${campaignId}/retry-all`
    );
    return response.data;
  },

  /**
   * Get all failed jobs for a campaign
   */
  getFailedJobs: async (campaignId: string): Promise<FailedJobInfo[]> => {
    const response = await apiClient.get<FailedJobInfo[]>(
      `/jobs/campaigns/${campaignId}/failed`
    );
    return response.data;
  },
};

export default jobsApi;
