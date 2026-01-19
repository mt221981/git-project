import { useQuery } from '@tanstack/react-query';
import { verdictApi, articleApi } from '../api/client';
import { useNavigate } from 'react-router-dom';

interface Stats {
  total_verdicts: number;
  anonymized_verdicts: number;
  total_articles: number;
  published_articles: number;
  verdicts_by_status: {
    new: number;
    extracted: number;
    anonymizing: number;
    anonymized: number;
    analyzed: number;
    article_created: number;
  };
  quality_scores: {
    content: number;
    seo: number;
    readability: number;
    eeat: number;
  };
}

export default function Dashboard() {
  const navigate = useNavigate();

  const { data: verdictStats } = useQuery({
    queryKey: ['verdict-stats'],
    queryFn: async () => {
      const response = await verdictApi.getStats();
      return response.data;
    },
    staleTime: 10000,
    refetchInterval: 10000,
    refetchOnWindowFocus: true,
  });

  const { data: articleStats } = useQuery({
    queryKey: ['article-stats'],
    queryFn: async () => {
      const response = await articleApi.getStats();
      return response.data;
    },
    staleTime: 10000,
    refetchInterval: 10000,
    refetchOnWindowFocus: true,
  });

  const { data: verdictsList } = useQuery({
    queryKey: ['verdicts-recent'],
    queryFn: async () => {
      const response = await verdictApi.list({ limit: 5 });
      return response.data;
    },
    staleTime: 10000,
    refetchInterval: 10000,
    refetchOnWindowFocus: true,
  });

  // Calculate stats from API data
  const stats: Stats = {
    total_verdicts: verdictStats?.total || 0,
    anonymized_verdicts: verdictStats?.by_status?.anonymized || 0,
    total_articles: articleStats?.total || 0,
    published_articles: articleStats?.by_status?.published || 0,
    verdicts_by_status: {
      new: verdictStats?.by_status?.new || 0,
      extracted: verdictStats?.by_status?.extracted || 0,
      anonymizing: verdictStats?.by_status?.anonymizing || 0,
      anonymized: verdictStats?.by_status?.anonymized || 0,
      analyzed: verdictStats?.by_status?.analyzed || 0,
      article_created: verdictStats?.by_status?.article_created || 0,
    },
    quality_scores: {
      content: articleStats?.average_scores?.content || 0,
      seo: articleStats?.average_scores?.seo || 0,
      readability: articleStats?.average_scores?.readability || 0,
      eeat: articleStats?.average_scores?.eeat || 0,
    },
  };

  const recentActivities = verdictsList?.items || [];

  return (
    <main className="px-4 md:px-10 lg:px-40 py-8 max-w-[1440px] mx-auto w-full">
        {/* Page Heading */}
        <div className="flex flex-wrap justify-between items-end gap-3 mb-8">
          <div className="flex min-w-72 flex-col gap-2">
            <h1 className="text-[#111618] dark:text-white text-4xl font-black leading-tight tracking-[-0.033em]">
              לוח בקרה (Dashboard)
            </h1>
            <p className="text-[#607c8a] text-lg font-normal leading-normal">
              סקירה כללית של מערכת ניהול התוכן המשפטי והמרת פסקי דין
            </p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={() => navigate('/upload')}
              className="flex min-w-[140px] cursor-pointer items-center justify-center overflow-hidden rounded-xl h-12 px-5 bg-primary text-white font-bold leading-normal hover:bg-primary/90 transition-all shadow-lg shadow-primary/20"
            >
              <span className="material-symbols-outlined ml-2">upload_file</span>
              <span className="truncate">העלאת פסק דין חדש</span>
            </button>
            <button
              onClick={() => navigate('/verdicts')}
              className="flex min-w-[140px] cursor-pointer items-center justify-center overflow-hidden rounded-xl h-12 px-5 bg-white dark:bg-[#1c2a31] border border-[#dbe2e6] dark:border-[#2d3a41] text-[#111618] dark:text-white font-bold leading-normal hover:bg-gray-50 dark:hover:bg-gray-800 transition-all"
            >
              <span className="material-symbols-outlined ml-2">list_alt</span>
              <span className="truncate">צפייה בכל פסקי הדין</span>
            </button>
          </div>
        </div>

        {/* Stats Row */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <button
            onClick={() => navigate('/verdicts')}
            className="flex flex-col gap-2 rounded-xl p-6 border border-[#dbe2e6] dark:border-[#2d3a41] bg-white dark:bg-[#1c2a31] shadow-sm hover:shadow-md hover:border-primary transition-all cursor-pointer text-right"
          >
            <div className="flex justify-between items-start">
              <p className="text-[#607c8a] dark:text-gray-400 text-base font-medium leading-normal">
                סה"כ פסקי דין
              </p>
              <span className="material-symbols-outlined text-primary">history_edu</span>
            </div>
            <p className="text-[#111618] dark:text-white tracking-light text-3xl font-bold leading-tight">
              {stats.total_verdicts.toLocaleString()}
            </p>
          </button>

          <button
            onClick={() => navigate('/verdicts?status=anonymized')}
            className="flex flex-col gap-2 rounded-xl p-6 border border-[#dbe2e6] dark:border-[#2d3a41] bg-white dark:bg-[#1c2a31] shadow-sm hover:shadow-md hover:border-primary transition-all cursor-pointer text-right"
          >
            <div className="flex justify-between items-start">
              <p className="text-[#607c8a] dark:text-gray-400 text-base font-medium leading-normal">
                עברו אנונימיזציה
              </p>
              <span className="material-symbols-outlined text-primary">security</span>
            </div>
            <p className="text-[#111618] dark:text-white tracking-light text-3xl font-bold leading-tight">
              {stats.anonymized_verdicts.toLocaleString()}
            </p>
          </button>

          <button
            onClick={() => navigate('/articles')}
            className="flex flex-col gap-2 rounded-xl p-6 border border-[#dbe2e6] dark:border-[#2d3a41] bg-white dark:bg-[#1c2a31] shadow-sm hover:shadow-md hover:border-primary transition-all cursor-pointer text-right"
          >
            <div className="flex justify-between items-start">
              <p className="text-[#607c8a] dark:text-gray-400 text-base font-medium leading-normal">
                סה"כ כתבות (SEO)
              </p>
              <span className="material-symbols-outlined text-primary">article</span>
            </div>
            <p className="text-[#111618] dark:text-white tracking-light text-3xl font-bold leading-tight">
              {stats.total_articles.toLocaleString()}
            </p>
          </button>

          <button
            onClick={() => navigate('/publishing')}
            className="flex flex-col gap-2 rounded-xl p-6 border border-[#dbe2e6] dark:border-[#2d3a41] bg-white dark:bg-[#1c2a31] shadow-sm hover:shadow-md hover:border-primary transition-all cursor-pointer text-right"
          >
            <div className="flex justify-between items-start">
              <p className="text-[#607c8a] dark:text-gray-400 text-base font-medium leading-normal">
                פורסמו ב-WordPress
              </p>
              <span className="material-symbols-outlined text-primary">cloud_done</span>
            </div>
            <p className="text-[#111618] dark:text-white tracking-light text-3xl font-bold leading-tight">
              {stats.published_articles.toLocaleString()}
            </p>
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Status Breakdown Card */}
          <div className="bg-white dark:bg-[#1c2a31] rounded-xl border border-[#dbe2e6] dark:border-[#2d3a41] p-6 shadow-sm">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-[#111618] dark:text-white text-xl font-bold leading-tight">
                סטטוס טיפול בפסקי דין
              </h2>
              <button
                onClick={() => navigate('/verdicts')}
                className="text-primary text-sm font-bold hover:underline"
              >
                פרטים נוספים
              </button>
            </div>
            <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
              <button
                onClick={() => navigate('/verdicts?status=new')}
                className="flex items-center gap-3 rounded-lg border border-[#dbe2e6] dark:border-[#2d3a41] p-3 bg-background-light dark:bg-background-dark/50 hover:border-primary hover:shadow-md transition-all cursor-pointer text-right"
              >
                <div className="bg-blue-100 dark:bg-blue-900/30 p-2 rounded-lg text-blue-600 dark:text-blue-400 shrink-0">
                  <span className="material-symbols-outlined text-xl">new_releases</span>
                </div>
                <div className="min-w-0">
                  <h3 className="text-[#111618] dark:text-white text-sm font-bold truncate">חדש</h3>
                  <p className="text-[#607c8a] dark:text-gray-400 text-xs font-medium">
                    {stats.verdicts_by_status.new}
                  </p>
                </div>
              </button>

              <button
                onClick={() => navigate('/verdicts?status=extracted')}
                className="flex items-center gap-3 rounded-lg border border-[#dbe2e6] dark:border-[#2d3a41] p-3 bg-background-light dark:bg-background-dark/50 hover:border-primary hover:shadow-md transition-all cursor-pointer text-right"
              >
                <div className="bg-amber-100 dark:bg-amber-900/30 p-2 rounded-lg text-amber-600 dark:text-amber-400 shrink-0">
                  <span className="material-symbols-outlined text-xl">description</span>
                </div>
                <div className="min-w-0">
                  <h3 className="text-[#111618] dark:text-white text-sm font-bold truncate">הופק</h3>
                  <p className="text-[#607c8a] dark:text-gray-400 text-xs font-medium">
                    {stats.verdicts_by_status.extracted}
                  </p>
                </div>
              </button>

              <button
                onClick={() => navigate('/verdicts?status=anonymizing')}
                className="flex items-center gap-3 rounded-lg border border-[#dbe2e6] dark:border-[#2d3a41] p-3 bg-background-light dark:bg-background-dark/50 hover:border-primary hover:shadow-md transition-all cursor-pointer text-right"
              >
                <div className="bg-purple-100 dark:bg-purple-900/30 p-2 rounded-lg text-purple-600 dark:text-purple-400 shrink-0">
                  <span className="material-symbols-outlined text-xl">privacy_tip</span>
                </div>
                <div className="min-w-0">
                  <h3 className="text-[#111618] dark:text-white text-sm font-bold truncate">מאנונם</h3>
                  <p className="text-[#607c8a] dark:text-gray-400 text-xs font-medium">
                    {stats.verdicts_by_status.anonymizing}
                  </p>
                </div>
              </button>

              <button
                onClick={() => navigate('/verdicts?status=anonymized')}
                className="flex items-center gap-3 rounded-lg border border-[#dbe2e6] dark:border-[#2d3a41] p-3 bg-background-light dark:bg-background-dark/50 hover:border-primary hover:shadow-md transition-all cursor-pointer text-right"
              >
                <div className="bg-indigo-100 dark:bg-indigo-900/30 p-2 rounded-lg text-indigo-600 dark:text-indigo-400 shrink-0">
                  <span className="material-symbols-outlined text-xl">verified_user</span>
                </div>
                <div className="min-w-0">
                  <h3 className="text-[#111618] dark:text-white text-sm font-bold truncate">אנונימי</h3>
                  <p className="text-[#607c8a] dark:text-gray-400 text-xs font-medium">
                    {stats.verdicts_by_status.anonymized}
                  </p>
                </div>
              </button>

              <button
                onClick={() => navigate('/verdicts?status=analyzed')}
                className="flex items-center gap-3 rounded-lg border border-[#dbe2e6] dark:border-[#2d3a41] p-3 bg-background-light dark:bg-background-dark/50 hover:border-primary hover:shadow-md transition-all cursor-pointer text-right"
              >
                <div className="bg-cyan-100 dark:bg-cyan-900/30 p-2 rounded-lg text-cyan-600 dark:text-cyan-400 shrink-0">
                  <span className="material-symbols-outlined text-xl">psychology</span>
                </div>
                <div className="min-w-0">
                  <h3 className="text-[#111618] dark:text-white text-sm font-bold truncate">נותח</h3>
                  <p className="text-[#607c8a] dark:text-gray-400 text-xs font-medium">
                    {stats.verdicts_by_status.analyzed}
                  </p>
                </div>
              </button>

              <button
                onClick={() => navigate('/verdicts?status=article_created')}
                className="flex items-center gap-3 rounded-lg border border-[#dbe2e6] dark:border-[#2d3a41] p-3 bg-background-light dark:bg-background-dark/50 hover:border-primary hover:shadow-md transition-all cursor-pointer text-right"
              >
                <div className="bg-green-100 dark:bg-green-900/30 p-2 rounded-lg text-green-600 dark:text-green-400 shrink-0">
                  <span className="material-symbols-outlined text-xl">article</span>
                </div>
                <div className="min-w-0">
                  <h3 className="text-[#111618] dark:text-white text-sm font-bold truncate">מאמר</h3>
                  <p className="text-[#607c8a] dark:text-gray-400 text-xs font-medium">
                    {stats.verdicts_by_status.article_created}
                  </p>
                </div>
              </button>
            </div>
          </div>

          {/* Quality Score Overview Card */}
          <div className="bg-white dark:bg-[#1c2a31] rounded-xl border border-[#dbe2e6] dark:border-[#2d3a41] p-6 shadow-sm">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-[#111618] dark:text-white text-xl font-bold leading-tight">
                מדדי איכות תוכן (ממוצע)
              </h2>
            </div>
            <div className="grid grid-cols-2 gap-6">
              <div className="flex flex-col items-center justify-center p-6 bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 rounded-xl border-2 border-primary/30">
                <div className="text-6xl font-black text-primary mb-2">{Math.round(stats.quality_scores.content)}</div>
                <div className="text-sm font-semibold text-[#111618] dark:text-white text-center">איכות תוכן משפטי</div>
                <div className="w-full mt-4 bg-gray-200 dark:bg-gray-700 rounded-full h-3">
                  <div
                    className="bg-primary h-3 rounded-full transition-all duration-500"
                    style={{ width: `${stats.quality_scores.content}%` }}
                  ></div>
                </div>
              </div>

              <div className="flex flex-col items-center justify-center p-6 bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20 rounded-xl border-2 border-green-500/30">
                <div className="text-6xl font-black text-green-600 dark:text-green-400 mb-2">{Math.round(stats.quality_scores.seo)}</div>
                <div className="text-sm font-semibold text-[#111618] dark:text-white text-center">אופטימיזציית SEO</div>
                <div className="w-full mt-4 bg-gray-200 dark:bg-gray-700 rounded-full h-3">
                  <div
                    className="bg-green-600 dark:bg-green-400 h-3 rounded-full transition-all duration-500"
                    style={{ width: `${stats.quality_scores.seo}%` }}
                  ></div>
                </div>
              </div>

              <div className="flex flex-col items-center justify-center p-6 bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900/20 dark:to-purple-800/20 rounded-xl border-2 border-purple-500/30">
                <div className="text-6xl font-black text-purple-600 dark:text-purple-400 mb-2">{Math.round(stats.quality_scores.readability)}</div>
                <div className="text-sm font-semibold text-[#111618] dark:text-white text-center">קריאות ונגישות</div>
                <div className="w-full mt-4 bg-gray-200 dark:bg-gray-700 rounded-full h-3">
                  <div
                    className="bg-purple-600 dark:bg-purple-400 h-3 rounded-full transition-all duration-500"
                    style={{ width: `${stats.quality_scores.readability}%` }}
                  ></div>
                </div>
              </div>

              <div className="flex flex-col items-center justify-center p-6 bg-gradient-to-br from-orange-50 to-orange-100 dark:from-orange-900/20 dark:to-orange-800/20 rounded-xl border-2 border-orange-500/30">
                <div className="text-6xl font-black text-orange-600 dark:text-orange-400 mb-2">{Math.round(stats.quality_scores.eeat)}</div>
                <div className="text-sm font-semibold text-[#111618] dark:text-white text-center">ציון E-E-A-T</div>
                <div className="w-full mt-4 bg-gray-200 dark:bg-gray-700 rounded-full h-3">
                  <div
                    className="bg-orange-600 dark:bg-orange-400 h-3 rounded-full transition-all duration-500"
                    style={{ width: `${stats.quality_scores.eeat}%` }}
                  ></div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Recent Activity */}
        <div className="mt-12 flex items-center justify-between px-4 pb-3 pt-5">
          <h2 className="text-[#111618] dark:text-white text-[22px] font-bold leading-tight tracking-[-0.015em]">
            פעילות אחרונה במערכת
          </h2>
          <button
            onClick={() => navigate('/verdicts')}
            className="text-primary text-sm font-bold hover:underline"
          >
            לכל הפעילויות
          </button>
        </div>

        <div className="bg-white dark:bg-[#1c2a31] rounded-xl border border-[#dbe2e6] dark:border-[#2d3a41] overflow-hidden shadow-sm">
          <div className="divide-y divide-[#dbe2e6] dark:divide-[#2d3a41]">
            {recentActivities.length === 0 ? (
              <div className="p-8 text-center text-[#607c8a]">אין פעילות אחרונה</div>
            ) : (
              recentActivities.map((verdict: any) => (
                <div
                  key={verdict.id}
                  className="p-4 flex items-center gap-4 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
                >
                  <div className="size-10 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center text-blue-600">
                    <span className="material-symbols-outlined">description</span>
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-bold text-[#111618] dark:text-white">
                      {verdict.case_number_display || verdict.case_number}
                    </p>
                    <p className="text-xs text-[#607c8a] dark:text-gray-400">
                      {verdict.court_name} • {verdict.status}
                    </p>
                  </div>
                  <button
                    onClick={() => navigate(`/verdicts/${verdict.id}`)}
                    className="text-sm text-primary font-medium px-3 py-1 rounded-lg hover:bg-primary/10"
                  >
                    צפייה
                  </button>
                </div>
              ))
            )}
          </div>
        </div>
      </main>
  );
}
