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
  getBatchProgress: (batchId: string) =>
    apiClient.get(`/wordpress/articles/batch-publish/${batchId}/progress`),
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
