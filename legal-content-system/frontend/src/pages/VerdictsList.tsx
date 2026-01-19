import { useQuery } from '@tanstack/react-query';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { verdictApi } from '../api/client';
import { useState } from 'react';

export default function VerdictsList() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const statusFromUrl = searchParams.get('status');
  const [searchQuery, _setSearchQuery] = useState('');

  const { data, isLoading, error } = useQuery({
    queryKey: ['verdicts', statusFromUrl],
    queryFn: async () => {
      const response = await verdictApi.list({ status: statusFromUrl || undefined });
      return response.data;
    },
    staleTime: 10000,
    refetchOnWindowFocus: false,
  });

  const handleStatusFilter = (status: string) => {
    if (status) {
      setSearchParams({ status });
    } else {
      setSearchParams({});
    }
  };

  const filteredVerdicts = data?.items?.filter((verdict: any) => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      verdict.case_number?.toLowerCase().includes(query) ||
      verdict.case_number_display?.toLowerCase().includes(query) ||
      verdict.court_name?.toLowerCase().includes(query)
    );
  }) || [];

  return (
    <div className="p-8">
        {/* Page Heading */}
        <div className="flex flex-wrap items-center justify-between gap-4 mb-8">
          <div>
            <h2 className="text-[#111618] dark:text-white text-3xl font-black tracking-tight">פסקי דין</h2>
            <p className="text-[#607c8a] text-sm mt-1">
              נהל את מסמכי בית המשפט והמר אותם לתוכן מותאם SEO
            </p>
          </div>
          <button
            onClick={() => navigate('/upload')}
            className="flex items-center gap-2 bg-primary hover:bg-primary/90 text-white px-6 py-3 rounded-xl font-bold transition-all shadow-lg shadow-primary/20"
          >
            <span className="material-symbols-outlined">add</span>
            <span>העלאה חדשה</span>
          </button>
        </div>

        {/* Filters/Chips */}
        <div className="flex flex-wrap items-center gap-3 mb-6">
          <button
            onClick={() => handleStatusFilter('')}
            className={`flex items-center gap-2 h-10 px-4 rounded-xl text-sm font-semibold ${
              !statusFromUrl
                ? 'bg-primary text-white'
                : 'bg-white dark:bg-gray-800 border border-[#dbe2e6] dark:border-gray-700 hover:border-primary transition-colors'
            }`}
          >
            <span>הכל</span>
            <span className={!statusFromUrl ? 'bg-white/20 px-2 rounded-md text-xs' : 'bg-gray-100 dark:bg-gray-700 px-2 rounded-md text-xs'}>
              {data?.total || 0}
            </span>
          </button>

          <button
            onClick={() => handleStatusFilter('new')}
            className={`flex items-center gap-2 h-10 px-4 rounded-xl text-sm font-medium transition-colors ${
              statusFromUrl === 'new'
                ? 'bg-primary text-white'
                : 'bg-white dark:bg-gray-800 border border-[#dbe2e6] dark:border-gray-700 hover:border-primary'
            }`}
          >
            <span>ממתין לניתוח</span>
            <span className="material-symbols-outlined text-sm">schedule</span>
          </button>

          <button
            onClick={() => handleStatusFilter('analyzed')}
            className={`flex items-center gap-2 h-10 px-4 rounded-xl text-sm font-medium transition-colors ${
              statusFromUrl === 'analyzed'
                ? 'bg-primary text-white'
                : 'bg-white dark:bg-gray-800 border border-[#dbe2e6] dark:border-gray-700 hover:border-primary'
            }`}
          >
            <span>נותח</span>
            <span className="material-symbols-outlined text-sm">psychology</span>
          </button>

          <button
            onClick={() => handleStatusFilter('published')}
            className={`flex items-center gap-2 h-10 px-4 rounded-xl text-sm font-medium transition-colors ${
              statusFromUrl === 'published'
                ? 'bg-primary text-white'
                : 'bg-white dark:bg-gray-800 border border-[#dbe2e6] dark:border-gray-700 hover:border-primary'
            }`}
          >
            <span>פורסם</span>
            <span className="material-symbols-outlined text-sm">check_circle</span>
          </button>
        </div>

        {/* Table Container */}
        <div className="bg-white dark:bg-background-dark border border-[#dbe2e6] dark:border-gray-800 rounded-xl overflow-hidden shadow-sm">
          {isLoading ? (
            <div className="p-8 text-center text-[#607c8a]">טוען...</div>
          ) : error ? (
            <div className="p-8 text-center text-red-600">
              שגיאה בטעינת פסקי הדין: {(error as Error).message}
            </div>
          ) : filteredVerdicts.length === 0 ? (
            <div className="p-8 text-center text-[#607c8a]">
              {searchQuery ? 'לא נמצאו תוצאות' : 'אין פסקי דין במערכת. לחץ על "העלאה חדשה" כדי להוסיף.'}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-right border-collapse">
                <thead>
                  <tr className="bg-[#fcfdfe] dark:bg-gray-900/50 border-b border-[#dbe2e6] dark:border-gray-800">
                    <th className="px-6 py-4 text-sm font-semibold text-[#111618] dark:text-white">מזהה תיק</th>
                    <th className="px-6 py-4 text-sm font-semibold text-[#111618] dark:text-white">שם בית המשפט</th>
                    <th className="px-6 py-4 text-sm font-semibold text-[#111618] dark:text-white">תאריך יצירה</th>
                    <th className="px-6 py-4 text-sm font-semibold text-[#111618] dark:text-white text-center">
                      סטטוס
                    </th>
                    <th className="px-6 py-4 text-sm font-semibold text-[#111618] dark:text-white">פעולות</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#f0f3f5] dark:divide-gray-800">
                  {filteredVerdicts.map((verdict: any) => (
                    <tr
                      key={verdict.id}
                      className="hover:bg-background-light dark:hover:bg-gray-800/50 transition-colors group"
                    >
                      <td className="px-6 py-5">
                        <div className="flex flex-col">
                          <span className="text-sm font-bold text-primary">
                            {verdict.case_number_display || verdict.case_number || `#${verdict.id}`}
                          </span>
                          <span className="text-xs text-[#607c8a]">{verdict.file_hash?.substring(0, 8)}</span>
                        </div>
                      </td>
                      <td className="px-6 py-5 text-sm text-[#111618] dark:text-gray-300">
                        {verdict.court_name || 'בית משפט לא ידוע'}
                      </td>
                      <td className="px-6 py-5 text-sm text-[#607c8a]">
                        {new Date(verdict.created_at).toLocaleDateString('he-IL')}
                      </td>
                      <td className="px-6 py-5">
                        <div className="flex justify-center">
                          <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-bold ${getStatusStyle(verdict.status)}`}>
                            <span className={`size-1.5 ${getStatusDotColor(verdict.status)} rounded-full ml-1.5`}></span>
                            {getStatusLabel(verdict.status)}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-5">
                        <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                          <button
                            onClick={() => navigate(`/verdicts/${verdict.id}`)}
                            className="p-2 hover:bg-white dark:hover:bg-gray-700 rounded-lg text-[#607c8a] hover:text-primary transition-colors"
                            title="צפייה"
                          >
                            <span className="material-symbols-outlined text-xl">visibility</span>
                          </button>
                          <button
                            onClick={() => {
                              if (confirm('האם אתה בטוח שברצונך למחוק פסק דין זה?')) {
                                verdictApi.delete(verdict.id);
                              }
                            }}
                            className="p-2 hover:bg-white dark:hover:bg-gray-700 rounded-lg text-[#607c8a] hover:text-red-500 transition-colors"
                            title="מחיקה"
                          >
                            <span className="material-symbols-outlined text-xl">delete</span>
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

      {/* Pagination info */}
      {filteredVerdicts.length > 0 && (
        <div className="mt-4 text-sm text-[#607c8a]">
          מציג {filteredVerdicts.length} מתוך {data?.total || 0} פסקי דין
        </div>
      )}
    </div>
  );
}

function getStatusStyle(status: string): string {
  const styles: Record<string, string> = {
    new: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
    extracting: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
    extracted: 'bg-cyan-100 text-cyan-700 dark:bg-cyan-900/30 dark:text-cyan-400',
    anonymizing: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
    anonymized: 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-400',
    analyzing: 'bg-pink-100 text-pink-700 dark:bg-pink-900/30 dark:text-pink-400',
    analyzed: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
    article_created: 'bg-teal-100 text-teal-700 dark:bg-teal-900/30 dark:text-teal-400',
    published: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
    failed: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  };
  return styles[status?.toLowerCase()] || styles.new;
}

function getStatusDotColor(status: string): string {
  const colors: Record<string, string> = {
    new: 'bg-blue-500',
    extracting: 'bg-amber-500',
    extracted: 'bg-cyan-500',
    anonymizing: 'bg-purple-500',
    anonymized: 'bg-indigo-500',
    analyzing: 'bg-pink-500',
    analyzed: 'bg-purple-500',
    article_created: 'bg-teal-500',
    published: 'bg-green-500',
    failed: 'bg-red-500',
  };
  return colors[status?.toLowerCase()] || colors.new;
}

function getStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    new: 'חדש',
    extracting: 'מיצוי נתונים',
    extracted: 'טקסט הופק',
    anonymizing: 'מאנוניזם',
    anonymized: 'מאונונם',
    analyzing: 'מנתח',
    analyzed: 'נותח',
    article_created: 'מאמר נוצר',
    published: 'פורסם',
    failed: 'נכשל',
  };
  return labels[status?.toLowerCase()] || status || 'לא ידוע';
}
