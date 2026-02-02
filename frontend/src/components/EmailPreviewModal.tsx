import { useState, useEffect } from 'react';
import { Modal, Button, Spinner } from '../components';
import { templatesApi } from '../api';
import type { PreviewResponse } from '../types';
import toast from 'react-hot-toast';

interface EmailPreviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  campaignId: string;
  templateId: string;
  stepNumber: number;
}

export function EmailPreviewModal({
  isOpen,
  onClose,
  campaignId,
  templateId,
  stepNumber,
}: EmailPreviewModalProps) {
  const [preview, setPreview] = useState<PreviewResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const loadPreview = async () => {
    setIsLoading(true);
    try {
      const data = await templatesApi.preview(campaignId, templateId);
      setPreview(data);
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to load preview');
    } finally {
      setIsLoading(false);
    }
  };

  // Load preview when modal opens or template changes
  useEffect(() => {
    if (isOpen && templateId) {
      setPreview(null);
      loadPreview();
    }
  }, [isOpen, templateId, campaignId]);

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`Preview Email ${stepNumber}`}
      size="large"
    >
      <div className="space-y-4">
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <Spinner />
          </div>
        ) : preview ? (
          <>
            {/* Preview Info */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <p className="text-sm text-blue-800">
                <strong>Preview using:</strong> {preview.lead_name} from {preview.lead_company} ({preview.lead_email})
              </p>
            </div>

            {/* Subject Line */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Subject Line
              </label>
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
                <p className="text-sm text-gray-900">{preview.subject}</p>
              </div>
            </div>

            {/* Email Body */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Email Body (with signature)
              </label>
              <div className="bg-white border border-gray-200 rounded-lg p-4 max-h-96 overflow-y-auto">
                <div 
                  className="prose prose-sm max-w-none"
                  dangerouslySetInnerHTML={{ __html: preview.body }}
                />
              </div>
            </div>
          </>
        ) : (
          <div className="text-center py-8 text-gray-500">
            No preview available
          </div>
        )}

        {/* Actions */}
        <div className="flex justify-end gap-3 pt-4 border-t">
          {!isLoading && preview && (
            <Button variant="secondary" onClick={loadPreview}>
              Refresh Preview
            </Button>
          )}
          <Button onClick={onClose}>
            Close
          </Button>
        </div>
      </div>
    </Modal>
  );
}
