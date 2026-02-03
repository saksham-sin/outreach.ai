import { useState, useMemo, useEffect } from 'react';
import { useWizard } from './CampaignWizardContext';
import { templatesApi } from '../api';
import { Button, Input, Modal, VariableHighlightPreview } from '../components';
import type { EmailTemplate } from '../types';
import toast from 'react-hot-toast';

export function WizardStep4() {
  const { state, updateTemplate, nextStep, prevStep, setTemplates, setStartTime } = useWizard();
  const [isSaving, setIsSaving] = useState(false);
  const [previewTemplate, setPreviewTemplate] = useState<EmailTemplate | null>(null);
  const [campaignStartDate, setCampaignStartDate] = useState('');
  const [campaignStartTime, setCampaignStartTime] = useState('09:00');
  const [sendImmediately, setSendImmediately] = useState(!state.startTime);
  
  const baseDate = useMemo(() => {
    const date = new Date();
    date.setHours(0, 0, 0, 0);
    return date;
  }, []);

  // Sync state.startTime with local state
  useEffect(() => {
    if (state.startTime) {
      const date = new Date(state.startTime);
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const day = String(date.getDate()).padStart(2, '0');
      const hours = String(date.getHours()).padStart(2, '0');
      const minutes = String(date.getMinutes()).padStart(2, '0');

      setCampaignStartDate(`${year}-${month}-${day}`);
      setCampaignStartTime(`${hours}:${minutes}`);
      setSendImmediately(false);
    }
  }, [state.startTime]);

  const getDelayMinutes = (delayMinutes: number, delayDays: number) => {
    if (delayMinutes && delayMinutes > 0) return delayMinutes;
    return delayDays * 1440;
  };

  const splitDelay = (totalMinutes: number) => {
    const days = Math.floor(totalMinutes / 1440);
    const hours = Math.floor((totalMinutes % 1440) / 60);
    const minutes = totalMinutes % 60;
    return { days, hours, minutes };
  };

  const formatDelay = (totalMinutes: number) => {
    if (totalMinutes <= 0) return 'Same time';
    const { days, hours, minutes } = splitDelay(totalMinutes);
    const parts = [
      days > 0 ? `${days}d` : '',
      hours > 0 ? `${hours}h` : '',
      minutes > 0 ? `${minutes}m` : '',
    ].filter(Boolean);
    return parts.join(' ');
  };

  const formatRelativeTime = (totalMinutes: number): { days: number; hours: number; minutes: number } => {
    const days = Math.floor(totalMinutes / 1440);
    const hours = Math.floor((totalMinutes % 1440) / 60);
    const minutes = totalMinutes % 60;
    return { days, hours, minutes };
  };

  const normalizeDateTimeValues = (days: number, hours: number, minutes: number): { days: number; hours: number; minutes: number } => {
    // Normalize minutes
    let normalizedMinutes = Math.max(0, Math.min(60, minutes));
    let normalizedHours = Math.max(0, Math.min(23, hours));
    let normalizedDays = Math.max(0, Math.min(31, days));

    // Carry over minutes to hours
    if (normalizedMinutes > 59) {
      normalizedHours += Math.floor(normalizedMinutes / 60);
      normalizedMinutes = normalizedMinutes % 60;
    }

    // Carry over hours to days
    if (normalizedHours > 23) {
      normalizedDays += Math.floor(normalizedHours / 24);
      normalizedHours = normalizedHours % 24;
    }

    return {
      days: Math.min(31, normalizedDays),
      hours: normalizedHours,
      minutes: normalizedMinutes,
    };
  };

  const handleDelayTimeUpdate = (index: number, days: number, hours: number, minutes: number) => {
    const normalized = normalizeDateTimeValues(days, hours, minutes);
    const totalMinutes = normalized.days * 1440 + normalized.hours * 60 + normalized.minutes;

    updateTemplate(index, {
      delay_minutes: totalMinutes,
      delay_days: normalized.days,
    });
  };

  const handleSaveDelays = async () => {
    if (!state.campaignId) return;

    setIsSaving(true);

    try {
      // Update campaign start time
      if (!sendImmediately && campaignStartDate && campaignStartTime) {
        const startDateTime = new Date(`${campaignStartDate}T${campaignStartTime}`);
        setStartTime(startDateTime.toISOString());
      } else if (sendImmediately) {
        setStartTime(null);
      }

      // Update all templates with their delay values
      await Promise.all(
        state.templates.map((template) =>
          templatesApi.update(state.campaignId!, template.id, {
            delay_minutes: template.delay_minutes,
            delay_days: Math.floor(template.delay_minutes / 1440),
          })
        )
      );

      toast.success('Schedule saved');
      nextStep();
    } catch {
      // Error handled by API client
    } finally {
      setIsSaving(false);
    }
  };

  const handleRemoveFollowup = (stepNumber: number) => {
    // Remove the template from state
    const filtered = state.templates.filter((t) => t.step_number !== stepNumber);
    setTemplates(filtered);
    toast.success(`Removed follow-up email ${stepNumber}`);
  };

  const sortedTemplates = [...state.templates].sort(
    (a, b) => a.step_number - b.step_number
  );

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-gray-900">Campaign & Follow-up Schedule</h2>
        <p className="mt-1 text-sm text-gray-500">
          Configure when the campaign should start and when each follow-up email should be sent.
        </p>
      </div>

      {/* Campaign Start Time */}
      <div className="bg-green-50 border border-green-200 rounded-lg p-4">
        <h3 className="font-medium text-gray-900 mb-3">Campaign Start Time</h3>
        <div className="space-y-3">
          <label className="flex items-center gap-3">
            <input
              type="radio"
              checked={sendImmediately}
              onChange={() => setSendImmediately(true)}
              className="rounded"
            />
            <span className="text-sm text-gray-700">Send immediately</span>
          </label>
          <label className="flex items-center gap-3">
            <input
              type="radio"
              checked={!sendImmediately}
              onChange={() => setSendImmediately(false)}
              className="rounded"
            />
            <span className="text-sm text-gray-700">Schedule for later</span>
          </label>

          {!sendImmediately && (
            <div className="flex items-center gap-2 ml-6">
              <Input
                type="date"
                value={campaignStartDate}
                min={baseDate.toISOString().split('T')[0] || ''}
                onChange={(e) => setCampaignStartDate(e.target.value)}
                className="w-40"
              />
              <Input
                type="time"
                value={campaignStartTime}
                onChange={(e) => setCampaignStartTime(e.target.value)}
                className="w-24"
              />
            </div>
          )}
        </div>
      </div>

      {/* Follow-up Emails */}
      <div>
        <h3 className="font-medium text-gray-900 mb-3">Follow-up Emails</h3>
        <div className="space-y-4">
        {sortedTemplates.map((template) => {
          const templateIndex = state.templates.findIndex(
            (t) => t.id === template.id
          );
          const delayMinutes = getDelayMinutes(
            template.delay_minutes,
            template.delay_days
          );
          const { days, hours, minutes } = formatRelativeTime(delayMinutes);

          return (
            <div
              key={template.id}
              className="space-y-3"
            >
              {/* Email Card */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <button
                  type="button"
                  onClick={() => setPreviewTemplate(template)}
                  className="text-left w-full hover:bg-blue-100 rounded-md p-2 -m-2 transition"
                >
                  <h3 className="font-medium text-gray-900">
                    Email {template.step_number}
                  </h3>
                  <p className="text-sm text-gray-500 mt-1">
                    {template.subject}
                  </p>
                </button>
              </div>

              {/* Schedule Card */}
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                {template.step_number === 1 ? (
                  <div className="text-sm text-gray-500">
                    Sent at campaign start time
                  </div>
                ) : (
                  <div className="flex items-center gap-3 flex-wrap">
                    <span className="text-sm font-semibold text-gray-700">Send after</span>
                    <div className="flex items-center gap-2">
                      <div className="flex flex-col items-center">
                        <input
                          type="number"
                          min="0"
                          max="31"
                          value={days}
                          onChange={(e) => {
                            const val = Math.max(0, parseInt(e.target.value) || 0);
                            handleDelayTimeUpdate(templateIndex, val, hours, minutes);
                          }}
                          className="w-16 px-2 py-2 border border-gray-300 rounded-lg text-center font-semibold text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                          placeholder="0"
                        />
                        <span className="text-xs text-gray-500 mt-1 font-medium">Days</span>
                      </div>
                      <span className="text-gray-400 font-semibold">:</span>
                      <div className="flex flex-col items-center">
                        <input
                          type="number"
                          min="0"
                          max="23"
                          value={hours}
                          onChange={(e) => {
                            const val = Math.max(0, parseInt(e.target.value) || 0);
                            handleDelayTimeUpdate(templateIndex, days, val, minutes);
                          }}
                          className="w-16 px-2 py-2 border border-gray-300 rounded-lg text-center font-semibold text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                          placeholder="0"
                        />
                        <span className="text-xs text-gray-500 mt-1 font-medium">Hours</span>
                      </div>
                      <span className="text-gray-400 font-semibold">:</span>
                      <div className="flex flex-col items-center">
                        <input
                          type="number"
                          min="0"
                          max="59"
                          value={minutes}
                          onChange={(e) => {
                            const val = Math.max(0, parseInt(e.target.value) || 0);
                            handleDelayTimeUpdate(templateIndex, days, hours, val);
                          }}
                          className="w-16 px-2 py-2 border border-gray-300 rounded-lg text-center font-semibold text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                          placeholder="0"
                        />
                        <span className="text-xs text-gray-500 mt-1 font-medium">Minutes</span>
                      </div>
                    </div>
                    <span className="text-sm text-gray-600 font-medium">
                      {template.step_number === 2 ? 'of initial email' : 'of previous email'}
                    </span>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleRemoveFollowup(template.step_number)}
                      className="text-red-600 hover:text-red-700 ml-auto"
                    >
                      Remove
                    </Button>
                  </div>
                )}
              </div>
            </div>
          );
        })}
        </div>
      </div>

      {/* Timeline preview */}
      <div className="bg-gray-50 rounded-lg p-4">
        <h4 className="text-sm font-medium text-gray-700 mb-3">
          Timeline Preview
        </h4>
        <div className="space-y-2">
          {sortedTemplates.map((template, index) => {
            // Calculate cumulative minutes
            let cumulativeMinutes = 0;
            for (let i = 0; i < index; i++) {
              const minutes = getDelayMinutes(
                sortedTemplates[i]?.delay_minutes || 0,
                sortedTemplates[i]?.delay_days || 0
              );
              cumulativeMinutes += minutes;
            }
            cumulativeMinutes += getDelayMinutes(
              template.delay_minutes,
              template.delay_days
            );

            return (
              <div key={template.id} className="flex items-center text-sm">
                <div className="w-8 h-8 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center font-medium">
                  {template.step_number}
                </div>
                <div className="ml-3 flex-1">
                  <span className="text-gray-900">
                    {template.subject.substring(0, 40)}
                    {template.subject.length > 40 ? '...' : ''}
                  </span>
                </div>
                <div className="text-gray-500">
                  {index === 0 ? (
                    'Day 0 (Launch)'
                  ) : (
                    formatDelay(cumulativeMinutes)
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Email Preview Modal */}
      <Modal
        isOpen={!!previewTemplate}
        onClose={() => setPreviewTemplate(null)}
        title={`Email ${previewTemplate?.step_number ?? ''} Preview`}
        size="large"
      >
        <div className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">
              Subject
            </label>
            <div className="bg-gray-50 p-3 rounded border border-gray-200">
              <p className="text-gray-900">
                {previewTemplate?.subject || '(No subject)'}
              </p>
            </div>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">
              Body
            </label>
            <div className="bg-white p-4 rounded border border-gray-200 max-h-96 overflow-y-auto">
              {previewTemplate?.body ? (
                <VariableHighlightPreview htmlContent={previewTemplate.body} />
              ) : (
                <p className="text-gray-500">No content yet.</p>
              )}
            </div>
          </div>
        </div>
      </Modal>

      {/* Navigation */}
      <div className="flex justify-between pt-4 border-t">
        <Button variant="ghost" onClick={prevStep}>
          Back
        </Button>
        <Button onClick={handleSaveDelays} isLoading={isSaving}>
          Next: Review
        </Button>
      </div>
    </div>
  );
}

export default WizardStep4;
