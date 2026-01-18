import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { articleApi } from '../api/client';

export default function ArticlesList() {
  const { data, isLoading } = useQuery({
    queryKey: ['articles'],
    queryFn: () => articleApi.list().then((res) => res.data),
  });

  if (isLoading) return <div>טוען...</div>;

  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-900 mb-8">מאמרים</h1>

      <div className="grid gap-4">
        {data?.items?.map((article: any) => (
          <Link
            key={article.id}
            to={`/articles/${article.id}`}
            className="card hover:shadow-lg transition-shadow"
          >
            <h3 className="font-bold text-xl mb-2">{article.title}</h3>
            <p className="text-gray-600 text-sm mb-4">{article.excerpt}</p>
            <div className="flex justify-between items-center">
              <div className="flex gap-2">
                <span className="badge bg-blue-100 text-blue-800">
                  {article.word_count} מילים
                </span>
                <span className="badge bg-green-100 text-green-800">
                  ציון: {article.overall_score}
                </span>
              </div>
              <span className={`badge ${getStatusColor(article.publish_status)}`}>
                {article.publish_status}
              </span>
            </div>
          </Link>
        ))}
      </div>
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
