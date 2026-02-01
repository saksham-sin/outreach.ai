import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../auth';
import { authApi, type UserProfileUpdate } from '../api/authApi';
import { toast } from 'react-hot-toast';

export function ProfilePage() {
  const navigate = useNavigate();
  const { user, refreshUser } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [formData, setFormData] = useState<UserProfileUpdate>({
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
    }
  }, [user]);

  const handleSaveProfile = async () => {
    setIsLoading(true);
    try {
      await authApi.updateProfile({
        first_name: formData.first_name,
        last_name: formData.last_name,
        job_title: formData.job_title,
        company_name: formData.company_name,
      });
      await refreshUser();
      toast.success('Profile updated successfully');
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to update profile');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSaveSignature = async () => {
    setIsLoading(true);
    try {
      await authApi.updateProfile({
        email_signature: formData.email_signature,
      });
      await refreshUser();
      toast.success('Signature saved successfully');
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to save signature');
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerateSignature = async () => {
    // Validate required fields
    if (!formData.first_name || !formData.last_name || !formData.job_title || !formData.company_name) {
      toast.error('Please fill in your name, job title, and company name first');
      return;
    }

    setIsGenerating(true);

    try {
      const { signature_html } = await authApi.generateSignature();
      setFormData({ ...formData, email_signature: signature_html });
      toast.success('Signature generated! Review and save to apply.');
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to generate signature');
    } finally {
      setIsGenerating(false);
    }
  };

  const isProfileComplete = formData.first_name && formData.last_name && formData.job_title && formData.company_name;

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => navigate('/')}
            className="text-gray-600 hover:text-gray-900 mb-4 flex items-center gap-2"
          >
            ← Back to Dashboard
          </button>
          <h1 className="text-3xl font-bold text-gray-900">Profile Settings</h1>
          <p className="text-gray-600 mt-2">Manage your account information and email signature</p>
        </div>

        <div className="space-y-6">
          {/* Basic Info Card */}
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
            
            {/* Save Profile Button */}
            <div className="flex justify-end mt-6 pt-4 border-t">
              <button
                type="button"
                onClick={handleSaveProfile}
                disabled={isLoading}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
              >
                {isLoading ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </div>

          {/* Email Signature Card */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-gray-900">Email Signature</h2>
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
            <p className="text-sm text-gray-600 mb-3">
              {!isProfileComplete ? (
                <span className="text-amber-600">Complete your profile above to generate a signature</span>
              ) : (
                'Your signature will be automatically added to all outbound emails'
              )}
            </p>
            <textarea
              value={formData.email_signature}
              onChange={(e) => setFormData({ ...formData, email_signature: e.target.value })}
              rows={6}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
              placeholder="<div>Your HTML signature here</div>"
            />
            
            {/* Preview */}
            {formData.email_signature && (
              <div className="mt-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Preview
                </label>
                <div className="border border-gray-200 rounded-lg p-4 bg-gray-50">
                  <div dangerouslySetInnerHTML={{ __html: formData.email_signature }} />
                </div>
              </div>
            )}
            
            {/* Save Signature Button */}
            <div className="flex justify-end mt-6 pt-4 border-t">
              <button
                type="button"
                onClick={handleSaveSignature}
                disabled={isLoading || !formData.email_signature}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
              >
                {isLoading ? 'Saving...' : 'Save Signature'}
              </button>
            </div>
          </div>
        </div>

        {/* Back to Dashboard Button */}
        <div className="mt-6">
          <button
            type="button"
            onClick={() => navigate('/')}
            className="text-gray-600 hover:text-gray-900 flex items-center gap-2"
          >
            ← Back to Dashboard
          </button>
        </div>
      </div>
    </div>
  );
}
