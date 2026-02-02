import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../auth';
import { authApi, type UserProfileUpdate } from '../api/authApi';
import { toast } from 'react-hot-toast';
import { Button } from '../components/Button';
import { Input } from '../components/Input';
import { TextArea } from '../components/TextArea';

export function ProfileCompletionPage() {
  const navigate = useNavigate();
  const { user, refreshUser } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [formData, setFormData] = useState<UserProfileUpdate>({
    first_name: '',
    last_name: '',
    company_name: '',
    job_title: '',
    email_signature: '',
  });

  // Redirect if profile already completed
  if (user?.profile_completed) {
    navigate('/');
    return null;
  }

  const handleGenerateSignature = async () => {
    // Validate required fields
    if (!formData.first_name || !formData.last_name || !formData.job_title || !formData.company_name) {
      toast.error('Please fill in all fields first');
      return;
    }

    setIsGenerating(true);

    try {
      const { signature_html } = await authApi.generateSignature();
      setFormData({ ...formData, email_signature: signature_html });
      toast.success('Signature generated! Review below and click Save.');
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to generate signature');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleComplete = async () => {
    // Validate required fields
    if (!formData.first_name || !formData.last_name || !formData.company_name || !formData.email_signature) {
      toast.error('Please fill in all required fields including signature');
      return;
    }

    setIsLoading(true);
    try {
      await authApi.updateProfile({
        first_name: formData.first_name,
        last_name: formData.last_name,
        job_title: formData.job_title,
        company_name: formData.company_name,
        email_signature: formData.email_signature,
      });
      await refreshUser();
      toast.success('Profile setup complete!');
      navigate('/');
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to complete profile');
    } finally {
      setIsLoading(false);
    }
  };

  const isProfileComplete = 
    formData.first_name && 
    formData.last_name && 
    formData.company_name && 
    formData.email_signature;

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="max-w-2xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Complete Your Profile</h1>
          <p className="text-gray-600 mt-2">
            Let's set up your account. This will take just a minute!
          </p>
        </div>

        {/* Main Card */}
        <div className="bg-white rounded-lg shadow-lg p-8">
          <div className="space-y-6">
            {/* Basic Info Section */}
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Basic Information</h2>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    First Name *
                  </label>
                  <Input
                    type="text"
                    value={formData.first_name}
                    onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                    placeholder="John"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Last Name *
                  </label>
                  <Input
                    type="text"
                    value={formData.last_name}
                    onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                    placeholder="Smith"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Company Name *
                  </label>
                  <Input
                    type="text"
                    value={formData.company_name}
                    onChange={(e) => setFormData({ ...formData, company_name: e.target.value })}
                    placeholder="Acme Inc"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Job Title
                  </label>
                  <Input
                    type="text"
                    value={formData.job_title}
                    onChange={(e) => setFormData({ ...formData, job_title: e.target.value })}
                    placeholder="Sales Director"
                  />
                </div>
              </div>
            </div>

            {/* Email Signature Section */}
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Email Signature *</h2>
              <p className="text-sm text-gray-600 mb-3">
                Your email signature will be added to all outreach emails
              </p>
              
              <TextArea
                value={formData.email_signature}
                onChange={(e) => setFormData({ ...formData, email_signature: e.target.value })}
                placeholder="Write your signature or click 'Generate' to create one automatically"
                rows={6}
              />

              <button
                onClick={handleGenerateSignature}
                disabled={!formData.first_name || !formData.last_name || !formData.company_name || !formData.job_title || isGenerating}
                className="mt-3 px-4 py-2 text-sm font-medium text-blue-600 hover:text-blue-700 disabled:text-gray-400 disabled:cursor-not-allowed"
              >
                {isGenerating ? 'Generating...' : '✨ Auto-Generate Signature'}
              </button>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-3 pt-4 border-t border-gray-200">
              <Button
                onClick={handleComplete}
                disabled={!isProfileComplete || isLoading}
                className="flex-1"
              >
                {isLoading ? 'Setting up...' : 'Complete Setup'}
              </Button>
            </div>

            <p className="text-xs text-gray-500 text-center">
              * Required fields
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
