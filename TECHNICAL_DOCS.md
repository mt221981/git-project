# Technical Documentation - Legal Content System

## Architecture Overview

### Stack
- **Backend**: FastAPI (Python 3.11+)
- **Frontend**: React 18 + TypeScript + Vite
- **Database**: SQLite with SQLAlchemy ORM
- **AI Engine**: Anthropic Claude API (claude-3-5-sonnet-20241022)
- **State Management**: React Query (TanStack Query)
- **Styling**: Tailwind CSS

### Design Pattern
Service-based architecture with clear separation of concerns:
- **Routers**: HTTP endpoint handlers
- **Services**: Business logic and orchestration
- **Models**: Database schema (SQLAlchemy)
- **Schemas**: Request/Response validation (Pydantic)

## Database Schema

### Verdicts Table
```sql
CREATE TABLE verdicts (
    id INTEGER PRIMARY KEY,
    file_hash VARCHAR(64) UNIQUE NOT NULL,
    case_number VARCHAR(50),
    court_name VARCHAR(200),
    court_level VARCHAR(50),
    judge_name VARCHAR(200),
    verdict_date DATE,
    legal_area VARCHAR(100),
    legal_sub_area VARCHAR(100),
    status VARCHAR(20) NOT NULL,  -- new, extracted, anonymizing, anonymized, analyzing, analyzed, article_created, failed

    -- Text fields
    original_text TEXT,
    cleaned_text TEXT,
    anonymized_text TEXT,

    -- Analysis results (JSON)
    key_facts JSON,
    legal_questions JSON,
    legal_principles JSON,
    relevant_laws JSON,
    precedents_cited JSON,
    practical_insights JSON,
    compensation_amount DECIMAL(15, 2),
    compensation_breakdown JSON,

    -- Progress tracking
    processing_progress INTEGER DEFAULT 0,
    processing_message VARCHAR(500),

    -- Anonymization report
    anonymization_changes JSON,
    anonymization_risk VARCHAR(20),

    -- Review
    requires_manual_review BOOLEAN DEFAULT FALSE,
    review_notes TEXT,

    -- Timestamps
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    -- Indexes
    INDEX ix_verdicts_status (status),
    INDEX ix_verdicts_case_number (case_number),
    INDEX ix_verdicts_file_hash (file_hash)
);
```

### Articles Table
```sql
CREATE TABLE articles (
    id INTEGER PRIMARY KEY,
    verdict_id INTEGER NOT NULL,

    -- Content
    title VARCHAR(70) NOT NULL,
    slug VARCHAR(200) UNIQUE NOT NULL,
    meta_title VARCHAR(70),
    meta_description VARCHAR(160),
    excerpt TEXT,
    content_html TEXT NOT NULL,

    -- SEO
    focus_keyword VARCHAR(100),
    secondary_keywords JSON,  -- array of strings
    long_tail_keywords JSON,  -- array of strings

    -- Extended content
    faq_items JSON,  -- [{question, answer}]
    common_mistakes JSON,  -- array of strings

    -- Schema markup
    schema_article JSON,
    schema_faq JSON,

    -- Links
    internal_links JSON,  -- array of {url, anchor, target}
    external_links JSON,  -- array of {url, anchor, target}

    -- Metadata
    word_count INTEGER,
    reading_time_minutes INTEGER,
    category_primary VARCHAR(100),
    categories_secondary JSON,
    tags JSON,

    -- Images
    featured_image_url VARCHAR(500),
    featured_image_prompt TEXT,
    featured_image_alt VARCHAR(200),

    -- Quality scores
    content_score INTEGER,
    seo_score INTEGER,
    readability_score INTEGER,
    eeat_score INTEGER,
    overall_score INTEGER,
    quality_issues JSON,  -- [{type, message}]

    -- Publishing
    publish_status VARCHAR(20) DEFAULT 'draft',  -- draft, pending_review, ready, published, failed
    wordpress_post_id INTEGER,
    wordpress_url VARCHAR(500),
    published_at DATETIME,

    -- Timestamps
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    -- Foreign keys
    FOREIGN KEY (verdict_id) REFERENCES verdicts(id),

    -- Indexes
    INDEX ix_articles_verdict_id (verdict_id),
    INDEX ix_articles_slug (slug),
    INDEX ix_articles_publish_status (publish_status)
);
```

### WordPress Sites Table
```sql
CREATE TABLE wordpress_sites (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    url VARCHAR(500) NOT NULL,
    username VARCHAR(100) NOT NULL,
    app_password VARCHAR(200) NOT NULL,  -- Encrypted
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Users Table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    role VARCHAR(20) DEFAULT 'editor',  -- admin, editor, viewer
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    INDEX ix_users_email (email)
);
```

## Services Architecture

### 1. VerdictService
**File**: `backend/app/services/verdict_service.py`

**Responsibilities**:
- Upload and store verdict PDFs
- Manage verdict lifecycle and status
- Reprocess verdicts from beginning
- Query and statistics

**Key Methods**:
```python
def upload_verdict(file: UploadFile) -> Verdict
def get_verdict(verdict_id: int) -> Optional[Verdict]
def update_verdict_status(verdict_id: int, status: VerdictStatus) -> Verdict
def reprocess_verdict(verdict_id: int) -> Verdict
def get_verdict_stats() -> dict
```

### 2. FileProcessor
**File**: `backend/app/services/file_processor.py`

**Responsibilities**:
- Extract text from PDF files
- Clean and normalize Hebrew text
- Handle various PDF formats

**Key Methods**:
```python
def extract_text_from_pdf(file_path: str) -> str
def clean_text(raw_text: str) -> str
```

**Dependencies**:
- PyPDF2
- pdfplumber

### 3. AnonymizationService
**File**: `backend/app/services/anonymization_service.py`

**Responsibilities**:
- Orchestrate anonymization process
- Manage background tasks
- Update progress tracking

**Key Methods**:
```python
def anonymize_verdict(verdict_id: int) -> Verdict
def _update_progress(verdict_id: int, progress: int, message: str)
```

### 4. Anonymizer
**File**: `backend/app/services/anonymizer.py`

**Responsibilities**:
- Call Claude API for anonymization
- Parse anonymization results
- Risk assessment

**Key Methods**:
```python
def anonymize(text: str) -> dict
    # Returns:
    # {
    #     "anonymized_text": str,
    #     "changes": list,
    #     "risk_assessment": str,
    #     "requires_manual_review": bool
    # }
```

**Prompt**: `ANONYMIZATION_SYSTEM_PROMPT` + `ANONYMIZATION_USER_PROMPT`

### 5. AnalysisService
**File**: `backend/app/services/analysis_service.py`

**Responsibilities**:
- Orchestrate legal analysis
- Manage background tasks
- Re-analysis capability

**Key Methods**:
```python
def analyze_verdict(verdict_id: int) -> Verdict
def re_analyze_verdict(verdict_id: int) -> Verdict
def get_analysis_stats() -> dict
```

### 6. VerdictAnalyzer
**File**: `backend/app/services/verdict_analyzer.py`

**Responsibilities**:
- Call Claude API for analysis
- Parse and validate results
- Extract structured legal data

**Key Methods**:
```python
def analyze(verdict_text: str, metadata: dict) -> dict
    # Returns:
    # {
    #     "key_facts": list,
    #     "legal_questions": list,
    #     "legal_principles": list,
    #     "relevant_laws": list,
    #     "precedents_cited": list,
    #     "practical_insights": list,
    #     "compensation_amount": float,
    #     "compensation_breakdown": dict
    # }
```

**Prompt**: `VERDICT_ANALYSIS_SYSTEM_PROMPT` + `VERDICT_ANALYSIS_USER_PROMPT`

### 7. ArticleService
**File**: `backend/app/services/article_service.py`

**Responsibilities**:
- Orchestrate article generation
- Calculate metrics (word count, reading time)
- Score article quality
- Generate schema markup
- Manage article CRUD operations

**Key Methods**:
```python
def generate_article_from_verdict(verdict_id: int) -> Article
def generate_article_content(verdict_metadata: dict, analysis_data: dict) -> dict
def score_article(article_content: dict) -> dict
def generate_schema_markup(article_data: dict) -> dict
def get_article_stats() -> dict
```

### 8. ArticleGenerator
**File**: `backend/app/services/article_generator.py`

**Responsibilities**:
- Call Claude API for article generation
- Parse article content
- Calculate quality scores

**Key Methods**:
```python
def generate(verdict_data: dict) -> dict
    # Returns:
    # {
    #     "title": str,
    #     "excerpt": str,
    #     "content_html": str,
    #     "meta_title": str,
    #     "meta_description": str,
    #     "focus_keyword": str,
    #     "secondary_keywords": list,
    #     "long_tail_keywords": list,
    #     "faq_items": list,
    #     "common_mistakes": list,
    #     "tags": list,
    #     ...
    # }

def calculate_scores(article_content: dict) -> dict
    # Returns:
    # {
    #     "content_score": int,
    #     "seo_score": int,
    #     "readability_score": int,
    #     "eeat_score": int,
    #     "overall_score": int
    # }
```

**Prompt**: `ARTICLE_GENERATION_SYSTEM_PROMPT` + `ARTICLE_GENERATION_USER_PROMPT`

### 9. QualityChecker
**File**: `backend/app/services/quality_checker.py`

**Responsibilities**:
- Score article quality across dimensions
- Identify quality issues
- Provide improvement recommendations

**Scoring Algorithm**:
```python
Content Score:
- Word count (800-2500 optimal): up to 30 points
- FAQ items (5-7 optimal): up to 25 points
- Common mistakes section: 20 points
- Internal links (3-5): up to 15 points
- External links (2-3): up to 10 points

SEO Score:
- Focus keyword in title: 20 points
- Meta title length (50-70): 15 points
- Meta description length (140-160): 15 points
- Secondary keywords (5-8): 20 points
- Long-tail keywords (3-5): 10 points
- Alt text present: 10 points
- Slug optimized: 10 points

Readability Score:
- Paragraph count (5-15): up to 30 points
- List usage: up to 30 points
- Heading structure (H2/H3): up to 40 points

E-E-A-T Score:
- Legal principles: 30 points
- Precedents cited: 25 points
- Relevant laws: 25 points
- FAQ comprehensive: 20 points
```

### 10. LinkEnhancementService
**File**: `backend/app/services/link_enhancement.py`

**Responsibilities**:
- Add internal links to related content
- Add external links to authoritative sources
- Ensure natural anchor text

**Key Methods**:
```python
def enhance_with_links(
    content_html: str,
    focus_keyword: str,
    secondary_keywords: list,
    max_internal: int = 5,
    max_external: int = 3
) -> str

def get_stats(content_html: str) -> dict
    # Returns:
    # {
    #     "internal_links": int,
    #     "external_links": int,
    #     "total_links": int
    # }
```

**Link Patterns**:
- Internal: Israeli legal sites, government resources
- External: Authoritative legal databases, court websites

### 11. AnthropicClient
**File**: `backend/app/utils/anthropic_client.py`

**Responsibilities**:
- Manage Claude API connection
- Handle rate limiting
- Retry logic
- Token optimization

**Key Methods**:
```python
def create_message(
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 4096,
    temperature: float = 0.7
) -> str

def create_structured_message(
    prompt: str,
    max_tokens: int = 4096
) -> str
```

**Configuration**:
- Model: claude-3-5-sonnet-20241022
- Max tokens: 4096 (configurable)
- Temperature: 0.7 (balance creativity/consistency)

## API Endpoints

### Verdicts Router
**File**: `backend/app/routers/verdicts.py`

```python
POST   /api/v1/verdicts/upload
GET    /api/v1/verdicts/
GET    /api/v1/verdicts/{verdict_id}
POST   /api/v1/verdicts/{verdict_id}/anonymize
POST   /api/v1/verdicts/{verdict_id}/reprocess
DELETE /api/v1/verdicts/{verdict_id}
GET    /api/v1/verdicts/statistics/overview
GET    /api/v1/verdicts/statistics/anonymization
```

### Articles Router
**File**: `backend/app/routers/articles.py`

```python
POST   /api/v1/articles/verdicts/{verdict_id}/analyze
POST   /api/v1/articles/generate/{verdict_id}
GET    /api/v1/articles/
GET    /api/v1/articles/{article_id}
GET    /api/v1/articles/by-verdict/{verdict_id}
POST   /api/v1/articles/verdicts/{verdict_id}/re-analyze
GET    /api/v1/articles/statistics/overview
GET    /api/v1/articles/verdicts/statistics/analysis
```

### WordPress Router
**File**: `backend/app/routers/wordpress.py`

```python
POST   /api/v1/wordpress/sites
GET    /api/v1/wordpress/sites
GET    /api/v1/wordpress/sites/{site_id}
PUT    /api/v1/wordpress/sites/{site_id}
DELETE /api/v1/wordpress/sites/{site_id}
POST   /api/v1/wordpress/articles/{article_id}/publish
GET    /api/v1/wordpress/statistics
```

### Auth Router
**File**: `backend/app/routers/auth.py`

```python
POST   /api/v1/auth/register
POST   /api/v1/auth/login
GET    /api/v1/auth/me
POST   /api/v1/auth/logout
```

## Frontend Architecture

### Pages

#### Dashboard
**File**: `frontend/src/pages/Dashboard.tsx`

**Features**:
- Statistics cards (verdicts by status, articles by status)
- Quick actions
- File upload
- Recent activity

**State**:
- React Query for fetching stats
- File upload mutation

#### VerdictDetail
**File**: `frontend/src/pages/VerdictDetail.tsx`

**Features**:
- Verdict metadata display
- Status indicator
- Action buttons (anonymize, analyze, generate, reprocess)
- Progress bar with real-time updates
- Timer for long operations
- Text preview

**State**:
- React Query with polling (2s interval during processing)
- Local state for progress tracking
- useEffect for status change detection

**Polling Logic**:
```typescript
refetchInterval: isProcessing ? 2000 : false
```

#### ArticlesListEnhanced
**File**: `frontend/src/pages/ArticlesListEnhanced.tsx`

**Features**:
- Article list with filtering
- Status badges
- Score indicators
- Quick preview
- Bulk actions (future)

#### PublishingDashboard
**File**: `frontend/src/pages/PublishingDashboard.tsx`

**Features**:
- Ready-to-publish articles
- WordPress site management
- Publishing queue (future)
- Publishing history

### API Client
**File**: `frontend/src/api/client.ts`

**Structure**:
```typescript
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json'
  }
});

export const verdictApi = {
  upload: (file: File) => FormData upload,
  get: (id: number) => GET /verdicts/{id},
  list: (params) => GET /verdicts/,
  anonymize: (id: number) => POST /verdicts/{id}/anonymize,
  reprocess: (id: number) => POST /verdicts/{id}/reprocess,
  stats: () => GET /verdicts/statistics/overview
};

export const articleApi = {
  generate: (verdictId: number) => POST /articles/generate/{id},
  analyze: (verdictId: number) => POST /articles/verdicts/{id}/analyze,
  get: (id: number) => GET /articles/{id},
  getByVerdict: (verdictId: number) => GET /articles/by-verdict/{id},
  list: (params) => GET /articles/,
  stats: () => GET /articles/statistics/overview
};

export const wordpressApi = {
  // WordPress endpoints
};
```

## Background Tasks

### FastAPI BackgroundTasks
Used for long-running operations:

```python
@router.post("/verdicts/{verdict_id}/anonymize")
async def anonymize_verdict(
    verdict_id: int,
    background_tasks: BackgroundTasks,
    ...
):
    # Set status to 'anonymizing'
    verdict = service.update_status(verdict_id, VerdictStatus.ANONYMIZING)

    # Add background task
    background_tasks.add_task(run_anonymization_background, verdict_id)

    # Return immediately
    return VerdictResponse.model_validate(verdict)

def run_anonymization_background(verdict_id: int):
    """Runs in background with own DB session."""
    db = SessionLocal()
    try:
        anonymization_service = AnonymizationService(db)
        anonymization_service.anonymize_verdict(verdict_id)
    except Exception as e:
        # Handle error, update verdict status to FAILED
        ...
    finally:
        db.close()
```

### Progress Tracking
Real-time progress updates during processing:

```python
def _update_progress(self, verdict_id: int, progress: int, message: str):
    """Update verdict progress and message."""
    verdict = self.db.query(Verdict).filter(Verdict.id == verdict_id).first()
    if verdict:
        verdict.processing_progress = progress
        verdict.processing_message = message
        self.db.commit()
```

Frontend polls for updates:
```typescript
useEffect(() => {
  if (verdict?.processing_progress !== undefined) {
    setOperationProgress(verdict.processing_progress);
  }
  if (verdict?.processing_message) {
    setOperationMessage(verdict.processing_message);
  }
}, [verdict?.processing_progress, verdict?.processing_message]);
```

## Error Handling

### Backend Error Handling

**Service Layer**:
```python
try:
    result = self.anonymizer.anonymize(text)
except AnonymizationError as e:
    raise  # Re-raise service-specific error
except Exception as e:
    # Catch unexpected errors
    raise AnonymizationError(f"Unexpected error: {str(e)}")
```

**Router Layer**:
```python
try:
    verdict = service.anonymize_verdict(verdict_id)
    return VerdictResponse.model_validate(verdict)
except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))
except AnonymizationError as e:
    raise HTTPException(status_code=422, detail=str(e))
except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
```

**Background Task Error Handling**:
```python
def run_anonymization_background(verdict_id: int):
    db = SessionLocal()
    try:
        anonymization_service.anonymize_verdict(verdict_id)
    except Exception as e:
        print(f"[Background] Anonymization failed: {str(e)}")
        verdict = db.query(Verdict).filter(Verdict.id == verdict_id).first()
        if verdict:
            verdict.status = VerdictStatus.FAILED
            verdict.review_notes = f"Anonymization failed: {str(e)}"
            db.commit()
    finally:
        db.close()
```

### Frontend Error Handling

**React Query Error Handling**:
```typescript
const anonymizeMutation = useMutation({
  mutationFn: () => verdictApi.anonymize(Number(id)),
  onError: (error: Error) => {
    setIsProcessing(false);
    setOperationProgress(0);
    setOperationMessage(`שגיאה: ${error.message}`);
  },
});
```

**Status-based Error Detection**:
```typescript
useEffect(() => {
  if (verdict?.status === 'failed' && isProcessing) {
    setIsProcessing(false);
    setOperationMessage('הפעולה נכשלה - ראה הערות למטה');
  }
}, [verdict?.status, isProcessing]);
```

## Configuration

### Backend Config
**File**: `backend/app/config.py`

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Legal Content System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "sqlite:///./legal_content.db"

    # Anthropic API
    ANTHROPIC_API_KEY: str
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20241022"

    # CORS
    ALLOWED_ORIGINS: list = ["http://localhost:3003"]

    # File Storage
    STORAGE_DIR: str = "storage"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB

    class Config:
        env_file = ".env"

settings = Settings()
```

### Frontend Config
**File**: `frontend/.env`

```env
VITE_API_URL=http://localhost:8000
```

## Testing

### Backend Testing (Future)
```python
# tests/test_anonymizer.py
import pytest
from app.services.anonymizer import Anonymizer

def test_anonymize_names():
    anonymizer = Anonymizer()
    text = "יוסי כהן הגיש תביעה נגד דוד לוי"
    result = anonymizer.anonymize(text)

    assert "יוסי כהן" not in result["anonymized_text"]
    assert "דוד לוי" not in result["anonymized_text"]
    assert len(result["changes"]) >= 2
```

### Frontend Testing (Future)
```typescript
// src/__tests__/Dashboard.test.tsx
import { render, screen } from '@testing-library/react';
import Dashboard from '../pages/Dashboard';

test('renders dashboard statistics', () => {
  render(<Dashboard />);
  expect(screen.getByText(/סטטיסטיקות/i)).toBeInTheDocument();
});
```

## Performance Optimization

### Database Indexes
All frequently queried fields have indexes:
- `verdicts.status` - for filtering by status
- `verdicts.file_hash` - for duplicate detection
- `articles.slug` - for URL lookups
- `articles.verdict_id` - for foreign key joins

### React Query Caching
```typescript
queryClient.setDefaultOptions({
  queries: {
    staleTime: 5000,  // 5 seconds
    cacheTime: 10 * 60 * 1000,  // 10 minutes
  },
});
```

### Frontend Code Splitting
Vite automatically code-splits routes:
```typescript
const Dashboard = lazy(() => import('./pages/Dashboard'));
const VerdictDetail = lazy(() => import('./pages/VerdictDetail'));
```

### API Response Optimization
- Pagination for lists (default 50 items)
- Partial field selection (future)
- Compressed responses (gzip)

## Security Considerations

### Anonymization
- Multi-pass identification of PII
- Risk assessment (low/medium/high)
- Manual review flag for high-risk content

### API Security
- CORS properly configured
- Input validation with Pydantic
- SQL injection prevention (SQLAlchemy ORM)
- File upload validation (size, type)

### Data Storage
- Local storage (no cloud exposure)
- Encrypted WordPress passwords (future)
- Hashed user passwords

## Deployment

### Development
```bash
# Backend
cd legal-content-system/backend
python -m uvicorn app.main:app --reload --port 8000

# Frontend
cd legal-content-system/frontend
npm run dev -- --port 3003
```

### Production Build
```bash
# Frontend build
cd legal-content-system/frontend
npm run build
# Outputs to dist/

# Backend with gunicorn
cd legal-content-system/backend
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Environment Variables
```bash
# Production backend .env
ANTHROPIC_API_KEY=sk-ant-...
DATABASE_URL=postgresql://user:pass@host/db
DEBUG=false
ALLOWED_ORIGINS=["https://yourdomain.com"]

# Production frontend .env
VITE_API_URL=https://api.yourdomain.com
```

## Monitoring and Logging

### Backend Logging
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
logger.info("Processing verdict %d", verdict_id)
```

### Error Tracking
Errors are logged to:
- Console (development)
- `review_notes` field (user-facing)
- Log files (production, future)

### Metrics
Current metrics available:
- Verdict statistics by status
- Article statistics by status
- Average quality scores
- Total storage used
- Processing success rate

## Future Enhancements

### Planned Features
1. **Batch Processing**: Upload multiple verdicts at once
2. **Scheduled Publishing**: Queue articles for future publication
3. **A/B Testing**: Test different article versions
4. **Analytics Integration**: Google Analytics, Search Console
5. **User Management**: Multi-user support with roles
6. **API Rate Limiting**: Prevent abuse
7. **Webhook Support**: Notify external systems
8. **Export**: CSV/Excel export of data

### Technical Debt
1. Add comprehensive unit tests
2. Add integration tests
3. Implement proper logging system
4. Add API documentation (OpenAPI/Swagger)
5. Implement caching layer (Redis)
6. Add database migrations (Alembic)
7. Encrypt sensitive fields
8. Add monitoring dashboard

---

**Last Updated**: January 2026
**Version**: 1.0
**Maintainer**: Legal Content System Team
