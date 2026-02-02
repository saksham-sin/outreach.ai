import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useWizard } from './CampaignWizardContext';
import { campaignsApi, leadsApi, templatesApi } from '../api';
import { Button, ConfirmModal, Spinner, Modal, VariableHighlightPreview } from '../components';
import type { PreviewResponse } from '../types';
import toast from 'react-hot-toast';

export function WizardStep5() {
  const { state, setStartTime, prevStep, resetWizard } = useWizard();
  const navigate = useNavigate();
  const [isLaunching, setIsLaunching] = useState(false);
  const [showLaunchConfirm, setShowLaunchConfirm] = useState(false);
  const [leadCount, setLeadCount] = useState<number | null>(null);
  const [isLoadingLeads, setIsLoadingLeads] = useState(true);
  const [sendImmediately, setSendImmediately] = useState(!state.startTime);
  const [scheduledDate, setScheduledDate] = useState('');
  const [scheduledTime, setScheduledTime] = useState('09:00');
  const [scheduleError, setScheduleError] = useState('');
  const [previewModal, setPreviewModal] = useState<{
    open: boolean;
    templateId: string;
    stepNumber: number;
  }>({ open: false, templateId: '', stepNumber: 1 });
  const [previewData, setPreviewData] = useState<PreviewResponse | null>(null);
  const [isLoadingPreview, setIsLoadingPreview] = useState(false);

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

  // Fetch actual lead count from server
  useEffect(() => {
    const fetchLeadCount = async () => {
      if (!state.campaignId) return;

      try {
        const response = await leadsApi.list(state.campaignId, { limit: 1 });
        setLeadCount(response.total);
      } catch {
        // Fallback to local count
        setLeadCount(state.leads.filter((l) => l.isValid).length);
      } finally {
        setIsLoadingLeads(false);
      }
    };

    fetchLeadCount();
  }, [state.campaignId, state.leads]);

  // Sync state.startTime with local state
  useEffect(() => {
    if (state.startTime) {
      const date = new Date(state.startTime);
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const day = String(date.getDate()).padStart(2, '0');
      const hours = String(date.getHours()).padStart(2, '0');
      const minutes = String(date.getMinutes()).padStart(2, '0');

      setScheduledDate(`${year}-${month}-${day}`);
      setScheduledTime(`${hours}:${minutes}`);
      setSendImmediately(false);
    }
  }, [state.startTime]);

  const handleShowPreview = async (templateId: string, stepNumber: number) => {
    if (!state.campaignId) return;

    setPreviewModal({ open: true, templateId, stepNumber });
    setIsLoadingPreview(true);

    try {
      const data = await templatesApi.preview(state.campaignId, templateId);
      setPreviewData(data);
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to load preview');
    } finally {
      setIsLoadingPreview(false);
    }
  };

  const handleLaunch = async () => {
    if (!state.campaignId) return;

    // Validate schedule if scheduled for later
    if (!sendImmediately) {
      if (!scheduledDate || !scheduledTime) {
        setScheduleError('Please select both date and time');
        return;
      }

      const scheduledDateTime = new Date(`${scheduledDate}T${scheduledTime}`);
      const now = new Date();

      if (scheduledDateTime <= now) {
        setScheduleError('Scheduled time must be in the future');
        return;
      }

      // Update start time before launch
      setStartTime(scheduledDateTime.toISOString());
    } else {
      setStartTime(null);
    }

    setIsLaunching(true);

    try {
      await campaignsApi.launch(state.campaignId, sendImmediately ? null : new Date(`${scheduledDate}T${scheduledTime}`).toISOString());
      toast.success('Campaign launched!');
      resetWizard();
      navigate(`/campaigns/${state.campaignId}`);
    } catch {
      // Error handled by API client
    } finally {
      setIsLaunching(false);
      setShowLaunchConfirm(false);
    }
  };

  const handleSaveDraft = async () => {
    toast.success('Campaign saved as draft');
    resetWizard();
    navigate('/');
  };

  const sortedTemplates = [...state.templates].sort(
    (a, b) => a.step_number - b.step_number
  );

  // Calculate total campaign duration
  const totalMinutes = sortedTemplates.reduce((sum, t, index) => {
    const delayMinutes = getDelayMinutes(t.delay_minutes, t.delay_days);
    return index === 0 ? 0 : sum + delayMinutes;
  }, 0);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-gray-900">Review & Launch</h2>
        <p className="mt-1 text-sm text-gray-500">
          Review your campaign settings before launching.
        </p>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 gap-4">
        <SummaryCard
          label="Campaign Name"
          value={state.name}
        />
        <SummaryCard
          label="Tone"
          value={state.tone.charAt(0).toUpperCase() + state.tone.slice(1)}
        />
        <SummaryCard
          label="Total Leads"
          value={
            isLoadingLeads ? (
              <Spinner size="sm" />
            ) : (
              (leadCount ?? 0).toString()
            )
          }
        />
        <SummaryCard
          label="Email Steps"
          value={state.templates.length.toString()}
        />
      </div>

      {/* Pitch */}
      <div className="border rounded-lg p-4">
        <h3 className="text-sm font-medium text-gray-500 mb-2">Pitch</h3>
        <p className="text-gray-900 whitespace-pre-wrap">{state.pitch}</p>
      </div>

      {/* Email sequence */}
      <div className="border rounded-lg overflow-hidden">
        <div className="bg-gray-50 px-4 py-3 border-b">
          <h3 className="text-sm font-medium text-gray-700">
            Email Sequence ({totalMinutes > 0 ? `${formatDelay(totalMinutes)} total` : 'Same time'})
          </h3>
        </div>
        <div className="divide-y">
          {sortedTemplates.map((template, index) => {
            // Calculate when this email will be sent
            let minuteOffset = 0;
            for (let i = 0; i < index; i++) {
              minuteOffset += getDelayMinutes(
                sortedTemplates[i]?.delay_minutes || 0,
                sortedTemplates[i]?.delay_days || 0
              );
            }
            minuteOffset += getDelayMinutes(
              template.delay_minutes,
              template.delay_days
            );

            return (
              <div
                key={template.id}
                className="p-4 cursor-pointer hover:bg-blue-50 transition"
                onClick={() => handleShowPreview(template.id, template.step_number)}
              >
                <div className="flex justify-between items-start mb-2">
                  <div className="flex items-center gap-2">
                    <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-blue-100 text-blue-600 text-xs font-medium">
                      {template.step_number}
                    </span>
                    <span className="font-medium text-gray-900">
                      {template.subject}
                    </span>
                  </div>
                  <span className="text-sm text-gray-500">
                    {index === 0 ? 'Launch time' : formatDelay(minuteOffset)}
                  </span>
                </div>
                <p className="text-sm text-gray-600 line-clamp-2 ml-8">
                  {template.body.replace(/<[^>]*>/g, '').substring(0, 150)}...
                </p>
              </div>
            );
          })}
        </div>
      </div>

      {/* Warnings */}
      {(leadCount === 0 || state.templates.length === 0) && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex">
            <svg
              className="h-5 w-5 text-yellow-400 mr-3"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
            <div>
              <h4 className="text-sm font-medium text-yellow-800">
                Cannot launch campaign
              </h4>
              <ul className="mt-1 text-sm text-yellow-700 list-disc list-inside">
                {leadCount === 0 && <li>No leads imported</li>}
                {state.templates.length === 0 && (
                  <li>No email templates created</li>
                )}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Launch Schedule */}
      <div className="border rounded-lg p-4">
        <h3 className="text-sm font-medium text-gray-700 mb-4">Launch Schedule</h3>
        
        <div className="space-y-4">
          {/* Send Immediately Option */}
          <div
            className={`p-3 border-2 rounded-lg cursor-pointer transition ${
              sendImmediately
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 bg-white hover:border-gray-300'
            }`}
            onClick={() => {
              setSendImmediately(true);
              setStartTime(null);
              setScheduleError('');
            }}
          >
            <div className="flex items-center gap-3">
              <input
                type="radio"
                name="launch-schedule"
                checked={sendImmediately}
                onChange={() => {
                  setSendImmediately(true);
                  setStartTime(null);
                  setScheduleError('');
                }}
                className="w-4 h-4"
              />
              <label className="flex-1 cursor-pointer">
                <p className="font-medium text-gray-900">Send Immediately</p>
                <p className="text-sm text-gray-600">Start sending emails right away</p>
              </label>
            </div>
          </div>

          {/* Schedule for Later Option */}
          <div
            className={`p-3 border-2 rounded-lg cursor-pointer transition ${
              !sendImmediately
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 bg-white hover:border-gray-300'
            }`}
            onClick={() => setSendImmediately(false)}
          >
            <div className="flex items-center gap-3 mb-3">
              <input
                type="radio"
                name="launch-schedule"
                checked={!sendImmediately}
                onChange={() => setSendImmediately(false)}
                className="w-4 h-4"
              />
              <label className="flex-1 cursor-pointer">
                <p className="font-medium text-gray-900">Schedule for Later</p>
                <p className="text-sm text-gray-600">Choose a specific date and time</p>
              </label>
            </div>

            {!sendImmediately && (
              <div className="ml-7 space-y-3 mb-3">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-gray-700 mb-1">
                      Date
                    </label>
                    <input
                      type="date"
                      value={scheduledDate}
                      onChange={(e) => {
                        setScheduledDate(e.target.value);
                        setScheduleError('');
                      }}
                      min={new Date().toISOString().split('T')[0]}
                      className="w-full px-2 py-1 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-700 mb-1">
                      Time
                    </label>
                    <input
                      type="time"
                      value={scheduledTime}
                      onChange={(e) => {
                        setScheduledTime(e.target.value);
                        setScheduleError('');
                      }}
                      className="w-full px-2 py-1 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>

                {scheduledDate && scheduledTime && (
                  <div className="bg-gray-50 p-2 rounded text-sm text-gray-600">
                    Emails will start on{' '}
                    <span className="font-medium">
                      {new Date(`${scheduledDate}T${scheduledTime}`).toLocaleString()}
                    </span>
                  </div>
                )}
              </div>
            )}
          </div>

          {scheduleError && (
            <div className="text-sm text-red-600 bg-red-50 p-2 rounded">
              {scheduleError}
            </div>
          )}
        </div>
      </div>

      {/* Actions */}
      <div className="flex justify-between pt-4 border-t">
        <Button variant="ghost" onClick={prevStep}>
          Back
        </Button>
        <div className="flex gap-3">
          <Button variant="secondary" onClick={handleSaveDraft}>
            Save as Draft
          </Button>
          <Button
            onClick={() => setShowLaunchConfirm(true)}
            disabled={
              leadCount === 0 ||
              state.templates.length === 0 ||
              isLoadingLeads
            }
          >
            Launch Campaign
          </Button>
        </div>
      </div>

      {/* Email Preview Modal */}
      <Modal
        isOpen={previewModal.open}
        onClose={() => setPreviewModal({ open: false, templateId: '', stepNumber: 1 })}
        title={`Email ${previewModal.stepNumber} Preview`}
        size="large"
      >
        <div className="space-y-4">
          {isLoadingPreview ? (
            <div className="flex items-center justify-center py-12">
              <Spinner />
            </div>
          ) : previewData ? (
            <>
              {/* Preview Info */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <p className="text-sm text-blue-800">
                  <strong>Preview for:</strong> {previewData.lead_name} from {previewData.lead_company} ({previewData.lead_email})
                </p>
              </div>

              {/* Subject */}
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  Subject
                </label>
                <div className="bg-gray-50 p-3 rounded border border-gray-200">
                  <p className="text-gray-900">{previewData.subject}</p>
                </div>
              </div>

              {/* Body with highlighted variables */}
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  Body
                </label>
                <div className="bg-white p-4 rounded border border-gray-200 max-h-96 overflow-y-auto">
                  <VariableHighlightPreview htmlContent={previewData.body} />
                </div>
              </div>
            </>
          ) : null}
        </div>
      </Modal>

      {/* Launch Confirmation */}
      <ConfirmModal
        isOpen={showLaunchConfirm}
        onClose={() => setShowLaunchConfirm(false)}
        onConfirm={handleLaunch}
        title="Launch Campaign"
        message={`This will start sending emails to ${leadCount} leads. Are you sure you want to launch?`}
        confirmText="Launch"
        isLoading={isLaunching}
      />
    </div>
  );
}

interface SummaryCardProps {
  label: string;
  value: React.ReactNode;
}

function SummaryCard({ label, value }: SummaryCardProps) {
  return (
    <div className="border rounded-lg p-4">
      <p className="text-sm text-gray-500">{label}</p>
      <p className="text-lg font-medium text-gray-900 mt-1">{value}</p>
    </div>
  );
}

export default WizardStep5;
