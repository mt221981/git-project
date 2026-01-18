import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { wordpressApi } from '../api/client';
import type { WordPressSite, WordPressSiteCreate } from '../types';
import { FiPlus, FiTrash2, FiEdit2, FiCheckCircle, FiXCircle } from 'react-icons/fi';

export default function WordPressManagement() {
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingSite, setEditingSite] = useState<WordPressSite | null>(null);
  const queryClient = useQueryClient();

  const { data: sites, isLoading } = useQuery({
    queryKey: ['wordpress-sites'],
    queryFn: () => wordpressApi.listSites().then((res) => res.data),
  });

  const { data: statistics } = useQuery({
    queryKey: ['wordpress-statistics'],
    queryFn: () => wordpressApi.getStatistics().then((res) => res.data),
  });

  const deleteMutation = useMutation({
    mutationFn: (siteId: number) => wordpressApi.deleteSite(siteId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['wordpress-sites'] });
      queryClient.invalidateQueries({ queryKey: ['wordpress-statistics'] });
    },
  });

  if (isLoading) return <div>טוען...</div>;

  return (
    <div>
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900">ניהול אתרי WordPress</h1>
        <button
          onClick={() => setShowAddForm(true)}
          className="btn btn-primary flex items-center gap-2"
        >
          <FiPlus />
          הוסף אתר חדש
        </button>
      </div>

      {/* Statistics Overview */}
      {statistics && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <StatCard title="סה״כ מאמרים" value={statistics.total_articles} color="blue" />
          <StatCard title="מפורסמים" value={statistics.published} color="green" />
          <StatCard title="טיוטות" value={statistics.draft} color="yellow" />
          <StatCard title="נכשלו" value={statistics.failed} color="red" />
        </div>
      )}

      {/* Sites List */}
      <div className="grid gap-6">
        {sites?.map((site: WordPressSite) => (
          <SiteCard
            key={site.id}
            site={site}
            statistics={statistics?.by_site?.[site.id]}
            onEdit={() => setEditingSite(site)}
            onDelete={() => {
              if (confirm(`האם למחוק את האתר "${site.site_name}"?`)) {
                deleteMutation.mutate(site.id);
              }
            }}
          />
        ))}

        {sites?.length === 0 && (
          <div className="card text-center py-12">
            <p className="text-gray-600 mb-4">לא הוגדרו אתרי WordPress</p>
            <button
              onClick={() => setShowAddForm(true)}
              className="btn btn-primary inline-flex items-center gap-2"
            >
              <FiPlus />
              הוסף אתר ראשון
            </button>
          </div>
        )}
      </div>

      {/* Add/Edit Site Modal */}
      {(showAddForm || editingSite) && (
        <SiteForm
          site={editingSite}
          onClose={() => {
            setShowAddForm(false);
            setEditingSite(null);
          }}
        />
      )}
    </div>
  );
}

function StatCard({
  title,
  value,
  color,
}: {
  title: string;
  value: number;
  color: string;
}) {
  return (
    <div className="card">
      <h3 className="text-sm font-medium text-gray-600 mb-2">{title}</h3>
      <p className={`text-3xl font-bold text-${color}-600`}>{value}</p>
    </div>
  );
}

function SiteCard({
  site,
  statistics,
  onEdit,
  onDelete,
}: {
  site: WordPressSite;
  statistics?: any;
  onEdit: () => void;
  onDelete: () => void;
}) {
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<'success' | 'error' | null>(null);

  const handleTest = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      await wordpressApi.testConnection(site.id);
      setTestResult('success');
    } catch (error) {
      setTestResult('error');
    } finally {
      setTesting(false);
    }
  };

  return (
    <div className="card">
      <div className="flex justify-between items-start mb-4">
        <div>
          <div className="flex items-center gap-3">
            <h3 className="text-xl font-bold">{site.site_name}</h3>
            {site.is_active ? (
              <span className="badge bg-green-100 text-green-800 flex items-center gap-1">
                <FiCheckCircle size={14} />
                פעיל
              </span>
            ) : (
              <span className="badge bg-gray-200 text-gray-600 flex items-center gap-1">
                <FiXCircle size={14} />
                לא פעיל
              </span>
            )}
          </div>
          <a
            href={site.site_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-600 hover:underline text-sm"
          >
            {site.site_url}
          </a>
        </div>

        <div className="flex gap-2">
          <button onClick={onEdit} className="btn btn-sm btn-secondary">
            <FiEdit2 />
          </button>
          <button onClick={onDelete} className="btn btn-sm btn-danger">
            <FiTrash2 />
          </button>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
        <div>
          <dt className="text-xs text-gray-600">משתמש</dt>
          <dd className="font-medium">{site.api_username}</dd>
        </div>
        <div>
          <dt className="text-xs text-gray-600">תוסף SEO</dt>
          <dd className="font-medium">{site.seo_plugin === 'yoast' ? 'Yoast' : 'Rank Math'}</dd>
        </div>
        {statistics && (
          <>
            <div>
              <dt className="text-xs text-gray-600">מפורסמים</dt>
              <dd className="font-medium text-green-600">{statistics.published}</dd>
            </div>
            <div>
              <dt className="text-xs text-gray-600">טיוטות</dt>
              <dd className="font-medium text-yellow-600">{statistics.draft}</dd>
            </div>
          </>
        )}
      </div>

      <div className="flex gap-2">
        <button
          onClick={handleTest}
          disabled={testing}
          className="btn btn-sm btn-secondary"
        >
          {testing ? 'בודק...' : 'בדוק חיבור'}
        </button>
        {testResult === 'success' && (
          <span className="text-green-600 text-sm flex items-center gap-1">
            <FiCheckCircle /> חיבור תקין
          </span>
        )}
        {testResult === 'error' && (
          <span className="text-red-600 text-sm flex items-center gap-1">
            <FiXCircle /> חיבור נכשל
          </span>
        )}
      </div>
    </div>
  );
}

function SiteForm({
  site,
  onClose,
}: {
  site: WordPressSite | null;
  onClose: () => void;
}) {
  const queryClient = useQueryClient();
  const [formData, setFormData] = useState<WordPressSiteCreate>({
    site_name: site?.site_name || '',
    site_url: site?.site_url || '',
    api_username: site?.api_username || '',
    api_password: '',
    seo_plugin: site?.seo_plugin || 'yoast',
  });

  const createMutation = useMutation({
    mutationFn: (data: WordPressSiteCreate) => wordpressApi.createSite(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['wordpress-sites'] });
      onClose();
    },
  });

  const updateMutation = useMutation({
    mutationFn: (data: any) => wordpressApi.updateSite(site!.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['wordpress-sites'] });
      onClose();
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (site) {
      updateMutation.mutate(formData);
    } else {
      createMutation.mutate(formData);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
        <h2 className="text-2xl font-bold mb-6">
          {site ? 'ערוך אתר' : 'הוסף אתר WordPress'}
        </h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">שם האתר</label>
            <input
              type="text"
              value={formData.site_name}
              onChange={(e) =>
                setFormData({ ...formData, site_name: e.target.value })
              }
              className="input w-full"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">כתובת URL</label>
            <input
              type="url"
              value={formData.site_url}
              onChange={(e) =>
                setFormData({ ...formData, site_url: e.target.value })
              }
              className="input w-full"
              placeholder="https://example.com"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">שם משתמש</label>
            <input
              type="text"
              value={formData.api_username}
              onChange={(e) =>
                setFormData({ ...formData, api_username: e.target.value })
              }
              className="input w-full"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">
              סיסמת Application Password
            </label>
            <input
              type="password"
              value={formData.api_password}
              onChange={(e) =>
                setFormData({ ...formData, api_password: e.target.value })
              }
              className="input w-full"
              placeholder={site ? '(השאר ריק אם לא משנה)' : ''}
              required={!site}
            />
            <p className="text-xs text-gray-600 mt-1">
              צור Application Password בהגדרות המשתמש ב-WordPress
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">תוסף SEO</label>
            <select
              value={formData.seo_plugin}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  seo_plugin: e.target.value as 'yoast' | 'rankmath',
                })
              }
              className="input w-full"
              required
            >
              <option value="yoast">Yoast SEO</option>
              <option value="rankmath">Rank Math</option>
            </select>
          </div>

          <div className="flex gap-3 pt-4">
            <button
              type="submit"
              disabled={createMutation.isPending || updateMutation.isPending}
              className="btn btn-primary flex-1"
            >
              {site ? 'עדכן' : 'הוסף'}
            </button>
            <button type="button" onClick={onClose} className="btn btn-secondary flex-1">
              ביטול
            </button>
          </div>

          {(createMutation.isError || updateMutation.isError) && (
            <div className="text-red-600 text-sm">
              שגיאה: {(createMutation.error || updateMutation.error)?.toString()}
            </div>
          )}
        </form>
      </div>
    </div>
  );
}
