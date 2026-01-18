import { useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { articleApi, wordpressApi } from '../api/client';
import { useState } from 'react';

export default function ArticleDetail() {
  const { id } = useParams<{ id: string }>();
  const [showPublish, setShowPublish] = useState(false);
  const queryClient = useQueryClient();

  const { data: article, isLoading } = useQuery({
    queryKey: ['article', id],
    queryFn: () => articleApi.get(Number(id)).then((res) => res.data),
    enabled: !!id,
  });

  const { data: sites } = useQuery({
    queryKey: ['wordpress-sites'],
    queryFn: () => wordpressApi.listSites().then((res) => res.data),
  });

  const publishMutation = useMutation({
    mutationFn: (data: { site_id: number; status: string }) =>
      wordpressApi.publish(Number(id), data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['article', id] });
      setShowPublish(false);
    },
  });

  if (isLoading) return <div>טוען...</div>;
  if (!article) return <div>מאמר לא נמצא</div>;

  return (
    <div>
      <h1 className="text-3xl font-bold mb-8">{article.title}</h1>

      <div className="grid gap-6">
        <div className="card">
          <h2 className="text-xl font-bold mb-4">פרטים</h2>
          <dl className="grid grid-cols-3 gap-4">
            <div>
              <dt className="text-gray-600">מילים</dt>
              <dd className="font-medium">{article.word_count}</dd>
            </div>
            <div>
              <dt className="text-gray-600">זמן קריאה</dt>
              <dd className="font-medium">{article.reading_time_minutes} דקות</dd>
            </div>
            <div>
              <dt className="text-gray-600">ציון כולל</dt>
              <dd className="font-medium">{article.overall_score}/100</dd>
            </div>
          </dl>
        </div>

        <div className="card">
          <h2 className="text-xl font-bold mb-4">ציונים</h2>
          <div className="grid grid-cols-2 gap-6">
            <ScoreCard label="תוכן" score={article.content_score} color="blue" />
            <ScoreCard label="SEO" score={article.seo_score} color="green" />
            <ScoreCard label="קריאות" score={article.readability_score} color="purple" />
            <ScoreCard label="E-E-A-T" score={article.eeat_score} color="orange" />
          </div>
        </div>

        <div className="card">
          <h2 className="text-xl font-bold mb-4">תוכן</h2>
          <div
            className="prose max-w-none"
            dangerouslySetInnerHTML={{ __html: article.content_html }}
          />
        </div>

        {!showPublish && (
          <button
            onClick={() => setShowPublish(true)}
            className="btn btn-primary"
          >
            פרסם ל-WordPress
          </button>
        )}

        {showPublish && sites && (
          <div className="card">
            <h2 className="text-xl font-bold mb-4">פרסום ל-WordPress</h2>
            <div className="space-y-4">
              {sites.map((site: any) => (
                <button
                  key={site.id}
                  onClick={() =>
                    publishMutation.mutate({
                      site_id: site.id,
                      status: 'publish',
                    })
                  }
                  disabled={publishMutation.isPending}
                  className="btn btn-primary w-full"
                >
                  פרסם ל-{site.site_name}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function ScoreCard({ label, score, color }: { label: string; score: number; color: string }) {
  const colorClasses = {
    blue: {
      bg: 'from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20',
      border: 'border-blue-500/30',
      text: 'text-blue-600 dark:text-blue-400',
      bar: 'bg-blue-600 dark:bg-blue-400',
    },
    green: {
      bg: 'from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20',
      border: 'border-green-500/30',
      text: 'text-green-600 dark:text-green-400',
      bar: 'bg-green-600 dark:bg-green-400',
    },
    purple: {
      bg: 'from-purple-50 to-purple-100 dark:from-purple-900/20 dark:to-purple-800/20',
      border: 'border-purple-500/30',
      text: 'text-purple-600 dark:text-purple-400',
      bar: 'bg-purple-600 dark:bg-purple-400',
    },
    orange: {
      bg: 'from-orange-50 to-orange-100 dark:from-orange-900/20 dark:to-orange-800/20',
      border: 'border-orange-500/30',
      text: 'text-orange-600 dark:text-orange-400',
      bar: 'bg-orange-600 dark:bg-orange-400',
    },
  };

  const classes = colorClasses[color as keyof typeof colorClasses];

  return (
    <div className={`flex flex-col items-center justify-center p-6 bg-gradient-to-br ${classes.bg} rounded-xl border-2 ${classes.border}`}>
      <div className={`text-6xl font-black ${classes.text} mb-2`}>{Math.round(score)}</div>
      <div className="text-sm font-semibold text-[#111618] dark:text-white text-center">{label}</div>
      <div className="w-full mt-4 bg-gray-200 dark:bg-gray-700 rounded-full h-3">
        <div
          className={`${classes.bar} h-3 rounded-full transition-all duration-500`}
          style={{ width: `${score}%` }}
        ></div>
      </div>
    </div>
  );
}
