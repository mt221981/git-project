import { useState, useEffect } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { wordpressApi } from '../api/client';
import { FiX, FiCheckCircle, FiXCircle, FiLoader } from 'react-icons/fi';

interface BulkPublishModalProps {
  selectedArticleIds: number[];
  onClose: () => void;
  onSuccess: () => void;
}

interface BatchProgress {
  status: 'processing' | 'completed' | 'error';
  current: number;
  total: number;
  successful: number[];
  failed: Array<{ article_id: number; error: string }>;
  current_article_id: number | null;
}

export default function BulkPublishModal({
  selectedArticleIds,
  onClose,
  onSuccess,
}: BulkPublishModalProps) {
  const [siteId, setSiteId] = useState<number | null>(null);
  const [status, setStatus] = useState<'draft' | 'publish'>('draft');
  const [stopOnError, setStopOnError] = useState(false);
  const [batchId, setBatchId] = useState<string | null>(null);
  const [progress, setProgress] = useState<BatchProgress | null>(null);
  const [isPublishing, setIsPublishing] = useState(false);

  // Fetch available WordPress sites
  const { data: sitesResponse } = useQuery({
    queryKey: ['wordpress-sites'],
    queryFn: () => wordpressApi.listSites().then((res) => res.data),
  });

  const sites = sitesResponse || [];

  // Start batch publish mutation
  const batchPublishMutation = useMutation({
    mutationFn: (data: {
      article_ids: number[];
      site_id: number;
      status: string;
      stop_on_error: boolean;
    }) => wordpressApi.batchPublish(data),
    onSuccess: (response) => {
      setBatchId(response.data.batch_id);
      setIsPublishing(true);
    },
    onError: (error: any) => {
      alert(`שגיאה: ${error.response?.data?.detail || error.message}`);
      setIsPublishing(false);
    },
  });

  // Poll for progress updates
  useEffect(() => {
    if (!batchId || !isPublishing) return;

    const interval = setInterval(async () => {
      try {
        const response = await wordpressApi.getBatchProgress(batchId);
        setProgress(response.data);

        if (response.data.status === 'completed') {
          setIsPublishing(false);
          clearInterval(interval);
        }
      } catch (error) {
        console.error('Failed to fetch progress:', error);
      }
    }, 2000); // Poll every 2 seconds

    return () => clearInterval(interval);
  }, [batchId, isPublishing]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!siteId) {
      alert('בחר אתר WordPress');
      return;
    }

    batchPublishMutation.mutate({
      article_ids: selectedArticleIds,
      site_id: siteId,
      status: status,
      stop_on_error: stopOnError,
    });
  };

  const handleClose = () => {
    if (isPublishing) {
      if (
        !confirm(
          'הפרסום עדיין מתבצע. האם אתה בטוח שברצונך לסגור? (הפרסום ימשיך ברקע)'
        )
      ) {
        return;
      }
    }

    if (progress?.status === 'completed') {
      onSuccess();
    }
    onClose();
  };

  const getProgressPercentage = () => {
    if (!progress) return 0;
    return Math.round((progress.current / progress.total) * 100);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-background-dark rounded-xl p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
            פרסום מרובה למאמרים
          </h2>
          <button
            onClick={handleClose}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg"
            disabled={isPublishing && !progress}
          >
            <FiX size={24} />
          </button>
        </div>

        {!isPublishing && !progress ? (
          // Configuration form
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg mb-4">
              <p className="text-sm text-blue-800 dark:text-blue-300">
                נבחרו {selectedArticleIds.length} מאמרים לפרסום
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2 text-gray-900 dark:text-white">
                אתר WordPress
              </label>
              <select
                value={siteId || ''}
                onChange={(e) => setSiteId(Number(e.target.value))}
                className="input w-full"
                required
              >
                <option value="">בחר אתר...</option>
                {sites.map((site: any) => (
                  <option key={site.id} value={site.id}>
                    {site.site_name} ({site.site_url})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2 text-gray-900 dark:text-white">
                סטטוס פרסום
              </label>
              <select
                value={status}
                onChange={(e) => setStatus(e.target.value as 'draft' | 'publish')}
                className="input w-full"
              >
                <option value="draft">טיוטה</option>
                <option value="publish">פרסום מיידי</option>
              </select>
            </div>

            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="stopOnError"
                checked={stopOnError}
                onChange={(e) => setStopOnError(e.target.checked)}
                className="w-4 h-4 text-primary border-gray-300 rounded focus:ring-primary"
              />
              <label
                htmlFor="stopOnError"
                className="text-sm text-gray-900 dark:text-white"
              >
                עצור בשגיאה ראשונה
              </label>
            </div>

            <div className="flex gap-3 pt-4">
              <button
                type="submit"
                disabled={batchPublishMutation.isPending}
                className="btn btn-primary flex-1"
              >
                {batchPublishMutation.isPending ? 'מתחיל...' : 'התחל פרסום'}
              </button>
              <button
                type="button"
                onClick={onClose}
                className="btn btn-secondary flex-1"
              >
                ביטול
              </button>
            </div>
          </form>
        ) : (
          // Progress display
          <div className="space-y-6">
            {/* Progress bar */}
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-gray-900 dark:text-white">
                  {progress?.status === 'completed' ? 'הושלם!' : 'מפרסם...'}
                </span>
                <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  {progress ? `${progress.current} מתוך ${progress.total}` : '0 מתוך 0'}
                </span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-4">
                <div
                  className="bg-primary h-4 rounded-full transition-all duration-300 flex items-center justify-center"
                  style={{ width: `${getProgressPercentage()}%` }}
                >
                  {getProgressPercentage() > 10 && (
                    <span className="text-xs font-bold text-white">
                      {getProgressPercentage()}%
                    </span>
                  )}
                </div>
              </div>
            </div>

            {/* Current status */}
            {isPublishing && progress && (
              <div className="flex items-center gap-2 text-blue-600 dark:text-blue-400">
                <FiLoader className="animate-spin" size={20} />
                <span className="text-sm">
                  מפרסם מאמר {progress.current_article_id || '...'}
                </span>
              </div>
            )}

            {/* Statistics */}
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-green-50 dark:bg-green-900/20 p-4 rounded-lg">
                <div className="flex items-center gap-2 mb-1">
                  <FiCheckCircle className="text-green-600 dark:text-green-400" />
                  <span className="text-sm font-medium text-gray-900 dark:text-white">
                    הצליחו
                  </span>
                </div>
                <p className="text-2xl font-bold text-green-600 dark:text-green-400">
                  {progress?.successful?.length || 0}
                </p>
              </div>

              <div className="bg-red-50 dark:bg-red-900/20 p-4 rounded-lg">
                <div className="flex items-center gap-2 mb-1">
                  <FiXCircle className="text-red-600 dark:text-red-400" />
                  <span className="text-sm font-medium text-gray-900 dark:text-white">
                    נכשלו
                  </span>
                </div>
                <p className="text-2xl font-bold text-red-600 dark:text-red-400">
                  {progress?.failed?.length || 0}
                </p>
              </div>
            </div>

            {/* Failed articles list */}
            {progress && progress.failed.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold mb-2 text-gray-900 dark:text-white">
                  מאמרים שנכשלו:
                </h3>
                <div className="space-y-2 max-h-40 overflow-y-auto">
                  {progress.failed.map((failure, idx) => (
                    <div
                      key={idx}
                      className="bg-red-50 dark:bg-red-900/20 p-3 rounded-lg text-sm"
                    >
                      <p className="font-medium text-red-900 dark:text-red-300">
                        מאמר #{failure.article_id}
                      </p>
                      <p className="text-red-700 dark:text-red-400 text-xs mt-1">
                        {failure.error}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Actions */}
            {progress?.status === 'completed' && (
              <div className="flex gap-3 pt-4">
                <button onClick={handleClose} className="btn btn-primary flex-1">
                  סגור
                </button>
                {progress.failed.length > 0 && (
                  <button
                    onClick={() => {
                      // TODO: Implement retry for failed articles
                      alert('תכונת ניסיון חוזר תוסף בקרוב');
                    }}
                    className="btn btn-secondary flex-1"
                  >
                    נסה שוב את הכשלונות
                  </button>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
