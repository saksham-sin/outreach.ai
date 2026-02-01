import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { CampaignWizardProvider, useWizard } from './CampaignWizardContext';
import { WizardStep1 } from './WizardStep1';
import { WizardStep2 } from './WizardStep2';
import { WizardStep3 } from './WizardStep3';
import { WizardStep4 } from './WizardStep4';
import { WizardStep5 } from './WizardStep5';
import { Header, Spinner } from '../components';
import { campaignsApi, templatesApi, leadsApi } from '../api';

const STEPS = [
  { number: 1, title: 'Campaign Basics' },
  { number: 2, title: 'Import Leads' },
  { number: 3, title: 'Email Templates' },
  { number: 4, title: 'Schedule' },
  { number: 5, title: 'Review & Launch' },
];

function WizardContent() {
  const { id } = useParams<{ id: string }>();
  const { currentStep, resetWizard, goToStep, setCampaignId, setName, setPitch, setTone, setTags, setTemplates, setLeads } = useWizard();
  const navigate = useNavigate();
  const [isLoadingCampaign, setIsLoadingCampaign] = useState(!!id);

  // Load existing campaign data when editing
  useEffect(() => {
    const loadCampaign = async () => {
      if (!id) return;

      try {
        const [campaign, templatesData, leadsData] = await Promise.all([
          campaignsApi.get(id),
          templatesApi.list(id),
          leadsApi.list(id, { limit: 500 }),
        ]);

        // Populate wizard state with existing campaign data
        setCampaignId(campaign.id);
        setName(campaign.name);
        setPitch(campaign.pitch);
        setTone(campaign.tone);
        setTags(campaign.tags || []);
        setTemplates(templatesData.templates);
        setLeads(leadsData.leads.map(lead => ({
          email: lead.email,
          first_name: lead.first_name || undefined,
          company: lead.company || undefined,
          isValid: true,
        })));
      } catch (error) {
        console.error('Failed to load campaign:', error);
      } finally {
        setIsLoadingCampaign(false);
      }
    };

    loadCampaign();
  }, [id, setCampaignId, setName, setPitch, setTone, setTemplates, setLeads]);

  // Reset wizard on unmount
  useEffect(() => {
    return () => {
      resetWizard();
    };
  }, [resetWizard]);

  const renderStep = () => {
    switch (currentStep) {
      case 1:
        return <WizardStep1 />;
      case 2:
        return <WizardStep2 />;
      case 3:
        return <WizardStep3 />;
      case 4:
        return <WizardStep4 />;
      case 5:
        return <WizardStep5 />;
      default:
        return <WizardStep1 />;
    }
  };

  if (isLoadingCampaign) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <div className="flex justify-center items-center py-24">
          <Spinner size="lg" />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />

      <main className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Back button */}
        <button
          onClick={() => navigate('/')}
          className="text-sm text-gray-500 hover:text-gray-700 mb-6 flex items-center"
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

        {/* Progress indicator */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            {STEPS.map((step, index) => (
              <div key={step.number} className="flex items-center flex-1">
                <button
                  onClick={() => {
                    // Allow navigation to completed steps and current step
                    if (step.number <= currentStep) {
                      goToStep(step.number);
                    }
                  }}
                  disabled={step.number > currentStep}
                  className={`
                    flex items-center justify-center w-8 h-8 rounded-full text-sm font-medium
                    transition-all flex-shrink-0
                    ${
                      currentStep >= step.number
                        ? 'bg-blue-600 text-white cursor-pointer hover:bg-blue-700'
                        : 'bg-gray-200 text-gray-600 cursor-not-allowed'
                    }
                  `}
                  title={step.number > currentStep ? 'Complete previous steps first' : `Go to ${step.title}`}
                >
                  {currentStep > step.number ? (
                    <svg
                      className="w-5 h-5"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M5 13l4 4L19 7"
                      />
                    </svg>
                  ) : (
                    step.number
                  )}
                </button>
                {index < STEPS.length - 1 && (
                  <div
                    className={`flex-1 h-1 mx-2 ${
                      currentStep > step.number ? 'bg-blue-600' : 'bg-gray-200'
                    }`}
                  />
                )}
              </div>
            ))}
          </div>
          <div className="flex justify-between mt-3 gap-2">
            {STEPS.map((step) => (
              <div key={step.number} className="flex-1 text-center">
                <button
                  onClick={() => {
                    if (step.number <= currentStep) {
                      goToStep(step.number);
                    }
                  }}
                  disabled={step.number > currentStep}
                  className={`text-xs transition-colors w-full py-1 px-1 rounded ${
                    currentStep >= step.number
                      ? 'text-blue-600 hover:text-blue-700 cursor-pointer hover:bg-blue-50'
                      : 'text-gray-400 cursor-not-allowed'
                  }`}
                >
                  {step.title}
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Step content */}
        <div className="bg-white rounded-lg shadow-sm p-6">{renderStep()}</div>
      </main>
    </div>
  );
}

export function CampaignWizard() {
  return (
    <CampaignWizardProvider>
      <WizardContent />
    </CampaignWizardProvider>
  );
}

export default CampaignWizard;
