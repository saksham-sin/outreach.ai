import { useState, useEffect, useRef } from 'react';
import { useWizard } from './CampaignWizardContext';
import { templatesApi, campaignsApi } from '../api';
import { Button, TextArea, Input, Modal, Select } from '../components';
import { EmailTone } from '../types';
import type { EmailTemplate } from '../types';
import toast from 'react-hot-toast';

const MAX_STEPS = 3;

const TONE_OPTIONS = [
  { value: EmailTone.PROFESSIONAL, label: 'Professional' },
  { value: EmailTone.CASUAL, label: 'Casual' },
  { value: EmailTone.URGENT, label: 'Urgent' },
  { value: EmailTone.FRIENDLY, label: 'Friendly' },
  { value: EmailTone.DIRECT, label: 'Direct' },
];

export function WizardStep3() {
  const { state, setTemplates, updateTemplate, setTone, nextStep, prevStep } = useWizard();
  const [templatesMode, setTemplatesMode] = useState<'manual' | 'ai'>('manual');
  const [isGenerating, setIsGenerating] = useState<number | null>(null);
  const [isGeneratingAll, setIsGeneratingAll] = useState(false);
  const [isRewriting, setIsRewriting] = useState<number | null>(null);
  const [isCreatingTemplate, setIsCreatingTemplate] = useState<number | null>(null);
  const [aiError, setAiError] = useState<string | null>(null);
  const maxFollowups = parseInt(import.meta.env.VITE_MAX_FOLLOWUPS || '3', 10);
  const [visibleSteps, setVisibleSteps] = useState<number[]>([1]); // Start with Email 1 only
  const [drafts, setDrafts] = useState<Record<number, { subject: string; body: string }>>({
    1: { subject: '', body: '' },
    2: { subject: '', body: '' },
    3: { subject: '', body: '' },
  });
  const [rewriteModal, setRewriteModal] = useState<{
    open: boolean;
    index: number;
    instructions: string;
  }>({ open: false, index: -1, instructions: '' });
  
  // Refs for TextArea elements to track cursor position
  const textAreaRefs = useRef<Record<number, HTMLTextAreaElement | null>>({});

  // Fetch existing templates on mount
  useEffect(() => {
    const fetchTemplates = async () => {
      if (!state.campaignId) return;

      try {
        const response = await templatesApi.list(state.campaignId);
        if (response.templates.length > 0) {
          setTemplates(response.templates);
          // Set visible steps based on existing templates
          const steps = response.templates.map((t) => t.step_number).sort();
          setVisibleSteps(steps);
        }
      } catch {
        // Ignore, templates may not exist yet
      }
    };

    fetchTemplates();
  }, [state.campaignId, setTemplates]);

  useEffect(() => {
    if (state.templates.length === 0) return;

    setDrafts((prev) => {
      const next = { ...prev };
      state.templates.forEach((template) => {
        const current = next[template.step_number];
        if (!current || (!current.subject && !current.body)) {
          next[template.step_number] = {
            subject: template.subject,
            body: template.body,
          };
        }
      });
      return next;
    });
  }, [state.templates]);

  // Update campaign tone when it changes (in AI mode only)
  useEffect(() => {
    const updateTone = async () => {
      if (!state.campaignId || templatesMode !== 'ai') return;

      try {
        await campaignsApi.update(state.campaignId, { tone: state.tone });
      } catch {
        // Silently fail, tone will be saved with campaign at launch
      }
    };

    updateTone();
  }, [state.tone, state.campaignId, templatesMode]);

  const getDraft = (stepNumber: number) => {
    return drafts[stepNumber] || { subject: '', body: '' };
  };

  const updateDraft = (stepNumber: number, field: 'subject' | 'body', value: string) => {
    setDrafts((prev) => ({
      ...prev,
      [stepNumber]: { ...(prev[stepNumber] || { subject: '', body: '' }), [field]: value },
    }));
  };

  const insertPlaceholder = (stepNumber: number, placeholder: string) => {
    const textArea = textAreaRefs.current[stepNumber];
    if (!textArea) {
      console.warn(`TextArea ref not found for step ${stepNumber}`);
      return;
    }

    // Get current textarea content from drafts, not from the DOM
    const currentValue = drafts[stepNumber]?.body || textArea.value || '';
    const start = textArea.selectionStart || currentValue.length;
    const end = textArea.selectionEnd || currentValue.length;
    
    const newValue = currentValue.substring(0, start) + placeholder + currentValue.substring(end);
    updateDraft(stepNumber, 'body', newValue);
    
    // Restore focus and move cursor after the inserted text
    setTimeout(() => {
      if (textArea) {
        textArea.focus();
        textArea.setSelectionRange(start + placeholder.length, start + placeholder.length);
      }
    }, 0);
  };

  const upsertTemplate = (template: EmailTemplate) => {
    const existingIndex = state.templates.findIndex(
      (t) => t.step_number === template.step_number
    );

    if (existingIndex >= 0) {
      updateTemplate(existingIndex, template);
    } else {
      const newTemplates = [...state.templates, template].sort(
        (a, b) => a.step_number - b.step_number
      );
      setTemplates(newTemplates);
    }
  };

  const handleCreateTemplate = async (
    stepNumber: number,
    subject: string,
    body: string
  ): Promise<boolean> => {
    if (!state.campaignId || isCreatingTemplate === stepNumber) return false;

    if (!subject.trim() || !body.trim()) return false;

    const existing = state.templates.find((t) => t.step_number === stepNumber);
    if (existing) return false;

    setIsCreatingTemplate(stepNumber);

    try {
      const created = await templatesApi.create(state.campaignId, {
        step_number: stepNumber,
        subject: subject.trim(),
        body: body.trim(),
        delay_days: 0,
      });
      upsertTemplate(created);
      return true;
    } catch {
      // Error handled by API client
      return false;
    } finally {
      setIsCreatingTemplate(null);
    }
  };

  const handleGenerateSingle = async (stepNumber: number) => {
    if (!state.campaignId) return;

    setIsGenerating(stepNumber);

    try {
      const template = await templatesApi.generate(state.campaignId, stepNumber);
      
      upsertTemplate(template);
      setAiError(null);

      toast.success(`Generated email ${stepNumber}`);
    } catch {
      setAiError(
        'AI generation is temporarily unavailable. You can continue by writing emails manually.'
      );
    } finally {
      setIsGenerating(null);
    }
  };

  const handleGenerateAll = async () => {
    if (!state.campaignId) return;

    setIsGeneratingAll(true);

    try {
      const response = await templatesApi.generateAll(state.campaignId, MAX_STEPS);
      setTemplates(response.templates);
      setAiError(null);
      toast.success('Generated all email templates');
    } catch {
      setAiError(
        'AI generation is temporarily unavailable. You can continue by writing emails manually.'
      );
    } finally {
      setIsGeneratingAll(false);
    }
  };

  const handleRewrite = async () => {
    if (!state.campaignId || rewriteModal.index < 0) return;

    const template = state.templates[rewriteModal.index];
    if (!template) return;

    setIsRewriting(rewriteModal.index);

    try {
      const updated = await templatesApi.rewrite(
        state.campaignId,
        template.id,
        rewriteModal.instructions
      );
      updateTemplate(rewriteModal.index, updated);
      setAiError(null);
      toast.success('Email rewritten');
      setRewriteModal({ open: false, index: -1, instructions: '' });
    } catch {
      setAiError(
        'AI generation is temporarily unavailable. You can continue by writing emails manually.'
      );
    } finally {
      setIsRewriting(null);
    }
  };

  const handleUpdateSubject = async (index: number, subject: string) => {
    const template = state.templates[index];
    if (!template || !state.campaignId) return;

    // Only update if the value actually changed
    if (template.subject === subject) return;

    try {
      await templatesApi.update(state.campaignId, template.id, { subject });
      updateTemplate(index, { subject });
    } catch {
      // Silently fail, will retry on next change
    }
  };

  const handleUpdateBody = async (index: number, body: string) => {
    const template = state.templates[index];
    if (!template || !state.campaignId) return;

    // Only update if the value actually changed
    if (template.body === body) return;

    try {
      await templatesApi.update(state.campaignId, template.id, { body });
      updateTemplate(index, { body });
    } catch {
      // Silently fail, will retry on next change
    }
  };

  const getTemplateForStep = (stepNumber: number): EmailTemplate | undefined => {
    return state.templates.find((t) => t.step_number === stepNumber);
  };

  const handleNext = async () => {
    if (!state.campaignId) return;

    let createdAny = false;

    for (const stepNumber of [1, 2, 3]) {
      const template = getTemplateForStep(stepNumber);
      if (template) continue;

      const draft = getDraft(stepNumber);
      if (draft.subject.trim() && draft.body.trim()) {
        const created = await handleCreateTemplate(stepNumber, draft.subject, draft.body);
        if (created) createdAny = true;
      }
    }

    if (state.templates.length === 0 && !createdAny) {
      toast.error('Please add at least one email template to continue.');
      return;
    }

    nextStep();
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">Email Templates</h2>
          <p className="mt-1 text-sm text-gray-500">
            You can write emails yourself or let AI generate a draft. You can edit everything.
          </p>
          {aiError && templatesMode === 'ai' && (
            <p className="mt-2 text-sm text-amber-600">{aiError}</p>
          )}
        </div>
        <div className="flex flex-col items-start gap-3">
          <div className="inline-flex rounded-md border border-gray-200 bg-white">
            <button
              type="button"
              onClick={() => setTemplatesMode('ai')}
              className={`px-3 py-1.5 text-sm font-medium rounded-l-md ${
                templatesMode === 'ai'
                  ? 'bg-gray-900 text-white'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              AI Assisted
            </button>
            <button
              type="button"
              onClick={() => setTemplatesMode('manual')}
              className={`px-3 py-1.5 text-sm font-medium rounded-r-md ${
                templatesMode === 'manual'
                  ? 'bg-gray-900 text-white'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Manual
            </button>
          </div>
          {templatesMode === 'ai' && (
            <Button
              variant="secondary"
              onClick={handleGenerateAll}
              isLoading={isGeneratingAll}
              disabled={isGenerating !== null}
            >
              Generate All
            </Button>
          )}
        </div>
      </div>

      {/* Tone selector - only show in AI mode */}
      {templatesMode === 'ai' && (
        <div className="max-w-xs">
          <Select
            label="Email Tone"
            value={state.tone}
            onChange={(e) => setTone(e.target.value as EmailTone)}
            options={TONE_OPTIONS}
          />
        </div>
      )}

      {/* Email steps */}
      <div className="space-y-6">
        {visibleSteps.map((stepNumber) => {
          const template = getTemplateForStep(stepNumber);
          const templateIndex = state.templates.findIndex(
            (t) => t.step_number === stepNumber
          );
          const draft = getDraft(stepNumber);
          const subjectValue = template?.subject ?? draft.subject;
          const bodyValue = template?.body ?? draft.body;

          return (
            <div
              key={stepNumber}
              className="border rounded-lg p-4 space-y-4"
            >
              <div className="flex justify-between items-center">
                <h3 className="font-medium text-gray-900">
                  Email {stepNumber}
                  {stepNumber === 1 && (
                    <span className="text-gray-500 font-normal ml-2">
                      (Initial outreach)
                    </span>
                  )}
                  {stepNumber > 1 && (
                    <span className="text-gray-500 font-normal ml-2">
                      (Follow-up)
                    </span>
                  )}
                </h3>
                {templatesMode === 'ai' && (
                  <div className="flex gap-2">
                    {template && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() =>
                          setRewriteModal({
                            open: true,
                            index: templateIndex,
                            instructions: '',
                          })
                        }
                        disabled={isRewriting === templateIndex}
                      >
                        Rewrite
                      </Button>
                    )}
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => handleGenerateSingle(stepNumber)}
                      isLoading={isGenerating === stepNumber}
                      disabled={isGeneratingAll || (isGenerating !== null && isGenerating !== stepNumber)}
                    >
                      {template ? 'Regenerate' : 'Generate'}
                    </Button>
                  </div>
                )}
              </div>

              <>
                <Input
                  label="Subject"
                  value={subjectValue}
                  onChange={(e) => {
                    updateDraft(stepNumber, 'subject', e.target.value);
                    if (template) {
                      updateTemplate(templateIndex, { subject: e.target.value });
                    }
                  }}
                  onBlur={(e) => {
                    if (template) {
                      handleUpdateSubject(templateIndex, e.target.value);
                    } else {
                      handleCreateTemplate(stepNumber, e.target.value, bodyValue);
                    }
                  }}
                  placeholder="Email subject line"
                />
                <div className="space-y-2">
                  <TextArea
                    ref={(el) => {
                      if (el) textAreaRefs.current[stepNumber] = el;
                    }}
                    label="Body"
                    value={bodyValue}
                    onChange={(e) => {
                      updateDraft(stepNumber, 'body', e.target.value);
                      if (template) {
                        updateTemplate(templateIndex, { body: e.target.value });
                      }
                    }}
                    onBlur={(e) => {
                      if (template) {
                        handleUpdateBody(templateIndex, e.target.value);
                      } else {
                        handleCreateTemplate(stepNumber, subjectValue, e.target.value);
                      }
                    }}
                    placeholder="Email body content..."
                    rows={6}
                  />
                  {templatesMode === 'manual' && (
                    <div className="flex gap-2 flex-wrap">
                      <button
                        type="button"
                        onMouseDown={(e) => {
                          e.preventDefault();
                          insertPlaceholder(stepNumber, '{{first_name}}');
                        }}
                        className="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition"
                      >
                        + {'{{first_name}}'}
                      </button>
                      <button
                        type="button"
                        onMouseDown={(e) => {
                          e.preventDefault();
                          insertPlaceholder(stepNumber, '{{company}}');
                        }}
                        className="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition"
                      >
                        + {'{{company}}'}
                      </button>
                    </div>
                  )}
                  {templatesMode === 'manual' && (
                    <p className="text-xs text-gray-500">
                      Click the buttons above to insert placeholders, or type them manually: {'{{first_name}}'}, {'{{company}}'}.
                    </p>
                  )}
                </div>
              </>
            </div>
          );
        })}
        
        {/* Add Follow-up Button */}
        {visibleSteps.length < maxFollowups && (
          <div className="flex justify-center pt-4">
            <Button
              variant="secondary"
              onClick={() => {
                const nextStep = visibleSteps.length + 1;
                setVisibleSteps([...visibleSteps, nextStep]);
              }}
            >
              + Add Follow-up Email
            </Button>
          </div>
        )}
      </div>

      {/* Navigation */}
      <div className="flex justify-between pt-4 border-t">
        <Button variant="ghost" onClick={prevStep}>
          Back
        </Button>
        <Button
          onClick={handleNext}
          disabled={state.templates.length === 0 &&
            !Object.values(drafts).some(
              (draft) => draft.subject.trim() && draft.body.trim()
            )}
        >
          Next: Schedule
        </Button>
      </div>

      {/* Rewrite Modal */}
      <Modal
        isOpen={rewriteModal.open}
        onClose={() =>
          setRewriteModal({ open: false, index: -1, instructions: '' })
        }
        title="Rewrite Email"
        footer={
          <>
            <Button
              variant="secondary"
              onClick={() =>
                setRewriteModal({ open: false, index: -1, instructions: '' })
              }
            >
              Cancel
            </Button>
            <Button
              onClick={handleRewrite}
              isLoading={isRewriting !== null}
              disabled={!rewriteModal.instructions.trim()}
            >
              Rewrite
            </Button>
          </>
        }
      >
        <TextArea
          label="Instructions"
          value={rewriteModal.instructions}
          onChange={(e) =>
            setRewriteModal((prev) => ({
              ...prev,
              instructions: e.target.value,
            }))
          }
          placeholder="e.g., Make it shorter and more casual"
          rows={3}
        />
      </Modal>
    </div>
  );
}

export default WizardStep3;
