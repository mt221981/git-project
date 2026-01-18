"""WordPress publishing service."""

from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.wordpress_site import WordPressSite, SEOPlugin
from app.models.article import Article, PublishStatus
from app.utils.encryption import encrypt_text, decrypt_text
from app.services.wordpress_client import WordPressClient, WordPressClientError


class WordPressService:
    """
    Service for managing WordPress sites and publishing articles.
    """

    def __init__(self, db: Session):
        """
        Initialize WordPress service.

        Args:
            db: Database session
        """
        self.db = db

    def create_site(
        self,
        site_name: str,
        site_url: str,
        api_username: str,
        api_password: str,
        seo_plugin: SEOPlugin = SEOPlugin.NONE,
        default_category_id: Optional[int] = None,
        default_author_id: Optional[int] = None,
        categories_map: Optional[Dict[str, int]] = None
    ) -> WordPressSite:
        """
        Create a new WordPress site configuration.

        Args:
            site_name: Site name
            site_url: Site URL
            api_username: WordPress username
            api_password: WordPress application password
            seo_plugin: SEO plugin type
            default_category_id: Default category ID
            default_author_id: Default author ID
            categories_map: Mapping of legal areas to WordPress category IDs

        Returns:
            Created WordPress site

        Raises:
            WordPressClientError: If connection test fails
        """
        # Test connection before saving
        client = WordPressClient(site_url, api_username, api_password)
        try:
            client.test_connection()
        except WordPressClientError as e:
            raise WordPressClientError(f"Failed to connect to WordPress site: {str(e)}")

        # Encrypt password
        encrypted_password = encrypt_text(api_password)

        # Create site record
        site = WordPressSite(
            site_name=site_name,
            site_url=site_url,
            api_username=api_username,
            api_password_encrypted=encrypted_password,
            seo_plugin=seo_plugin,
            default_category_id=default_category_id,
            default_author_id=default_author_id,
            categories_map=categories_map or {},
            is_active=True
        )

        self.db.add(site)
        self.db.commit()
        self.db.refresh(site)

        return site

    def get_site(self, site_id: int) -> Optional[WordPressSite]:
        """Get WordPress site by ID."""
        return self.db.query(WordPressSite).filter(WordPressSite.id == site_id).first()

    def list_sites(self, active_only: bool = True) -> List[WordPressSite]:
        """
        List WordPress sites.

        Args:
            active_only: If True, only return active sites

        Returns:
            List of WordPress sites
        """
        query = self.db.query(WordPressSite)
        if active_only:
            query = query.filter(WordPressSite.is_active == True)
        return query.all()

    def update_site(
        self,
        site_id: int,
        **kwargs
    ) -> Optional[WordPressSite]:
        """
        Update WordPress site.

        Args:
            site_id: Site ID
            **kwargs: Fields to update

        Returns:
            Updated site or None if not found
        """
        site = self.get_site(site_id)
        if not site:
            return None

        # Encrypt password if provided
        if 'api_password' in kwargs:
            kwargs['api_password_encrypted'] = encrypt_text(kwargs.pop('api_password'))

        for key, value in kwargs.items():
            if hasattr(site, key):
                setattr(site, key, value)

        self.db.commit()
        self.db.refresh(site)

        return site

    def delete_site(self, site_id: int) -> bool:
        """
        Delete WordPress site.

        Args:
            site_id: Site ID

        Returns:
            True if deleted, False if not found
        """
        site = self.get_site(site_id)
        if not site:
            return False

        self.db.delete(site)
        self.db.commit()
        return True

    def get_client(self, site_id: int) -> WordPressClient:
        """
        Get WordPress client for a site.

        Args:
            site_id: Site ID

        Returns:
            WordPressClient instance

        Raises:
            ValueError: If site not found or inactive
        """
        site = self.get_site(site_id)
        if not site:
            raise ValueError(f"WordPress site with ID {site_id} not found")

        if not site.is_active:
            raise ValueError(f"WordPress site {site.site_name} is inactive")

        # Decrypt password
        password = decrypt_text(site.api_password_encrypted)

        return WordPressClient(site.site_url, site.api_username, password)

    def test_site_connection(self, site_id: int) -> Dict[str, Any]:
        """
        Test connection to WordPress site.

        Args:
            site_id: Site ID

        Returns:
            Connection test result

        Raises:
            ValueError: If site not found
            WordPressClientError: If connection fails
        """
        client = self.get_client(site_id)
        return client.test_connection()

    def get_site_categories(self, site_id: int) -> List[Dict[str, Any]]:
        """
        Get categories from WordPress site.

        Args:
            site_id: Site ID

        Returns:
            List of categories
        """
        client = self.get_client(site_id)
        return client.get_categories()

    def get_site_tags(self, site_id: int) -> List[Dict[str, Any]]:
        """
        Get tags from WordPress site.

        Args:
            site_id: Site ID

        Returns:
            List of tags
        """
        client = self.get_client(site_id)
        return client.get_tags()

    def publish_article(
        self,
        article_id: int,
        site_id: int,
        status: str = "draft",
        author_id: Optional[int] = None,
        category_ids: Optional[List[int]] = None,
        tag_names: Optional[List[str]] = None
    ) -> Article:
        """
        Publish an article to WordPress.

        Args:
            article_id: Article ID
            site_id: WordPress site ID
            status: Post status (draft or publish)
            author_id: Author ID (uses site default if not provided)
            category_ids: Category IDs (uses site default if not provided)
            tag_names: Tag names (creates tags if they don't exist)

        Returns:
            Updated article

        Raises:
            ValueError: If article or site not found
            WordPressClientError: If publishing fails
        """
        # Get article
        article = self.db.query(Article).filter(Article.id == article_id).first()
        if not article:
            raise ValueError(f"Article with ID {article_id} not found")

        # Get site
        site = self.get_site(site_id)
        if not site:
            raise ValueError(f"WordPress site with ID {site_id} not found")

        # Get WordPress client
        client = self.get_client(site_id)

        # Use defaults from site if not provided
        if author_id is None:
            author_id = site.default_author_id

        if category_ids is None:
            category_ids = []
            if site.default_category_id:
                category_ids.append(site.default_category_id)
            # Try to map from article's primary category
            if article.category_primary and site.categories_map:
                mapped_id = site.categories_map.get(article.category_primary)
                if mapped_id:
                    category_ids.append(mapped_id)

        # Get or create tags
        if tag_names is None and article.tags:
            tag_names = article.tags

        tag_ids = []
        if tag_names:
            tag_ids = client.get_or_create_tags(tag_names)

        try:
            # Create or update post
            if article.wordpress_post_id:
                # Update existing post
                post_data = client.update_post(
                    post_id=article.wordpress_post_id,
                    title=article.title,
                    content=article.content_html,
                    status=status,
                    excerpt=article.excerpt,
                    categories=category_ids if category_ids else None,
                    tags=tag_ids if tag_ids else None
                )
            else:
                # Create new post
                post_data = client.create_post(
                    title=article.title,
                    content=article.content_html,
                    status=status,
                    excerpt=article.excerpt,
                    categories=category_ids if category_ids else None,
                    tags=tag_ids if tag_ids else None,
                    author=author_id
                )

            # Update SEO plugin fields if applicable
            if site.seo_plugin == SEOPlugin.YOAST:
                client.update_yoast_seo(
                    post_id=post_data["id"],
                    title=article.meta_title,
                    description=article.meta_description,
                    focus_keyword=article.focus_keyword
                )
            elif site.seo_plugin == SEOPlugin.RANKMATH:
                client.update_rankmath_seo(
                    post_id=post_data["id"],
                    title=article.meta_title,
                    description=article.meta_description,
                    focus_keyword=article.focus_keyword
                )

            # Update article with WordPress info
            article.wordpress_post_id = post_data["id"]
            article.wordpress_url = post_data["link"]

            if status == "publish":
                article.publish_status = PublishStatus.PUBLISHED
                article.published_at = datetime.utcnow()
            else:
                article.publish_status = PublishStatus.READY

            self.db.commit()
            self.db.refresh(article)

            return article

        except WordPressClientError as e:
            article.publish_status = PublishStatus.FAILED
            self.db.commit()
            raise WordPressClientError(f"Failed to publish article: {str(e)}")

    def unpublish_article(self, article_id: int) -> Article:
        """
        Unpublish an article (move to draft in WordPress).

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

        # Get the site (we need to find which site this article was published to)
        # For simplicity, we'll use the default site
        from app.config import settings
        if not settings.WORDPRESS_DEFAULT_SITE_ID:
            raise ValueError("No default WordPress site configured")

        client = self.get_client(settings.WORDPRESS_DEFAULT_SITE_ID)

        try:
            # Update post to draft status
            client.update_post(article.wordpress_post_id, status="draft")

            article.publish_status = PublishStatus.DRAFT
            article.published_at = None

            self.db.commit()
            self.db.refresh(article)

            return article

        except WordPressClientError as e:
            raise WordPressClientError(f"Failed to unpublish article: {str(e)}")
