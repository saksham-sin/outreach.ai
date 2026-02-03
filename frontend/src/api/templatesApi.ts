import apiClient from './client';
import type {
  EmailTemplate,
  TemplateListResponse,
  EmailTemplateCreate,
  EmailTemplateUpdate,
} from '../types';

export const templatesApi = {
  /**
   * List all templates for a campaign (ordered by step_number)
   */
  list: async (campaignId: string): Promise<TemplateListResponse> => {
    const response = await apiClient.get<TemplateListResponse>(
      `/campaigns/${campaignId}/templates`
    );
    return response.data;
  },

  /**
   * Get a single template
   */
  get: async (campaignId: string, templateId: string): Promise<EmailTemplate> => {
    const response = await apiClient.get<EmailTemplate>(
      `/campaigns/${campaignId}/templates/${templateId}`
    );
    return response.data;
  },

  /**
   * Create a template manually
   */
  create: async (
    campaignId: string,
    data: EmailTemplateCreate
  ): Promise<EmailTemplate> => {
    const response = await apiClient.post<EmailTemplate>(
      `/campaigns/${campaignId}/templates`,
      data
    );
    return response.data;
  },

  /**
   * Update a template
   */
  update: async (
    campaignId: string,
    templateId: string,
    data: EmailTemplateUpdate
  ): Promise<EmailTemplate> => {
    const response = await apiClient.patch<EmailTemplate>(
      `/campaigns/${campaignId}/templates/${templateId}`,
      data
    );
    return response.data;
  },

  /**
   * Generate a template with AI for a specific step
   */
  generate: async (
    campaignId: string,
    stepNumber: number
  ): Promise<EmailTemplate> => {
    const response = await apiClient.post<EmailTemplate>(
      `/campaigns/${campaignId}/templates/generate`,
      { step_number: stepNumber },
      { timeout: 30000 }
    );
    return response.data;
  },

  /**
   * Generate all templates with AI
   */
  generateAll: async (
    campaignId: string,
    numSteps = 3
  ): Promise<TemplateListResponse> => {
    const response = await apiClient.post<TemplateListResponse>(
      `/campaigns/${campaignId}/templates/generate-all`,
      { num_steps: numSteps },
      { timeout: 30000 }
    );
    return response.data;
  },

  /**
   * Rewrite a template with AI based on instructions
   */
  rewrite: async (
    campaignId: string,
    templateId: string,
    instructions: string
  ): Promise<EmailTemplate> => {
    const response = await apiClient.post<EmailTemplate>(
      `/campaigns/${campaignId}/templates/${templateId}/rewrite`,
      { instructions }
    );
    return response.data;
  },

  /**
   * Preview a template with real lead data and signature
   */
  preview: async (
    campaignId: string,
    templateId: string
  ): Promise<import('../types').PreviewResponse> => {
    const response = await apiClient.get<import('../types').PreviewResponse>(
      `/campaigns/${campaignId}/templates/${templateId}/preview`
    );
    return response.data;
  },
};

export default templatesApi;
