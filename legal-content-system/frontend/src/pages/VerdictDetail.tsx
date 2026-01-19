import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { verdictApi, articleApi } from '../api/client';

// Progress bar component
function ProgressBar({ progress, message }: { progress: number; message: string }) {
  return (
    <div className="w-full">
      <div className="flex justify-between mb-1">
        <span className="text-sm font-medium text-blue-700">{message}</span>
        <span className="text-sm font-medium text-blue-700">{progress}%</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-4">
        <div
          className="bg-blue-600 h-4 rounded-full transition-all duration-500 ease-out"
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );
}

// Timer component
function Timer({ startTime }: { startTime: number | null }) {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    if (!startTime) return;

    const interval = setInterval(() => {
      setElapsed(Math.floor((Date.now() - startTime) / 1000));
    }, 1000);

    return () => clearInterval(interval);
  }, [startTime]);

  if (!startTime) return null;

  const minutes = Math.floor(elapsed / 60);
  const seconds = elapsed % 60;

  return (
    <div className="text-sm text-gray-600">
      זמן שעבר: {minutes}:{seconds.toString().padStart(2, '0')}
    </div>
  );
}

export default function VerdictDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [operationProgress, setOperationProgress] = useState(0);
  const [operationMessage, setOperationMessage] = useState('');
  const [operationStartTime, setOperationStartTime] = useState<number | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);

  const { data: verdict, isLoading, error, refetch } = useQuery({
    queryKey: ['verdict', id],
    queryFn: () => verdictApi.get(Number(id)).then((res) => res.data),
    enabled: !!id,
    refetchInterval: isProcessing ? 2000 : false, // Poll every 2s during processing
  });

  // Update processing state based on verdict status
  useEffect(() => {
    if (verdict?.status === 'anonymizing' || verdict?.status === 'analyzing') {
      setIsProcessing(true);
    } else if (verdict?.status === 'failed' && isProcessing) {
      // Operation failed - show error and reset
      setIsProcessing(false);
      setOperationProgress(0);
      setOperationMessage('הפעולה נכשלה - ראה הערות למטה');
      setOperationStartTime(null);
      // Clear message after delay
      setTimeout(() => {
        setOperationMessage('');
      }, 5000);
    } else if (verdict?.status === 'article_created' && isProcessing) {
      // Article was created - fetch it and navigate
      setOperationProgress(100);
      setOperationMessage('המאמר נוצר בהצלחה! מעביר לדף המאמר...');
      articleApi.getByVerdict(Number(id)).then((response) => {
        const articleId = response.data.id;
        setTimeout(() => {
          setIsProcessing(false);
          navigate(`/articles/${articleId}`);
        }, 1000);
      }).catch(() => {
        setIsProcessing(false);
        setOperationMessage('המאמר נוצר אך לא ניתן לטעון אותו');
      });
    } else if (isProcessing && !['anonymizing', 'analyzing', 'failed'].includes(verdict?.status || '')) {
      // Operation completed successfully (anonymized, analyzed, etc.)
      setIsProcessing(false);
      setOperationProgress(100);
      setOperationMessage('הושלם!');
      setTimeout(() => {
        setOperationProgress(0);
        setOperationMessage('');
        setOperationStartTime(null);
      }, 2000);
    }
  }, [verdict?.status, isProcessing, id, navigate]);

  const anonymizeMutation = useMutation({
    mutationFn: () => verdictApi.anonymize(Number(id)),
    onMutate: () => {
      setIsProcessing(true);
      setOperationProgress(5);
      setOperationMessage('מתחיל אנונימיזציה...');
      setOperationStartTime(Date.now());
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['verdict', id] });
      setOperationProgress(100);
      setOperationMessage('האנונימיזציה הושלמה בהצלחה!');
    },
    onError: (error: Error) => {
      setIsProcessing(false);
      setOperationProgress(0);
      setOperationMessage(`שגיאה: ${error.message}`);
    },
  });

  const analyzeMutation = useMutation({
    mutationFn: () => articleApi.analyze(Number(id)),
    onMutate: () => {
      setIsProcessing(true);
      setOperationProgress(5);
      setOperationMessage('מתחיל ניתוח...');
      setOperationStartTime(Date.now());
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['verdict', id] });
      setOperationProgress(100);
      setOperationMessage('הניתוח הושלם בהצלחה!');
    },
    onError: (error: Error) => {
      setIsProcessing(false);
      setOperationProgress(0);
      setOperationMessage(`שגיאה: ${error.message}`);
    },
  });

  const generateMutation = useMutation({
    mutationFn: () => articleApi.generate(Number(id)),
    onMutate: () => {
      setIsProcessing(true);
      setOperationProgress(5);
      setOperationMessage('מייצר מאמר...');
      setOperationStartTime(Date.now());
    },
    onSuccess: () => {
      // Article generation is async - polling will detect status change to 'article_created'
      // and then fetch the article and navigate
      queryClient.invalidateQueries({ queryKey: ['verdict', id] });
    },
    onError: (error: Error) => {
      setIsProcessing(false);
      setOperationProgress(0);
      setOperationMessage(`שגיאה: ${error.message}`);
    },
  });

  const reprocessMutation = useMutation({
    mutationFn: () => verdictApi.reprocess(Number(id)),
    onMutate: () => {
      setIsProcessing(true);
      setOperationProgress(5);
      setOperationMessage('מתחיל עיבוד מחדש...');
      setOperationStartTime(Date.now());
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['verdict', id] });
      // The polling will handle the rest of the status updates
    },
    onError: (error: Error) => {
      setIsProcessing(false);
      setOperationProgress(0);
      setOperationMessage(`שגיאה: ${error.message}`);
    },
  });

  // Update progress from backend (real progress tracking)
  useEffect(() => {
    if (!isProcessing) return;

    // Use real progress from backend
    if (verdict?.processing_progress !== undefined && verdict?.processing_progress !== null) {
      setOperationProgress(verdict.processing_progress);
    }

    if (verdict?.processing_message) {
      setOperationMessage(verdict.processing_message);
    }
  }, [verdict?.processing_progress, verdict?.processing_message, isProcessing]);

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

  const getStatusLabel = (status: string) => {
    const labels: Record<string, string> = {
      new: 'חדש',
      extracted: 'טקסט הופק',
      anonymizing: 'מאנוניזם...',
      anonymized: 'מאונונם',
      analyzing: 'מנתח...',
      analyzed: 'נותח',
      article_created: 'מאמר נוצר',
      failed: 'נכשל',
    };
    return labels[status] || status;
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      new: 'bg-gray-100 text-gray-800',
      extracted: 'bg-blue-100 text-blue-800',
      anonymizing: 'bg-yellow-100 text-yellow-800',
      anonymized: 'bg-green-100 text-green-800',
      analyzing: 'bg-yellow-100 text-yellow-800',
      analyzed: 'bg-purple-100 text-purple-800',
      article_created: 'bg-indigo-100 text-indigo-800',
      failed: 'bg-red-100 text-red-800',
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

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

      {/* Progress section */}
      {(isProcessing || operationProgress > 0) && (
        <div className="card mb-6 bg-blue-50 border-blue-200">
          <div className="flex items-center justify-between mb-2">
            <h3 className="font-bold text-blue-800">מצב העיבוד</h3>
            <Timer startTime={operationStartTime} />
          </div>
          <ProgressBar progress={Math.round(operationProgress)} message={operationMessage} />
        </div>
      )}

      {/* Error/Review notes */}
      {verdict.review_notes && (
        <div className="card mb-6 bg-yellow-50 border-yellow-200">
          <h3 className="font-bold text-yellow-800 mb-2">הערות</h3>
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
                    מעבד אוטומטית...
                  </span>
                ) : (
                  'עבד אוטומטית (אנונימיזציה + ניתוח + יצירת מאמר)'
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
                    מאנוניזם...
                  </span>
                ) : (
                  'אנוניזם טקסט'
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
                    מייצר מאמר...
                  </span>
                ) : (
                  'צור מאמר'
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

            {/* Reprocess button - available for most states except new/processing */}
            {!['new', 'anonymizing', 'analyzing'].includes(verdict.status) && verdict.original_text && (
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
