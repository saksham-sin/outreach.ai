import { useState, useEffect, useRef } from 'react';
import { useWizard } from './CampaignWizardContext';
import { templatesApi, campaignsApi } from '../api';
import { Button, TextArea, Input, Modal, Select, EmailPreviewModal, RichTextEditor, VariableHighlightPreview } from '../components';
import { EmailTone } from '../types';
import type { EmailTemplate } from '../types';
import toast from 'react-hot-toast';

const TONE_OPTIONS = [
  { value: EmailTone.PROFESSIONAL, label: 'Professional' },
  { value: EmailTone.CASUAL, label: 'Casual' },
  { value: EmailTone.URGENT, label: 'Urgent' },
  { value: EmailTone.FRIENDLY, label: 'Friendly' },
  { value: EmailTone.DIRECT, label: 'Direct' },
];

export function WizardStep3() {
  const { state, setTemplates, updateTemplate, setTone, nextStep, prevStep } = useWizard();
  const [templatesMode, setTemplatesMode] = useState<'manual' | 'ai'>('ai');
  const [isGenerating, setIsGenerating] = useState<number | null>(null);
  const [isGeneratingAll, setIsGeneratingAll] = useState(false);
  const [isRewriting, setIsRewriting] = useState<number | null>(null);
  const [isCreatingTemplate, setIsCreatingTemplate] = useState<number | null>(null);
  const [aiError, setAiError] = useState<string | null>(null);
  const maxFollowups = Number.parseInt(import.meta.env.VITE_MAX_FOLLOWUPS || '3', 10);
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
  const [previewModal, setPreviewModal] = useState<{
    open: boolean;
    templateId: string;
    stepNumber: number;
  }>({ open: false, templateId: '', stepNumber: 1 });
  const [draftPreviewModal, setDraftPreviewModal] = useState<{
    open: boolean;
    subject: string;
    body: string;
    stepNumber: number;
  }>({ open: false, subject: '', body: '', stepNumber: 1 });
  const [stepViewMode, setStepViewMode] = useState<Record<number, 'edit' | 'preview'>>({});
  
  // Refs for RichTextEditor insert functions
  const editorInsertRefs = useRef<Record<number, ((text: string) => void) | null>>({});
  const creatingStepsRef = useRef<Set<number>>(new Set());
  const knownTemplateStepsRef = useRef<Set<number>>(new Set());

  // Fetch existing templates on mount
  useEffect(() => {
    const fetchTemplates = async () => {
      if (!state.campaignId) return;

      try {
        const response = await templatesApi.list(state.campaignId);
        if (response.templates.length > 0) {
          setTemplates(response.templates);
          // Set visible steps based on existing templates
          const steps = response.templates.map((t) => t.step_number).sort((a, b) => a - b);
          setVisibleSteps(steps);
        }
      } catch {
        // Ignore, templates may not exist yet
      }
    };

    fetchTemplates();
  }, [state.campaignId, setTemplates]);

  // Keep known template steps in sync with state
  useEffect(() => {
    knownTemplateStepsRef.current = new Set(
      state.templates.map((template) => template.step_number)
    );
  }, [state.templates]);

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
  const stripHtml = (html: string) =>
    html.replace(/<[^>]*>/g, '').replaceAll('&nbsp;', ' ').trim();

  const insertPlaceholder = (stepNumber: number, placeholder: string) => {
    const insertFn = editorInsertRefs.current[stepNumber];
    if (insertFn) {
      // Use the editor's insert function
      insertFn(placeholder);
    } else {
      // Fallback: append to the end
      const draft = getDraft(stepNumber);
      updateDraft(stepNumber, 'body', draft.body + placeholder);
    }
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
    knownTemplateStepsRef.current.add(template.step_number);
  };

  const handleCreateTemplate = async (
    stepNumber: number,
    subject: string,
    body: string
  ): Promise<EmailTemplate | null> => {
    if (!state.campaignId || isCreatingTemplate === stepNumber) return null;
    if (creatingStepsRef.current.has(stepNumber)) return null;
    if (knownTemplateStepsRef.current.has(stepNumber)) return null;

    if (!subject.trim() || !stripHtml(body)) return null;

    const existing = state.templates.find((t) => t.step_number === stepNumber);
    if (existing) return existing;

    creatingStepsRef.current.add(stepNumber);
    knownTemplateStepsRef.current.add(stepNumber);
    setIsCreatingTemplate(stepNumber);

    try {
      const created = await templatesApi.create(state.campaignId, {
        step_number: stepNumber,
        subject: subject.trim(),
        body: body.trim(),
        delay_days: 0,
      });
      upsertTemplate(created);
      return created;
    } catch (error: any) {
      const detail = error?.response?.data?.detail || '';
      if (detail.toLowerCase().includes('already exists')) {
        try {
          const response = await templatesApi.list(state.campaignId);
          setTemplates(response.templates);
          return response.templates.find((t) => t.step_number === stepNumber) || null;
        } catch {
          return null;
        }
      }
      // Error handled by API client
      return null;
    } finally {
      creatingStepsRef.current.delete(stepNumber);
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
      for (const stepNumber of visibleSteps) {
        setIsGenerating(stepNumber);
        const template = await templatesApi.generate(state.campaignId, stepNumber);
        upsertTemplate(template);
      }
      setAiError(null);
      toast.success(
        `Generated ${visibleSteps.length} email template${visibleSteps.length > 1 ? 's' : ''}`
      );
    } catch {
      setAiError(
        'AI generation is temporarily unavailable. You can continue by writing emails manually.'
      );
    } finally {
      setIsGeneratingAll(false);
      setIsGenerating(null);
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

  const getTemplateForStep = (stepNumber: number): EmailTemplate | undefined => {
    return state.templates.find((t) => t.step_number === stepNumber);
  };

  const handleRemoveFollowup = (stepNumber: number) => {
    // Remove the template from visible steps
    setVisibleSteps(visibleSteps.filter((s) => s !== stepNumber));
    // Remove from state templates
    const filtered = state.templates.filter((t) => t.step_number !== stepNumber);
    setTemplates(filtered);
    toast.success(`Removed follow-up email ${stepNumber}`);
  };

  const handleNext = async () => {
    if (!state.campaignId) return;

    const createdTemplates: EmailTemplate[] = [];

    // Only process visible steps (user's actual selections)
    for (const stepNumber of visibleSteps) {
      const template = getTemplateForStep(stepNumber);
      if (template) continue;

      const draft = getDraft(stepNumber);
      if (draft.subject.trim() && stripHtml(draft.body)) {
        const created = await handleCreateTemplate(stepNumber, draft.subject, draft.body);
        if (created) createdTemplates.push(created);
      }
    }

    const totalTemplates = state.templates.length + createdTemplates.length;
    if (totalTemplates === 0) {
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
          const viewMode = stepViewMode[stepNumber] ?? 'preview';

          return (
            <div
              key={stepNumber}
              className="border rounded-lg p-4 space-y-4"
            >
              <div className="flex justify-between items-center">
                <div>
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
                </div>
                <div className="flex items-center gap-2">
                  {stepNumber > 1 && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleRemoveFollowup(stepNumber)}
                      className="text-red-600 hover:text-red-700"
                    >
                      Remove
                    </Button>
                  )}
                  <div className="flex gap-2">
                    {(template || subjectValue.trim() || stripHtml(bodyValue)) && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={async () => {
                          if (template && state.campaignId) {
                            try {
                              // Always persist current content before server preview
                              await templatesApi.update(
                                state.campaignId,
                                template.id,
                                { subject: subjectValue, body: bodyValue }
                              );
                              updateTemplate(templateIndex, {
                                subject: subjectValue,
                                body: bodyValue,
                              });
                            } catch {
                              setDraftPreviewModal({
                                open: true,
                                subject: subjectValue,
                                body: bodyValue,
                                stepNumber,
                              });
                              return;
                            }

                            setPreviewModal({
                              open: true,
                              templateId: template.id,
                              stepNumber,
                            });
                            return;
                          }

                          setDraftPreviewModal({
                            open: true,
                            subject: subjectValue,
                            body: bodyValue,
                            stepNumber,
                          });
                        }}
                      >
                        👁️ Preview
                      </Button>
                    )}

                    {templatesMode === 'ai' && template && (
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

                    {templatesMode === 'ai' && !template && (
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => handleGenerateSingle(stepNumber)}
                        isLoading={isGenerating === stepNumber}
                        disabled={isGeneratingAll || (isGenerating !== null && isGenerating !== stepNumber)}
                      >
                        Generate
                      </Button>
                    )}
                  </div>
                </div>
              </div>

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
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-700">Email Body</span>
                    {viewMode === 'preview' ? (
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() =>
                          setStepViewMode((prev) => ({ ...prev, [stepNumber]: 'edit' }))
                        }
                      >
                        Edit
                      </Button>
                    ) : (
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() =>
                          setStepViewMode((prev) => ({ ...prev, [stepNumber]: 'preview' }))
                        }
                      >
                        Preview
                      </Button>
                    )}
                  </div>

                  {viewMode === 'preview' ? (
                    <div className="border border-gray-200 rounded-lg p-4 bg-gray-50">
                      {bodyValue ? (
                        <VariableHighlightPreview htmlContent={bodyValue} />
                      ) : (
                        <p className="text-gray-500">No content yet.</p>
                      )}
                    </div>
                  ) : (
                    <div>
                      <RichTextEditor
                        value={bodyValue}
                        onChange={(value) => {
                          updateDraft(stepNumber, 'body', value);
                          if (template) {
                            updateTemplate(templateIndex, { body: value });
                          }
                        }}
                        onEditorReady={(insertFn) => {
                          editorInsertRefs.current[stepNumber] = insertFn;
                        }}
                        height="300px"
                      />
                    </div>
                  )}

                  {viewMode === 'edit' && (
                    <div className="flex items-center gap-3">
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
                    </div>
                  )}

                  {templatesMode === 'manual' && viewMode === 'edit' && (
                    <p className="text-xs text-gray-500">
                      Click the buttons above to insert placeholders, or type them manually: {'{{first_name}}'}, {'{{company}}'}.
                    </p>
                  )}
                </div>
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

      {/* Preview Modal */}
      {state.campaignId && (
        <EmailPreviewModal
          isOpen={previewModal.open}
          onClose={() => setPreviewModal({ open: false, templateId: '', stepNumber: 1 })}
          campaignId={state.campaignId}
          templateId={previewModal.templateId}
          stepNumber={previewModal.stepNumber}
        />
      )}

      {/* Draft Preview Modal */}
      <Modal
        isOpen={draftPreviewModal.open}
        onClose={() =>
          setDraftPreviewModal({ open: false, subject: '', body: '', stepNumber: 1 })
        }
        title={`Email ${draftPreviewModal.stepNumber} Preview (Draft)`}
        size="large"
      >
        <div className="space-y-4">
          <div>
            <div className="block text-xs font-medium text-gray-700 mb-1">
              Subject
            </div>
            <div className="bg-gray-50 p-3 rounded border border-gray-200">
              <p className="text-gray-900">{draftPreviewModal.subject || '(No subject)'}</p>
            </div>
          </div>
          <div>
            <div className="block text-xs font-medium text-gray-700 mb-1">
              Body
            </div>
            <div className="bg-white p-4 rounded border border-gray-200 max-h-96 overflow-y-auto">
              {draftPreviewModal.body ? (
                <VariableHighlightPreview htmlContent={draftPreviewModal.body} />
              ) : (
                <p className="text-gray-500">No content yet.</p>
              )}
            </div>
          </div>
        </div>
      </Modal>

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
