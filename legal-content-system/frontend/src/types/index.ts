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
  api_username: string;
  is_active: boolean;
  seo_plugin: 'yoast' | 'rankmath';
  created_at: string;
  updated_at: string;
}

export interface WordPressSiteCreate {
  site_name: string;
  site_url: string;
  api_username: string;
  api_password: string;
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
