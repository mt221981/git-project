# Complete Frontend Code Reference - Legal Content System

A comprehensive reference containing all frontend source code for building the Legal Content Management System UI.

## Table of Contents

1. [Project Configuration](#project-configuration)
   - [package.json](#packagejson)
   - [vite.config.ts](#viteconfigts)
   - [tailwind.config.js](#tailwindconfigjs)
   - [tsconfig.json](#tsconfigjson)
2. [Core Application Files](#core-application-files)
   - [src/main.tsx](#srcmaintsx)
   - [src/App.tsx](#srcapptsx)
   - [src/index.css](#srcindexcss)
3. [API & Types](#api--types)
   - [src/api/client.ts](#srcapiclientts)
   - [src/types/index.ts](#srctypesindexts)
4. [Page Components](#page-components)
   - [Dashboard.tsx](#dashboardtsx)
   - [UploadVerdict.tsx](#uploadverdictx)
   - [VerdictsList.tsx](#verdictslisttsx)
   - [VerdictDetail.tsx](#verdictdetailtsx)
   - [ArticlesList.tsx](#articleslisttsx)
   - [ArticlesListEnhanced.tsx](#articleslistenhancedtsx)
   - [ArticleDetail.tsx](#articledetailtsx)
   - [WordPressManagement.tsx](#wordpressmanagementtsx)
   - [PublishingDashboard.tsx](#publishingdashboardtsx)

---

## Project Configuration

### package.json

```json
{
  "name": "legal-content-system-frontend",
  "version": "1.0.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.21.0",
    "axios": "^1.6.5",
    "@tanstack/react-query": "^5.17.9",
    "react-dropzone": "^14.2.3",
    "react-icons": "^5.0.1",
    "date-fns": "^3.0.6",
    "clsx": "^2.1.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.48",
    "@types/react-dom": "^18.2.18",
    "@typescript-eslint/eslint-plugin": "^6.19.0",
    "@typescript-eslint/parser": "^6.19.0",
    "@vitejs/plugin-react": "^4.2.1",
    "autoprefixer": "^10.4.16",
    "eslint": "^8.56.0",
    "eslint-plugin-react-hooks": "^4.6.0",
    "eslint-plugin-react-refresh": "^0.4.5",
    "postcss": "^8.4.33",
    "tailwindcss": "^3.4.1",
    "typescript": "^5.3.3",
    "vite": "^5.0.12"
  }
}
```

### vite.config.ts

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
```

### tailwind.config.js

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f0f9ff',
          100: '#e0f2fe',
          200: '#bae6fd',
          300: '#7dd3fc',
          400: '#38bdf8',
          500: '#0ea5e9',
          600: '#0284c7',
          700: '#0369a1',
          800: '#075985',
          900: '#0c4a6e',
        },
      },
    },
  },
  plugins: [],
}
```

### tsconfig.json

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,

    /* Bundler mode */
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",

    /* Linting */
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

---

## Core Application Files

### src/main.tsx

```typescript
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.tsx';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
```

### src/App.tsx

```typescript
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Dashboard from './pages/Dashboard';
import VerdictsList from './pages/VerdictsList';
import VerdictDetail from './pages/VerdictDetail';
import ArticlesList from './pages/ArticlesListEnhanced';
import ArticleDetail from './pages/ArticleDetail';
import UploadVerdict from './pages/UploadVerdict';
import WordPressManagement from './pages/WordPressManagement';
import PublishingDashboard from './pages/PublishingDashboard';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="min-h-screen bg-gray-50">
          <nav className="bg-white shadow-sm border-b">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <div className="flex justify-between h-16">
                <div className="flex space-x-8 space-x-reverse">
                  <Link
                    to="/"
                    className="inline-flex items-center px-1 pt-1 text-sm font-medium text-gray-900"
                  >
                    מערכת תוכן משפטי
                  </Link>
                  <Link
                    to="/verdicts"
                    className="inline-flex items-center px-1 pt-1 text-sm font-medium text-gray-600 hover:text-gray-900"
                  >
                    פסקי דין
                  </Link>
                  <Link
                    to="/articles"
                    className="inline-flex items-center px-1 pt-1 text-sm font-medium text-gray-600 hover:text-gray-900"
                  >
                    מאמרים
                  </Link>
                  <Link
                    to="/publishing"
                    className="inline-flex items-center px-1 pt-1 text-sm font-medium text-gray-600 hover:text-gray-900"
                  >
                    לוח פרסום
                  </Link>
                  <Link
                    to="/wordpress"
                    className="inline-flex items-center px-1 pt-1 text-sm font-medium text-gray-600 hover:text-gray-900"
                  >
                    WordPress
                  </Link>
                  <Link
                    to="/upload"
                    className="inline-flex items-center px-1 pt-1 text-sm font-medium text-gray-600 hover:text-gray-900"
                  >
                    העלאה חדשה
                  </Link>
                </div>
              </div>
            </div>
          </nav>

          <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/verdicts" element={<VerdictsList />} />
              <Route path="/verdicts/:id" element={<VerdictDetail />} />
              <Route path="/articles" element={<ArticlesList />} />
              <Route path="/articles/:id" element={<ArticleDetail />} />
              <Route path="/publishing" element={<PublishingDashboard />} />
              <Route path="/wordpress" element={<WordPressManagement />} />
              <Route path="/upload" element={<UploadVerdict />} />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
```

### src/index.css

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  * {
    direction: rtl;
  }

  body {
    @apply bg-gray-50 text-gray-900;
  }
}

@layer components {
  .btn {
    @apply px-4 py-2 rounded-lg font-medium transition-colors duration-200;
  }

  .btn-primary {
    @apply bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed;
  }

  .btn-secondary {
    @apply bg-gray-200 text-gray-800 hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed;
  }

  .btn-danger {
    @apply bg-red-600 text-white hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed;
  }

  .btn-sm {
    @apply px-3 py-1 text-sm;
  }

  .card {
    @apply bg-white rounded-lg shadow-md p-6;
  }

  .input {
    @apply w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent;
  }

  .badge {
    @apply inline-flex items-center px-3 py-1 rounded-full text-sm font-medium;
  }
}

@layer utilities {
  .line-clamp-2 {
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
}
```

---

## API & Types

### src/api/client.ts

```typescript
import axios from 'axios';

const apiClient = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

export const verdictApi = {
  upload: (file: File, overwrite: boolean = false) => {
    const formData = new FormData();
    formData.append('file', file);
    return apiClient.post('/verdicts/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      params: { overwrite },
    });
  },
  list: (params?: { skip?: number; limit?: number; status?: string }) =>
    apiClient.get('/verdicts/', { params }),
  get: (id: number) => apiClient.get(`/verdicts/${id}`),
  anonymize: (id: number) => apiClient.post(`/verdicts/${id}/anonymize`),
  reprocess: (id: number) => apiClient.post(`/verdicts/${id}/reprocess`),
  delete: (id: number) => apiClient.delete(`/verdicts/${id}`),
  getStats: () => apiClient.get('/verdicts/statistics/overview'),
};

export const articleApi = {
  analyze: (verdictId: number) =>
    apiClient.post(`/articles/verdicts/${verdictId}/analyze`),
  generate: (verdictId: number) =>
    apiClient.post(`/articles/generate/${verdictId}`),
  list: (params?: { skip?: number; limit?: number; status?: string }) =>
    apiClient.get('/articles', { params }),
  get: (id: number) => apiClient.get(`/articles/${id}`),
  getByVerdict: (verdictId: number) =>
    apiClient.get(`/articles/by-verdict/${verdictId}`),
  getStats: () => apiClient.get('/articles/statistics/overview'),
};

export const wordpressApi = {
  // Sites management
  listSites: () => apiClient.get('/wordpress/sites'),
  createSite: (data: any) => apiClient.post('/wordpress/sites', data),
  updateSite: (siteId: number, data: any) =>
    apiClient.put(`/wordpress/sites/${siteId}`, data),
  deleteSite: (siteId: number) => apiClient.delete(`/wordpress/sites/${siteId}`),
  testConnection: (siteId: number) =>
    apiClient.get(`/wordpress/sites/${siteId}/test`),

  // Publishing operations
  publish: (articleId: number, data: { site_id: number; status: string }) =>
    apiClient.post(`/wordpress/publish/${articleId}`, data),
  publishWithRetry: (
    articleId: number,
    data: {
      site_id: number;
      status: string;
      max_retries?: number;
      retry_delay?: number;
    }
  ) => apiClient.post(`/wordpress/articles/${articleId}/publish`, data),
  batchPublish: (data: {
    article_ids: number[];
    site_id: number;
    status: string;
    stop_on_error?: boolean;
  }) => apiClient.post('/wordpress/articles/batch-publish', data),
  republishFailed: (data: { site_id: number; max_articles?: number }) =>
    apiClient.post('/wordpress/articles/republish-failed', data),

  // Validation
  validateArticle: (articleId: number) =>
    apiClient.get(`/wordpress/articles/${articleId}/validate`),

  // Statistics and monitoring
  getStatistics: (siteId?: number) =>
    apiClient.get('/wordpress/statistics', {
      params: siteId ? { site_id: siteId } : {},
    }),

  // Queue management
  scheduleQueue: (data: {
    site_id: number;
    articles_per_day: number;
    min_score?: number;
  }) => apiClient.post('/wordpress/queue/schedule', data),
  getUnpublishedArticles: (params: { min_score?: number; limit?: number }) =>
    apiClient.get('/wordpress/articles/unpublished', { params }),

  // Status sync
  syncArticleStatus: (articleId: number) =>
    apiClient.post(`/wordpress/articles/${articleId}/sync`),
};

export default apiClient;
```

### src/types/index.ts

```typescript
// Article types
export interface Article {
  id: number;
  verdict_id: number;
  title: string;
  slug: string;
  meta_title: string;
  meta_description: string;
  content_html: string;
  excerpt: string;
  focus_keyword: string;
  secondary_keywords: string[];
  long_tail_keywords: string[];
  word_count: number;
  reading_time_minutes: number;
  faq_items: FAQItem[];
  common_mistakes: string[];
  internal_links: Link[];
  external_links: Link[];
  category_primary: string;
  categories_secondary: string[];
  tags: string[];
  featured_image_url?: string;
  featured_image_prompt: string;
  featured_image_alt: string;
  content_score: number;
  seo_score: number;
  readability_score: number;
  eeat_score: number;
  overall_score: number;
  quality_issues: string[];
  publish_status: PublishStatus;
  wordpress_post_id?: number;
  wordpress_url?: string;
  wordpress_site_id?: number;
  published_at?: string;
  metadata?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface FAQItem {
  question: string;
  answer: string;
}

export interface Link {
  url: string;
  anchor_text: string;
}

export type PublishStatus = 'draft' | 'ready' | 'published' | 'failed';

// WordPress types
export interface WordPressSite {
  id: number;
  site_name: string;
  site_url: string;
  username: string;
  is_active: boolean;
  seo_plugin: 'yoast' | 'rankmath';
  created_at: string;
  updated_at: string;
}

export interface WordPressSiteCreate {
  site_name: string;
  site_url: string;
  username: string;
  password: string;
  seo_plugin: 'yoast' | 'rankmath';
}

export interface PublishRequest {
  site_id: number;
  status: 'draft' | 'publish';
  max_retries?: number;
  retry_delay?: number;
}

export interface BatchPublishRequest {
  article_ids: number[];
  site_id: number;
  status: 'draft' | 'publish';
  stop_on_error?: boolean;
}

export interface BatchPublishResult {
  successful: number[];
  failed: FailedArticle[];
  total: number;
  success_count: number;
  error_count: number;
}

export interface FailedArticle {
  article_id: number;
  error: string;
}

export interface PublishingStatistics {
  total_articles: number;
  published: number;
  draft: number;
  ready: number;
  failed: number;
  by_site: Record<
    number,
    {
      site_name: string;
      site_url: string;
      total: number;
      published: number;
      draft: number;
    }
  >;
}

export interface PublishingQueue {
  site_id: number;
  total_queued: number;
  articles_per_day: number;
  estimated_days: number;
  articles: QueuedArticle[];
}

export interface QueuedArticle {
  id: number;
  title: string;
  word_count: number;
  overall_score: number;
  focus_keyword: string;
}

export interface ValidationError {
  field: string;
  message: string;
}

// Verdict types
export interface Verdict {
  id: number;
  file_hash: string;
  original_filename?: string;
  file_path: string;
  file_size: number;
  status: VerdictStatus;
  original_text?: string;
  cleaned_text?: string;
  anonymized_text?: string;
  case_number?: string;
  court_name?: string;
  court_level?: CourtLevel;
  judge_name?: string;
  verdict_date?: string;
  legal_area?: string;
  legal_sub_area?: string;
  parties_involved?: string[];
  key_facts?: string[];
  legal_questions?: string[];
  legal_principles?: string[];
  compensation_amount?: number;
  compensation_breakdown?: Record<string, number>;
  relevant_laws?: Law[];
  precedents_cited?: Precedent[];
  practical_insights?: string[];
  case_type?: string;
  outcome?: string;
  error_message?: string;
  processing_time_seconds?: number;
  created_at: string;
  updated_at: string;
}

export type VerdictStatus =
  | 'uploaded'
  | 'processing'
  | 'cleaned'
  | 'anonymized'
  | 'analyzed'
  | 'article_created'
  | 'failed';

export type CourtLevel = 'supreme' | 'district' | 'magistrate' | 'other';

export interface Law {
  name: string;
  section?: string;
  year?: number;
}

export interface Precedent {
  name: string;
  citation?: string;
  year?: number;
}

// Statistics types
export interface VerdictStatistics {
  total: number;
  by_status: Record<string, number>;
  by_legal_area?: Record<string, number>;
  by_court_level?: Record<string, number>;
}

export interface ArticleStatistics {
  total: number;
  by_status: Record<string, number>;
  average_scores: {
    content: number;
    seo: number;
    readability: number;
    eeat: number;
    overall: number;
  };
}

// API response types
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  skip: number;
  limit: number;
}

export interface ApiError {
  detail: string;
  status_code?: number;
}
```

---

## Page Components

### Dashboard.tsx

**File:** `src/pages/Dashboard.tsx`

```typescript
import { useQuery } from '@tanstack/react-query';
import { verdictApi, articleApi } from '../api/client';
import { Link } from 'react-router-dom';

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

export default function Dashboard() {
  const { data: verdictStats } = useQuery({
    queryKey: ['verdict-stats'],
    queryFn: () => verdictApi.getStats().then((res) => res.data),
  });

  const { data: articleStats } = useQuery({
    queryKey: ['article-stats'],
    queryFn: () => articleApi.getStats().then((res) => res.data),
  });

  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-900 mb-8">לוח בקרה</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard
          title={'סה"כ פסקי דין'}
          value={verdictStats?.total || 0}
          color="blue"
          href="/verdicts"
        />
        <StatCard
          title="מאונונמים"
          value={verdictStats?.by_status?.anonymized || 0}
          color="green"
          href="/verdicts?status=anonymized"
        />
        <StatCard
          title={'סה"כ מאמרים'}
          value={articleStats?.total || 0}
          color="purple"
          href="/articles"
        />
        <StatCard
          title="מפורסמים"
          value={articleStats?.by_status?.published || 0}
          color="indigo"
          href="/articles?status=published"
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="text-xl font-bold mb-4">פסקי דין לפי סטטוס</h2>
          {verdictStats?.by_status && (
            <div className="space-y-1">
              {Object.entries(verdictStats.by_status).map(([status, count]) => (
                <Link
                  key={status}
                  to={`/verdicts?status=${status}`}
                  className="flex justify-between hover:bg-gray-50 p-2 rounded transition-colors cursor-pointer"
                >
                  <span className="text-gray-600">{getStatusLabel(status)}</span>
                  <span className="font-medium">{count as number}</span>
                </Link>
              ))}
            </div>
          )}
        </div>

        <div className="card">
          <h2 className="text-xl font-bold mb-4">ציוני איכות ממוצעים</h2>
          {articleStats?.average_scores && (
            <div className="space-y-2">
              <ScoreBar label="תוכן" score={articleStats.average_scores.content} />
              <ScoreBar label="SEO" score={articleStats.average_scores.seo} />
              <ScoreBar
                label="קריאות"
                score={articleStats.average_scores.readability}
              />
              <ScoreBar label="E-E-A-T" score={articleStats.average_scores.eeat} />
            </div>
          )}
        </div>
      </div>

      <div className="mt-8 flex gap-4">
        <Link to="/upload" className="btn btn-primary">
          העלה פסק דין חדש
        </Link>
        <Link to="/verdicts" className="btn btn-secondary">
          צפה בכל פסקי הדין
        </Link>
      </div>
    </div>
  );
}

function StatCard({ title, value, color, href }: { title: string; value: number; color: string; href?: string }) {
  const content = (
    <>
      <h3 className="text-sm font-medium text-gray-600 mb-2">{title}</h3>
      <p className={`text-3xl font-bold text-${color}-600`}>{value}</p>
    </>
  );

  if (href) {
    return (
      <Link to={href} className="card block hover:shadow-lg hover:scale-[1.02] transition-all cursor-pointer">
        {content}
      </Link>
    );
  }

  return <div className="card">{content}</div>;
}

function ScoreBar({ label, score }: { label: string; score: number }) {
  return (
    <div>
      <div className="flex justify-between text-sm mb-1">
        <span>{label}</span>
        <span className="font-medium">{score.toFixed(1)}</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div
          className="bg-primary-600 h-2 rounded-full transition-all"
          style={{ width: `${score}%` }}
        />
      </div>
    </div>
  );
}
```

### UploadVerdict.tsx

**File:** `src/pages/UploadVerdict.tsx`

```typescript
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
```

### VerdictsList.tsx

**File:** `src/pages/VerdictsList.tsx`

```typescript
import { useQuery } from '@tanstack/react-query';
import { Link, useSearchParams } from 'react-router-dom';
import { verdictApi } from '../api/client';

export default function VerdictsList() {
  const [searchParams, setSearchParams] = useSearchParams();
  const statusFromUrl = searchParams.get('status');

  const { data, isLoading, error } = useQuery({
    queryKey: ['verdicts', statusFromUrl],
    queryFn: () => verdictApi.list({ status: statusFromUrl || undefined }).then((res) => res.data),
  });

  const handleStatusChange = (status: string) => {
    if (status) {
      setSearchParams({ status });
    } else {
      setSearchParams({});
    }
  };

  if (isLoading) {
    return <div className="text-center py-8">טוען...</div>;
  }

  if (error) {
    return (
      <div className="text-center py-8 text-red-600">
        שגיאה בטעינת פסקי הדין: {(error as Error).message}
      </div>
    );
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900">פסקי דין</h1>
        <div className="flex items-center gap-4">
          <select
            value={statusFromUrl || ''}
            onChange={(e) => handleStatusChange(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">כל הסטטוסים</option>
            <option value="new">חדש</option>
            <option value="extracted">טקסט הופק</option>
            <option value="anonymizing">מאנוניזם...</option>
            <option value="anonymized">מאונונם</option>
            <option value="analyzing">מנתח...</option>
            <option value="analyzed">נותח</option>
            <option value="article_created">מאמר נוצר</option>
            <option value="failed">נכשל</option>
          </select>
          <Link to="/upload" className="btn btn-primary">
            העלאה חדשה
          </Link>
        </div>
      </div>

      <div className="card">
        {(!data?.items || data.items.length === 0) ? (
          <div className="text-center py-8 text-gray-500">
            אין פסקי דין במערכת. לחץ על "העלאה חדשה" כדי להוסיף.
          </div>
        ) : (
          <div className="space-y-4">
            <div className="text-sm text-gray-500 mb-4">
              נמצאו {data.total} פסקי דין
            </div>
            {data.items.map((verdict: any) => (
              <Link
                key={verdict.id}
                to={`/verdicts/${verdict.id}`}
                className="block p-4 border rounded-lg hover:bg-gray-50 transition-colors"
              >
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="font-bold text-lg">
                      {verdict.case_number
                        ? `תיק מספר: ${verdict.case_number}`
                        : `פסק דין #${verdict.id}`}
                    </h3>
                    <p className="text-gray-600 text-sm">
                      {verdict.court_name || 'בית משפט לא ידוע'}
                    </p>
                    <p className="text-gray-400 text-xs mt-1">
                      נוצר: {new Date(verdict.created_at).toLocaleDateString('he-IL')}
                    </p>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(verdict.status)}`}>
                    {getStatusLabel(verdict.status)}
                  </span>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function getStatusColor(status: string): string {
  const colors: Record<string, string> = {
    new: 'bg-gray-200 text-gray-800',
    extracted: 'bg-blue-200 text-blue-800',
    anonymized: 'bg-green-200 text-green-800',
    analyzed: 'bg-purple-200 text-purple-800',
    article_created: 'bg-indigo-200 text-indigo-800',
    published: 'bg-emerald-200 text-emerald-800',
    failed: 'bg-red-200 text-red-800',
  };
  return colors[status?.toLowerCase()] || colors.new;
}

function getStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    new: 'חדש',
    extracted: 'טקסט הופק',
    anonymized: 'מאונונם',
    analyzed: 'נותח',
    article_created: 'מאמר נוצר',
    published: 'פורסם',
    failed: 'נכשל',
  };
  return labels[status?.toLowerCase()] || status || 'לא ידוע';
}
```

### VerdictDetail.tsx

**File:** `src/pages/VerdictDetail.tsx`

```typescript
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

  // Simulate progress during processing
  useEffect(() => {
    if (!isProcessing || operationProgress >= 90) return;

    const interval = setInterval(() => {
      setOperationProgress((prev) => {
        if (prev >= 90) return prev;
        return prev + Math.random() * 5;
      });
    }, 2000);

    return () => clearInterval(interval);
  }, [isProcessing, operationProgress]);

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
            {verdict.status === 'extracted' && (
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
```

### ArticlesList.tsx

**File:** `src/pages/ArticlesList.tsx` (Basic Version)

```typescript
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
```

### ArticlesListEnhanced.tsx

**File:** `src/pages/ArticlesListEnhanced.tsx` (Enhanced Version with Batch Publishing)

```typescript
import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link, useSearchParams } from 'react-router-dom';
import { articleApi, wordpressApi } from '../api/client';
import type { Article, PublishStatus } from '../types';
import { FiCheckSquare, FiSquare, FiUpload, FiFilter } from 'react-icons/fi';

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

  const { data: sites } = useQuery({
    queryKey: ['wordpress-sites'],
    queryFn: () => wordpressApi.listSites().then((res) => res.data),
  });

  const batchPublishMutation = useMutation({
    mutationFn: (data: { article_ids: number[]; site_id: number; status: string }) =>
      wordpressApi.batchPublish(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['articles'] });
      setSelectedIds([]);
      setShowBatchPublish(false);
      alert('הפרסום הצליח!');
    },
  });

  const articles: Article[] = data?.items || [];

  const toggleSelection = (id: number) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  const selectAll = () => {
    if (selectedIds.length === articles.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(articles.map((a) => a.id));
    }
  };

  if (isLoading) return <div>טוען...</div>;

  return (
    <div>
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900">מאמרים</h1>

        {selectedIds.length > 0 && (
          <div className="flex gap-2">
            <button
              onClick={() => setShowBatchPublish(true)}
              className="btn btn-primary flex items-center gap-2"
            >
              <FiUpload />
              פרסם {selectedIds.length} מאמרים
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

      {/* Batch Publish Modal */}
      {showBatchPublish && sites && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h2 className="text-2xl font-bold mb-6">פרסם מאמרים ל-WordPress</h2>

            <p className="text-gray-600 mb-4">
              נבחרו {selectedIds.length} מאמרים לפרסום
            </p>

            <div className="space-y-3">
              {sites.map((site: any) => (
                <div key={site.id} className="space-y-2">
                  <button
                    onClick={() =>
                      batchPublishMutation.mutate({
                        article_ids: selectedIds,
                        site_id: site.id,
                        status: 'draft',
                      })
                    }
                    disabled={batchPublishMutation.isPending}
                    className="btn btn-secondary w-full"
                  >
                    פרסם כטיוטה ל-{site.site_name}
                  </button>
                  <button
                    onClick={() =>
                      batchPublishMutation.mutate({
                        article_ids: selectedIds,
                        site_id: site.id,
                        status: 'publish',
                      })
                    }
                    disabled={batchPublishMutation.isPending}
                    className="btn btn-primary w-full"
                  >
                    פרסם מיידית ל-{site.site_name}
                  </button>
                </div>
              ))}
            </div>

            <button
              onClick={() => setShowBatchPublish(false)}
              className="btn btn-secondary w-full mt-4"
            >
              ביטול
            </button>

            {batchPublishMutation.isError && (
              <div className="text-red-600 text-sm mt-4">
                שגיאה: {batchPublishMutation.error?.toString()}
              </div>
            )}
          </div>
        </div>
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
```

### ArticleDetail.tsx

**File:** `src/pages/ArticleDetail.tsx`

```typescript
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
          <div className="space-y-3">
            <ScoreBar label="תוכן" score={article.content_score} />
            <ScoreBar label="SEO" score={article.seo_score} />
            <ScoreBar label="קריאות" score={article.readability_score} />
            <ScoreBar label="E-E-A-T" score={article.eeat_score} />
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

function ScoreBar({ label, score }: { label: string; score: number }) {
  return (
    <div>
      <div className="flex justify-between text-sm mb-1">
        <span>{label}</span>
        <span className="font-medium">{score}</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div
          className="bg-primary-600 h-2 rounded-full"
          style={{ width: `${score}%` }}
        />
      </div>
    </div>
  );
}
```

### WordPressManagement.tsx

**File:** `src/pages/WordPressManagement.tsx`

```typescript
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
          <dd className="font-medium">{site.username}</dd>
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
    username: site?.username || '',
    password: '',
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
              value={formData.username}
              onChange={(e) =>
                setFormData({ ...formData, username: e.target.value })
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
              value={formData.password}
              onChange={(e) =>
                setFormData({ ...formData, password: e.target.value })
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
```

### PublishingDashboard.tsx

**File:** `src/pages/PublishingDashboard.tsx`

```typescript
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { wordpressApi, articleApi } from '../api/client';
import type { PublishingStatistics, Article } from '../types';
import {
  FiAlertCircle,
  FiRefreshCw,
  FiCalendar,
  FiTrendingUp,
  FiCheckCircle,
} from 'react-icons/fi';

export default function PublishingDashboard() {
  const [selectedSite, setSelectedSite] = useState<number | null>(null);
  const queryClient = useQueryClient();

  const { data: statistics, isLoading } = useQuery<PublishingStatistics>({
    queryKey: ['wordpress-statistics', selectedSite],
    queryFn: () =>
      wordpressApi.getStatistics(selectedSite || undefined).then((res) => res.data),
  });

  const { data: sites } = useQuery({
    queryKey: ['wordpress-sites'],
    queryFn: () => wordpressApi.listSites().then((res) => res.data),
  });

  const { data: failedArticles } = useQuery({
    queryKey: ['articles', 'failed'],
    queryFn: () =>
      articleApi.list({ status: 'failed' }).then((res) => res.data?.items || []),
  });

  const { data: readyArticles } = useQuery({
    queryKey: ['articles', 'ready'],
    queryFn: () =>
      articleApi.list({ status: 'ready' }).then((res) => res.data?.items || []),
  });

  const republishMutation = useMutation({
    mutationFn: (siteId: number) =>
      wordpressApi.republishFailed({ site_id: siteId, max_articles: 10 }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['articles'] });
      queryClient.invalidateQueries({ queryKey: ['wordpress-statistics'] });
      alert('ניסיון הפרסום מחדש הושלם!');
    },
  });

  if (isLoading) return <div>טוען...</div>;

  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-900 mb-8">לוח בקרת פרסום</h1>

      {/* Site Filter */}
      <div className="card mb-6">
        <div className="flex items-center gap-4">
          <label className="font-medium">סינון לפי אתר:</label>
          <select
            value={selectedSite || ''}
            onChange={(e) =>
              setSelectedSite(e.target.value ? Number(e.target.value) : null)
            }
            className="input"
          >
            <option value="">כל האתרים</option>
            {sites?.map((site: any) => (
              <option key={site.id} value={site.id}>
                {site.site_name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Statistics Cards */}
      {statistics && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6 mb-8">
          <StatCard
            title="סה״כ מאמרים"
            value={statistics.total_articles}
            icon={<FiTrendingUp />}
            color="blue"
          />
          <StatCard
            title="מפורסמים"
            value={statistics.published}
            icon={<FiCheckCircle />}
            color="green"
          />
          <StatCard
            title="מוכנים"
            value={statistics.ready}
            icon={<FiCalendar />}
            color="blue"
          />
          <StatCard
            title="טיוטות"
            value={statistics.draft}
            icon={<FiRefreshCw />}
            color="yellow"
          />
          <StatCard
            title="נכשלו"
            value={statistics.failed}
            icon={<FiAlertCircle />}
            color="red"
          />
        </div>
      )}

      {/* Per-Site Statistics */}
      {!selectedSite && statistics?.by_site && (
        <div className="card mb-8">
          <h2 className="text-xl font-bold mb-6">סטטיסטיקות לפי אתר</h2>
          <div className="grid gap-4">
            {Object.entries(statistics.by_site).map(([siteId, siteStats]) => (
              <div
                key={siteId}
                className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
              >
                <div className="flex justify-between items-center mb-3">
                  <div>
                    <h3 className="font-bold text-lg">{siteStats.site_name}</h3>
                    <a
                      href={siteStats.site_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm text-blue-600 hover:underline"
                    >
                      {siteStats.site_url}
                    </a>
                  </div>
                  <span className="text-2xl font-bold text-gray-700">
                    {siteStats.total}
                  </span>
                </div>
                <div className="flex gap-4 text-sm">
                  <div>
                    <span className="text-gray-600">מפורסמים: </span>
                    <span className="font-medium text-green-600">
                      {siteStats.published}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-600">טיוטות: </span>
                    <span className="font-medium text-yellow-600">
                      {siteStats.draft}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Failed Articles Section */}
      {failedArticles && failedArticles.length > 0 && (
        <div className="card mb-8">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-bold flex items-center gap-2">
              <FiAlertCircle className="text-red-600" />
              מאמרים שנכשלו ({failedArticles.length})
            </h2>
            {sites && sites.length > 0 && (
              <button
                onClick={() => republishMutation.mutate(sites[0].id)}
                disabled={republishMutation.isPending}
                className="btn btn-primary flex items-center gap-2"
              >
                <FiRefreshCw />
                נסה לפרסם מחדש
              </button>
            )}
          </div>

          <div className="space-y-3">
            {failedArticles.slice(0, 10).map((article: Article) => (
              <Link
                key={article.id}
                to={`/articles/${article.id}`}
                className="block p-4 border border-red-200 rounded-lg hover:bg-red-50 transition-colors"
              >
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="font-medium text-gray-900">{article.title}</h3>
                    {article.metadata?.last_publish_error && (
                      <p className="text-sm text-red-600 mt-1">
                        שגיאה: {article.metadata.last_publish_error}
                      </p>
                    )}
                  </div>
                  <span className="badge bg-red-200 text-red-800">נכשל</span>
                </div>
              </Link>
            ))}
          </div>

          {failedArticles.length > 10 && (
            <Link
              to="/articles?status=failed"
              className="text-blue-600 hover:underline text-sm mt-4 inline-block"
            >
              צפה בכל המאמרים שנכשלו →
            </Link>
          )}
        </div>
      )}

      {/* Ready to Publish Section */}
      {readyArticles && readyArticles.length > 0 && (
        <div className="card mb-8">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-bold flex items-center gap-2">
              <FiCalendar className="text-blue-600" />
              מוכנים לפרסום ({readyArticles.length})
            </h2>
            <Link to="/articles?status=ready" className="btn btn-primary">
              ניהול תור פרסום
            </Link>
          </div>

          <div className="space-y-3">
            {readyArticles.slice(0, 5).map((article: Article) => (
              <Link
                key={article.id}
                to={`/articles/${article.id}`}
                className="block p-4 border border-blue-200 rounded-lg hover:bg-blue-50 transition-colors"
              >
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="font-medium text-gray-900">{article.title}</h3>
                    <div className="flex gap-3 mt-2 text-sm text-gray-600">
                      <span>{article.word_count} מילים</span>
                      <span>ציון: {article.overall_score}/100</span>
                      {article.focus_keyword && (
                        <span className="text-purple-600">
                          🔑 {article.focus_keyword}
                        </span>
                      )}
                    </div>
                  </div>
                  <span className="badge bg-blue-200 text-blue-800">מוכן</span>
                </div>
              </Link>
            ))}
          </div>

          {readyArticles.length > 5 && (
            <Link
              to="/articles?status=ready"
              className="text-blue-600 hover:underline text-sm mt-4 inline-block"
            >
              צפה בכל המאמרים המוכנים →
            </Link>
          )}
        </div>
      )}

      {/* Queue Management */}
      <QueueManagement />

      {/* Publishing Tips */}
      <div className="card bg-blue-50 border-blue-200">
        <h3 className="font-bold mb-3 flex items-center gap-2">
          <FiCheckCircle className="text-blue-600" />
          טיפים לפרסום יעיל
        </h3>
        <ul className="space-y-2 text-sm text-gray-700">
          <li>• פרסם מאמרים עם ציון איכות מעל 70 לתוצאות SEO מיטביות</li>
          <li>• השתמש בפרסום אצווה (Batch) לפרסום מספר מאמרים בבת אחת</li>
          <li>• בדוק מאמרים שנכשלו באופן קבוע ונסה לפרסם מחדש</li>
          <li>• תכנן תור פרסום ל-5-10 מאמרים ביום לקצב עדכון קבוע</li>
          <li>• התחל עם סטטוס "טיוטה" לבדיקה לפני פרסום סופי</li>
        </ul>
      </div>
    </div>
  );
}

function StatCard({
  title,
  value,
  icon,
  color,
}: {
  title: string;
  value: number;
  icon: React.ReactNode;
  color: string;
}) {
  const colorClasses = {
    blue: 'bg-blue-100 text-blue-600',
    green: 'bg-green-100 text-green-600',
    yellow: 'bg-yellow-100 text-yellow-600',
    red: 'bg-red-100 text-red-600',
  };

  return (
    <div className="card">
      <div className="flex items-start justify-between mb-3">
        <div className={`p-2 rounded-lg ${colorClasses[color as keyof typeof colorClasses]}`}>
          {icon}
        </div>
      </div>
      <h3 className="text-sm font-medium text-gray-600 mb-1">{title}</h3>
      <p className="text-3xl font-bold text-gray-900">{value}</p>
    </div>
  );
}

function QueueManagement() {
  const [showQueueModal, setShowQueueModal] = useState(false);
  const [queueConfig, setQueueConfig] = useState({
    site_id: 0,
    articles_per_day: 5,
    min_score: 70,
  });

  const { data: sites } = useQuery({
    queryKey: ['wordpress-sites'],
    queryFn: () => wordpressApi.listSites().then((res) => res.data),
  });

  const queueMutation = useMutation({
    mutationFn: (config: typeof queueConfig) => wordpressApi.scheduleQueue(config),
    onSuccess: (response) => {
      alert(`תור פרסום נוצר: ${response.data.total_queued} מאמרים לאורך ${response.data.estimated_days} ימים`);
      setShowQueueModal(false);
    },
  });

  return (
    <div className="card mb-8">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-bold">ניהול תור פרסום</h2>
        <button
          onClick={() => setShowQueueModal(true)}
          className="btn btn-primary"
        >
          צור תור פרסום
        </button>
      </div>

      <p className="text-gray-600 text-sm">
        תכנן מראש את פרסום המאמרים עם תור פרסום מבוקר. קבע כמות מאמרים ליום וציון איכות מינימלי.
      </p>

      {showQueueModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-2xl font-bold mb-6">צור תור פרסום</h3>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">אתר WordPress</label>
                <select
                  value={queueConfig.site_id}
                  onChange={(e) =>
                    setQueueConfig({ ...queueConfig, site_id: Number(e.target.value) })
                  }
                  className="input w-full"
                >
                  <option value={0}>בחר אתר</option>
                  {sites?.map((site: any) => (
                    <option key={site.id} value={site.id}>
                      {site.site_name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">מאמרים ליום</label>
                <input
                  type="number"
                  value={queueConfig.articles_per_day}
                  onChange={(e) =>
                    setQueueConfig({
                      ...queueConfig,
                      articles_per_day: Number(e.target.value),
                    })
                  }
                  min={1}
                  max={20}
                  className="input w-full"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">ציון איכות מינימלי</label>
                <input
                  type="number"
                  value={queueConfig.min_score}
                  onChange={(e) =>
                    setQueueConfig({
                      ...queueConfig,
                      min_score: Number(e.target.value),
                    })
                  }
                  min={0}
                  max={100}
                  className="input w-full"
                />
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  onClick={() => queueMutation.mutate(queueConfig)}
                  disabled={queueMutation.isPending || queueConfig.site_id === 0}
                  className="btn btn-primary flex-1"
                >
                  צור תור
                </button>
                <button
                  onClick={() => setShowQueueModal(false)}
                  className="btn btn-secondary flex-1"
                >
                  ביטול
                </button>
              </div>

              {queueMutation.isError && (
                <div className="text-red-600 text-sm">
                  שגיאה: {queueMutation.error?.toString()}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
```

---

## Usage Guide

### Getting Started

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Run development server:**
   ```bash
   npm run dev
   ```

3. **Build for production:**
   ```bash
   npm run build
   ```

### Key Features

- **RTL Support**: Full Hebrew/RTL layout support via Tailwind CSS
- **React Query**: Data fetching and caching with TanStack Query
- **Type Safety**: Full TypeScript support with comprehensive type definitions
- **Responsive Design**: Mobile-first responsive design with Tailwind CSS
- **File Upload**: Drag-and-drop file upload with react-dropzone
- **Real-time Updates**: Polling for processing status updates
- **Batch Operations**: Bulk article publishing to WordPress
- **WordPress Integration**: Multi-site WordPress management and publishing

### Architecture

- **Component Structure**: Functional components with React hooks
- **State Management**: React Query for server state, useState for local state
- **Routing**: React Router v6 with nested routes
- **API Layer**: Centralized Axios client with typed API methods
- **Styling**: Tailwind CSS with custom components and utilities

---

**Document Generated:** 2026-01-18
**Total Files:** 18 files (4 config files, 3 core files, 2 API/types files, 9 page components)
**Purpose:** Complete frontend code reference for rebuilding the Legal Content Management System UI
