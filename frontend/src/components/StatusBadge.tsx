import type { CampaignStatus, LeadStatus, JobStatus } from '../types';

interface StatusBadgeProps {
  status: CampaignStatus | LeadStatus | JobStatus;
  size?: 'sm' | 'md';
}

// Map status values to their display config
// Note: Some statuses share the same string value (e.g., 'pending', 'failed')
// so we only need to define them once
const statusConfig: Record<string, { bg: string; text: string; label: string }> = {
  // Shared/common statuses
  draft: {
    bg: 'bg-gray-100',
    text: 'text-gray-800',
    label: 'Draft',
  },
  active: {
    bg: 'bg-green-100',
    text: 'text-green-800',
    label: 'Active',
  },
  paused: {
    bg: 'bg-yellow-100',
    text: 'text-yellow-800',
    label: 'Paused',
  },
  completed: {
    bg: 'bg-blue-100',
    text: 'text-blue-800',
    label: 'Completed',
  },
  pending: {
    bg: 'bg-gray-100',
    text: 'text-gray-800',
    label: 'Pending',
  },
  contacted: {
    bg: 'bg-blue-100',
    text: 'text-blue-800',
    label: 'Contacted',
  },
  replied: {
    bg: 'bg-green-100',
    text: 'text-green-800',
    label: 'Replied',
  },
  failed: {
    bg: 'bg-red-100',
    text: 'text-red-800',
    label: 'Failed',
  },
  sent: {
    bg: 'bg-green-100',
    text: 'text-green-800',
    label: 'Sent',
  },
  skipped: {
    bg: 'bg-yellow-100',
    text: 'text-yellow-800',
    label: 'Skipped',
  },
};

export function StatusBadge({ status, size = 'md' }: StatusBadgeProps) {
  const config = statusConfig[status] || {
    bg: 'bg-gray-100',
    text: 'text-gray-800',
    label: status,
  };

  const sizeClasses = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-sm';

  return (
    <span
      className={`inline-flex items-center font-medium rounded-full ${config.bg} ${config.text} ${sizeClasses}`}
    >
      {config.label}
    </span>
  );
}

export default StatusBadge;
