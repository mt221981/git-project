"""WordPress publishing manager with advanced features."""

import time
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.article import Article, PublishStatus
from app.models.wordpress_site import WordPressSite
from app.services.wordpress_service import WordPressService
from app.services.wordpress_client import WordPressClientError


class PublishingError(Exception):
    """Exception raised when publishing fails."""
    pass


class WordPressManager:
    """
    Manager for advanced WordPress publishing operations.

    Features:
    - Batch publishing
    - Retry logic for failed publishes
    - Publishing statistics
    - Content validation before publishing
    """

    def __init__(self, db: Session, wordpress_service: Optional[WordPressService] = None):
        """
        Initialize WordPress manager.

        Args:
            db: Database session
            wordpress_service: Optional WordPressService instance
        """
        self.db = db
        self.wp_service = wordpress_service or WordPressService(db)

    def validate_article_for_publishing(self, article: Article) -> List[str]:
        """
        Validate article is ready for publishing.

        Args:
            article: Article to validate

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        if not article.title:
            errors.append("Article must have a title")

        if not article.content_html:
            errors.append("Article must have content")

        if article.word_count < 500:
            errors.append(f"Article too short ({article.word_count} words, minimum 500)")

        if not article.focus_keyword:
            errors.append("Article must have a focus keyword")

        if article.overall_score < 50:
            errors.append(f"Quality score too low ({article.overall_score}, minimum 50)")

        if not article.meta_title:
            errors.append("Article must have meta title")

        if not article.meta_description:
            errors.append("Article must have meta description")

        return errors

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

        Args:
            article_id: Article ID
            site_id: WordPress site ID
            status: Post status (draft/publish)
            max_retries: Maximum number of retries
            retry_delay: Delay between retries in seconds

        Returns:
            Published article

        Raises:
            PublishingError: If publishing fails after retries
            ValueError: If article validation fails
        """
        # Get article
        article = self.db.query(Article).filter(Article.id == article_id).first()
        if not article:
            raise ValueError(f"Article with ID {article_id} not found")

        # Validate article
        errors = self.validate_article_for_publishing(article)
        if errors:
            raise ValueError(f"Article validation failed: {', '.join(errors)}")

        # Try publishing with retries
        last_error = None
        for attempt in range(max_retries):
            try:
                # Attempt to publish
                published_article = self.wp_service.publish_article(
                    article_id=article_id,
                    site_id=site_id,
                    status=status
                )

                # Success - update metadata
                if not article.metadata:
                    article.metadata = {}

                article.metadata['publish_attempts'] = attempt + 1
                article.metadata['last_publish_success'] = datetime.utcnow().isoformat()
                self.db.commit()

                return published_article

            except WordPressClientError as e:
                last_error = e

                # Don't retry on certain errors
                if "not found" in str(e).lower() or "authentication" in str(e).lower():
                    raise PublishingError(f"Publishing failed: {str(e)}")

                # Wait before retry (unless last attempt)
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))  # Exponential backoff

        # All retries failed
        article.publish_status = PublishStatus.FAILED
        if not article.metadata:
            article.metadata = {}
        article.metadata['last_publish_error'] = str(last_error)
        article.metadata['last_publish_attempt'] = datetime.utcnow().isoformat()
        self.db.commit()

        raise PublishingError(
            f"Publishing failed after {max_retries} attempts: {str(last_error)}"
        )

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
            Dictionary with:
            {
                "successful": List[int],      # Successfully published article IDs
                "failed": List[Dict],          # Failed articles with errors
                "total": int,                  # Total articles processed
                "success_count": int,          # Number of successful publishes
                "error_count": int             # Number of failed publishes
            }
        """
        results = {
            "successful": [],
            "failed": [],
            "total": len(article_ids),
            "success_count": 0,
            "error_count": 0
        }

        for article_id in article_ids:
            try:
                # Publish with retry
                self.publish_article_with_retry(
                    article_id=article_id,
                    site_id=site_id,
                    status=status
                )

                results["successful"].append(article_id)
                results["success_count"] += 1

            except (PublishingError, ValueError) as e:
                results["failed"].append({
                    "article_id": article_id,
                    "error": str(e)
                })
                results["error_count"] += 1

                if stop_on_error:
                    break

        return results

    def republish_failed_articles(
        self,
        site_id: int,
        max_articles: int = 10
    ) -> Dict[str, Any]:
        """
        Retry publishing articles that previously failed.

        Args:
            site_id: WordPress site ID
            max_articles: Maximum number of articles to retry

        Returns:
            Batch publishing results
        """
        # Get failed articles
        failed_articles = self.db.query(Article).filter(
            Article.publish_status == PublishStatus.FAILED
        ).limit(max_articles).all()

        article_ids = [article.id for article in failed_articles]

        if not article_ids:
            return {
                "successful": [],
                "failed": [],
                "total": 0,
                "success_count": 0,
                "error_count": 0,
                "message": "No failed articles to retry"
            }

        # Attempt to republish
        return self.publish_articles_batch(
            article_ids=article_ids,
            site_id=site_id,
            status="draft",  # Start as draft for safety
            stop_on_error=False
        )

    def get_publishing_statistics(self, site_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Get publishing statistics.

        Args:
            site_id: Optional site ID to filter by

        Returns:
            Dictionary with statistics:
            {
                "total_articles": int,
                "published": int,
                "draft": int,
                "ready": int,
                "failed": int,
                "by_site": Dict[int, Dict]  # Stats per site
            }
        """
        from sqlalchemy import func

        stats = {
            "total_articles": 0,
            "published": 0,
            "draft": 0,
            "ready": 0,
            "failed": 0,
            "by_site": {}
        }

        # Total articles
        query = self.db.query(func.count(Article.id))
        if site_id:
            query = query.filter(Article.wordpress_site_id == site_id)
        stats["total_articles"] = query.scalar() or 0

        # By status
        for status in PublishStatus:
            query = self.db.query(func.count(Article.id)).filter(
                Article.publish_status == status
            )
            if site_id:
                query = query.filter(Article.wordpress_site_id == site_id)

            count = query.scalar() or 0
            stats[status.value] = count

        # By site (if not filtering by site)
        if not site_id:
            sites = self.db.query(WordPressSite).filter(
                WordPressSite.is_active == True
            ).all()

            for site in sites:
                site_stats = {
                    "site_name": site.site_name,
                    "site_url": site.site_url,
                    "total": 0,
                    "published": 0,
                    "draft": 0
                }

                # Count articles for this site
                for status in [PublishStatus.PUBLISHED, PublishStatus.DRAFT]:
                    count = self.db.query(func.count(Article.id)).filter(
                        Article.wordpress_post_id.isnot(None),
                        Article.publish_status == status
                    ).scalar() or 0

                    if status == PublishStatus.PUBLISHED:
                        site_stats["published"] = count
                    elif status == PublishStatus.DRAFT:
                        site_stats["draft"] = count

                site_stats["total"] = site_stats["published"] + site_stats["draft"]
                stats["by_site"][site.id] = site_stats

        return stats

    def sync_article_status(self, article_id: int) -> Article:
        """
        Sync article status with WordPress.

        Useful for checking if a published article is still live.

        Args:
            article_id: Article ID

        Returns:
            Updated article

        Raises:
            ValueError: If article not found or not published
        """
        article = self.db.query(Article).filter(Article.id == article_id).first()
        if not article:
            raise ValueError(f"Article with ID {article_id} not found")

        if not article.wordpress_post_id:
            raise ValueError("Article is not published to WordPress")

        # Get site (assuming default site for now)
        from app.config import settings
        if not settings.WORDPRESS_DEFAULT_SITE_ID:
            raise ValueError("No default WordPress site configured")

        try:
            client = self.wp_service.get_client(settings.WORDPRESS_DEFAULT_SITE_ID)
            wp_post = client.get_post(article.wordpress_post_id)

            # Update status based on WordPress post status
            if wp_post["status"] == "publish":
                article.publish_status = PublishStatus.PUBLISHED
            elif wp_post["status"] == "draft":
                article.publish_status = PublishStatus.DRAFT
            else:
                article.publish_status = PublishStatus.READY

            # Update URL if changed
            if wp_post.get("link"):
                article.wordpress_url = wp_post["link"]

            self.db.commit()
            self.db.refresh(article)

            return article

        except WordPressClientError as e:
            # Post might have been deleted
            if "not found" in str(e).lower():
                article.wordpress_post_id = None
                article.wordpress_url = None
                article.publish_status = PublishStatus.DRAFT
                self.db.commit()

            raise

    def get_unpublished_articles(
        self,
        min_score: int = 70,
        limit: int = 50
    ) -> List[Article]:
        """
        Get articles ready for publishing.

        Args:
            min_score: Minimum overall score required
            limit: Maximum number of articles to return

        Returns:
            List of articles ready to publish
        """
        return self.db.query(Article).filter(
            Article.publish_status == PublishStatus.READY,
            Article.overall_score >= min_score,
            Article.wordpress_post_id.is_(None)
        ).order_by(
            Article.overall_score.desc(),
            Article.created_at.desc()
        ).limit(limit).all()

    def schedule_publishing_queue(
        self,
        site_id: int,
        articles_per_day: int = 5,
        min_score: int = 70
    ) -> Dict[str, Any]:
        """
        Create a publishing queue for scheduled publishing.

        Args:
            site_id: WordPress site ID
            articles_per_day: Number of articles to queue per day
            min_score: Minimum quality score

        Returns:
            Dictionary with queue information
        """
        # Get unpublished articles
        articles = self.get_unpublished_articles(
            min_score=min_score,
            limit=articles_per_day * 7  # One week worth
        )

        queue = {
            "site_id": site_id,
            "total_queued": len(articles),
            "articles_per_day": articles_per_day,
            "estimated_days": len(articles) // articles_per_day if articles_per_day > 0 else 0,
            "articles": [
                {
                    "id": article.id,
                    "title": article.title,
                    "word_count": article.word_count,
                    "overall_score": article.overall_score,
                    "focus_keyword": article.focus_keyword
                }
                for article in articles
            ]
        }

        return queue
