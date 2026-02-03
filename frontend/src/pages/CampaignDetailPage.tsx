import { useState, useEffect, useCallback, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { campaignsApi, leadsApi, jobsApi, templatesApi } from '../api';
import type { StepSummary, LeadJobInfo } from '../api/jobsApi';
import { useInterval } from '../hooks';
import {
  Button,
  Spinner,
  StatusBadge,
  Header,
  Modal,
  ConfirmModal,
  EmptyState,
  EmailPreviewModal,
} from '../components';
import { CampaignStatus, LeadStatus } from '../types';
import type { CampaignWithStats, Lead, EmailTemplate } from '../types';
import toast from 'react-hot-toast';

// Read from environment, default to 30 seconds
const POLL_INTERVAL = parseInt(import.meta.env.VITE_POLL_INTERVAL_MS || '30000', 10);

export function CampaignDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [campaign, setCampaign] = useState<CampaignWithStats | null>(null);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [templates, setTemplates] = useState<EmailTemplate[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);
  const [showPauseConfirm, setShowPauseConfirm] = useState(false);
  const [showResumeConfirm, setShowResumeConfirm] = useState(false);
  const [isActionLoading, setIsActionLoading] = useState(false);
  const [retryingAll, setRetryingAll] = useState(false);
  const [retryingJobId, setRetryingJobId] = useState<string | null>(null);
  const [leadJobs, setLeadJobs] = useState<Record<string, any>>({});
  const [stepSummaries, setStepSummaries] = useState<StepSummary[]>([]);
  const [now, setNow] = useState(Date.now());
  const [showMarkRepliedConfirm, setShowMarkRepliedConfirm] = useState(false);
  const [isMarkingReplied, setIsMarkingReplied] = useState(false);
  const [previewModal, setPreviewModal] = useState({ open: false, templateId: '', stepNumber: 1 });
  const [selectedLeadJobs, setSelectedLeadJobs] = useState<LeadJobInfo[]>([]);
  const [isLoadingLeadJobs, setIsLoadingLeadJobs] = useState(false);
  const replyMode = (import.meta.env.VITE_REPLY_MODE || 'SIMULATED').toUpperCase();
  const enableSimulatedReply = replyMode === 'SIMULATED';

  const getDelayMinutes = (delayMinutes: number, delayDays: number) => {
    if (delayMinutes && delayMinutes > 0) return delayMinutes;
    return delayDays * 1440;
  };

  const formatDelay = (totalMinutes: number) => {
    if (totalMinutes <= 0) return 'Same time';
    const days = Math.floor(totalMinutes / 1440);
    const hours = Math.floor((totalMinutes % 1440) / 60);
    const minutes = totalMinutes % 60;
    const parts = [
      days > 0 ? `${days}d` : '',
      hours > 0 ? `${hours}h` : '',
      minutes > 0 ? `${minutes}m` : '',
    ].filter(Boolean);
    return parts.join(' ');
  };

  const fetchData = useCallback(async () => {
    if (!id) return;

    try {
      const [campaignData, leadsData, failedJobs, templatesData, stepSummaryData] = await Promise.all([
        campaignsApi.get(id),
        leadsApi.list(id, { limit: 500 }),
        jobsApi.getFailedJobs(id),
        templatesApi.list(id),
        jobsApi.getStepSummary(id),
      ]);
      setCampaign(campaignData);
      setLeads(leadsData.leads);
      setTemplates(templatesData.templates);
      setStepSummaries(stepSummaryData);
      
      // Build mapping of lead_id -> job_id for failed jobs
      const jobMapping: Record<string, string> = {};
      failedJobs.forEach(job => {
        jobMapping[job.lead_id] = job.job_id;
      });
      setLeadJobs(jobMapping);
    } catch {
      // Error handled by API client
    } finally {
      setIsLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Fetch jobs when a lead is selected
  useEffect(() => {
    if (selectedLead && id) {
      setIsLoadingLeadJobs(true);
      leadsApi.getEmailHistory(id, selectedLead.id)
        .then((history) => {
          // Transform email history to LeadJobInfo format for compatibility
          const jobs = history.events.map((event) => ({
            job_id: `${selectedLead.id}-step${event.step_number}`,
            step_number: event.step_number,
            status: event.status,
            scheduled_at: event.scheduled_at,
            sent_at: event.sent_at,
          }));
          setSelectedLeadJobs(jobs);
        })
        .catch(() => setSelectedLeadJobs([]))
        .finally(() => setIsLoadingLeadJobs(false));
    } else {
      setSelectedLeadJobs([]);
    }
  }, [selectedLead?.id, id]);

  // Auto-poll for active campaigns
  useInterval(
    () => {
      if (campaign?.status === CampaignStatus.ACTIVE) {
        fetchData();
      }
    },
    campaign?.status === CampaignStatus.ACTIVE ? POLL_INTERVAL : null
  );

  // Tick countdown timers
  useInterval(
    () => {
      setNow(Date.now());
    },
    campaign ? 1000 : null
  );

  const sortedTemplates = useMemo(
    () => [...templates].sort((a, b) => a.step_number - b.step_number),
    [templates]
  );

  // Helper to get step summary by step number
  const getStepSummary = useCallback(
    (stepNumber: number): StepSummary | undefined =>
      stepSummaries.find((s) => s.step_number === stepNumber),
    [stepSummaries]
  );

  const formatCountdown = (msRemaining: number) => {
    if (msRemaining <= 0) return 'Sent';
    const totalSeconds = Math.floor(msRemaining / 1000);
    const days = Math.floor(totalSeconds / 86400);
    const hours = Math.floor((totalSeconds % 86400) / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = totalSeconds % 60;
    const parts = [
      days > 0 ? `${days}d` : '',
      hours > 0 ? `${hours}h` : '',
      minutes > 0 ? `${minutes}m` : '',
      days === 0 && hours === 0 ? `${seconds}s` : '',
    ].filter(Boolean);
    return parts.join(' ');
  };

  const handlePause = async () => {
    if (!id) return;

    setIsActionLoading(true);
    try {
      const updated = await campaignsApi.pause(id);
      setCampaign((prev) => (prev ? { ...prev, ...updated } : null));
      toast.success('Campaign paused');
      setShowPauseConfirm(false);
    } catch {
      // Error handled by API client
    } finally {
      setIsActionLoading(false);
    }
  };

  const handleResume = async () => {
    if (!id) return;

    setIsActionLoading(true);
    try {
      const updated = await campaignsApi.resume(id);
      setCampaign((prev) => (prev ? { ...prev, ...updated } : null));
      toast.success('Campaign resumed');
      setShowResumeConfirm(false);
    } catch {
      // Error handled by API client
    } finally {
      setIsActionLoading(false);
    }
  };

  const handleRetryAll = async () => {
    if (!id) return;

    setRetryingAll(true);
    try {
      await jobsApi.retryAllFailed(id);
      toast.success('All failed emails will be retried shortly');
      // Refresh campaign data to update counts
      await fetchData();
    } catch {
      // Error handled by API client
    } finally {
      setRetryingAll(false);
    }
  };

  const handleRetryJob = async (jobId: string) => {
    setRetryingJobId(jobId);
    try {
      await jobsApi.retry(jobId);
      toast.success('Email will be retried shortly');
      // Refresh campaign data to update the lead status
      await fetchData();
    } catch {
      // Error handled by API client
    } finally {
      setRetryingJobId(null);
    }
  };

  const handleMarkReplied = async () => {
    if (!id || !selectedLead) return;

    setIsMarkingReplied(true);
    try {
      await leadsApi.markReplied(id, selectedLead.id);
      toast.success(`${selectedLead.email} marked as replied`);
      // Update the selected lead and refresh data
      setSelectedLead({ ...selectedLead, status: LeadStatus.REPLIED });
      await fetchData();
      setShowMarkRepliedConfirm(false);
    } catch {
      // Error handled by API client
    } finally {
      setIsMarkingReplied(false);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <div className="flex justify-center py-12">
          <Spinner size="lg" />
        </div>
      </div>
    );
  }

  if (!campaign) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <EmptyState
            title="Campaign not found"
            description="The campaign you're looking for doesn't exist."
            action={
              <Button onClick={() => navigate('/')}>Back to Dashboard</Button>
            }
          />
        </div>
      </div>
    );
  }

  const canPause = campaign.status === CampaignStatus.ACTIVE;
  const canResume = campaign.status === CampaignStatus.PAUSED;
  const canEdit = campaign.status === CampaignStatus.DRAFT;

  const getStatusExplanation = () => {
    switch (campaign.status) {
      case CampaignStatus.DRAFT:
        return 'This campaign is in draft mode. You can edit it before launching.';
      case CampaignStatus.ACTIVE:
        return 'This campaign is actively sending emails according to your schedule.';
      case CampaignStatus.PAUSED:
        return 'This campaign is paused. Resume it to continue sending emails.';
      case CampaignStatus.COMPLETED:
        return 'This campaign has finished sending all emails to all leads.';
      default:
        return '';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="flex justify-between items-start mb-8">
          <div>
            <button
              onClick={() => navigate('/')}
              className="text-sm text-gray-500 hover:text-gray-700 mb-2 flex items-center"
            >
              <svg
                className="w-4 h-4 mr-1"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 19l-7-7 7-7"
                />
              </svg>
              Back to campaigns
            </button>
            <h1 className="text-2xl font-bold text-gray-900">{campaign.name}</h1>
            <div className="mt-2 flex items-center gap-4">
              <StatusBadge status={campaign.status} />
              {campaign.status === CampaignStatus.ACTIVE && (
                <span className="text-sm text-gray-500">
                  Auto-refreshing every 30s
                </span>
              )}
            </div>
            <p className="mt-2 text-sm text-gray-600">{getStatusExplanation()}</p>
          </div>

          <div className="flex gap-3">
            {canEdit && (
              <Button
                variant="secondary"
                onClick={() => navigate(`/campaigns/${id}/edit`)}
              >
                Edit Campaign
              </Button>
            )}
            {campaign.failed_leads > 0 && (
              <Button
                variant="secondary"
                onClick={handleRetryAll}
                disabled={retryingAll}
              >
                {retryingAll ? 'Retrying...' : 'Retry All Failed'}
              </Button>
            )}
            {canPause && (
              <Button
                variant="secondary"
                onClick={() => setShowPauseConfirm(true)}
              >
                Pause
              </Button>
            )}
            {canResume && (
              <Button onClick={() => setShowResumeConfirm(true)}>Resume</Button>
            )}
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
          <StatCard label="Total Leads" value={campaign.total_leads} />
          <StatCard label="Pending" value={campaign.pending_leads} color="gray" />
          <StatCard
            label="Contacted"
            value={campaign.contacted_leads}
            color="blue"
          />
          <StatCard
            label="Replied"
            value={campaign.replied_leads}
            color="green"
          />
          <StatCard label="Failed" value={campaign.failed_leads} color="red" />
        </div>

        {/* Email Sequence Preview */}
        {sortedTemplates.length > 0 && (
          <div className="bg-white rounded-lg shadow-sm p-6 mb-8">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Email Sequence</h2>
            <div className="space-y-4">
              {sortedTemplates.map((template) => {
                const waitMinutes = getDelayMinutes(template.delay_minutes, template.delay_days);
                const stepSummary = getStepSummary(template.step_number);
                
                // Determine step status based on actual job data
                const hasSentJobs = stepSummary && stepSummary.sent > 0;
                const hasPendingJobs = stepSummary && stepSummary.pending > 0;
                const nextScheduledAt = stepSummary?.next_scheduled_at;
                
                // Show timer if: active campaign, has pending jobs, and has scheduled time
                const showNextTimer =
                  campaign &&
                  campaign.status === CampaignStatus.ACTIVE &&
                  hasPendingJobs &&
                  nextScheduledAt;
                
                // Calculate countdown from actual scheduled time
                const targetTime = nextScheduledAt ? new Date(nextScheduledAt).getTime() : null;
                const countdown = targetTime ? formatCountdown(targetTime - now) : null;
                
                // Determine badge to show
                let statusBadge = null;
                if (hasSentJobs && !hasPendingJobs) {
                  // All jobs sent
                  statusBadge = (
                    <span className="text-xs text-green-700 bg-green-50 border border-green-200 rounded-full px-2 py-0.5">
                      ✓ Sent
                    </span>
                  );
                } else if (showNextTimer && countdown) {
                  statusBadge = (
                    <span className="text-xs text-blue-700 bg-blue-50 border border-blue-200 rounded-full px-2 py-0.5">
                      ⏱ {countdown}
                    </span>
                  );
                }

                return (
                <div
                  key={template.id}
                  onClick={() => setPreviewModal({ open: true, templateId: template.id, stepNumber: template.step_number })}
                  className="flex items-start gap-4 pb-4 border-b last:border-b-0 last:pb-0 cursor-pointer hover:bg-gray-50 p-2 -m-2 rounded transition"
                >
                  <div className="flex-shrink-0 w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                    <span className="text-sm font-semibold text-blue-700">{template.step_number}</span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="text-sm font-medium text-gray-900 truncate">
                        {template.subject}
                      </h3>
                      {waitMinutes > 0 && (
                        <span className="text-xs text-gray-500">
                          (Wait {formatDelay(
                            waitMinutes
                          )})
                        </span>
                      )}
                      {statusBadge}
                    </div>
                    <p className="text-xs text-gray-500 line-clamp-2">
                      {template.body.replace(/<[^>]*>/g, '').substring(0, 150)}...
                    </p>
                  </div>
                </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Leads Table */}
        <div className="bg-white rounded-lg shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b">
            <h2 className="text-lg font-semibold text-gray-900">Leads</h2>
          </div>

          {leads.length === 0 ? (
            <EmptyState
              title="No leads"
              description="This campaign has no leads yet."
            />
          ) : (
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Email
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Company
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {leads.map((lead) => (
                  <tr key={lead.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {lead.email}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {lead.first_name || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {lead.company || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <StatusBadge status={lead.status} size="sm" />
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                      <div className="flex justify-end gap-3">
                        <button
                          className="text-blue-600 hover:text-blue-700"
                          onClick={() => setSelectedLead(lead)}
                        >
                          Details
                        </button>
                        {lead.status === LeadStatus.FAILED && leadJobs[lead.id] && (
                          <button
                            className="text-orange-600 hover:text-orange-700 disabled:opacity-50"
                            onClick={() => handleRetryJob(leadJobs[lead.id])}
                            disabled={retryingJobId === leadJobs[lead.id]}
                          >
                            {retryingJobId === leadJobs[lead.id] ? 'Retrying...' : 'Retry'}
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </main>

      {/* Lead Detail Modal */}
      <Modal
        isOpen={!!selectedLead}
        onClose={() => setSelectedLead(null)}
        title="Lead Details"
      >
        {selectedLead && (
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium text-gray-500">Email</label>
              <p className="text-gray-900">{selectedLead.email}</p>
            </div>
            {selectedLead.first_name && (
              <div>
                <label className="text-sm font-medium text-gray-500">Name</label>
                <p className="text-gray-900">{selectedLead.first_name}</p>
              </div>
            )}
            {selectedLead.company && (
              <div>
                <label className="text-sm font-medium text-gray-500">
                  Company
                </label>
                <p className="text-gray-900">{selectedLead.company}</p>
              </div>
            )}
            <div>
              <label className="text-sm font-medium text-gray-500">Status</label>
              <div className="mt-1">
                <StatusBadge status={selectedLead.status} />
              </div>
            </div>

            {/* Email Transaction Timeline */}
            <div>
              <label className="text-sm font-medium text-gray-500">Email Timeline</label>
              {isLoadingLeadJobs ? (
                <div className="mt-3 flex justify-center">
                  <Spinner size="sm" />
                </div>
              ) : (
              <div className="mt-3 relative pl-8 border-l border-gray-200 space-y-4">
                {sortedTemplates.map((template) => {
                  // Find the job for this step
                  const job = selectedLeadJobs.find((j) => j.step_number === template.step_number);
                  
                  let statusText = 'Not scheduled';
                  let statusColor = 'text-gray-500';
                  let dotColor = 'bg-gray-300';
                  let subText: string | null = null;

                  if (job) {
                    switch (job.status) {
                      case 'sent':
                        statusText = 'Sent';
                        statusColor = 'text-green-600';
                        dotColor = 'bg-green-500';
                        if (job.sent_at) {
                          subText = new Date(job.sent_at).toLocaleString();
                        }
                        break;
                      case 'pending':
                        statusText = 'Scheduled';
                        statusColor = 'text-blue-600';
                        dotColor = 'bg-blue-500';
                        if (job.scheduled_at) {
                          const scheduledDate = new Date(job.scheduled_at);
                          const isPast = scheduledDate.getTime() <= Date.now();
                          if (isPast) {
                            statusText = 'Sending soon...';
                            statusColor = 'text-yellow-600';
                            dotColor = 'bg-yellow-500';
                          } else {
                            subText = scheduledDate.toLocaleString();
                          }
                        }
                        break;
                      case 'failed':
                        statusText = 'Failed';
                        statusColor = 'text-red-600';
                        dotColor = 'bg-red-500';
                        break;
                      case 'skipped':
                        statusText = 'Skipped';
                        statusColor = 'text-gray-500';
                        dotColor = 'bg-gray-400';
                        if (selectedLead.status === LeadStatus.REPLIED) {
                          subText = 'Lead replied';
                        }
                        break;
                    }
                  }

                  return (
                    <div key={template.id} className="relative">
                      <span className={`absolute -left-[14px] top-1.5 w-3 h-3 rounded-full ${dotColor}`} />
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <p className="text-sm font-medium text-gray-900">
                            Email {template.step_number}
                          </p>
                          <p className="text-xs text-gray-500 truncate max-w-[260px]">
                            {template.subject}
                          </p>
                          {subText && (
                            <p className="text-xs text-gray-400 mt-0.5">{subText}</p>
                          )}
                        </div>
                        <span className={`text-xs font-medium ${statusColor} whitespace-nowrap`}>{statusText}</span>
                      </div>
                    </div>
                  );
                })}

                {selectedLead.status === LeadStatus.REPLIED && (
                  <div className="relative">
                    <span className="absolute -left-[14px] top-1.5 w-3 h-3 rounded-full bg-green-500" />
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="text-sm font-medium text-gray-900">Reply received</p>
                        <p className="text-xs text-green-600">Follow-ups canceled</p>
                      </div>
                      <span className="text-xs font-medium text-green-600">Replied</span>
                    </div>
                  </div>
                )}
              </div>
              )}
            </div>
            {selectedLead.status === LeadStatus.REPLIED && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <p className="text-sm font-medium text-green-800">
                  This lead has replied!
                </p>
                <p className="text-sm text-green-600 mt-1">
                  Follow-up emails have been automatically stopped.
                </p>
              </div>
            )}
            {enableSimulatedReply && selectedLead.status !== LeadStatus.REPLIED && (
              <div>
                <Button
                  onClick={() => setShowMarkRepliedConfirm(true)}
                  isLoading={isMarkingReplied}
                  className="w-full"
                >
                  Mark as Replied
                </Button>
              </div>
            )}
            {!enableSimulatedReply && selectedLead.status !== LeadStatus.REPLIED && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                <p className="text-sm text-blue-800">
                  Reply detection is webhook-based ({replyMode}).
                </p>
                <p className="text-xs text-blue-600 mt-1">
                  Replies will stop follow-ups automatically.
                </p>
              </div>
            )}
          </div>
        )}
      </Modal>

      {/* Pause Confirmation */}
      <ConfirmModal
        isOpen={showPauseConfirm}
        onClose={() => setShowPauseConfirm(false)}
        onConfirm={handlePause}
        title="Pause Campaign"
        message="Are you sure you want to pause this campaign? No more emails will be sent until you resume."
        confirmText="Pause Campaign"
        isLoading={isActionLoading}
      />

      {/* Resume Confirmation */}
      <ConfirmModal
        isOpen={showResumeConfirm}
        onClose={() => setShowResumeConfirm(false)}
        onConfirm={handleResume}
        title="Resume Campaign"
        message="Are you sure you want to resume this campaign? Emails will start being sent again."
        confirmText="Resume Campaign"
        isLoading={isActionLoading}
      />

      {/* Mark as Replied Confirmation */}
      <ConfirmModal
        isOpen={showMarkRepliedConfirm}
        onClose={() => setShowMarkRepliedConfirm(false)}
        onConfirm={handleMarkReplied}
        title="Mark as Replied"
        message={`Mark ${selectedLead?.email} as having replied? This will stop all follow-up emails to this lead.`}
        confirmText="Mark as Replied"
        isLoading={isMarkingReplied}
      />

      {/* Email Preview Modal */}
      {campaign && (
        <EmailPreviewModal
          isOpen={previewModal.open}
          onClose={() => setPreviewModal({ open: false, templateId: '', stepNumber: 1 })}
          campaignId={campaign.id}
          templateId={previewModal.templateId}
          stepNumber={previewModal.stepNumber}
        />
      )}
    </div>
  );
}

interface StatCardProps {
  label: string;
  value: number;
  color?: 'gray' | 'blue' | 'green' | 'red';
}

function StatCard({ label, value, color }: StatCardProps) {
  const colorClasses = {
    gray: 'text-gray-600',
    blue: 'text-blue-600',
    green: 'text-green-600',
    red: 'text-red-600',
  };

  return (
    <div className="bg-white rounded-lg shadow-sm p-4">
      <p className="text-sm text-gray-500">{label}</p>
      <p
        className={`text-2xl font-semibold ${color ? colorClasses[color] : 'text-gray-900'}`}
      >
        {value}
      </p>
    </div>
  );
}

export default CampaignDetailPage;
