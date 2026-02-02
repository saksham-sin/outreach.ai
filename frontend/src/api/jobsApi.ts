import apiClient from './client';

interface FailedJobInfo {
  job_id: string;
  lead_id: string;
}

interface StepSummary {
  step_number: number;
  sent: number;
  pending: number;
  failed: number;
  skipped: number;
  next_scheduled_at: string | null;
}

interface LeadJobInfo {
  job_id: string;
  step_number: number;
  status: string;
  scheduled_at: string | null;
  sent_at: string | null;
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

  /**
   * Get step-by-step job status summary for a campaign
   */
  getStepSummary: async (campaignId: string): Promise<StepSummary[]> => {
    const response = await apiClient.get<StepSummary[]>(
      `/jobs/campaigns/${campaignId}/step-summary`
    );
    return response.data;
  },

  /**
   * Get all jobs for a specific lead
   */
  getJobsForLead: async (leadId: string): Promise<LeadJobInfo[]> => {
    const response = await apiClient.get<LeadJobInfo[]>(
      `/jobs/leads/${leadId}/jobs`
    );
    return response.data;
  },
};

export type { StepSummary, LeadJobInfo };
export default jobsApi;
