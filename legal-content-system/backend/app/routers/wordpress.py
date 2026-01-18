"""WordPress API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import uuid
import asyncio

from app.database import get_db
from app.services.wordpress_service import WordPressService
from app.services.wordpress_manager import WordPressManager
from app.services.wordpress_client import WordPressClientError
from app.schemas.wordpress import (
    WordPressSiteCreate,
    WordPressSiteUpdate,
    WordPressSiteResponse,
    WordPressCategory,
    WordPressTag,
    WordPressPublishRequest,
    WordPressPublishResponse,
    WordPressSiteTestResponse,
    BatchPublishRequest,
    BatchPublishResponse,
    BatchPublishProgress
)
from app.schemas.article import ArticleResponse
from app.models.article import Article, PublishStatus
from app.models.wordpress_site import WordPressSite
from typing import Optional
from sqlalchemy import func

router = APIRouter()

# In-memory progress store for batch publishing
# In production, this should be replaced with Redis
batch_progress_store: Dict[str, Dict[str, Any]] = {}


def get_wordpress_service(db: Session = Depends(get_db)) -> WordPressService:
    """Dependency to get WordPressService instance."""
    return WordPressService(db)


@router.get("/statistics")
async def get_wordpress_statistics(
    db: Session = Depends(get_db)
):
    """
    Get WordPress publishing statistics.

    Returns:
        Statistics including total published, by status, and recent publications
    """
    # Total articles published to WordPress
    total_published = db.query(func.count(Article.id)).filter(
        Article.wordpress_post_id.isnot(None)
    ).scalar() or 0

    # Count by publish status
    status_counts = db.query(
        Article.publish_status,
        func.count(Article.id)
    ).filter(
        Article.wordpress_post_id.isnot(None)
    ).group_by(Article.publish_status).all()

    by_status = {status.value if status else 'unknown': count for status, count in status_counts}

    # Total sites configured
    total_sites = db.query(func.count(WordPressSite.id)).filter(
        WordPressSite.is_active == True
    ).scalar() or 0

    # Recent publications (last 5)
    recent = db.query(Article).filter(
        Article.wordpress_post_id.isnot(None),
        Article.published_at.isnot(None)
    ).order_by(Article.published_at.desc()).limit(5).all()

    recent_publications = [
        {
            "article_id": a.id,
            "title": a.title,
            "wordpress_url": a.wordpress_url,
            "published_at": a.published_at.isoformat() if a.published_at else None
        }
        for a in recent
    ]

    # Total articles (all)
    total_articles = db.query(func.count(Article.id)).scalar() or 0

    return {
        "total_published": total_published,
        "total_articles": total_articles,
        "total_sites": total_sites,
        "by_status": by_status,
        "recent_publications": recent_publications
    }


@router.post("/sites", response_model=WordPressSiteResponse, status_code=status.HTTP_201_CREATED)
async def create_wordpress_site(
    site_data: WordPressSiteCreate,
    service: WordPressService = Depends(get_wordpress_service)
):
    """
    Add a new WordPress site configuration.

    This endpoint will:
    1. Test the connection to the WordPress site
    2. Verify authentication with application password
    3. Store the site configuration with encrypted credentials

    Requirements:
    - WordPress site with REST API enabled
    - Application Password created for the user
    - Username and application password provided

    Returns:
        Created WordPress site configuration
    """
    try:
        site = service.create_site(
            site_name=site_data.site_name,
            site_url=str(site_data.site_url),
            api_username=site_data.api_username,
            api_password=site_data.api_password,
            seo_plugin=site_data.seo_plugin,
            default_category_id=site_data.default_category_id,
            default_author_id=site_data.default_author_id,
            categories_map=site_data.categories_map
        )

        return WordPressSiteResponse.model_validate(site)

    except WordPressClientError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create WordPress site: {str(e)}"
        )


@router.get("/sites", response_model=List[WordPressSiteResponse])
async def list_wordpress_sites(
    active_only: bool = True,
    service: WordPressService = Depends(get_wordpress_service)
):
    """
    List all configured WordPress sites.

    Args:
        active_only: If True, only return active sites

    Returns:
        List of WordPress sites
    """
    sites = service.list_sites(active_only=active_only)
    return [WordPressSiteResponse.model_validate(site) for site in sites]


@router.get("/sites/{site_id}", response_model=WordPressSiteResponse)
async def get_wordpress_site(
    site_id: int,
    service: WordPressService = Depends(get_wordpress_service)
):
    """Get WordPress site details."""
    site = service.get_site(site_id)

    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"WordPress site with ID {site_id} not found"
        )

    return WordPressSiteResponse.model_validate(site)


@router.patch("/sites/{site_id}", response_model=WordPressSiteResponse)
async def update_wordpress_site(
    site_id: int,
    update_data: WordPressSiteUpdate,
    service: WordPressService = Depends(get_wordpress_service)
):
    """
    Update WordPress site configuration.

    You can update any of the site settings including credentials.
    """
    update_dict = update_data.model_dump(exclude_unset=True)

    # Convert HttpUrl to string if present
    if 'site_url' in update_dict and update_dict['site_url']:
        update_dict['site_url'] = str(update_dict['site_url'])

    site = service.update_site(site_id, **update_dict)

    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"WordPress site with ID {site_id} not found"
        )

    return WordPressSiteResponse.model_validate(site)


@router.delete("/sites/{site_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_wordpress_site(
    site_id: int,
    service: WordPressService = Depends(get_wordpress_service)
):
    """
    Delete a WordPress site configuration.

    WARNING: This will remove the site configuration but will NOT delete any posts
    from WordPress itself. Published articles will remain on the WordPress site.
    """
    success = service.delete_site(site_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"WordPress site with ID {site_id} not found"
        )

    return None


@router.post("/sites/{site_id}/test", response_model=WordPressSiteTestResponse)
async def test_wordpress_site(
    site_id: int,
    service: WordPressService = Depends(get_wordpress_service)
):
    """
    Test connection to a WordPress site.

    Verifies:
    - Site is reachable
    - REST API is enabled
    - Authentication is working

    Returns:
        Connection test result with site information
    """
    try:
        site_info = service.test_site_connection(site_id)

        return WordPressSiteTestResponse(
            success=True,
            message="Connection successful",
            site_info=site_info
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except WordPressClientError as e:
        return WordPressSiteTestResponse(
            success=False,
            message=str(e),
            site_info=None
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Test failed: {str(e)}"
        )


@router.get("/sites/{site_id}/categories", response_model=List[WordPressCategory])
async def get_wordpress_categories(
    site_id: int,
    service: WordPressService = Depends(get_wordpress_service)
):
    """
    Get all categories from a WordPress site.

    Useful for mapping article categories to WordPress categories.

    Returns:
        List of WordPress categories
    """
    try:
        categories = service.get_site_categories(site_id)
        return [WordPressCategory(**cat) for cat in categories]

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except WordPressClientError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )


@router.get("/sites/{site_id}/tags", response_model=List[WordPressTag])
async def get_wordpress_tags(
    site_id: int,
    service: WordPressService = Depends(get_wordpress_service)
):
    """
    Get all tags from a WordPress site.

    Returns:
        List of WordPress tags
    """
    try:
        tags = service.get_site_tags(site_id)
        return [WordPressTag(**tag) for tag in tags]

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except WordPressClientError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )


# Publishing endpoints

@router.post("/publish/{article_id}", response_model=WordPressPublishResponse)
async def publish_article(
    article_id: int,
    publish_data: WordPressPublishRequest,
    service: WordPressService = Depends(get_wordpress_service)
):
    """
    Publish an article to WordPress.

    This endpoint will:
    1. Create or update a WordPress post
    2. Set categories and tags
    3. Apply SEO plugin settings (if configured)
    4. Update the article with WordPress post ID and URL

    Args:
        article_id: Article ID to publish
        publish_data: Publishing configuration

    Returns:
        Publishing result with WordPress post ID and URL
    """
    try:
        article = service.publish_article(
            article_id=article_id,
            site_id=publish_data.site_id,
            status=publish_data.status,
            author_id=publish_data.author_id,
            category_ids=publish_data.category_ids,
            tag_names=publish_data.tag_names
        )

        return WordPressPublishResponse(
            message="Article published successfully" if publish_data.status == "publish"
                    else "Article saved as draft",
            article_id=article.id,
            wordpress_post_id=article.wordpress_post_id,
            wordpress_url=article.wordpress_url,
            published_at=article.published_at
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except WordPressClientError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Publishing failed: {str(e)}"
        )


@router.post("/unpublish/{article_id}", response_model=ArticleResponse)
async def unpublish_article(
    article_id: int,
    service: WordPressService = Depends(get_wordpress_service)
):
    """
    Unpublish an article (move to draft in WordPress).

    Changes the article status to draft in WordPress without deleting it.

    Returns:
        Updated article
    """
    try:
        article = service.unpublish_article(article_id)
        return ArticleResponse.model_validate(article)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except WordPressClientError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unpublishing failed: {str(e)}"
        )


# Batch publishing endpoints

async def process_batch_publish(
    batch_id: str,
    article_ids: List[int],
    site_id: int,
    status: str,
    stop_on_error: bool,
    db: Session
):
    """
    Background task to publish articles with progress tracking.

    Args:
        batch_id: Unique identifier for this batch
        article_ids: List of article IDs to publish
        site_id: WordPress site ID
        status: Publish status (draft/publish/private)
        stop_on_error: Whether to stop on first error
        db: Database session
    """
    wp_manager = WordPressManager(db)

    # Initialize progress
    batch_progress_store[batch_id] = {
        "status": "processing",
        "current": 0,
        "total": len(article_ids),
        "successful": [],
        "failed": [],
        "current_article_id": None
    }

    # Process each article sequentially
    for idx, article_id in enumerate(article_ids, 1):
        batch_progress_store[batch_id]["current"] = idx
        batch_progress_store[batch_id]["current_article_id"] = article_id

        try:
            # Use the existing publish_article_with_retry method
            result = wp_manager.publish_article_with_retry(
                article_id=article_id,
                site_id=site_id,
                status=status
            )
            batch_progress_store[batch_id]["successful"].append(article_id)

        except Exception as e:
            error_detail = {
                "article_id": article_id,
                "error": str(e)
            }
            batch_progress_store[batch_id]["failed"].append(error_detail)

            if stop_on_error:
                break

    # Mark as completed
    batch_progress_store[batch_id]["status"] = "completed"
    batch_progress_store[batch_id]["current_article_id"] = None

    # Schedule cleanup after 1 hour
    await asyncio.sleep(3600)
    if batch_id in batch_progress_store:
        del batch_progress_store[batch_id]


@router.post("/articles/batch-publish", response_model=BatchPublishResponse)
async def batch_publish_articles(
    request: BatchPublishRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Publish multiple articles to WordPress sequentially.

    This endpoint starts a background task to publish articles one by one.
    Use the returned batch_id to track progress via the progress endpoint.

    Args:
        request: Batch publish configuration

    Returns:
        Batch ID for tracking progress
    """
    # Validate article count
    if len(request.article_ids) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot publish more than 100 articles at once"
        )

    # Validate articles exist
    articles = db.query(Article).filter(Article.id.in_(request.article_ids)).all()
    if len(articles) != len(request.article_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or more article IDs not found"
        )

    # Validate WordPress site exists
    wp_site = db.query(WordPressSite).filter(WordPressSite.id == request.site_id).first()
    if not wp_site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"WordPress site with ID {request.site_id} not found"
        )

    # Generate unique batch ID
    batch_id = str(uuid.uuid4())

    # Start background task
    background_tasks.add_task(
        process_batch_publish,
        batch_id=batch_id,
        article_ids=request.article_ids,
        site_id=request.site_id,
        status=request.status,
        stop_on_error=request.stop_on_error,
        db=db
    )

    return BatchPublishResponse(
        batch_id=batch_id,
        status="started",
        total=len(request.article_ids)
    )


@router.get("/articles/batch-publish/{batch_id}/progress", response_model=BatchPublishProgress)
async def get_batch_progress(
    batch_id: str
):
    """
    Get the progress of a batch publishing operation.

    Poll this endpoint to get real-time progress updates.

    Args:
        batch_id: The batch ID returned from batch-publish endpoint

    Returns:
        Current progress information
    """
    if batch_id not in batch_progress_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch not found or has expired"
        )

    progress = batch_progress_store[batch_id]

    return BatchPublishProgress(
        status=progress["status"],
        current=progress["current"],
        total=progress["total"],
        successful=progress["successful"],
        failed=progress["failed"],
        current_article_id=progress["current_article_id"]
    )
