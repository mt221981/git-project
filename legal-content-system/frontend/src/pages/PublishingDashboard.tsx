import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { wordpressApi, articleApi } from '../api/client';
import type { PublishingStatistics, Article } from '../types';
import {
  FiAlertCircle,
  FiRefreshCw,
  FiCalendar,
  FiTrendingUp,
  FiCheckCircle,
} from 'react-icons/fi';

export default function PublishingDashboard() {
  const [selectedSite, setSelectedSite] = useState<number | null>(null);
  const queryClient = useQueryClient();

  const { data: statistics, isLoading } = useQuery<PublishingStatistics>({
    queryKey: ['wordpress-statistics', selectedSite],
    queryFn: () =>
      wordpressApi.getStatistics(selectedSite || undefined).then((res) => res.data),
  });

  const { data: sites } = useQuery({
    queryKey: ['wordpress-sites'],
    queryFn: () => wordpressApi.listSites().then((res) => res.data),
  });

  const { data: failedArticles } = useQuery({
    queryKey: ['articles', 'failed'],
    queryFn: () =>
      articleApi.list({ status: 'failed' }).then((res) => res.data?.items || []),
  });

  const { data: readyArticles } = useQuery({
    queryKey: ['articles', 'ready'],
    queryFn: () =>
      articleApi.list({ status: 'ready' }).then((res) => res.data?.items || []),
  });

  const republishMutation = useMutation({
    mutationFn: (siteId: number) =>
      wordpressApi.republishFailed({ site_id: siteId, max_articles: 10 }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['articles'] });
      queryClient.invalidateQueries({ queryKey: ['wordpress-statistics'] });
      alert('ניסיון הפרסום מחדש הושלם!');
    },
  });

  if (isLoading) return <div>טוען...</div>;

  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-900 mb-8">לוח בקרת פרסום</h1>

      {/* Site Filter */}
      <div className="card mb-6">
        <div className="flex items-center gap-4">
          <label className="font-medium">סינון לפי אתר:</label>
          <select
            value={selectedSite || ''}
            onChange={(e) =>
              setSelectedSite(e.target.value ? Number(e.target.value) : null)
            }
            className="input"
          >
            <option value="">כל האתרים</option>
            {sites?.map((site: any) => (
              <option key={site.id} value={site.id}>
                {site.site_name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Statistics Cards */}
      {statistics && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6 mb-8">
          <StatCard
            title="סה״כ מאמרים"
            value={statistics.total_articles}
            icon={<FiTrendingUp />}
            color="blue"
          />
          <StatCard
            title="מפורסמים"
            value={statistics.published}
            icon={<FiCheckCircle />}
            color="green"
          />
          <StatCard
            title="מוכנים"
            value={statistics.ready}
            icon={<FiCalendar />}
            color="blue"
          />
          <StatCard
            title="טיוטות"
            value={statistics.draft}
            icon={<FiRefreshCw />}
            color="yellow"
          />
          <StatCard
            title="נכשלו"
            value={statistics.failed}
            icon={<FiAlertCircle />}
            color="red"
          />
        </div>
      )}

      {/* Per-Site Statistics */}
      {!selectedSite && statistics?.by_site && (
        <div className="card mb-8">
          <h2 className="text-xl font-bold mb-6">סטטיסטיקות לפי אתר</h2>
          <div className="grid gap-4">
            {Object.entries(statistics.by_site).map(([siteId, siteStats]) => (
              <div
                key={siteId}
                className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
              >
                <div className="flex justify-between items-center mb-3">
                  <div>
                    <h3 className="font-bold text-lg">{siteStats.site_name}</h3>
                    <a
                      href={siteStats.site_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm text-blue-600 hover:underline"
                    >
                      {siteStats.site_url}
                    </a>
                  </div>
                  <span className="text-2xl font-bold text-gray-700">
                    {siteStats.total}
                  </span>
                </div>
                <div className="flex gap-4 text-sm">
                  <div>
                    <span className="text-gray-600">מפורסמים: </span>
                    <span className="font-medium text-green-600">
                      {siteStats.published}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-600">טיוטות: </span>
                    <span className="font-medium text-yellow-600">
                      {siteStats.draft}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Failed Articles Section */}
      {failedArticles && failedArticles.length > 0 && (
        <div className="card mb-8">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-bold flex items-center gap-2">
              <FiAlertCircle className="text-red-600" />
              מאמרים שנכשלו ({failedArticles.length})
            </h2>
            {sites && sites.length > 0 && (
              <button
                onClick={() => republishMutation.mutate(sites[0].id)}
                disabled={republishMutation.isPending}
                className="btn btn-primary flex items-center gap-2"
              >
                <FiRefreshCw />
                נסה לפרסם מחדש
              </button>
            )}
          </div>

          <div className="space-y-3">
            {failedArticles.slice(0, 10).map((article: Article) => (
              <Link
                key={article.id}
                to={`/articles/${article.id}`}
                className="block p-4 border border-red-200 rounded-lg hover:bg-red-50 transition-colors"
              >
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="font-medium text-gray-900">{article.title}</h3>
                    {article.metadata?.last_publish_error && (
                      <p className="text-sm text-red-600 mt-1">
                        שגיאה: {article.metadata.last_publish_error}
                      </p>
                    )}
                  </div>
                  <span className="badge bg-red-200 text-red-800">נכשל</span>
                </div>
              </Link>
            ))}
          </div>

          {failedArticles.length > 10 && (
            <Link
              to="/articles?status=failed"
              className="text-blue-600 hover:underline text-sm mt-4 inline-block"
            >
              צפה בכל המאמרים שנכשלו →
            </Link>
          )}
        </div>
      )}

      {/* Ready to Publish Section */}
      {readyArticles && readyArticles.length > 0 && (
        <div className="card mb-8">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-bold flex items-center gap-2">
              <FiCalendar className="text-blue-600" />
              מוכנים לפרסום ({readyArticles.length})
            </h2>
            <Link to="/articles?status=ready" className="btn btn-primary">
              ניהול תור פרסום
            </Link>
          </div>

          <div className="space-y-3">
            {readyArticles.slice(0, 5).map((article: Article) => (
              <Link
                key={article.id}
                to={`/articles/${article.id}`}
                className="block p-4 border border-blue-200 rounded-lg hover:bg-blue-50 transition-colors"
              >
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="font-medium text-gray-900">{article.title}</h3>
                    <div className="flex gap-3 mt-2 text-sm text-gray-600">
                      <span>{article.word_count} מילים</span>
                      <span>ציון: {article.overall_score}/100</span>
                      {article.focus_keyword && (
                        <span className="text-purple-600">
                          🔑 {article.focus_keyword}
                        </span>
                      )}
                    </div>
                  </div>
                  <span className="badge bg-blue-200 text-blue-800">מוכן</span>
                </div>
              </Link>
            ))}
          </div>

          {readyArticles.length > 5 && (
            <Link
              to="/articles?status=ready"
              className="text-blue-600 hover:underline text-sm mt-4 inline-block"
            >
              צפה בכל המאמרים המוכנים →
            </Link>
          )}
        </div>
      )}

      {/* Queue Management */}
      <QueueManagement />

      {/* Publishing Tips */}
      <div className="card bg-blue-50 border-blue-200">
        <h3 className="font-bold mb-3 flex items-center gap-2">
          <FiCheckCircle className="text-blue-600" />
          טיפים לפרסום יעיל
        </h3>
        <ul className="space-y-2 text-sm text-gray-700">
          <li>• פרסם מאמרים עם ציון איכות מעל 70 לתוצאות SEO מיטביות</li>
          <li>• השתמש בפרסום אצווה (Batch) לפרסום מספר מאמרים בבת אחת</li>
          <li>• בדוק מאמרים שנכשלו באופן קבוע ונסה לפרסם מחדש</li>
          <li>• תכנן תור פרסום ל-5-10 מאמרים ביום לקצב עדכון קבוע</li>
          <li>• התחל עם סטטוס "טיוטה" לבדיקה לפני פרסום סופי</li>
        </ul>
      </div>
    </div>
  );
}

function StatCard({
  title,
  value,
  icon,
  color,
}: {
  title: string;
  value: number;
  icon: React.ReactNode;
  color: string;
}) {
  const colorClasses = {
    blue: 'bg-blue-100 text-blue-600',
    green: 'bg-green-100 text-green-600',
    yellow: 'bg-yellow-100 text-yellow-600',
    red: 'bg-red-100 text-red-600',
  };

  return (
    <div className="card">
      <div className="flex items-start justify-between mb-3">
        <div className={`p-2 rounded-lg ${colorClasses[color as keyof typeof colorClasses]}`}>
          {icon}
        </div>
      </div>
      <h3 className="text-sm font-medium text-gray-600 mb-1">{title}</h3>
      <p className="text-3xl font-bold text-gray-900">{value}</p>
    </div>
  );
}

function QueueManagement() {
  const [showQueueModal, setShowQueueModal] = useState(false);
  const [queueConfig, setQueueConfig] = useState({
    site_id: 0,
    articles_per_day: 5,
    min_score: 70,
  });

  const { data: sites } = useQuery({
    queryKey: ['wordpress-sites'],
    queryFn: () => wordpressApi.listSites().then((res) => res.data),
  });

  // TEMPORARILY DISABLED: Queue scheduling endpoint not implemented in backend yet
  const queueMutation = useMutation({
    mutationFn: async (_config: typeof queueConfig) => {
      console.warn('Queue scheduling not implemented - backend endpoint missing');
      throw new Error('תור פרסום אוטומטי זמין בקרוב - נא להשתמש בפרסום ידני בינתיים');
    },
    onSuccess: () => {
      setShowQueueModal(false);
    },
    onError: (error: any) => {
      alert(error.message || 'שגיאה ביצירת תור פרסום');
    },
  });

  return (
    <div className="card mb-8">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-bold">ניהול תור פרסום</h2>
        <button
          onClick={() => setShowQueueModal(true)}
          className="btn btn-primary"
        >
          צור תור פרסום
        </button>
      </div>

      <p className="text-gray-600 text-sm">
        תכנן מראש את פרסום המאמרים עם תור פרסום מבוקר. קבע כמות מאמרים ליום וציון איכות מינימלי.
      </p>

      {showQueueModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-2xl font-bold mb-6">צור תור פרסום</h3>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">אתר WordPress</label>
                <select
                  value={queueConfig.site_id}
                  onChange={(e) =>
                    setQueueConfig({ ...queueConfig, site_id: Number(e.target.value) })
                  }
                  className="input w-full"
                >
                  <option value={0}>בחר אתר</option>
                  {sites?.map((site: any) => (
                    <option key={site.id} value={site.id}>
                      {site.site_name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">מאמרים ליום</label>
                <input
                  type="number"
                  value={queueConfig.articles_per_day}
                  onChange={(e) =>
                    setQueueConfig({
                      ...queueConfig,
                      articles_per_day: Number(e.target.value),
                    })
                  }
                  min={1}
                  max={20}
                  className="input w-full"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">ציון איכות מינימלי</label>
                <input
                  type="number"
                  value={queueConfig.min_score}
                  onChange={(e) =>
                    setQueueConfig({
                      ...queueConfig,
                      min_score: Number(e.target.value),
                    })
                  }
                  min={0}
                  max={100}
                  className="input w-full"
                />
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  onClick={() => queueMutation.mutate(queueConfig)}
                  disabled={queueMutation.isPending || queueConfig.site_id === 0}
                  className="btn btn-primary flex-1"
                >
                  צור תור
                </button>
                <button
                  onClick={() => setShowQueueModal(false)}
                  className="btn btn-secondary flex-1"
                >
                  ביטול
                </button>
              </div>

              {queueMutation.isError && (
                <div className="text-red-600 text-sm">
                  שגיאה: {queueMutation.error?.toString()}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
