import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link, useSearchParams } from 'react-router-dom';
import { articleApi, wordpressApi } from '../api/client';
import type { Article, PublishStatus } from '../types';
import { FiCheckSquare, FiSquare, FiUpload, FiFilter } from 'react-icons/fi';
import BulkPublishModal from '../components/BulkPublishModal';

export default function ArticlesList() {
  const [searchParams, setSearchParams] = useSearchParams();
  const statusFromUrl = searchParams.get('status') as PublishStatus | null;

  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [statusFilter, setStatusFilter] = useState<PublishStatus | 'all'>(statusFromUrl || 'all');
  const [showBatchPublish, setShowBatchPublish] = useState(false);
  const queryClient = useQueryClient();

  // Sync URL params with filter state
  useEffect(() => {
    if (statusFromUrl && statusFromUrl !== statusFilter) {
      setStatusFilter(statusFromUrl);
    }
  }, [statusFromUrl]);

  // Update URL when filter changes
  const handleStatusChange = (status: PublishStatus | 'all') => {
    setStatusFilter(status);
    if (status && status !== 'all') {
      setSearchParams({ status });
    } else {
      setSearchParams({});
    }
  };

  const { data, isLoading } = useQuery({
    queryKey: ['articles', statusFilter],
    queryFn: () =>
      articleApi
        .list({ status: statusFilter === 'all' ? undefined : statusFilter })
        .then((res) => res.data),
  });

  const articles: Article[] = data?.items || [];

  const toggleSelection = (id: number) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  const selectAll = () => {
    const limit = Math.min(articles.length, 100); // Limit to 100 articles
    if (selectedIds.length === limit) {
      setSelectedIds([]);
    } else {
      setSelectedIds(articles.slice(0, limit).map((a) => a.id));
    }
  };

  const handleBulkPublishSuccess = () => {
    queryClient.invalidateQueries({ queryKey: ['articles'] });
    setSelectedIds([]);
  };

  if (isLoading) return <div>טוען...</div>;

  return (
    <div>
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">מאמרים</h1>

        {selectedIds.length > 0 && (
          <div className="flex gap-2">
            <button
              onClick={() => setShowBatchPublish(true)}
              className="btn btn-primary flex items-center gap-2"
              disabled={selectedIds.length > 100}
            >
              <FiUpload />
              פרסם {selectedIds.length} מאמרים
              {selectedIds.length > 100 && ' (מקסימום 100)'}
            </button>
            <button
              onClick={() => setSelectedIds([])}
              className="btn btn-secondary"
            >
              בטל בחירה
            </button>
          </div>
        )}
      </div>

      {/* Filters */}
      <div className="card mb-6">
        <div className="flex items-center gap-4">
          <FiFilter className="text-gray-600" />
          <select
            value={statusFilter}
            onChange={(e) => handleStatusChange(e.target.value as PublishStatus | 'all')}
            className="input"
          >
            <option value="all">כל הסטטוסים</option>
            <option value="draft">טיוטה</option>
            <option value="ready">מוכן לפרסום</option>
            <option value="published">מפורסם</option>
            <option value="failed">נכשל</option>
          </select>

          {articles.length > 0 && (
            <button
              onClick={selectAll}
              className="btn btn-sm btn-secondary flex items-center gap-2 mr-auto"
            >
              {selectedIds.length === articles.length ? (
                <>
                  <FiCheckSquare />
                  בטל הכל
                </>
              ) : (
                <>
                  <FiSquare />
                  בחר הכל
                </>
              )}
            </button>
          )}
        </div>
      </div>

      {/* Articles Grid */}
      <div className="grid gap-4">
        {articles.map((article) => (
          <div key={article.id} className="card hover:shadow-lg transition-shadow">
            <div className="flex gap-4">
              {/* Selection Checkbox */}
              <div className="flex items-start pt-1">
                <button
                  onClick={() => toggleSelection(article.id)}
                  className="text-2xl text-gray-400 hover:text-gray-600"
                >
                  {selectedIds.includes(article.id) ? <FiCheckSquare /> : <FiSquare />}
                </button>
              </div>

              {/* Article Content */}
              <Link
                to={`/articles/${article.id}`}
                className="flex-1"
              >
                <h3 className="font-bold text-xl mb-2">{article.title}</h3>
                <p className="text-gray-600 text-sm mb-4 line-clamp-2">
                  {article.excerpt}
                </p>
                <div className="flex justify-between items-center">
                  <div className="flex gap-2 flex-wrap">
                    <span className="badge bg-blue-100 text-blue-800">
                      {article.word_count} מילים
                    </span>
                    <span className="badge bg-green-100 text-green-800">
                      ציון: {article.overall_score}
                    </span>
                    {article.focus_keyword && (
                      <span className="badge bg-purple-100 text-purple-800">
                        {article.focus_keyword}
                      </span>
                    )}
                  </div>
                  <span className={`badge ${getStatusColor(article.publish_status)}`}>
                    {getStatusLabel(article.publish_status)}
                  </span>
                </div>
              </Link>
            </div>
          </div>
        ))}

        {articles.length === 0 && (
          <div className="card text-center py-12">
            <p className="text-gray-600">לא נמצאו מאמרים</p>
          </div>
        )}
      </div>

      {/* Bulk Publish Modal */}
      {showBatchPublish && (
        <BulkPublishModal
          selectedArticleIds={selectedIds}
          onClose={() => setShowBatchPublish(false)}
          onSuccess={handleBulkPublishSuccess}
        />
      )}
    </div>
  );
}

function getStatusColor(status: string): string {
  const colors: Record<string, string> = {
    draft: 'bg-gray-200 text-gray-800',
    ready: 'bg-blue-200 text-blue-800',
    published: 'bg-green-200 text-green-800',
    failed: 'bg-red-200 text-red-800',
  };
  return colors[status] || colors.draft;
}

function getStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    draft: 'טיוטה',
    ready: 'מוכן',
    published: 'מפורסם',
    failed: 'נכשל',
  };
  return labels[status] || status;
}
