import { createContext, useContext, useState, useCallback, type ReactNode } from 'react';
import { EmailTone, type ParsedLead, type EmailTemplate, type WizardState } from '../types';

interface WizardContextType {
  state: WizardState;
  // Navigation
  currentStep: number;
  goToStep: (step: number) => void;
  nextStep: () => void;
  prevStep: () => void;
  // Campaign basics
  setCampaignId: (id: string) => void;
  setName: (name: string) => void;
  setPitch: (pitch: string) => void;
  setTone: (tone: EmailTone) => void;
  setTags: (tags: string[]) => void;
  // Leads
  setLeads: (leads: ParsedLead[]) => void;
  clearLeads: () => void;
  // Templates
  setTemplates: (templates: EmailTemplate[]) => void;
  updateTemplate: (index: number, template: Partial<EmailTemplate>) => void;
  // Schedule
  setStartTime: (startTime: string | null) => void;
  // Reset
  resetWizard: () => void;
}

const initialState: WizardState = {
  campaignId: null,
  name: '',
  pitch: '',
  tone: EmailTone.PROFESSIONAL,
  tags: [],
  leads: [],
  templates: [],
  currentStep: 1,
  startTime: null,
};

const WizardContext = createContext<WizardContextType | undefined>(undefined);

export function CampaignWizardProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<WizardState>(initialState);

  const goToStep = useCallback((step: number) => {
    setState((prev) => ({ ...prev, currentStep: step }));
  }, []);

  const nextStep = useCallback(() => {
    setState((prev) => ({ ...prev, currentStep: Math.min(prev.currentStep + 1, 5) }));
  }, []);

  const prevStep = useCallback(() => {
    setState((prev) => ({ ...prev, currentStep: Math.max(prev.currentStep - 1, 1) }));
  }, []);

  const setCampaignId = useCallback((id: string) => {
    setState((prev) => ({ ...prev, campaignId: id }));
  }, []);

  const setName = useCallback((name: string) => {
    setState((prev) => ({ ...prev, name }));
  }, []);

  const setPitch = useCallback((pitch: string) => {
    setState((prev) => ({ ...prev, pitch }));
  }, []);

  const setTone = useCallback((tone: EmailTone) => {
    setState((prev) => ({ ...prev, tone }));
  }, []);

  const setTags = useCallback((tags: string[]) => {
    setState((prev) => ({ ...prev, tags }));
  }, []);

  const setLeads = useCallback((leads: ParsedLead[]) => {
    setState((prev) => ({ ...prev, leads }));
  }, []);

  const clearLeads = useCallback(() => {
    setState((prev) => ({ ...prev, leads: [] }));
  }, []);

  const setTemplates = useCallback((templates: EmailTemplate[]) => {
    setState((prev) => ({ ...prev, templates }));
  }, []);

  const updateTemplate = useCallback((index: number, update: Partial<EmailTemplate>) => {
    setState((prev) => {
      const templates = [...prev.templates];
      if (templates[index]) {
        templates[index] = { ...templates[index], ...update };
      }
      return { ...prev, templates };
    });
  }, []);

  const setStartTime = useCallback((startTime: string | null) => {
    setState((prev) => ({ ...prev, startTime }));
  }, []);

  const resetWizard = useCallback(() => {
    setState(initialState);
  }, []);

  const value: WizardContextType = {
    state,
    currentStep: state.currentStep,
    goToStep,
    nextStep,
    prevStep,
    setCampaignId,
    setName,
    setPitch,
    setTone,
    setTags,
    setLeads,
    clearLeads,
    setTemplates,
    updateTemplate,
    setStartTime,
    resetWizard,
  };

  return (
    <WizardContext.Provider value={value}>{children}</WizardContext.Provider>
  );
}

export function useWizard(): WizardContextType {
  const context = useContext(WizardContext);
  if (context === undefined) {
    throw new Error('useWizard must be used within a CampaignWizardProvider');
  }
  return context;
}

export default WizardContext;
