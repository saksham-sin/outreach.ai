import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../auth';
import { authApi } from '../api/authApi';
import { toast } from 'react-hot-toast';
import { RichTextEditor } from '../components';

export function OnboardingPage() {
  const navigate = useNavigate();
  const { user, refreshUser } = useAuth();
  const [isSavingProfile, setIsSavingProfile] = useState(false);
  const [isSavingSignature, setIsSavingSignature] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [signatureEditMode, setSignatureEditMode] = useState(false);
  const [formData, setFormData] = useState<Record<string, string>>({
    first_name: user?.first_name || '',
    last_name: user?.last_name || '',
    company_name: user?.company_name || '',
    job_title: user?.job_title || '',
    email_signature: user?.email_signature || '',
  });

  useEffect(() => {
    if (user) {
      setFormData({
        first_name: user.first_name || '',
        last_name: user.last_name || '',
        company_name: user.company_name || '',
        job_title: user.job_title || '',
        email_signature: user.email_signature || '',
      });
      
      // Auto-redirect to dashboard if onboarding is complete
      if (user.profile_completed) {
        navigate('/', { replace: true });
      }
    }
  }, [user, navigate]);

  const handleSaveProfile = async () => {
    if (isSavingProfile) return;
    setIsSavingProfile(true);
    try {
      const updatedUser = await authApi.updateProfile({
        first_name: formData.first_name,
        last_name: formData.last_name,
        job_title: formData.job_title,
        company_name: formData.company_name,
      });
      setFormData((prev) => ({
        ...prev,
        first_name: updatedUser.first_name || '',
        last_name: updatedUser.last_name || '',
        job_title: updatedUser.job_title || '',
        company_name: updatedUser.company_name || '',
      }));
      await refreshUser();
      toast.success('Profile updated successfully');
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to update profile');
    } finally {
      setIsSavingProfile(false);
    }
  };

  const handleSaveSignature = async () => {
    if (isSavingSignature) return;
    setIsSavingSignature(true);
    try {
      const updatedUser = await authApi.updateProfile({
        email_signature: formData.email_signature,
      });
      setFormData((prev) => ({
        ...prev,
        email_signature: updatedUser.email_signature || '',
      }));
      await refreshUser();
      toast.success('Signature saved successfully');
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to save signature');
    } finally {
      setIsSavingSignature(false);
    }
  };

  const handleGenerateSignature = async () => {
    if (!formData.first_name || !formData.last_name || !formData.job_title || !formData.company_name) {
      toast.error('Please fill in your name, job title, and company name first');
      return;
    }

    setIsGenerating(true);

    try {
      const { signature_html } = await authApi.generateSignature();
      setFormData({ ...formData, email_signature: signature_html });
      toast.success('Signature generated! Click Save to apply.');
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to generate signature');
    } finally {
      setIsGenerating(false);
    }
  };

  const isProfileComplete = formData.first_name && formData.last_name && formData.job_title && formData.company_name;
  const isOnboardingComplete = Boolean(user?.profile_completed);

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Welcome,</h1>
          <p className="text-gray-600 mt-2">
            Please complete your profile and generate an email signature to get started
          </p>
        </div>

        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Basic Information</h2>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  First Name
                </label>
                <input
                  type="text"
                  value={formData.first_name}
                  onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="John"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Last Name
                </label>
                <input
                  type="text"
                  value={formData.last_name}
                  onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Smith"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Job Title
                </label>
                <input
                  type="text"
                  value={formData.job_title}
                  onChange={(e) => setFormData({ ...formData, job_title: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Sales Director"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Company Name
                </label>
                <input
                  type="text"
                  value={formData.company_name}
                  onChange={(e) => setFormData({ ...formData, company_name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Acme Corp"
                />
              </div>
            </div>
            <div className="mt-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Email
              </label>
              <input
                type="email"
                value={user?.email || ''}
                disabled
                className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-50 text-gray-500"
              />
            </div>

            <div className="flex justify-end mt-6 pt-4 border-t">
              <button
                type="button"
                onClick={handleSaveProfile}
                disabled={isSavingProfile}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
              >
                {isSavingProfile ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-gray-900">Email Signature</h2>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setSignatureEditMode(!signatureEditMode)}
                  className="px-3 py-2 text-sm bg-gray-200 text-gray-900 rounded hover:bg-gray-300 transition-colors"
                >
                  {signatureEditMode ? '✓ Done' : '✎ Edit'}
                </button>
                <button
                  type="button"
                  onClick={handleGenerateSignature}
                  disabled={!isProfileComplete || isGenerating}
                  className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
                >
                  {isGenerating ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      Generating...
                    </>
                  ) : (
                    <>
                      ✨ Generate with AI
                    </>
                  )}
                </button>
              </div>
            </div>
            <p className="text-sm text-gray-600 mb-3">
              {!isProfileComplete ? (
                <span className="text-amber-600">Complete your profile above to generate a signature</span>
              ) : (
                'Your signature will be automatically added to all outbound emails'
              )}
            </p>

            {signatureEditMode ? (
              <div>
                <RichTextEditor
                  value={formData.email_signature || ''}
                  onChange={(value) => setFormData({ ...formData, email_signature: value })}
                  height="300px"
                />

                <div className="flex justify-end mt-6 pt-4 border-t">
                  <button
                    type="button"
                    onClick={handleSaveSignature}
                    disabled={isSavingSignature || !formData.email_signature}
                    className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
                  >
                    {isSavingSignature ? 'Saving...' : 'Save Signature'}
                  </button>
                </div>
              </div>
            ) : (
              <div>
                {formData.email_signature ? (
                  <>
                    <div className="border border-gray-200 rounded-lg p-4 bg-gray-50 mb-4">
                      <div dangerouslySetInnerHTML={{ __html: formData.email_signature }} />
                    </div>
                    <div className="flex justify-end pt-4 border-t">
                      <button
                        type="button"
                        onClick={handleSaveSignature}
                        disabled={isSavingSignature}
                        className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
                      >
                        {isSavingSignature ? 'Saving...' : 'Save Signature'}
                      </button>
                    </div>
                  </>
                ) : (
                  <div className="border border-gray-200 rounded-lg p-4 bg-gray-50">
                    <p className="text-gray-500">No signature yet. Generate one with AI or click "Edit" to add manually.</p>
                  </div>
                )}
              </div>
            )}
          </div>

          {isOnboardingComplete && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-6 text-center">
              <p className="text-green-700 font-semibold mb-4">
                Onboarding successfully completed
              </p>
              <button
                onClick={() => navigate('/')}
                className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
              >
                Go to Dashboard
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
