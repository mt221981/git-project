# Phase 5: WordPress Publishing Integration

**Status**: ✅ Complete
**Last Updated**: 2026-01-14

## Overview

Phase 5 implements advanced WordPress publishing integration with enterprise-grade features including retry logic, batch operations, validation, and comprehensive monitoring.

### Key Features

- 📝 **Article Validation**: Pre-publish validation to ensure content quality
- 🔄 **Retry Logic**: Exponential backoff for failed publishes
- 📦 **Batch Operations**: Publish multiple articles efficiently
- 📊 **Statistics & Monitoring**: Track publishing status and performance
- 🔁 **Failed Article Recovery**: Automatic retry for failed publishes
- 📅 **Queue Management**: Schedule publishing with configurable rates
- 🔄 **Status Sync**: Keep local database in sync with WordPress

## Architecture

### Component Overview

```
┌──────────────────────────────────────────────────────────┐
│                   WordPress Manager                       │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Validation | Retry | Batch | Stats | Queue        │  │
│  └────────────────────────────────────────────────────┘  │
└─────────────────────┬────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
        ▼             ▼             ▼
┌──────────────┐ ┌──────────┐ ┌─────────────┐
│ WordPress    │ │ Database │ │   Article   │
│   Service    │ │  Session │ │   Models    │
└──────────────┘ └──────────┘ └─────────────┘
        │
        ▼
┌──────────────┐
│ WordPress    │
│   Client     │ ──────► WordPress REST API
└──────────────┘
```

### Service Hierarchy

1. **WordPressManager** (High-Level)
   - Orchestrates complex publishing workflows
   - Implements retry logic and batch operations
   - Provides statistics and monitoring
   - Manages publishing queues

2. **WordPressService** (Mid-Level)
   - Manages WordPress sites
   - Handles basic publish/unpublish operations
   - Manages credential encryption
   - Maps categories and handles SEO plugins

3. **WordPressClient** (Low-Level)
   - Direct REST API communication
   - HTTP request handling
   - Authentication management
   - Error handling

## Core Components

### 1. WordPressManager

**File**: `app/services/wordpress_manager.py`

The central service for advanced WordPress publishing operations.

#### Key Methods

##### validate_article_for_publishing()

Validates an article is ready for publishing.

```python
def validate_article_for_publishing(self, article: Article) -> List[str]:
    """
    Validate article is ready for publishing.

    Checks:
    - Title presence
    - Content presence
    - Word count (minimum 500)
    - Quality score (minimum 50)
    - Focus keyword presence
    - Meta title and description

    Returns:
        List of validation errors (empty if valid)
    """
```

**Validation Rules**:
- ✓ Title must be present
- ✓ Content HTML must be present
- ✓ Word count ≥ 500 words
- ✓ Overall score ≥ 50
- ✓ Focus keyword must be set
- ✓ Meta title must be set
- ✓ Meta description must be set

##### publish_article_with_retry()

Publishes an article with automatic retry logic.

```python
def publish_article_with_retry(
    self,
    article_id: int,
    site_id: int,
    status: str = "draft",
    max_retries: int = 3,
    retry_delay: float = 2.0
) -> Article:
    """
    Publish article with retry logic.

    Features:
    - Validates article before publishing
    - Retries on transient failures
    - Exponential backoff between retries
    - Tracks attempts in metadata
    - Updates article status on failure

    Raises:
        PublishingError: If publishing fails after retries
        ValueError: If article validation fails
    """
```

**Retry Behavior**:
- Default: 3 retry attempts
- Exponential backoff: delay × (attempt + 1)
- Non-retryable errors:
  - Authentication failures
  - "Not found" errors
- Records attempts in article metadata
- Updates article status to FAILED after max retries

**Example**:
```python
from app.services import WordPressManager

manager = WordPressManager(db)

try:
    article = manager.publish_article_with_retry(
        article_id=123,
        site_id=1,
        status="publish",  # or "draft"
        max_retries=3,
        retry_delay=2.0
    )
    print(f"Published: {article.wordpress_url}")
except PublishingError as e:
    print(f"Failed: {e}")
```

##### publish_articles_batch()

Publishes multiple articles in batch.

```python
def publish_articles_batch(
    self,
    article_ids: List[int],
    site_id: int,
    status: str = "draft",
    stop_on_error: bool = False
) -> Dict[str, Any]:
    """
    Publish multiple articles in batch.

    Args:
        article_ids: List of article IDs
        site_id: WordPress site ID
        status: Post status for all articles
        stop_on_error: If True, stop on first error

    Returns:
        {
            "successful": [article_ids],
            "failed": [{"article_id": int, "error": str}],
            "total": int,
            "success_count": int,
            "error_count": int
        }
    """
```

**Example**:
```python
results = manager.publish_articles_batch(
    article_ids=[101, 102, 103, 104],
    site_id=1,
    status="draft",
    stop_on_error=False
)

print(f"Successful: {results['success_count']}/{results['total']}")
print(f"Failed: {results['error_count']}")

for failed in results['failed']:
    print(f"  Article {failed['article_id']}: {failed['error']}")
```

##### republish_failed_articles()

Retries publishing articles that previously failed.

```python
def republish_failed_articles(
    self,
    site_id: int,
    max_articles: int = 10
) -> Dict[str, Any]:
    """
    Retry publishing articles that previously failed.

    Finds articles with publish_status=FAILED and attempts
    to republish them.

    Returns:
        Batch publishing results
    """
```

**Example**:
```python
# Retry up to 10 failed articles
results = manager.republish_failed_articles(
    site_id=1,
    max_articles=10
)

print(f"Retried {results['total']} failed articles")
print(f"Now successful: {results['success_count']}")
```

##### get_publishing_statistics()

Gets publishing statistics overall or per-site.

```python
def get_publishing_statistics(
    self,
    site_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Get publishing statistics.

    Returns:
        {
            "total_articles": int,
            "published": int,
            "draft": int,
            "ready": int,
            "failed": int,
            "by_site": {
                site_id: {
                    "site_name": str,
                    "site_url": str,
                    "total": int,
                    "published": int,
                    "draft": int
                }
            }
        }
    """
```

**Example**:
```python
# Overall statistics
stats = manager.get_publishing_statistics()
print(f"Total: {stats['total_articles']}")
print(f"Published: {stats['published']}")
print(f"Failed: {stats['failed']}")

# Per-site statistics
for site_id, site_stats in stats['by_site'].items():
    print(f"{site_stats['site_name']}: {site_stats['published']} published")

# Site-specific statistics
site_stats = manager.get_publishing_statistics(site_id=1)
```

##### schedule_publishing_queue()

Creates a publishing queue for scheduled publishing.

```python
def schedule_publishing_queue(
    self,
    site_id: int,
    articles_per_day: int = 5,
    min_score: int = 70
) -> Dict[str, Any]:
    """
    Create a publishing queue for scheduled publishing.

    Returns:
        {
            "site_id": int,
            "total_queued": int,
            "articles_per_day": int,
            "estimated_days": int,
            "articles": [
                {
                    "id": int,
                    "title": str,
                    "word_count": int,
                    "overall_score": int,
                    "focus_keyword": str
                }
            ]
        }
    """
```

**Example**:
```python
# Create queue for 5 articles per day
queue = manager.schedule_publishing_queue(
    site_id=1,
    articles_per_day=5,
    min_score=75
)

print(f"Queued {queue['total_queued']} articles")
print(f"Will take approximately {queue['estimated_days']} days")

# Process articles from queue
for article in queue['articles'][:5]:  # First day
    manager.publish_article_with_retry(
        article_id=article['id'],
        site_id=queue['site_id']
    )
```

##### get_unpublished_articles()

Gets articles ready for publishing.

```python
def get_unpublished_articles(
    self,
    min_score: int = 70,
    limit: int = 50
) -> List[Article]:
    """
    Get articles ready for publishing.

    Filters:
    - publish_status = READY
    - overall_score >= min_score
    - wordpress_post_id is NULL

    Sorted by:
    - overall_score DESC
    - created_at DESC
    """
```

##### sync_article_status()

Syncs article status with WordPress.

```python
def sync_article_status(self, article_id: int) -> Article:
    """
    Sync article status with WordPress.

    Checks WordPress post status and updates local database:
    - "publish" → PUBLISHED
    - "draft" → DRAFT
    - Post deleted → Clear wordpress_post_id

    Raises:
        ValueError: If article not found or not published
    """
```

### 2. Publishing Workflow

#### Standard Publishing Flow

```
┌─────────────────┐
│ Create Article  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Set Status to  │
│      READY      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Validate     │ ◄─── validate_article_for_publishing()
└────────┬────────┘
         │
         ▼
    ┌────────┐
    │ Valid? │
    └───┬────┘
        │ Yes
        ▼
┌─────────────────┐
│ Publish with    │ ◄─── publish_article_with_retry()
│ Retry Logic     │
└────────┬────────┘
         │
    ┌────┴────┐
    │Success? │
    └───┬─────┘
        │ Yes
        ▼
┌─────────────────┐
│  Status: DRAFT  │
│  or PUBLISHED   │
└─────────────────┘
```

#### Batch Publishing Flow

```
┌─────────────────┐
│ Select Multiple │
│    Articles     │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│ publish_articles_batch()│
└────────┬────────────────┘
         │
         ▼
    ┌─────────────────┐
    │ For each article│
    │   in batch:     │
    └────────┬────────┘
             │
             ▼
    ┌────────────────┐
    │   Validate     │
    └────────┬───────┘
             │
             ▼
    ┌────────────────┐
    │ Publish with   │
    │     Retry      │
    └────────┬───────┘
             │
             ▼
    ┌────────────────┐
    │ Track Success  │
    │   or Failure   │
    └────────┬───────┘
             │
             ▼
    ┌────────────────┐
    │ stop_on_error? │──Yes──► Stop
    └────────┬───────┘
             │ No
             ▼
         Continue
             │
             ▼
    ┌────────────────┐
    │ Return Results │
    └────────────────┘
```

## Configuration

### WordPress Site Setup

**Database Schema** (`app/models/wordpress_site.py`):

```python
class WordPressSite(Base):
    id: int
    site_name: str
    site_url: str
    username: str
    encrypted_password: str  # Fernet encrypted
    is_active: bool
    seo_plugin: str  # "yoast" or "rankmath"
```

**Create Site**:

```python
from app.services import WordPressService

wp_service = WordPressService(db)

site = wp_service.create_site(
    site_name="My Legal Site",
    site_url="https://mysite.com",
    username="admin",
    password="app_password_here",
    seo_plugin="yoast"
)
```

### WordPress Application Passwords

WordPress REST API requires Application Passwords for authentication.

**Creating Application Password in WordPress**:

1. Log in to WordPress admin
2. Go to **Users** → **Profile**
3. Scroll to **Application Passwords** section
4. Enter application name (e.g., "Legal Content System")
5. Click **Add New Application Password**
6. **Copy the generated password** (shown only once!)
7. Use this password in the system

**Format**: `xxxx xxxx xxxx xxxx xxxx xxxx`

### Environment Variables

```env
# WordPress Configuration
WORDPRESS_DEFAULT_SITE_ID=1

# API Configuration (if needed)
ANTHROPIC_API_KEY=your-key-here
```

## API Endpoints

### Publish Article with Retry

```http
POST /api/wordpress/articles/{article_id}/publish
Content-Type: application/json

{
  "site_id": 1,
  "status": "draft",
  "max_retries": 3,
  "retry_delay": 2.0
}
```

**Response**:
```json
{
  "id": 123,
  "title": "Article Title",
  "wordpress_post_id": 456,
  "wordpress_url": "https://site.com/article-title",
  "publish_status": "draft",
  "published_at": "2026-01-14T10:30:00Z"
}
```

### Batch Publish

```http
POST /api/wordpress/articles/batch-publish
Content-Type: application/json

{
  "article_ids": [101, 102, 103],
  "site_id": 1,
  "status": "draft",
  "stop_on_error": false
}
```

**Response**:
```json
{
  "successful": [101, 103],
  "failed": [
    {
      "article_id": 102,
      "error": "Connection timeout"
    }
  ],
  "total": 3,
  "success_count": 2,
  "error_count": 1
}
```

### Get Publishing Statistics

```http
GET /api/wordpress/statistics
GET /api/wordpress/statistics?site_id=1
```

**Response**:
```json
{
  "total_articles": 150,
  "published": 100,
  "draft": 20,
  "ready": 25,
  "failed": 5,
  "by_site": {
    "1": {
      "site_name": "Main Site",
      "site_url": "https://main-site.com",
      "total": 120,
      "published": 100,
      "draft": 20
    }
  }
}
```

### Republish Failed Articles

```http
POST /api/wordpress/articles/republish-failed
Content-Type: application/json

{
  "site_id": 1,
  "max_articles": 10
}
```

### Schedule Publishing Queue

```http
POST /api/wordpress/queue/schedule
Content-Type: application/json

{
  "site_id": 1,
  "articles_per_day": 5,
  "min_score": 75
}
```

**Response**:
```json
{
  "site_id": 1,
  "total_queued": 25,
  "articles_per_day": 5,
  "estimated_days": 5,
  "articles": [
    {
      "id": 101,
      "title": "Article Title",
      "word_count": 1500,
      "overall_score": 85,
      "focus_keyword": "פיצויי פיטורים"
    }
  ]
}
```

## Error Handling

### Exception Hierarchy

```
Exception
└── PublishingError
    └── WordPressClientError
```

### Common Errors

#### Validation Errors

```python
try:
    manager.publish_article_with_retry(article_id=123, site_id=1)
except ValueError as e:
    # Article validation failed
    print(f"Validation error: {e}")
    # Example: "Article validation failed: Article too short (300 words, minimum 500)"
```

#### Publishing Errors

```python
try:
    manager.publish_article_with_retry(article_id=123, site_id=1)
except PublishingError as e:
    # Publishing failed after retries
    print(f"Publishing error: {e}")
    # Example: "Publishing failed after 3 attempts: Connection timeout"
```

#### Client Errors

```python
from app.services import WordPressClientError

try:
    client.create_post(...)
except WordPressClientError as e:
    # WordPress API error
    print(f"API error: {e}")
    # Examples:
    # - "Authentication failed"
    # - "Post not found"
    # - "Connection timeout"
```

### Retry Strategy

**Retryable Errors**:
- Connection timeout
- Temporary network failures
- 5xx server errors
- Rate limiting (429)

**Non-Retryable Errors**:
- Authentication failures (401)
- Not found errors (404)
- Bad request errors (400)
- Forbidden errors (403)

**Backoff Calculation**:
```python
delay = retry_delay * (attempt + 1)

# Example with retry_delay=2.0:
# Attempt 1: 2.0 seconds
# Attempt 2: 4.0 seconds
# Attempt 3: 6.0 seconds
```

## Best Practices

### 1. Article Validation

Always validate articles before publishing:

```python
# Check if article is valid
errors = manager.validate_article_for_publishing(article)

if errors:
    print("Article needs improvements:")
    for error in errors:
        print(f"  - {error}")
    # Fix issues before publishing
else:
    # Proceed with publishing
    manager.publish_article_with_retry(article.id, site_id)
```

### 2. Batch Publishing

Use batch operations for multiple articles:

```python
# Get articles ready for publishing
articles = manager.get_unpublished_articles(min_score=75, limit=10)
article_ids = [a.id for a in articles]

# Publish in batch
results = manager.publish_articles_batch(
    article_ids=article_ids,
    site_id=1,
    status="draft",
    stop_on_error=False  # Continue even if some fail
)

# Handle results
for article_id in results['successful']:
    print(f"✓ Article {article_id} published")

for failed in results['failed']:
    print(f"✗ Article {failed['article_id']}: {failed['error']}")
```

### 3. Queue Management

Use queues for scheduled publishing:

```python
# Create weekly queue (5 articles per day)
queue = manager.schedule_publishing_queue(
    site_id=1,
    articles_per_day=5,
    min_score=75
)

# Publish first batch
for article in queue['articles'][:5]:
    manager.publish_article_with_retry(
        article_id=article['id'],
        site_id=queue['site_id'],
        status="publish"
    )
```

### 4. Failed Article Recovery

Regularly retry failed articles:

```python
# Daily: Retry failed articles
results = manager.republish_failed_articles(site_id=1, max_articles=10)

if results['success_count'] > 0:
    print(f"Recovered {results['success_count']} articles")

if results['error_count'] > 0:
    print(f"Still failing: {results['error_count']} articles")
    # May need manual intervention
```

### 5. Monitoring

Monitor publishing statistics:

```python
# Get statistics
stats = manager.get_publishing_statistics()

# Alert if too many failures
if stats['failed'] > 10:
    send_alert(f"High failure rate: {stats['failed']} failed articles")

# Alert if low publish rate
if stats['ready'] > 50:
    send_alert(f"Publishing backlog: {stats['ready']} articles waiting")
```

### 6. Status Sync

Periodically sync with WordPress:

```python
# Sync published articles
published_articles = db.query(Article).filter(
    Article.publish_status == PublishStatus.PUBLISHED,
    Article.wordpress_post_id.isnot(None)
).all()

for article in published_articles:
    try:
        manager.sync_article_status(article.id)
    except Exception as e:
        print(f"Sync failed for article {article.id}: {e}")
```

## Performance Considerations

### Batch Size

**Recommendations**:
- Small batch: 5-10 articles (fast feedback)
- Medium batch: 10-25 articles (balanced)
- Large batch: 25-50 articles (efficient)
- Avoid: >50 articles (may timeout)

### Retry Configuration

**Default Settings** (recommended):
```python
max_retries=3
retry_delay=2.0
```

**Aggressive** (for reliable connections):
```python
max_retries=2
retry_delay=1.0
```

**Conservative** (for unreliable connections):
```python
max_retries=5
retry_delay=3.0
```

### Rate Limiting

WordPress may rate limit requests. Recommended:
- **Articles per hour**: 60 (1 per minute)
- **Articles per day**: 500
- **Burst limit**: 10 articles at once

Implement delays between batches:
```python
import time

batch_size = 10
batches = [article_ids[i:i+batch_size] for i in range(0, len(article_ids), batch_size)]

for batch in batches:
    results = manager.publish_articles_batch(batch, site_id=1)
    print(f"Batch complete: {results['success_count']} successful")
    time.sleep(60)  # Wait 1 minute between batches
```

## Testing

### Run Phase 5 Tests

```bash
cd backend
python test_phase5.py
```

**Test Coverage**:
- ✓ Article validation
- ✓ Retry logic with exponential backoff
- ✓ Batch publishing (continue/stop on error)
- ✓ Publishing statistics (overall and per-site)
- ✓ Unpublished articles retrieval
- ✓ Publishing queue management
- ✓ Failed articles republish
- ✓ Complete workflow integration

### Manual Testing

```python
# Test validation
from app.services import WordPressManager
manager = WordPressManager(db)

article = db.query(Article).first()
errors = manager.validate_article_for_publishing(article)
print(f"Validation errors: {errors}")

# Test statistics
stats = manager.get_publishing_statistics()
print(f"Total articles: {stats['total_articles']}")
print(f"Failed: {stats['failed']}")

# Test queue
queue = manager.schedule_publishing_queue(site_id=1, articles_per_day=5)
print(f"Queued: {queue['total_queued']} articles")
```

## Troubleshooting

### Issue: Authentication Failed

**Symptoms**: `WordPressClientError: Authentication failed`

**Solutions**:
1. Verify Application Password is correct
2. Check username matches WordPress user
3. Ensure REST API is enabled in WordPress
4. Verify WordPress site URL is correct

```python
# Test connection
from app.services import WordPressClient

client = WordPressClient(
    site_url="https://mysite.com",
    username="admin",
    app_password="xxxx xxxx xxxx xxxx"
)

try:
    categories = client.get_categories()
    print(f"✓ Connected. Found {len(categories)} categories")
except Exception as e:
    print(f"✗ Connection failed: {e}")
```

### Issue: Publishing Fails After Max Retries

**Symptoms**: `PublishingError: Publishing failed after 3 attempts`

**Solutions**:
1. Check WordPress site is accessible
2. Verify network connectivity
3. Check WordPress error logs
4. Increase retry delay
5. Check WordPress site status:

```python
# Check site status
try:
    stats = manager.get_publishing_statistics(site_id=1)
    print(f"Site stats: {stats}")
except Exception as e:
    print(f"Site unavailable: {e}")
```

### Issue: Batch Publishing Slow

**Symptoms**: Batch operations take too long

**Solutions**:
1. Reduce batch size
2. Publish as "draft" first, then update to "publish"
3. Check network latency
4. Verify WordPress server performance

```python
# Profile batch performance
import time

start = time.time()
results = manager.publish_articles_batch([1,2,3,4,5], site_id=1)
duration = time.time() - start

print(f"Published {results['success_count']} articles in {duration:.2f}s")
print(f"Average: {duration / len([1,2,3,4,5]):.2f}s per article")
```

### Issue: High Failure Rate

**Symptoms**: Many articles failing validation or publishing

**Solutions**:
1. Check validation rules are appropriate
2. Review article quality scores
3. Verify WordPress site configuration
4. Check for systematic issues:

```python
# Analyze failures
stats = manager.get_publishing_statistics()
failure_rate = stats['failed'] / stats['total_articles'] * 100

print(f"Failure rate: {failure_rate:.1f}%")

if failure_rate > 10:
    # Get failed articles
    failed = db.query(Article).filter(
        Article.publish_status == PublishStatus.FAILED
    ).all()

    # Analyze errors
    errors = [a.metadata.get('last_publish_error') for a in failed if a.metadata]
    print("Common errors:", set(errors))
```

### Issue: Articles Not Syncing

**Symptoms**: Local status doesn't match WordPress

**Solutions**:
1. Run sync manually
2. Check WordPress post IDs are correct
3. Verify WordPress posts still exist

```python
# Sync all published articles
published = db.query(Article).filter(
    Article.publish_status == PublishStatus.PUBLISHED
).all()

for article in published:
    try:
        synced = manager.sync_article_status(article.id)
        if synced.publish_status != article.publish_status:
            print(f"Article {article.id} status changed: {synced.publish_status}")
    except Exception as e:
        print(f"Sync failed for {article.id}: {e}")
```

## Monitoring & Alerts

### Key Metrics to Monitor

1. **Publishing Success Rate**
   ```python
   stats = manager.get_publishing_statistics()
   success_rate = (stats['published'] / stats['total_articles']) * 100
   ```

2. **Failed Articles Count**
   ```python
   failed_count = stats['failed']
   if failed_count > threshold:
       alert("High failure rate!")
   ```

3. **Publishing Queue Size**
   ```python
   ready_articles = manager.get_unpublished_articles(limit=1000)
   queue_size = len(ready_articles)
   ```

4. **Average Quality Score**
   ```python
   from app.services import ArticleService
   article_service = ArticleService(db)
   stats = article_service.get_article_stats()
   avg_score = stats['average_scores']['overall']
   ```

### Automated Monitoring Script

```python
def monitor_publishing():
    """Monitor publishing health."""
    manager = WordPressManager(db)
    stats = manager.get_publishing_statistics()

    # Calculate metrics
    total = stats['total_articles']
    failed = stats['failed']
    ready = stats['ready']

    failure_rate = (failed / total * 100) if total > 0 else 0

    # Alerts
    alerts = []

    if failure_rate > 5:
        alerts.append(f"High failure rate: {failure_rate:.1f}%")

    if failed > 20:
        alerts.append(f"Too many failed articles: {failed}")

    if ready > 100:
        alerts.append(f"Large publishing backlog: {ready}")

    # Send alerts
    if alerts:
        for alert in alerts:
            send_alert(alert)

    return {
        "status": "ok" if not alerts else "warning",
        "alerts": alerts,
        "metrics": {
            "total": total,
            "failed": failed,
            "ready": ready,
            "failure_rate": failure_rate
        }
    }
```

## Security Considerations

### 1. Credential Storage

Passwords are encrypted using Fernet (symmetric encryption):

```python
from cryptography.fernet import Fernet
from app.config import settings

# Encryption key from settings
key = settings.ENCRYPTION_KEY.encode()
cipher = Fernet(key)

# Encrypt password
encrypted = cipher.encrypt(password.encode())

# Decrypt password
decrypted = cipher.decrypt(encrypted).decode()
```

**Important**: Keep `ENCRYPTION_KEY` secure and never commit to version control.

### 2. Application Passwords

Use WordPress Application Passwords, NOT user passwords:

- ✓ Can be revoked individually
- ✓ Limited to REST API access
- ✓ No 2FA conflicts
- ✗ Don't use main user password

### 3. HTTPS Only

Always use HTTPS for WordPress sites:

```python
site = wp_service.create_site(
    site_url="https://mysite.com",  # ✓ HTTPS
    # site_url="http://mysite.com",  # ✗ HTTP
    ...
)
```

### 4. Permission Levels

Recommended WordPress user roles:
- **Author**: Can create and publish posts (minimum)
- **Editor**: Can edit all posts (recommended)
- **Administrator**: Full control (use sparingly)

## Next Steps

### Phase 6 Preview: Frontend Integration

Upcoming features:
- React admin dashboard
- Real-time publishing status
- Batch operation UI
- Statistics visualization
- Queue management interface

### Integration with Existing Phases

Phase 5 completes the backend pipeline:

```
Phase 1-2: File Upload → Text Extraction → Anonymization
           ↓
Phase 3-4: Analysis → Article Generation
           ↓
Phase 5:   WordPress Publishing ← YOU ARE HERE
           ↓
Phase 6:   Frontend Dashboard (Coming Soon)
```

### Production Deployment

Checklist:
- [ ] Configure WordPress sites
- [ ] Set up Application Passwords
- [ ] Configure encryption key
- [ ] Set up monitoring
- [ ] Configure backup strategy
- [ ] Test failover scenarios
- [ ] Set up automated retry jobs
- [ ] Configure rate limiting

## Resources

### WordPress REST API Documentation

- [REST API Handbook](https://developer.wordpress.org/rest-api/)
- [Application Passwords](https://make.wordpress.org/core/2020/11/05/application-passwords-integration-guide/)
- [Posts Endpoint](https://developer.wordpress.org/rest-api/reference/posts/)

### Related Files

- `app/services/wordpress_manager.py` - Main service
- `app/services/wordpress_service.py` - Site management
- `app/services/wordpress_client.py` - REST API client
- `app/models/wordpress_site.py` - Site model
- `app/models/article.py` - Article model
- `test_phase5.py` - Integration tests

### SEO Plugin Documentation

- [Yoast SEO](https://developer.yoast.com/customization/apis/rest-api/)
- [Rank Math](https://rankmath.com/kb/wordpress-rest-api/)

---

**Phase 5 Status**: ✅ Complete and tested

For questions or issues, refer to the troubleshooting section or check the test suite.
