# Phase 5: WordPress Publishing - Testing Guide

## Overview

Phase 5 implements WordPress publishing functionality. The system connects to WordPress sites via the REST API and can publish articles with full SEO optimization.

## What Was Implemented

### 1. WordPress API Client (`app/services/wordpress_client.py`)
Full-featured REST API client:
- Authentication with Application Passwords
- Post creation, update, and deletion
- Category and tag management
- SEO plugin integration (Yoast, Rank Math)
- Connection testing

### 2. WordPress Service (`app/services/wordpress_service.py`)
Business logic layer:
- Site configuration management
- Secure credential storage (encrypted)
- Publishing workflow
- Category mapping
- Default settings

### 3. Encryption Utilities (`app/utils/encryption.py`)
Secure credential storage:
- Fernet symmetric encryption
- Uses SECRET_KEY for key derivation
- Encrypt/decrypt passwords before storage

### 4. API Endpoints

#### Site Management
- `POST /api/v1/wordpress/sites` - Add WordPress site
- `GET /api/v1/wordpress/sites` - List sites
- `GET /api/v1/wordpress/sites/{id}` - Get site details
- `PATCH /api/v1/wordpress/sites/{id}` - Update site
- `DELETE /api/v1/wordpress/sites/{id}` - Delete site
- `POST /api/v1/wordpress/sites/{id}/test` - Test connection
- `GET /api/v1/wordpress/sites/{id}/categories` - Get categories
- `GET /api/v1/wordpress/sites/{id}/tags` - Get tags

#### Publishing
- `POST /api/v1/wordpress/publish/{article_id}` - Publish article
- `POST /api/v1/wordpress/unpublish/{article_id}` - Unpublish article

## Prerequisites

### WordPress Site Setup

1. **WordPress 5.6+** with REST API enabled (enabled by default)

2. **Create Application Password**:
   ```
   WordPress Admin → Users → Your Profile → Application Passwords

   - Name: "Legal Content System"
   - Click "Add New Application Password"
   - Save the generated password (you won't see it again!)
   ```

3. **Optional - Install SEO Plugin**:
   - Yoast SEO or Rank Math
   - Ensures better SEO metadata handling

4. **Verify REST API Access**:
   ```bash
   curl https://your-site.com/wp-json/
   # Should return JSON with site info
   ```

## Complete Workflow

### Step 1: Add WordPress Site

```bash
curl -X POST "http://localhost:8000/api/v1/wordpress/sites" \
  -H "Content-Type: application/json" \
  -d '{
    "site_name": "My Legal Blog",
    "site_url": "https://your-wordpress-site.com",
    "api_username": "your-username",
    "api_password": "xxxx xxxx xxxx xxxx xxxx xxxx",
    "seo_plugin": "yoast",
    "default_category_id": 5,
    "default_author_id": 1
  }'
```

Response:
```json
{
  "id": 1,
  "site_name": "My Legal Blog",
  "site_url": "https://your-wordpress-site.com",
  "api_username": "your-username",
  "seo_plugin": "yoast",
  "default_category_id": 5,
  "default_author_id": 1,
  "is_active": true,
  "created_at": "2026-01-13T..."
}
```

**Note**: Password is encrypted before storage. It's never returned in responses.

### Step 2: Test Connection

```bash
curl -X POST "http://localhost:8000/api/v1/wordpress/sites/1/test"
```

Response:
```json
{
  "success": true,
  "message": "Connection successful",
  "site_info": {
    "name": "My Legal Blog",
    "description": "...",
    "url": "https://your-wordpress-site.com",
    "namespaces": ["wp/v2", "..."]
  }
}
```

### Step 3: Get Categories

```bash
curl "http://localhost:8000/api/v1/wordpress/sites/1/categories"
```

Response:
```json
[
  {
    "id": 1,
    "name": "Uncategorized",
    "slug": "uncategorized",
    "description": "",
    "parent": null
  },
  {
    "id": 5,
    "name": "נזיקין",
    "slug": "torts",
    "description": "Torts and damages",
    "parent": null
  }
]
```

### Step 4: Publish an Article

First, ensure you have an article ready (from Phase 4):

```bash
# Verify article exists and is ready
curl "http://localhost:8000/api/v1/articles/1"
```

Then publish:

```bash
curl -X POST "http://localhost:8000/api/v1/wordpress/publish/1" \
  -H "Content-Type: application/json" \
  -d '{
    "site_id": 1,
    "status": "draft",
    "category_ids": [5],
    "tag_names": ["תאונת דרכים", "פיצויים", "נזיקין"]
  }'
```

**Status Options**:
- `"draft"` - Save as draft (preview before publishing)
- `"publish"` - Publish immediately

Response:
```json
{
  "message": "Article saved as draft",
  "article_id": 1,
  "wordpress_post_id": 123,
  "wordpress_url": "https://your-site.com/piẓuy-btavnt-drkim",
  "published_at": null
}
```

### Step 5: Publish the Draft

To change status from draft to published:

```bash
curl -X POST "http://localhost:8000/api/v1/wordpress/publish/1" \
  -H "Content-Type: application/json" \
  -d '{
    "site_id": 1,
    "status": "publish"
  }'
```

Response:
```json
{
  "message": "Article published successfully",
  "article_id": 1,
  "wordpress_post_id": 123,
  "wordpress_url": "https://your-site.com/piẓuy-btavnt-drkim",
  "published_at": "2026-01-13T..."
}
```

### Step 6: View on WordPress

Visit the WordPress URL from the response to see your published article!

## SEO Plugin Integration

### Yoast SEO

When `seo_plugin` is set to `"yoast"`, the system automatically sets:
- **SEO Title**: `article.meta_title`
- **Meta Description**: `article.meta_description`
- **Focus Keyword**: `article.focus_keyword`

These fields are set via WordPress meta fields:
- `yoast_wpseo_title`
- `yoast_wpseo_metadesc`
- `yoast_wpseo_focuskw`

### Rank Math

When `seo_plugin` is set to `"rankmath"`, the system automatically sets:
- **SEO Title**: `article.meta_title`
- **Meta Description**: `article.meta_description`
- **Focus Keyword**: `article.focus_keyword`

Using Rank Math meta fields:
- `rank_math_title`
- `rank_math_description`
- `rank_math_focus_keyword`

## Category Mapping

You can map legal areas to WordPress categories:

```bash
curl -X PATCH "http://localhost:8000/api/v1/wordpress/sites/1" \
  -H "Content-Type: application/json" \
  -d '{
    "categories_map": {
      "נזיקין": 5,
      "חוזים": 6,
      "דיני עבודה": 7,
      "משפחה": 8
    }
  }'
```

Now when you publish an article with `category_primary="נזיקין"`, it will automatically be assigned to WordPress category ID 5.

## Complete Workflow: Verdict to WordPress

```python
import requests

base_url = "http://localhost:8000/api/v1"

# 1. Upload verdict
with open("verdict.pdf", "rb") as f:
    r = requests.post(f"{base_url}/verdicts/upload", files={"file": f})
verdict_id = r.json()["verdict_id"]

# 2. Anonymize
requests.post(f"{base_url}/verdicts/{verdict_id}/anonymize")

# 3. Analyze
requests.post(f"{base_url}/articles/verdicts/{verdict_id}/analyze")

# 4. Generate article
r = requests.post(f"{base_url}/articles/generate/{verdict_id}")
article_id = r.json()["article_id"]

# 5. Publish to WordPress
r = requests.post(
    f"{base_url}/wordpress/publish/{article_id}",
    json={
        "site_id": 1,
        "status": "publish",
        "category_ids": [5],
        "tag_names": ["פיצוי", "תאונת דרכים"]
    }
)

wordpress_url = r.json()["wordpress_url"]
print(f"Published: {wordpress_url}")
```

## Site Management

### List All Sites

```bash
curl "http://localhost:8000/api/v1/wordpress/sites"
```

### Update Site

```bash
curl -X PATCH "http://localhost:8000/api/v1/wordpress/sites/1" \
  -H "Content-Type: application/json" \
  -d '{
    "default_category_id": 10,
    "is_active": true
  }'
```

### Delete Site

```bash
curl -X DELETE "http://localhost:8000/api/v1/wordpress/sites/1"
```

**Note**: This only removes the configuration. Published articles remain on WordPress.

## Unpublishing

To change an article from published to draft:

```bash
curl -X POST "http://localhost:8000/api/v1/wordpress/unpublish/1"
```

This changes the WordPress post status to "draft" without deleting it.

## Tag Management

Tags are automatically created if they don't exist:

```json
{
  "tag_names": ["תאונת דרכים", "פיצויים", "חדש"]
}
```

If "חדש" (new) tag doesn't exist, it will be created automatically.

## Troubleshooting

### "Authentication failed"

**Causes**:
- Incorrect username
- Wrong application password
- Application Passwords not enabled

**Solution**:
1. Verify username is correct
2. Create a new Application Password
3. Ensure Application Passwords feature is enabled (WordPress 5.6+)

### "Cannot connect to WordPress site"

**Causes**:
- Site URL is wrong
- REST API is disabled
- SSL/firewall issues

**Solution**:
1. Test manually: `curl https://your-site.com/wp-json/`
2. Verify site URL is correct (with https://)
3. Check WordPress REST API is not disabled by plugin

### "Publishing failed"

**Common issues**:
- Invalid category IDs
- Article ID doesn't exist
- Site is inactive

**Solution**:
1. Verify category IDs exist: `GET /api/v1/wordpress/sites/{id}/categories`
2. Check article exists: `GET /api/v1/articles/{id}`
3. Verify site is active: `GET /api/v1/wordpress/sites/{id}`

### SEO Plugin Fields Not Set

**Causes**:
- Plugin not installed
- REST API access not enabled for plugin
- Wrong plugin type configured

**Solution**:
1. Install Yoast SEO or Rank Math
2. Verify `seo_plugin` setting matches installed plugin
3. Update site configuration if needed

## Security Notes

1. **Passwords Are Encrypted**: WordPress passwords are encrypted using Fernet (symmetric encryption) before storage
2. **Use Application Passwords**: Never use your main WordPress password. Always use Application Passwords
3. **HTTPS Required**: Always use HTTPS for WordPress sites in production
4. **Rotate Passwords**: Regularly rotate Application Passwords
5. **Limit Permissions**: Use a WordPress user with only necessary permissions (Author or Editor role)

## Advanced Usage

### Publishing to Multiple Sites

```python
# Publish same article to multiple sites
sites = [1, 2, 3]  # Different WordPress sites

for site_id in sites:
    requests.post(
        f"{base_url}/wordpress/publish/{article_id}",
        json={"site_id": site_id, "status": "publish"}
    )
```

### Scheduled Publishing

Use WordPress post status "future" with a publication date:

```python
from datetime import datetime, timedelta

# Publish 1 hour from now
publish_time = datetime.now() + timedelta(hours=1)

# Note: Requires direct WordPress API access for date scheduling
# Or use WordPress plugins for scheduled publishing
```

### Bulk Publishing

```python
# Get all articles ready for publishing
r = requests.get(f"{base_url}/articles", params={"status": "ready"})
articles = r.json()["items"]

# Publish them all
for article in articles:
    requests.post(
        f"{base_url}/wordpress/publish/{article['id']}",
        json={"site_id": 1, "status": "publish"}
    )
    print(f"Published: {article['title']}")
```

## Interactive Documentation

Visit **http://localhost:8000/docs** for:
- All endpoints documented
- Interactive testing
- Try publishing directly from browser
- See request/response examples

## Next Steps

After Phase 5, you can proceed to:
- **Phase 6**: Frontend Interface - Build a user-friendly web interface

The complete backend is now functional! You can upload verdicts, process them, and publish to WordPress automatically.
