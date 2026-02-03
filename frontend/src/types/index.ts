// ===== Enums =====

export enum CampaignStatus {
  DRAFT = 'draft',
  ACTIVE = 'active',
  PAUSED = 'paused',
  COMPLETED = 'completed',
}

export enum LeadStatus {
  PENDING = 'pending',
  CONTACTED = 'contacted',
  REPLIED = 'replied',
  FAILED = 'failed',
}

export enum JobStatus {
  PENDING = 'pending',
  SENT = 'sent',
  FAILED = 'failed',
  SKIPPED = 'skipped',
}

export enum EmailTone {
  PROFESSIONAL = 'professional',
  CASUAL = 'casual',
  URGENT = 'urgent',
  FRIENDLY = 'friendly',
  DIRECT = 'direct',
}

// ===== User =====

export interface User {
  id: string;
  email: string;
  created_at: string;
  first_name?: string;
  last_name?: string;
  company_name?: string;
  job_title?: string;
  email_signature?: string;
  updated_at?: string;
  profile_completed?: boolean;
}

// ===== Auth =====

export interface AuthTokenResponse {
  access_token: string;
  token_type: string;
}

// ===== Campaign =====

export interface Campaign {
  id: string;
  user_id: string;
  name: string;
  pitch: string;
  tone: EmailTone;
  status: CampaignStatus;
  start_time: string | null;
  created_at: string;
  updated_at: string;
  tags?: string[];
}

export interface CampaignWithStats extends Campaign {
  total_leads: number;
  pending_leads: number;
  contacted_leads: number;
  replied_leads: number;
  failed_leads: number;
  pending_jobs: number;
}

export interface CampaignListResponse {
  campaigns: Campaign[];
  total: number;
}

export interface CampaignCreate {
  name: string;
  pitch: string;
  tone?: EmailTone;
}

export interface CampaignUpdate {
  name?: string;
  pitch?: string;
  tone?: EmailTone;
}

// ===== Lead =====

export interface Lead {
  id: string;
  campaign_id: string;
  email: string;
  first_name: string | null;
  company: string | null;
  status: LeadStatus;
  created_at: string;
  updated_at: string;
}

export interface LeadListResponse {
  leads: Lead[];
  total: number;
}

export interface LeadCreate {
  email: string;
  first_name?: string;
  company?: string;
}

export interface LeadImportResult {
  total_rows: number;
  imported: number;
  skipped: number;
  errors: string[];
}

export interface CopyLeadsResponse {
  copied: number;
}

// ===== Email Template =====

export interface EmailTemplate {
  id: string;
  campaign_id: string;
  step_number: number;
  subject: string;
  body: string;
  delay_days: number;
  delay_minutes: number;
  created_at: string;
  updated_at: string;
}

export interface TemplateListResponse {
  templates: EmailTemplate[];
}

export interface PreviewResponse {
  subject: string;
  body: string;
  lead_email: string;
  lead_name: string;
  lead_company: string;
}

export interface EmailTemplateCreate {
  step_number: number;
  subject: string;
  body: string;
  delay_days?: number;
  delay_minutes?: number;
}

export interface EmailTemplateUpdate {
  subject?: string;
  body?: string;
  delay_days?: number;
  delay_minutes?: number;
}

export interface GenerateTemplateRequest {
  step_number: number;
}

export interface GenerateAllTemplatesRequest {
  num_steps?: number;
}

export interface RewriteTemplateRequest {
  instructions: string;
}

// ===== Email Job =====

export interface EmailJob {
  id: string;
  campaign_id: string;
  lead_id: string;
  step_number: number;
  scheduled_at: string;
  sent_at: string | null;
  status: JobStatus;
  attempts: number;
  last_error: string | null;
  message_id: string | null;
  created_at: string;
  updated_at: string;
}

// ===== Email History =====

export interface EmailSendEvent {
  step_number: number;
  status: string;
  scheduled_at: string;
  sent_at: string | null;
  subject: string;
  attempts: number;
  last_error: string | null;
}

export interface EmailHistoryResponse {
  lead_id: string;
  email: string;
  events: EmailSendEvent[];
}

// ===== CSV Parsing =====

export interface ParsedLead {
  email: string;
  first_name?: string;
  company?: string;
  isValid: boolean;
  error?: string;
}

// ===== Wizard State =====

export interface WizardState {
  campaignId: string | null;
  name: string;
  pitch: string;
  tone: EmailTone;
  tags: string[];
  leads: ParsedLead[];
  templates: EmailTemplate[];
  currentStep: number;
  startTime: string | null; // ISO datetime for scheduled launch
}
