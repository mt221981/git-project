import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { verdictApi, articleApi } from '../api/client';

// Enhanced Progress bar component with stages
function ProgressBar({
  progress,
  message,
  status
}: {
  progress: number;
  message: string;
  status: string;
}) {
  // Determine stage based on status
  const getStage = () => {
    switch (status) {
      case 'extracted':
        return { stage: 1, label: 'ממתין לעיבוד' };
      case 'anonymizing':
        return { stage: 2, label: 'מנקה טקסט' };
      case 'anonymized':
        return { stage: 2, label: 'טקסט נוקה' };
      case 'analyzing':
        return { stage: 3, label: 'מנתח פסק דין' };
      case 'analyzed':
        return { stage: 3, label: 'ניתוח הושלם' };
      case 'article_creating':
        return { stage: 4, label: 'יוצר מאמר' };
      case 'article_created':
        return { stage: 5, label: 'מאמר נוצר!' };
      case 'published':
        return { stage: 5, label: 'פורסם!' };
      case 'failed':
        return { stage: 0, label: 'נכשל' };
      default:
        return { stage: 0, label: 'לא ידוע' };
    }
  };

  const { stage, label } = getStage();
  const isProcessing = ['anonymizing', 'analyzing', 'article_creating'].includes(status);
  const isFailed = status === 'failed';
  const isComplete = ['article_created', 'published'].includes(status);

  return (
    <div className="w-full">
      {/* Stage indicators */}
      <div className="flex justify-between mb-4 text-xs">
        <div className={`flex flex-col items-center ${stage >= 1 ? 'text-blue-600' : 'text-gray-400'}`}>
          <div className={`w-8 h-8 rounded-full flex items-center justify-center mb-1 ${
            stage >= 1 ? 'bg-blue-600 text-white' : 'bg-gray-200'
          }`}>1</div>
          <span>טעינה</span>
        </div>
        <div className={`flex flex-col items-center ${stage >= 2 ? 'text-blue-600' : 'text-gray-400'}`}>
          <div className={`w-8 h-8 rounded-full flex items-center justify-center mb-1 ${
            stage >= 2 ? 'bg-blue-600 text-white' : 'bg-gray-200'
          }`}>2</div>
          <span>ניקוי</span>
        </div>
        <div className={`flex flex-col items-center ${stage >= 3 ? 'text-blue-600' : 'text-gray-400'}`}>
          <div className={`w-8 h-8 rounded-full flex items-center justify-center mb-1 ${
            stage >= 3 ? 'bg-blue-600 text-white' : 'bg-gray-200'
          }`}>3</div>
          <span>ניתוח</span>
        </div>
        <div className={`flex flex-col items-center ${stage >= 4 ? 'text-blue-600' : 'text-gray-400'}`}>
          <div className={`w-8 h-8 rounded-full flex items-center justify-center mb-1 ${
            stage >= 4 ? 'bg-blue-600 text-white' : 'bg-gray-200'
          } ${status === 'article_creating' ? 'animate-pulse' : ''}`}>4</div>
          <span>מאמר</span>
        </div>
        <div className={`flex flex-col items-center ${stage >= 5 ? 'text-green-600' : 'text-gray-400'}`}>
          <div className={`w-8 h-8 rounded-full flex items-center justify-center mb-1 ${
            stage >= 5 ? 'bg-green-600 text-white' : 'bg-gray-200'
          }`}>✓</div>
          <span>סיום</span>
        </div>
      </div>

      {/* Progress bar */}
      <div className="flex justify-between mb-1">
        <span className={`text-sm font-medium ${isFailed ? 'text-red-700' : isComplete ? 'text-green-700' : 'text-blue-700'}`}>
          {message || label}
        </span>
        <span className={`text-sm font-medium ${isFailed ? 'text-red-700' : isComplete ? 'text-green-700' : 'text-blue-700'}`}>
          {progress}%
        </span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-4 overflow-hidden">
        <div
          className={`h-4 rounded-full transition-all duration-700 ease-out ${
            isFailed ? 'bg-red-500' : isComplete ? 'bg-green-500' : 'bg-blue-600'
          } ${isProcessing ? 'animate-pulse' : ''}`}
          style={{ width: `${Math.min(progress, 100)}%` }}
        />
      </div>

      {/* Processing indicator */}
      {isProcessing && (
        <div className="flex items-center gap-2 mt-2 text-blue-600">
          <div className="animate-spin h-4 w-4 border-2 border-blue-600 border-t-transparent rounded-full"></div>
          <span className="text-sm">מעבד... אנא המתן</span>
        </div>
      )}
    </div>
  );
}

// Timer component
function Timer({ startTime }: { startTime: number | null }) {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    if (!startTime) return;

    // Calculate initial elapsed time
    setElapsed(Math.floor((Date.now() - startTime) / 1000));

    const interval = setInterval(() => {
      setElapsed(Math.floor((Date.now() - startTime) / 1000));
    }, 1000);

    return () => clearInterval(interval);
  }, [startTime]);

  if (!startTime) return null;

  const minutes = Math.floor(elapsed / 60);
  const seconds = elapsed % 60;

  return (
    <div className="text-sm text-gray-600 font-mono">
      זמן שעבר: {minutes}:{seconds.toString().padStart(2, '0')}
    </div>
  );
}

export default function VerdictDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [operationStartTime, setOperationStartTime] = useState<number | null>(null);
  const [localMessage, setLocalMessage] = useState<string>('');

  // Define processing statuses
  const processingStatuses = ['anonymizing', 'analyzing', 'article_creating'];

  const { data: verdict, isLoading, error, refetch } = useQuery({
    queryKey: ['verdict', id],
    queryFn: () => verdictApi.get(Number(id)).then((res) => res.data),
    enabled: !!id,
    // Poll more frequently during processing
    refetchInterval: (query) => {
      const data = query.state.data;
      if (data && processingStatuses.includes(data.status)) {
        return 2000; // Poll every 2 seconds during processing
      }
      return false; // Don't poll when not processing
    },
  });

  // Determine if currently processing
  const isProcessing = verdict ? processingStatuses.includes(verdict.status) : false;

  // Set start time when processing begins
  useEffect(() => {
    if (isProcessing && !operationStartTime) {
      setOperationStartTime(Date.now());
    } else if (!isProcessing && operationStartTime) {
      // Processing ended - keep timer for a moment then clear
      setTimeout(() => {
        setOperationStartTime(null);
      }, 3000);
    }
  }, [isProcessing, operationStartTime]);

  // Handle navigation to article when created
  useEffect(() => {
    if (verdict?.status === 'article_created' || verdict?.status === 'published') {
      // Fetch article and offer navigation
      articleApi.getByVerdict(Number(id)).then((response) => {
        const articleId = response.data.id;
        setLocalMessage(`מאמר נוצר בהצלחה! מעביר לדף המאמר...`);
        setTimeout(() => {
          navigate(`/articles/${articleId}`);
        }, 2000);
      }).catch(() => {
        setLocalMessage('המאמר נוצר אך לא נמצא - רענן את הדף');
      });
    }
  }, [verdict?.status, id, navigate]);

  // Mutations
  const createMutationConfig = useCallback((initialMessage: string, initialProgress?: number) => ({
    onMutate: () => {
      setOperationStartTime(Date.now());
      setLocalMessage(initialMessage);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['verdict', id] });
    },
    onError: (error: Error) => {
      setLocalMessage(`שגיאה: ${error.message}`);
      setTimeout(() => setLocalMessage(''), 5000);
    },
  }), [id, queryClient]);

  const anonymizeMutation = useMutation({
    mutationFn: () => verdictApi.anonymize(Number(id)),
    ...createMutationConfig('מתחיל עיבוד...'),
  });

  const analyzeMutation = useMutation({
    mutationFn: () => articleApi.analyze(Number(id)),
    ...createMutationConfig('מתחיל ניתוח...'),
  });

  const generateMutation = useMutation({
    mutationFn: () => articleApi.generate(Number(id)),
    ...createMutationConfig('מתחיל יצירת מאמר...'),
  });

  const retryArticleMutation = useMutation({
    mutationFn: () => articleApi.retryGeneration(Number(id)),
    ...createMutationConfig('מתחיל יצירת מאמר מחדש...'),
  });

  const reprocessMutation = useMutation({
    mutationFn: () => verdictApi.reprocess(Number(id)),
    ...createMutationConfig('מתחיל עיבוד מחדש מההתחלה...'),
  });

  const resetMutation = useMutation({
    mutationFn: () => verdictApi.reset(Number(id)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['verdict', id] });
      setLocalMessage('פסק הדין אופס בהצלחה');
      setTimeout(() => setLocalMessage(''), 3000);
    },
    onError: (error: Error) => {
      setLocalMessage(`שגיאה באיפוס: ${error.message}`);
    },
  });

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">טוען פסק דין...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-center">
        <p className="text-red-600">שגיאה בטעינת פסק הדין</p>
        <button onClick={() => refetch()} className="btn btn-secondary mt-2">
          נסה שוב
        </button>
      </div>
    );
  }

  if (!verdict) return <div>פסק דין לא נמצא</div>;

  // Get progress and message from verdict (backend) or local state
  const progress = verdict.processing_progress || 0;
  const message = localMessage || verdict.processing_message || '';

  const getStatusLabel = (status: string) => {
    const labels: Record<string, string> = {
      new: 'חדש',
      extracted: 'טקסט הופק',
      anonymizing: 'מעבד טקסט...',
      anonymized: 'טקסט נוקה',
      analyzing: 'מנתח...',
      analyzed: 'נותח - מוכן למאמר',
      article_creating: 'יוצר מאמר...',
      article_created: 'מאמר נוצר',
      published: 'פורסם',
      failed: 'נכשל',
    };
    return labels[status] || status;
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      new: 'bg-gray-100 text-gray-800',
      extracted: 'bg-blue-100 text-blue-800',
      anonymizing: 'bg-yellow-100 text-yellow-800 animate-pulse',
      anonymized: 'bg-green-100 text-green-800',
      analyzing: 'bg-yellow-100 text-yellow-800 animate-pulse',
      analyzed: 'bg-purple-100 text-purple-800',
      article_creating: 'bg-orange-100 text-orange-800 animate-pulse',
      article_created: 'bg-indigo-100 text-indigo-800',
      published: 'bg-green-100 text-green-800',
      failed: 'bg-red-100 text-red-800',
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  // Show progress section if processing or has progress
  const showProgress = isProcessing || progress > 0 || verdict.status === 'article_created' || verdict.status === 'failed';

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-3xl font-bold">
          תיק מספר: {verdict.case_number || `#${verdict.id}`}
        </h1>
        <span className={`px-4 py-2 rounded-full text-sm font-medium ${getStatusColor(verdict.status)}`}>
          {getStatusLabel(verdict.status)}
        </span>
      </div>

      {/* Progress section - always show during processing */}
      {showProgress && (
        <div className={`card mb-6 ${
          verdict.status === 'failed' ? 'bg-red-50 border-red-200' :
          verdict.status === 'article_created' ? 'bg-green-50 border-green-200' :
          'bg-blue-50 border-blue-200'
        }`}>
          <div className="flex items-center justify-between mb-4">
            <h3 className={`font-bold ${
              verdict.status === 'failed' ? 'text-red-800' :
              verdict.status === 'article_created' ? 'text-green-800' :
              'text-blue-800'
            }`}>
              {verdict.status === 'failed' ? 'העיבוד נכשל' :
               verdict.status === 'article_created' ? 'העיבוד הושלם!' :
               'מצב העיבוד'}
            </h3>
            {isProcessing && <Timer startTime={operationStartTime} />}
          </div>
          <ProgressBar
            progress={Math.round(progress)}
            message={message}
            status={verdict.status}
          />
        </div>
      )}

      {/* Error/Review notes */}
      {verdict.review_notes && (
        <div className="card mb-6 bg-yellow-50 border-yellow-200">
          <h3 className="font-bold text-yellow-800 mb-2">הערות ביקורת</h3>
          <p className="text-yellow-700 text-sm whitespace-pre-wrap">{verdict.review_notes}</p>
        </div>
      )}

      <div className="grid gap-6">
        {/* Details card */}
        <div className="card">
          <h2 className="text-xl font-bold mb-4">פרטים</h2>
          <dl className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <dt className="text-gray-600 text-sm">בית משפט</dt>
              <dd className="font-medium">{verdict.court_name || '-'}</dd>
            </div>
            <div>
              <dt className="text-gray-600 text-sm">שופט</dt>
              <dd className="font-medium">{verdict.judge_name || '-'}</dd>
            </div>
            <div>
              <dt className="text-gray-600 text-sm">תחום משפטי</dt>
              <dd className="font-medium">{verdict.legal_area || '-'}</dd>
            </div>
            <div>
              <dt className="text-gray-600 text-sm">תאריך יצירה</dt>
              <dd className="font-medium">
                {new Date(verdict.created_at).toLocaleDateString('he-IL')}
              </dd>
            </div>
          </dl>
        </div>

        {/* Actions card */}
        <div className="card">
          <h2 className="text-xl font-bold mb-4">פעולות</h2>
          <div className="flex flex-wrap gap-4">
            {/* Main action button - Full automatic processing */}
            {verdict.status === 'extracted' && verdict.original_text && (
              <button
                onClick={() => reprocessMutation.mutate()}
                disabled={reprocessMutation.isPending || isProcessing}
                className="btn bg-green-600 hover:bg-green-700 text-white text-lg px-6 py-3 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {reprocessMutation.isPending ? (
                  <span className="flex items-center gap-2">
                    <span className="animate-spin h-5 w-5 border-2 border-white border-t-transparent rounded-full"></span>
                    מתחיל עיבוד...
                  </span>
                ) : (
                  'עבד אוטומטית (ניתוח + יצירת מאמר)'
                )}
              </button>
            )}

            {verdict.status === 'extracted' && !verdict.original_text && (
              <button
                onClick={() => anonymizeMutation.mutate()}
                disabled={anonymizeMutation.isPending || isProcessing}
                className="btn btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {anonymizeMutation.isPending ? (
                  <span className="flex items-center gap-2">
                    <span className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></span>
                    מעבד...
                  </span>
                ) : (
                  'עבד אוטומטית (ניתוח + מאמר)'
                )}
              </button>
            )}

            {verdict.status === 'anonymized' && (
              <button
                onClick={() => analyzeMutation.mutate()}
                disabled={analyzeMutation.isPending || isProcessing}
                className="btn btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {analyzeMutation.isPending ? (
                  <span className="flex items-center gap-2">
                    <span className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></span>
                    מנתח...
                  </span>
                ) : (
                  'נתח פסק דין'
                )}
              </button>
            )}

            {verdict.status === 'analyzed' && (
              <button
                onClick={() => generateMutation.mutate()}
                disabled={generateMutation.isPending || isProcessing}
                className="btn btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {generateMutation.isPending ? (
                  <span className="flex items-center gap-2">
                    <span className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></span>
                    מתחיל יצירה...
                  </span>
                ) : (
                  'צור מאמר'
                )}
              </button>
            )}

            {(verdict.status === 'article_created' || verdict.status === 'failed' || verdict.status === 'published') && (
              <button
                onClick={() => retryArticleMutation.mutate()}
                disabled={retryArticleMutation.isPending || isProcessing}
                className="btn bg-orange-600 hover:bg-orange-700 text-white disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {retryArticleMutation.isPending ? (
                  <span className="flex items-center gap-2">
                    <span className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></span>
                    מתחיל יצירה מחדש...
                  </span>
                ) : (
                  'צור מאמר מחדש'
                )}
              </button>
            )}

            {verdict.status === 'failed' && (
              <button
                onClick={() => refetch()}
                className="btn btn-secondary"
              >
                רענן סטטוס
              </button>
            )}

            {/* Reset button - for stuck verdicts */}
            {['anonymizing', 'analyzing', 'article_creating', 'failed'].includes(verdict.status) && (
              <button
                onClick={() => resetMutation.mutate()}
                disabled={resetMutation.isPending}
                className="btn bg-red-600 hover:bg-red-700 text-white disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {resetMutation.isPending ? (
                  <span className="flex items-center gap-2">
                    <span className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></span>
                    מאפס...
                  </span>
                ) : (
                  'אפס ונסה מחדש'
                )}
              </button>
            )}

            {/* Reprocess button - available for most states except new/processing */}
            {!['new', 'extracted', 'anonymizing', 'analyzing', 'article_creating'].includes(verdict.status) && verdict.original_text && (
              <button
                onClick={() => reprocessMutation.mutate()}
                disabled={reprocessMutation.isPending || isProcessing}
                className="btn bg-amber-500 hover:bg-amber-600 text-white disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {reprocessMutation.isPending ? (
                  <span className="flex items-center gap-2">
                    <span className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></span>
                    מעבד מחדש...
                  </span>
                ) : (
                  'עבד מחדש מההתחלה'
                )}
              </button>
            )}

            <button
              onClick={() => navigate('/verdicts')}
              className="btn btn-secondary"
            >
              חזרה לרשימה
            </button>
          </div>
        </div>

        {/* Text preview card */}
        {verdict.cleaned_text && (
          <div className="card">
            <h2 className="text-xl font-bold mb-4">תצוגה מקדימה של הטקסט</h2>
            <div className="bg-gray-50 p-4 rounded-lg max-h-64 overflow-y-auto">
              <pre className="text-sm whitespace-pre-wrap text-right" dir="rtl">
                {verdict.anonymized_text || verdict.cleaned_text.substring(0, 2000)}
                {(verdict.anonymized_text || verdict.cleaned_text).length > 2000 && '...'}
              </pre>
            </div>
            <p className="text-sm text-gray-500 mt-2">
              אורך הטקסט: {(verdict.anonymized_text || verdict.cleaned_text).length.toLocaleString()} תווים
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
