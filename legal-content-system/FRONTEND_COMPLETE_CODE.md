# Frontend Complete Code - Legal Content System
## קוד מלא של ממשק המשתמש

---

## תוכן עניינים
1. [הגדרות פרויקט](#1-הגדרות-פרויקט)
2. [API Client](#2-api-client)
3. [Types & Interfaces](#3-types--interfaces)
4. [App.tsx](#4-apptsx)
5. [Main.tsx](#5-maintsx)
6. [Styles](#6-styles)
7. [Pages](#7-pages)
   - Dashboard
   - Upload Verdict
   - Verdicts List
   - Verdict Detail
   - Articles List
   - Article Detail
   - WordPress Management
   - Publishing Dashboard

---

## 1. הגדרות פרויקט

### `package.json`
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

### `vite.config.ts`
```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  }
})
```

### `tailwind.config.js`
```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
```

### `tsconfig.json`
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
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

## 2. API Client

### `src/api/client.ts`
```typescript
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Verdicts API
export const verdictApi = {
  upload: (file: File, overwrite = false) => {
    const formData = new FormData();
    formData.append('file', file);
    if (overwrite) {
      formData.append('overwrite', 'true');
    }
    return apiClient.post('/verdicts/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  list: (params?: { status?: string; skip?: number; limit?: number }) =>
    apiClient.get('/verdicts', { params }),

  get: (id: number) =>
    apiClient.get(`/verdicts/${id}`),

  update: (id: number, data: any) =>
    apiClient.patch(`/verdicts/${id}`, data),

  delete: (id: number) =>
    apiClient.delete(`/verdicts/${id}`),

  anonymize: (id: number) =>
    apiClient.post(`/verdicts/${id}/anonymize`),

  reAnonymize: (id: number) =>
    apiClient.post(`/verdicts/${id}/re-anonymize`),

  reprocess: (id: number) =>
    apiClient.post(`/verdicts/${id}/reprocess`),

  getStats: () =>
    apiClient.get('/verdicts/statistics/overview'),

  getAnonymizationStats: () =>
    apiClient.get('/verdicts/statistics/anonymization'),
};

// Articles API
export const articleApi = {
  analyze: (verdictId: number) =>
    apiClient.post(`/articles/verdicts/${verdictId}/analyze`),

  reAnalyze: (verdictId: number) =>
    apiClient.post(`/articles/verdicts/${verdictId}/re-analyze`),

  generate: (verdictId: number) =>
    apiClient.post(`/articles/generate/${verdictId}`),

  list: (params?: { publish_status?: string; skip?: number; limit?: number }) =>
    apiClient.get('/articles', { params }),

  get: (id: number) =>
    apiClient.get(`/articles/${id}`),

  getByVerdict: (verdictId: number) =>
    apiClient.get(`/articles/by-verdict/${verdictId}`),

  getStats: () =>
    apiClient.get('/articles/statistics/overview'),

  getAnalysisStats: () =>
    apiClient.get('/articles/verdicts/statistics/analysis'),
};

// WordPress API
export const wordpressApi = {
  listSites: () =>
    apiClient.get('/wordpress/sites'),

  getSite: (id: number) =>
    apiClient.get(`/wordpress/sites/${id}`),

  createSite: (data: any) =>
    apiClient.post('/wordpress/sites', data),

  updateSite: (id: number, data: any) =>
    apiClient.patch(`/wordpress/sites/${id}`, data),

  deleteSite: (id: number) =>
    apiClient.delete(`/wordpress/sites/${id}`),

  testSite: (id: number) =>
    apiClient.post(`/wordpress/sites/${id}/test`),

  getCategories: (siteId: number) =>
    apiClient.get(`/wordpress/sites/${siteId}/categories`),

  getTags: (siteId: number) =>
    apiClient.get(`/wordpress/sites/${siteId}/tags`),

  publish: (articleId: number, data: { site_id: number; draft?: boolean }) =>
    apiClient.post(`/wordpress/publish/${articleId}`, data),

  unpublish: (articleId: number) =>
    apiClient.post(`/wordpress/unpublish/${articleId}`),

  validateArticle: (articleId: number) =>
    apiClient.post(`/wordpress/articles/${articleId}/validate`),

  batchPublish: (data: { article_ids: number[]; site_id: number; draft?: boolean }) =>
    apiClient.post('/wordpress/batch-publish', data),

  republishFailed: (data: { site_id?: number }) =>
    apiClient.post('/wordpress/republish-failed', data),

  getStatistics: (siteId?: number) =>
    apiClient.get('/wordpress/statistics', { params: { site_id: siteId } }),
};

export default apiClient;
```

---

## 3. Types & Interfaces

### `src/types/index.ts`
```typescript
export interface Verdict {
  id: number;
  file_hash: string;
  case_number: string;
  case_number_display: string;
  court_name: string | null;
  court_level: string | null;
  judge_name: string | null;
  verdict_date: string | null;
  case_type: string | null;
  legal_area: string | null;
  legal_sub_area: string | null;
  original_text: string;
  cleaned_text: string;
  anonymized_text: string | null;
  anonymization_report: any | null;
  privacy_risk_level: 'low' | 'medium' | 'high';
  key_facts: string[] | null;
  legal_questions: string[] | null;
  legal_principles: string[] | null;
  compensation_amount: number | null;
  compensation_breakdown: any | null;
  relevant_laws: any[] | null;
  precedents_cited: any[] | null;
  practical_insights: string[] | null;
  status: VerdictStatus;
  requires_manual_review: boolean;
  review_notes: string | null;
  created_at: string;
  updated_at: string;
}

export type VerdictStatus =
  | 'new'
  | 'extracting'
  | 'extracted'
  | 'anonymizing'
  | 'anonymized'
  | 'analyzing'
  | 'analyzed'
  | 'article_created'
  | 'published'
  | 'failed';

export interface Article {
  id: number;
  verdict_id: number;
  title: string;
  slug: string;
  meta_description: string;
  focus_keyword: string;
  secondary_keywords: string[];
  long_tail_keywords: string[];
  content_html: string;
  word_count: number;
  reading_time_minutes: number;
  faq_items: FAQItem[];
  common_mistakes: string[];
  internal_links: LinkSuggestion[];
  external_links: LinkSuggestion[];
  schema_markup: any;
  content_score: number;
  seo_score: number;
  readability_score: number;
  eeat_score: number;
  overall_score: number;
  publish_status: PublishStatus;
  wordpress_site_id: number | null;
  wordpress_post_id: number | null;
  wordpress_url: string | null;
  published_at: string | null;
  created_at: string;
  updated_at: string;
}

export type PublishStatus =
  | 'draft'
  | 'pending_review'
  | 'ready'
  | 'published'
  | 'failed';

export interface FAQItem {
  question: string;
  answer: string;
}

export interface LinkSuggestion {
  text: string;
  url: string;
  relevance: string;
}

export interface WordPressSite {
  id: number;
  name: string;
  url: string;
  username: string;
  is_active: boolean;
  seo_plugin: 'yoast' | 'rankmath' | null;
  default_author_id: number | null;
  default_category_id: number | null;
  category_mapping: any;
  created_at: string;
  updated_at: string;
}

export interface Statistics {
  total: number;
  by_status: Record<string, number>;
  pending_review: number;
}

export interface PublishingStatistics {
  total_articles: number;
  published: number;
  draft: number;
  ready: number;
  failed: number;
  by_site: Record<string, number>;
  recent_publications: any[];
}
```

---

*המשך בהודעה הבאה...*
