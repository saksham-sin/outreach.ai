import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../auth';
import { campaignsApi } from '../api';
import { Button, Spinner, StatusBadge, EmptyState, Header, Countdown, ConfirmModal, SearchableSelect } from '../components';
import { CampaignStatus } from '../types';
import type { Campaign } from '../types';
import toast from 'react-hot-toast';

type TabFilter = 'all' | CampaignStatus;

interface CampaignWithNextSend extends Campaign {
  nextSendAt?: string | null;
  jobId?: string | null;
}

export function DashboardPage() {
  const { user } = useAuth();
  const [campaigns, setCampaigns] = useState<CampaignWithNextSend[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [sendingNowId, setSendingNowId] = useState<string | null>(null);
  const [showSendConfirm, setShowSendConfirm] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<TabFilter>('all');
  const [selectedTag, setSelectedTag] = useState<string>('all');
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<{ id: string; name: string } | null>(null);
  const [isDeletingId, setIsDeletingId] = useState<string | null>(null);
  const navigate = useNavigate();
  const replyMode = (import.meta.env.VITE_REPLY_MODE || 'SIMULATED').toUpperCase();

  // Redirect to onboarding if profile is not completed
  useEffect(() => {
    if (user && !user.profile_completed) {
      navigate('/onboarding', { replace: true });
    }
  }, [user, navigate]);

  const fetchCampaigns = async () => {
    try {
      const response = await campaignsApi.list();
      const baseCampaigns = response.campaigns;

      const nextSendPairs = await Promise.all(
        baseCampaigns.map(async (campaign) => {
          if (campaign.status !== 'active') {
            return { id: campaign.id, nextSendAt: null, jobId: null };
          }

          try {
            const nextSend = await campaignsApi.getNextSend(campaign.id);
            return {
              id: campaign.id,
              nextSendAt: nextSend.next_send_at,
              jobId: nextSend.job_id,
            };
          } catch {
            return { id: campaign.id, nextSendAt: null, jobId: null };
          }
        })
      );

      const nextSendById = new Map(
        nextSendPairs.map((item) => [item.id, item])
      );

      setCampaigns(
        baseCampaigns.map((campaign) => {
          const nextSend = nextSendById.get(campaign.id);
          return nextSend
            ? { ...campaign, nextSendAt: nextSend.nextSendAt, jobId: nextSend.jobId }
            : campaign;
        })
      );
    } catch {
      // Error handled by API client
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchCampaigns();
    
    // Poll for updates every 30 seconds
    const interval = setInterval(fetchCampaigns, 30000);
    return () => clearInterval(interval);
  }, []);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  const handleSendNow = async (campaignId: string) => {
    setSendingNowId(campaignId);
    
    try {
      await campaignsApi.sendNow(campaignId);
      toast.success('Email sent immediately!');
      setShowSendConfirm(null);
      fetchCampaigns();
    } catch {
      // Error handled by API client
    } finally {
      setSendingNowId(null);
    }
  };

  const handleDelete = async (campaignId: string) => {
    setIsDeletingId(campaignId);
    
    try {
      await campaignsApi.delete(campaignId);
      toast.success('Campaign deleted');
      setShowDeleteConfirm(null);
      fetchCampaigns();
    } catch {
      // Error handled by API client
      toast.error('Failed to delete campaign');
    } finally {
      setIsDeletingId(null);
    }
  };

  // Get all unique tags from campaigns
  const allTags = Array.from(
    new Set(campaigns.flatMap((c) => c.tags || []))
  ).sort((a, b) => a.localeCompare(b));

  // Filter campaigns by status and tag
  const filteredCampaigns = campaigns
    .filter((campaign) => activeTab === 'all' ? true : campaign.status === activeTab)
    .filter((campaign) => {
      if (selectedTag === 'all') return true;
      return campaign.tags?.includes(selectedTag);
    });

  let mainContent: JSX.Element;
  if (isLoading) {
    mainContent = (
      <div className="flex justify-center py-12">
        <Spinner size="lg" />
      </div>
    );
  } else if (campaigns.length === 0) {
    mainContent = (
      <div className="bg-white rounded-lg shadow-sm">
        <EmptyState
          title="No campaigns yet"
          description="Create your first campaign to start reaching out to leads."
          icon={
            <svg
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={1.5}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M21.75 6.75v10.5a2.25 2.25 0 01-2.25 2.25h-15a2.25 2.25 0 01-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25m19.5 0v.243a2.25 2.25 0 01-1.07 1.916l-7.5 4.615a2.25 2.25 0 01-2.36 0L3.32 8.91a2.25 2.25 0 01-1.07-1.916V6.75"
              />
            </svg>
          }
          action={
            <Button onClick={() => navigate('/campaigns/new')}>
              Create Campaign
            </Button>
          }
        />
      </div>
    );
  } else {
    mainContent = (
      <div className="bg-white rounded-lg shadow-sm overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Campaign
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Tags
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Next Send
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Created
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {filteredCampaigns.map((campaign) => (
              <tr
                key={campaign.id}
                className="hover:bg-gray-50 cursor-pointer"
                onClick={() => navigate(`/campaigns/${campaign.id}`)}
              >
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm font-medium text-gray-900">
                    {campaign.name}
                  </div>
                </td>
                <td className="px-6 py-4">
                  {campaign.tags && campaign.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1">
                      {campaign.tags.map((tag) => (
                        <span
                          key={tag}
                          className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <StatusBadge status={campaign.status} />
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  {campaign.status === 'active' && campaign.nextSendAt ? (
                    (() => {
                      const isPast = new Date(campaign.nextSendAt).getTime() <= Date.now();
                      if (isPast) {
                        return (
                          <span className="text-green-600 font-medium">Sent</span>
                        );
                      }
                      return (
                        <div className="flex items-center gap-2">
                          <span className="text-gray-700 w-24">
                            <Countdown 
                              targetTime={campaign.nextSendAt}
                              onComplete={() => fetchCampaigns()}
                            />
                          </span>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setShowSendConfirm(campaign.id);
                            }}
                            className="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition"
                            disabled={sendingNowId === campaign.id}
                          >
                            {sendingNowId === campaign.id ? 'Sending...' : 'Send Now'}
                          </button>
                        </div>
                      );
                    })()
                  ) : (
                    <span className="text-gray-400">-</span>
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {formatDate(campaign.created_at)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                  <div className="flex justify-end gap-2">
                    <Link
                      to={`/campaigns/${campaign.id}`}
                      className="text-blue-600 hover:text-blue-700"
                      onClick={(e) => e.stopPropagation()}
                    >
                      View
                    </Link>
                    {campaign.status === CampaignStatus.DRAFT && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setShowDeleteConfirm({ id: campaign.id, name: campaign.name });
                        }}
                        className="text-red-600 hover:text-red-700"
                      >
                        Delete
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Campaigns</h1>
            <p className="text-xs text-gray-500 mt-1">
              Reply detection: {replyMode}
            </p>
          </div>
          <Button onClick={() => navigate('/campaigns/new')}>
            New Campaign
          </Button>
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-200 mb-6">
          <nav className="-mb-px flex space-x-8">
            {[
              { key: 'all' as const, label: 'All' },
              { key: CampaignStatus.DRAFT, label: 'Draft' },
              { key: CampaignStatus.ACTIVE, label: 'Active' },
              { key: CampaignStatus.PAUSED, label: 'Paused' },
              { key: CampaignStatus.COMPLETED, label: 'Completed' },
            ].map((tab) => {
              const count =
                tab.key === 'all'
                  ? campaigns.length
                  : campaigns.filter((c) => c.status === tab.key).length;

              return (
                <button
                  key={tab.key}
                  onClick={() => setActiveTab(tab.key)}
                  className={`
                    whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors
                    ${
                      activeTab === tab.key
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }
                  `}
                >
                  {tab.label}
                  <span
                    className={`ml-2 py-0.5 px-2 rounded-full text-xs ${
                      activeTab === tab.key
                        ? 'bg-blue-100 text-blue-600'
                        : 'bg-gray-100 text-gray-600'
                    }`}
                  >
                    {count}
                  </span>
                </button>
              );
            })}
          </nav>
        </div>

        {/* Tag Filter */}
        {allTags.length > 0 && (
          <div className="mb-6 max-w-xs">
            <SearchableSelect
              label="Filter by Tag"
              options={allTags}
              value={selectedTag}
              onChange={setSelectedTag}
              placeholder="Search tags..."
              allLabel="All Tags"
            />
          </div>
        )}

        {mainContent}

        {/* Send Now Confirmation Modal */}
        <ConfirmModal
          isOpen={!!showSendConfirm}
          onClose={() => setShowSendConfirm(null)}
          onConfirm={() => {
            if (showSendConfirm) {
              handleSendNow(showSendConfirm);
            }
          }}
          title="Send Next Email Now"
          message="This will send the next scheduled email immediately. Are you sure?"
          confirmText="Send"
          isLoading={!!sendingNowId}
        />

        {/* Delete Campaign Confirmation Modal */}
        <ConfirmModal
          isOpen={!!showDeleteConfirm}
          onClose={() => setShowDeleteConfirm(null)}
          onConfirm={() => {
            if (showDeleteConfirm) {
              handleDelete(showDeleteConfirm.id);
            }
          }}
          title="Delete Campaign?"
          message={`Are you sure you want to delete the draft campaign "${showDeleteConfirm?.name}"? This cannot be undone.`}
          confirmText="Delete"
          confirmVariant="danger"
          isLoading={!!isDeletingId}
        />
      </main>
    </div>
  );
}

export default DashboardPage;
