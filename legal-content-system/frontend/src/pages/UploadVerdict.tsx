import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDropzone } from 'react-dropzone';
import { verdictApi } from '../api/client';

export default function UploadVerdict() {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showOverwriteConfirm, setShowOverwriteConfirm] = useState(false);
  const [pendingFile, setPendingFile] = useState<File | null>(null);
  const navigate = useNavigate();

  const uploadFile = async (file: File, overwrite: boolean = false) => {
    setUploading(true);
    setError(null);
    setShowOverwriteConfirm(false);

    try {
      const response = await verdictApi.upload(file, overwrite);
      const verdictId = response.data.verdict_id;

      // Redirect to verdict detail page
      navigate(`/verdicts/${verdictId}`);
    } catch (err: any) {
      const status = err.response?.status;
      const detail = err.response?.data?.detail || 'העלאה נכשלה';

      if (status === 409) {
        // Duplicate file - show overwrite confirmation
        setPendingFile(file);
        setShowOverwriteConfirm(true);
        setError(null);
      } else {
        setError(detail);
      }
    } finally {
      setUploading(false);
    }
  };

  const onDrop = async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;
    const file = acceptedFiles[0];
    await uploadFile(file, false);
  };

  const handleOverwriteConfirm = async () => {
    if (pendingFile) {
      await uploadFile(pendingFile, true);
      setPendingFile(null);
    }
  };

  const handleOverwriteCancel = () => {
    setShowOverwriteConfirm(false);
    setPendingFile(null);
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'text/plain': ['.txt'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    },
    maxFiles: 1,
    disabled: uploading,
  });

  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-900 mb-8">העלאת פסק דין חדש</h1>

      <div className="max-w-2xl mx-auto">
        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors ${
            isDragActive
              ? 'border-primary-500 bg-primary-50'
              : 'border-gray-300 hover:border-primary-400'
          } ${uploading ? 'opacity-50 cursor-not-allowed' : ''}`}
        >
          <input {...getInputProps()} />

          <div className="space-y-4">
            <div className="text-6xl">📄</div>

            {uploading ? (
              <div>
                <div className="text-lg font-medium text-gray-900 mb-2">
                  מעלה קובץ...
                </div>
                <div className="w-48 mx-auto bg-gray-200 rounded-full h-2">
                  <div className="bg-primary-600 h-2 rounded-full animate-pulse w-1/2" />
                </div>
              </div>
            ) : isDragActive ? (
              <p className="text-lg font-medium text-primary-600">
                שחרר כדי להעלות...
              </p>
            ) : (
              <div>
                <p className="text-lg font-medium text-gray-900 mb-2">
                  גרור ושחרר קובץ או לחץ כדי לבחור
                </p>
                <p className="text-sm text-gray-600">
                  פורמטים נתמכים: PDF, TXT, DOC, DOCX
                </p>
                <p className="text-sm text-gray-600">
                  גודל מקסימלי: 50MB
                </p>
              </div>
            )}
          </div>
        </div>

        {error && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-800 font-medium">שגיאה: {error}</p>
          </div>
        )}

        {showOverwriteConfirm && (
          <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
            <div className="flex items-start gap-3">
              <span className="text-2xl">⚠️</span>
              <div className="flex-1">
                <h4 className="font-bold text-yellow-800 mb-2">קובץ כבר קיים במערכת</h4>
                <p className="text-yellow-700 text-sm mb-4">
                  קובץ עם תוכן זהה כבר הועלה למערכת. האם ברצונך להחליף את הגרסה הקיימת?
                  <br />
                  <strong>שים לב:</strong> פעולה זו תמחק את כל הנתונים הקיימים של פסק הדין (כולל אנונימיזציה, ניתוח ומאמרים).
                </p>
                <div className="flex gap-3">
                  <button
                    onClick={handleOverwriteConfirm}
                    disabled={uploading}
                    className="px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 disabled:opacity-50"
                  >
                    {uploading ? 'מחליף...' : 'החלף קובץ'}
                  </button>
                  <button
                    onClick={handleOverwriteCancel}
                    disabled={uploading}
                    className="px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 disabled:opacity-50"
                  >
                    ביטול
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        <div className="mt-8 p-6 bg-blue-50 rounded-lg">
          <h3 className="font-bold text-gray-900 mb-2">מה יקרה אחרי ההעלאה?</h3>
          <ol className="space-y-2 text-sm text-gray-700">
            <li>1. המערכת תחלץ טקסט מהקובץ</li>
            <li>2. תנקה ותנרמל את הטקסט</li>
            <li>3. תחלץ מטא-דאטה בסיסי (מספר תיק, בית משפט, שופט)</li>
            <li>4. תשמור את הקובץ במערכת</li>
            <li>5. תוכל להמשיך לאנונימיזציה, ניתוח, וייצור מאמר</li>
          </ol>
        </div>
      </div>
    </div>
  );
}
