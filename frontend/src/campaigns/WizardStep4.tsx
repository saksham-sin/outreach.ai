import { useState } from 'react';
import { useWizard } from './CampaignWizardContext';
import { templatesApi } from '../api';
import { Button, Input } from '../components';
import toast from 'react-hot-toast';

export function WizardStep4() {
  const { state, updateTemplate, nextStep, prevStep } = useWizard();
  const [isSaving, setIsSaving] = useState(false);

  const handleDelayChange = (index: number, value: string) => {
    const delayDays = parseInt(value, 10) || 0;
    updateTemplate(index, { delay_days: Math.max(0, delayDays) });
  };

  const handleSaveDelays = async () => {
    if (!state.campaignId) return;

    setIsSaving(true);

    try {
      // Update all templates with their delay values
      await Promise.all(
        state.templates.map((template) =>
          templatesApi.update(state.campaignId!, template.id, {
            delay_days: template.delay_days,
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

  const sortedTemplates = [...state.templates].sort(
    (a, b) => a.step_number - b.step_number
  );

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-gray-900">Follow-up Schedule</h2>
        <p className="mt-1 text-sm text-gray-500">
          Configure when each follow-up email should be sent after the previous one.
        </p>
      </div>

      <div className="space-y-4">
        {sortedTemplates.map((template) => {
          const templateIndex = state.templates.findIndex(
            (t) => t.id === template.id
          );

          return (
            <div
              key={template.id}
              className="border rounded-lg p-4"
            >
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-medium text-gray-900">
                    Email {template.step_number}
                  </h3>
                  <p className="text-sm text-gray-500 mt-1">
                    {template.subject}
                  </p>
                </div>

                {template.step_number === 1 ? (
                  <div className="text-sm text-gray-500">
                    Sent immediately when campaign launches
                  </div>
                ) : (
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-gray-500">Wait</span>
                    <Input
                      type="number"
                      min={0}
                      value={template.delay_days}
                      onChange={(e) =>
                        handleDelayChange(templateIndex, e.target.value)
                      }
                      className="w-20 text-center"
                    />
                    <span className="text-sm text-gray-500">
                      day{template.delay_days !== 1 ? 's' : ''} after previous
                      email
                    </span>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Timeline preview */}
      <div className="bg-gray-50 rounded-lg p-4">
        <h4 className="text-sm font-medium text-gray-700 mb-3">
          Timeline Preview
        </h4>
        <div className="space-y-2">
          {sortedTemplates.map((template, index) => {
            // Calculate cumulative days
            let cumulativeDays = 0;
            for (let i = 0; i < index; i++) {
              cumulativeDays += sortedTemplates[i]?.delay_days || 0;
            }
            cumulativeDays += template.delay_days;

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
                    `Day ${cumulativeDays}`
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

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
