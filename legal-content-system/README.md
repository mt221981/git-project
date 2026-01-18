# Legal Content System - מערכת תוכן משפטי

<div dir="rtl">

מערכת מקצה-לקצה לעיבוד פסקי דין, ניתוח בינה מלאכותית, ויצירת תוכן SEO אופטימלי עם פרסום אוטומטי ל-WordPress.

</div>

A complete end-to-end system for processing legal verdicts, AI-powered analysis, and SEO-optimized content generation with automated WordPress publishing.

## Project Structure

```
legal-content-system/
├── backend/                # Python FastAPI backend
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py        # FastAPI application entry point
│   │   ├── config.py      # Configuration with pydantic-settings
│   │   ├── database.py    # SQLAlchemy setup
│   │   ├── models/        # Database models
│   │   │   ├── verdict.py
│   │   │   ├── article.py
│   │   │   └── wordpress_site.py
│   │   ├── schemas/       # Pydantic schemas
│   │   │   ├── verdict.py
│   │   │   ├── article.py
│   │   │   └── common.py
│   │   ├── routers/       # API route handlers
│   │   │   ├── verdicts.py
│   │   │   └── articles.py
│   │   ├── services/      # Business logic
│   │   │   ├── file_storage.py
│   │   │   ├── verdict_service.py
│   │   │   ├── anonymization_service.py
│   │   │   ├── analysis_service.py
│   │   │   ├── article_service.py
│   │   │   └── prompts.py
│   │   └── utils/         # Utility functions
│   │       ├── file_extraction.py
│   │       ├── text_cleaning.py
│   │       ├── hash_utils.py
│   │       └── anthropic_client.py
│   ├── requirements.txt   # Python dependencies
│   ├── .env.example       # Environment variables template
│   ├── PHASE3_TESTING.md  # Phase 3 testing guide
│   └── PHASE4_TESTING.md  # Phase 4 testing guide
├── frontend/              # Frontend (to be created)
└── README.md
```

## Tech Stack

- **Backend**: Python 3.11+ with FastAPI
- **Database**: SQLite (development) / PostgreSQL (production)
- **ORM**: SQLAlchemy 2.0
- **AI**: Anthropic Claude API (Claude 3.5 Sonnet)
- **Document Processing**: PyPDF2, python-docx
- **SEO**: python-slugify, markdown

## Quick Start (Docker - Recommended)

The easiest way to run the entire system is using Docker:

1. **Clone the repository**:
```bash
git clone https://github.com/YOUR_USERNAME/legal-content-system.git
cd legal-content-system
```

2. **Configure environment**:
```bash
cp .env.production.example .env
# Edit .env and set your values (ANTHROPIC_API_KEY, passwords, etc.)
```

3. **Deploy**:
```bash
# Linux/Mac
chmod +x deploy.sh
./deploy.sh production

# Windows
deploy.bat production
```

4. **Access the application**:
- Frontend Dashboard: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

See `PHASE7.md` for detailed deployment documentation.

## Setup Instructions

### Backend Setup (Development)

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file from the example:
```bash
cp .env.example .env
```

5. Edit `.env` and add your configuration:
   - Set `SECRET_KEY` to a secure random string
   - Add your `ANTHROPIC_API_KEY` (required)
   - Configure `DATABASE_URL` if not using SQLite

6. Run the application:
```bash
python app/main.py
```

Or use uvicorn directly:
```bash
uvicorn app.main:app --reload
```

7. Access the API:
   - API: http://localhost:8000
   - Interactive docs: http://localhost:8000/docs
   - Alternative docs: http://localhost:8000/redoc

## Database Models

### Verdict Model
Stores court verdict documents with extracted information:
- File identification (hash, case number)
- Court information (name, level, judge, date)
- Case categorization (type, legal area)
- Text content (original, cleaned, anonymized)
- Anonymization report and privacy risk assessment
- Structured analysis (facts, legal questions, principles)
- Financial information (compensation)
- Legal references (laws, precedents)
- Processing status and review flags

### Article Model
Stores generated SEO articles:
- SEO metadata (title, slug, meta tags, keywords)
- HTML content with proper structure
- Word count and reading time
- FAQ items and common mistakes
- Schema.org JSON-LD markup
- Internal and external link suggestions
- Quality scores (Content, SEO, Readability, E-E-A-T)
- WordPress publishing information

### WordPressSite Model
Stores WordPress site configurations:
- Site credentials (encrypted)
- SEO plugin configuration
- Category mappings
- Default settings

## Development Status

✅ **Phase 1 Complete**: Project structure and database models
✅ **Phase 2 Complete**: File upload and text extraction
✅ **Phase 3 Complete**: Anonymization service with Claude API
✅ **Phase 4 Complete**: AI analysis and SEO article generation
✅ **Phase 5 Complete**: WordPress integration and publishing
✅ **Phase 6 Complete**: Frontend dashboard (React + TypeScript)
✅ **Phase 7 Complete**: Deployment & production setup

## API Endpoints

### Verdicts
- ✅ `POST /api/v1/verdicts/upload` - Upload verdict file (PDF, TXT, DOC, DOCX)
- ✅ `GET /api/v1/verdicts` - List verdicts with pagination and filtering
- ✅ `GET /api/v1/verdicts/{id}` - Get verdict details
- ✅ `PATCH /api/v1/verdicts/{id}` - Update verdict metadata
- ✅ `PATCH /api/v1/verdicts/{id}/status` - Update verdict status
- ✅ `DELETE /api/v1/verdicts/{id}` - Delete verdict
- ✅ `POST /api/v1/verdicts/{id}/anonymize` - Anonymize verdict using Claude API
- ✅ `POST /api/v1/verdicts/{id}/re-anonymize` - Re-anonymize verdict
- ✅ `GET /api/v1/verdicts/statistics/overview` - Get system statistics
- ✅ `GET /api/v1/verdicts/statistics/anonymization` - Get anonymization statistics

### Analysis & Articles
- ✅ `POST /api/v1/articles/verdicts/{id}/analyze` - Analyze verdict structure
- ✅ `POST /api/v1/articles/verdicts/{id}/re-analyze` - Re-analyze verdict
- ✅ `GET /api/v1/articles/verdicts/statistics/analysis` - Analysis statistics
- ✅ `POST /api/v1/articles/generate/{verdict_id}` - Generate SEO article from verdict
- ✅ `GET /api/v1/articles` - List articles with pagination
- ✅ `GET /api/v1/articles/{id}` - Get article details
- ✅ `GET /api/v1/articles/by-verdict/{verdict_id}` - Get article by verdict
- ✅ `GET /api/v1/articles/statistics/overview` - Article statistics

### WordPress
- ✅ `GET /api/v1/wordpress/sites` - List configured sites
- ✅ `POST /api/v1/wordpress/sites` - Add new site
- ✅ `PUT /api/v1/wordpress/sites/{id}` - Update site configuration
- ✅ `DELETE /api/v1/wordpress/sites/{id}` - Delete site
- ✅ `POST /api/v1/wordpress/sites/{id}/test` - Test site connection
- ✅ `POST /api/v1/wordpress/articles/{id}/publish` - Publish article to WordPress
- ✅ `POST /api/v1/wordpress/articles/{id}/publish-retry` - Retry failed publish
- ✅ `POST /api/v1/wordpress/batch-publish` - Batch publish multiple articles
- ✅ `POST /api/v1/wordpress/republish-failed` - Republish all failed articles
- ✅ `POST /api/v1/wordpress/articles/{id}/validate` - Validate article before publish
- ✅ `GET /api/v1/wordpress/statistics` - Get publishing statistics
- ✅ `POST /api/v1/wordpress/queue/schedule` - Schedule publishing queue

## Features

### Phase 1: Foundation
- SQLAlchemy models for Verdicts, Articles, and WordPress sites
- Pydantic settings with environment variable support
- FastAPI application structure

### Phase 2: File Processing
- Multi-format file upload (PDF, TXT, DOC, DOCX)
- Text extraction with encoding detection
- Text cleaning and normalization for Hebrew legal documents
- Automatic metadata extraction (case numbers, court info, judges)
- SHA-256 hash-based duplicate detection
- Organized file storage system

### Phase 3: Anonymization
- Claude API integration for intelligent anonymization
- Personal information identification (names, IDs, addresses, phones, emails)
- Context-aware replacement with consistent placeholders
- Detailed anonymization reporting
- Privacy risk assessment (LOW/MEDIUM/HIGH)
- Automatic flagging for manual review
- Hebrew language support with legal domain expertise

### Phase 4: Analysis & Article Generation
- **Verdict Analysis**: Extracts key facts, legal questions, principles, compensation details, laws, precedents, and practical insights
- **SEO Article Generation**: Creates 1500-2500 word articles with optimal structure
- **Quality Scoring**: Content, SEO, Readability, and E-E-A-T scores (0-100)
- **Schema Markup**: Automatic JSON-LD generation (Article, FAQPage)
- **FAQ Generation**: 5-8 relevant questions with detailed answers
- **Keyword Optimization**: Focus, secondary, and long-tail keywords
- **Link Suggestions**: Internal and external link recommendations
- **Hebrew Content**: Native Hebrew writing optimized for Israeli audience

### Phase 5: WordPress Integration
- **Multi-Site Support**: Manage multiple WordPress sites from one dashboard
- **Automatic Publishing**: One-click publish with retry mechanism
- **Batch Operations**: Publish multiple articles simultaneously
- **SEO Plugin Integration**: Yoast SEO and Rank Math support
- **Category Mapping**: Automatic category assignment based on legal area
- **Featured Images**: Automatic image handling and upload
- **Status Tracking**: Monitor publishing status and handle failures
- **Validation**: Pre-publish article validation
- **Statistics**: Publishing success rates and performance metrics

### Phase 6: Frontend Dashboard
- **React + TypeScript**: Modern, type-safe frontend application
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Verdict Management**: Upload, view, and manage verdicts
- **Article Management**: Review, edit, and publish articles
- **WordPress Sites**: Configure and manage WordPress sites
- **Batch Publishing**: Select and publish multiple articles at once
- **Publishing Dashboard**: Monitor publishing queue and statistics
- **Statistics & Analytics**: System-wide metrics and insights
- **Real-time Updates**: Live status updates using React Query

### Phase 7: Deployment & Production
- **Docker Configuration**: Multi-container setup with Docker Compose
- **Production Ready**: Gunicorn, Nginx, PostgreSQL, health checks
- **SSL/TLS Support**: HTTPS configuration with Let's Encrypt
- **Rate Limiting**: API and traffic rate limiting with Nginx
- **Security Headers**: HSTS, CSP, X-Frame-Options, etc.
- **Automated Deployment**: Scripts for easy deployment and updates
- **Backup & Restore**: Automated backup scripts with retention
- **Monitoring**: Health checks and logging configuration
- **Scalability**: Horizontal and vertical scaling support

## Complete Workflow Example

```bash
# 1. Upload verdict
curl -X POST "http://localhost:8000/api/v1/verdicts/upload" \
  -F "file=@verdict.pdf"
# Response: {"verdict_id": 1, "status": "extracted"}

# 2. Anonymize
curl -X POST "http://localhost:8000/api/v1/verdicts/1/anonymize"
# Response: {"status": "anonymized", "privacy_risk_level": "medium"}

# 3. Analyze
curl -X POST "http://localhost:8000/api/v1/articles/verdicts/1/analyze"
# Response: {"status": "analyzed", "key_facts": [...], "legal_questions": [...]}

# 4. Generate article
curl -X POST "http://localhost:8000/api/v1/articles/generate/1"
# Response: {"article_id": 1, "overall_score": 85, "publish_status": "draft"}

# 5. Get the article
curl "http://localhost:8000/api/v1/articles/1"
# Response: Complete article with content, SEO, schema markup, etc.
```

## Documentation

Each phase has comprehensive documentation:

- **PHASE3_TESTING.md**: Anonymization service testing guide
- **PHASE4_TESTING.md**: Analysis and article generation testing guide
- **PHASE5.md**: WordPress integration documentation
- **PHASE6.md**: Frontend dashboard documentation
- **PHASE7.md**: Deployment and production setup guide
- **GITHUB_SETUP.md**: Git and GitHub setup instructions (Hebrew)

## Python SDK Example

```python
import requests

class LegalContentClient:
    def __init__(self, base_url="http://localhost:8000/api/v1"):
        self.base_url = base_url

    def process_verdict(self, file_path):
        """Complete workflow: upload → anonymize → analyze → generate article"""

        # Upload
        with open(file_path, "rb") as f:
            r = requests.post(f"{self.base_url}/verdicts/upload", files={"file": f})
        verdict_id = r.json()["verdict_id"]

        # Anonymize
        requests.post(f"{self.base_url}/verdicts/{verdict_id}/anonymize")

        # Analyze
        requests.post(f"{self.base_url}/articles/verdicts/{verdict_id}/analyze")

        # Generate article
        r = requests.post(f"{self.base_url}/articles/generate/{verdict_id}")
        article_id = r.json()["article_id"]

        # Get full article
        r = requests.get(f"{self.base_url}/articles/{article_id}")
        return r.json()


# Usage
client = LegalContentClient()
article = client.process_verdict("verdict.pdf")

print(f"Title: {article['title']}")
print(f"Word count: {article['word_count']}")
print(f"SEO Score: {article['seo_score']}/100")
print(f"Overall Score: {article['overall_score']}/100")
```

## Interactive Documentation

Visit **http://localhost:8000/docs** for Swagger UI with:
- All endpoints documented
- Interactive testing interface
- Request/response examples
- Schema definitions
- Try out all features directly from your browser

## License

Proprietary
