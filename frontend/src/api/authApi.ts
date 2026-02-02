import apiClient from './client';
import type { User, AuthTokenResponse } from '../types';

export interface UserProfileUpdate {
  first_name?: string;
  last_name?: string;
  company_name?: string;
  job_title?: string;
  email_signature?: string;
}

export interface GenerateSignatureResponse {
  signature_html: string;
}

export const authApi = {
  /**
   * Request a magic link to be sent to the email
   */
  requestMagicLink: async (email: string): Promise<{ message: string }> => {
    const response = await apiClient.post<{ message: string }>('/auth/magic-link', { email });
    return response.data;
  },

  /**
   * Verify the magic link token and get access token
   */
  verifyToken: async (token: string): Promise<AuthTokenResponse> => {
    const response = await apiClient.post<AuthTokenResponse>('/auth/verify', { token });
    return response.data;
  },

  /**
   * Get the current authenticated user
   */
  getCurrentUser: async (): Promise<User> => {
    const response = await apiClient.get<User>('/auth/me');
    return response.data;
  },

  /**
   * Update user profile
   */
  updateProfile: async (data: UserProfileUpdate): Promise<User> => {
    const response = await apiClient.patch<User>('/auth/me', data);
    return response.data;
  },

  /**
   * Generate AI-powered email signature
   */
  generateSignature: async (): Promise<GenerateSignatureResponse> => {
    const response = await apiClient.post<GenerateSignatureResponse>('/auth/generate-signature');
    return response.data;
  },
};

export default authApi;
