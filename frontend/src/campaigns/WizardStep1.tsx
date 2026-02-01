import { useState } from 'react';
import { useWizard } from './CampaignWizardContext';
import { campaignsApi } from '../api';
import { Button, Input, TextArea, TagInput } from '../components';
import toast from 'react-hot-toast';

export function WizardStep1() {
  const { state, setName, setPitch, setTags, setCampaignId, nextStep } = useWizard();
  const [isLoading, setIsLoading] = useState(false);
  const [isEnhancing, setIsEnhancing] = useState(false);
  const [errors, setErrors] = useState<{ name?: string; pitch?: string }>({});

  const validate = (): boolean => {
    const newErrors: { name?: string; pitch?: string } = {};

    if (!state.name.trim()) {
      newErrors.name = 'Campaign name is required';
    } else if (state.name.length > 255) {
      newErrors.name = 'Campaign name must be less than 255 characters';
    }

    if (!state.pitch.trim()) {
      newErrors.pitch = 'Pitch is required';
    } else if (state.pitch.length > 2000) {
      newErrors.pitch = 'Pitch must be less than 2000 characters';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleNext = async () => {
    if (!validate()) return;

    setIsLoading(true);

    try {
      // Create campaign if not already created
      if (!state.campaignId) {
        const campaign = await campaignsApi.create({
          name: state.name,
          pitch: state.pitch,
        });
        setCampaignId(campaign.id);
        
        // Add tags if any
        if (state.tags.length > 0) {
          for (const tag of state.tags) {
            try {
              await campaignsApi.addTag(campaign.id, tag);
            } catch (error) {
              console.error(`Failed to add tag '${tag}':`, error);
            }
          }
        }
        
        toast.success('Campaign created');
      } else {
        // Update existing campaign
        await campaignsApi.update(state.campaignId, {
          name: state.name,
          pitch: state.pitch,
        });
        toast.success('Campaign updated');
      }

      nextStep();
    } catch {
      // Error handled by API client
    } finally {
      setIsLoading(false);
    }
  };

  const handleEnhancePitch = async () => {
    if (!state.pitch.trim()) {
      toast.error('Pitch is required to enhance');
      return;
    }

    setIsEnhancing(true);

    try {
      const result = await campaignsApi.enhancePitch(
        state.name.trim() || 'Campaign',
        state.pitch
      );
      setPitch(result.pitch);
      toast.success('Pitch enhanced');
    } catch {
      // Error handled by API client
    } finally {
      setIsEnhancing(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-gray-900">Campaign Basics</h2>
        <p className="mt-1 text-sm text-gray-500">
          Tell us about your outreach campaign.
        </p>
      </div>

      <Input
        label="Campaign Name"
        value={state.name}
        onChange={(e) => setName(e.target.value)}
        placeholder="e.g., Q1 Outreach - Enterprise"
        error={errors.name}
      />

      <TextArea
        label="Pitch"
        value={state.pitch}
        onChange={(e) => setPitch(e.target.value)}
        placeholder="Describe your value proposition. What problem do you solve? Why should the recipient care?"
        rows={5}
        error={errors.pitch}
      />

      <div className="flex justify-end">
        <Button
          variant="secondary"
          size="sm"
          onClick={handleEnhancePitch}
          isLoading={isEnhancing}
          disabled={!state.pitch.trim()}
        >
          Enhance with AI
        </Button>
      </div>

      <TagInput
        label="Tags (optional)"
        tags={state.tags}
        onTagsChange={setTags}
        placeholder="Add tags to organize your campaigns (e.g., Q1, Enterprise, Follow-up)"
        maxTags={10}
      />

      <div className="flex justify-end pt-4">
        <Button onClick={handleNext} isLoading={isLoading}>
          Next: Import Leads
        </Button>
      </div>
    </div>
  );
}

export default WizardStep1;
