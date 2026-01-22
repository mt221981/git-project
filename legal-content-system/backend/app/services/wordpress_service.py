"""WordPress publishing service."""

import os
import re
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.wordpress_site import WordPressSite, SEOPlugin
from app.models.article import Article, PublishStatus
from app.utils.encryption import encrypt_text, decrypt_text
from app.services.wordpress_client import WordPressClient, WordPressClientError


class ContentValidationError(Exception):
    """Exception raised when content validation fails."""
    pass


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

        # PRE-PUBLISH VALIDATION: Check for foreign characters
        validation_result = self._validate_content_before_publish(article)
        if not validation_result["passed"]:
            print(f"[WordPress] Content validation FAILED for article {article_id}")
            print(f"[WordPress] Foreign characters detected: {validation_result['details']}")
            # Clean the content and update the article in DB
            self._clean_article_content(article)
            self.db.commit()
            print(f"[WordPress] Content cleaned and saved to database")

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

        # Prepare content with author byline if available
        content_with_author = article.content_html
        if article.author_name:
            # Add author byline at the beginning of the content
            author_byline = f'<p class="article-author" style="font-weight: bold; color: #333; margin-bottom: 20px;">מאת: {article.author_name}</p>'
            content_with_author = author_byline + article.content_html

        try:
            # Create or update post
            if article.wordpress_post_id:
                # Update existing post
                post_data = client.update_post(
                    post_id=article.wordpress_post_id,
                    title=article.title,
                    content=content_with_author,
                    status=status,
                    excerpt=article.excerpt,
                    categories=category_ids if category_ids else None,
                    tags=tag_ids if tag_ids else None
                )
            else:
                # Create new post
                post_data = client.create_post(
                    title=article.title,
                    content=content_with_author,
                    status=status,
                    excerpt=article.excerpt,
                    categories=category_ids if category_ids else None,
                    tags=tag_ids if tag_ids else None,
                    author=author_id
                )

            # Upload featured image if available
            if article.featured_image_url and not article.featured_image_wp_id:
                try:
                    print(f"[WordPress] Uploading featured image for article {article.id}")
                    media_id = self.upload_featured_image(
                        client=client,
                        article=article
                    )
                    if media_id:
                        # Set featured image on post
                        client.set_featured_image(post_data["id"], media_id)
                        article.featured_image_wp_id = media_id
                        # Commit immediately to persist the media ID
                        self.db.commit()
                        print(f"[WordPress] Featured image set and saved: Media ID {media_id}")
                except Exception as e:
                    print(f"[WordPress] Featured image upload failed: {e}")
                    # Continue without featured image - not critical

            # Set author name as custom meta field
            if article.author_name:
                try:
                    print(f"[WordPress] Setting author meta: {article.author_name}")
                    client.update_post_meta(post_data["id"], "article_author", article.author_name)
                    print(f"[WordPress] Author meta set successfully")
                except Exception as e:
                    print(f"[WordPress] Author meta update failed: {e}")
                    # Continue without author meta - not critical

            # Update SEO plugin fields if applicable
            if site.seo_plugin == SEOPlugin.YOAST:
                print(f"[WordPress] Updating Yoast SEO for post {post_data['id']}")
                print(f"[WordPress] meta_title: {article.meta_title}")
                print(f"[WordPress] meta_description: {article.meta_description}")
                print(f"[WordPress] focus_keyword: {article.focus_keyword}")
                try:
                    client.update_yoast_seo(
                        post_id=post_data["id"],
                        title=article.meta_title,
                        description=article.meta_description,
                        focus_keyword=article.focus_keyword
                    )
                    print("[WordPress] Yoast SEO updated successfully")
                except Exception as e:
                    print(f"[WordPress] Yoast SEO update failed: {e}")
            elif site.seo_plugin == SEOPlugin.RANKMATH:
                print(f"[WordPress] Updating RankMath SEO for post {post_data['id']}")
                try:
                    client.update_rankmath_seo(
                        post_id=post_data["id"],
                        title=article.meta_title,
                        description=article.meta_description,
                        focus_keyword=article.focus_keyword
                    )
                    print("[WordPress] RankMath SEO updated successfully")
                except Exception as e:
                    print(f"[WordPress] RankMath SEO update failed: {e}")

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

    def upload_featured_image(
        self,
        client: WordPressClient,
        article: Article
    ) -> Optional[int]:
        """
        Upload featured image to WordPress and return media ID.

        Args:
            client: WordPress client
            article: Article with featured_image_url

        Returns:
            Media ID if successful, None otherwise
        """
        if not article.featured_image_url:
            return None

        try:
            # Import image service to download image
            from app.services.image_service import PexelsImageService, ImageServiceError
            import requests

            # Download image from URL
            print(f"[WordPress] Downloading image from {article.featured_image_url[:50]}...")
            response = requests.get(article.featured_image_url, timeout=30)
            response.raise_for_status()

            # Determine content type and filename
            content_type = response.headers.get("Content-Type", "image/jpeg")
            extension = ".jpg"
            if "png" in content_type:
                extension = ".png"
            elif "webp" in content_type:
                extension = ".webp"

            # Generate filename from article slug
            filename = f"{article.slug[:50]}-featured{extension}"

            # Build caption with credit
            caption = article.featured_image_alt or ""
            if article.featured_image_credit:
                caption = f"{caption} | {article.featured_image_credit}" if caption else article.featured_image_credit

            # Upload to WordPress
            media_data = client.upload_media(
                file_content=response.content,
                filename=filename,
                content_type=content_type,
                alt_text=article.featured_image_alt,
                caption=caption,
                title=article.title[:100]
            )

            return media_data.get("id")

        except Exception as e:
            print(f"[WordPress] Featured image upload error: {e}")
            return None

    def _detect_foreign_characters(self, text: str) -> Dict[str, Any]:
        """
        Detect foreign (non-Hebrew/Latin) characters in text.
        This is a pre-publish validation gate to catch any foreign characters.

        Returns:
            Dictionary with detection results
        """
        if not text:
            return {"has_foreign": False, "chars": [], "scripts": []}

        foreign_chars = []
        foreign_scripts = set()

        # Define forbidden character ranges
        forbidden_ranges = [
            (0x0600, 0x06FF, "Arabic"),
            (0x0750, 0x077F, "Arabic Supplement"),
            (0x08A0, 0x08FF, "Arabic Extended-A"),
            (0x0400, 0x04FF, "Cyrillic"),
            (0x0370, 0x03FF, "Greek"),
            (0x0E00, 0x0E7F, "Thai"),
            (0x4E00, 0x9FFF, "Chinese"),
            (0x3040, 0x309F, "Japanese Hiragana"),
            (0x30A0, 0x30FF, "Japanese Katakana"),
            (0xAC00, 0xD7AF, "Korean"),
            (0x0900, 0x097F, "Devanagari"),
            (0x0980, 0x09FF, "Bengali"),
        ]

        for char in text:
            code = ord(char)
            for start, end, script_name in forbidden_ranges:
                if start <= code <= end:
                    foreign_chars.append(char)
                    foreign_scripts.add(script_name)
                    break

        return {
            "has_foreign": len(foreign_chars) > 0,
            "chars": foreign_chars[:10],
            "scripts": list(foreign_scripts)
        }

    def _clean_text_hebrew_only(self, text: str) -> str:
        """
        Clean text to contain only Hebrew, Latin (for HTML), numbers, and punctuation.
        """
        if not text:
            return text

        # Remove Arabic and other foreign scripts
        text = re.sub(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]', '', text)
        text = re.sub(r'[\u0400-\u04FF\u0370-\u03FF\u0E00-\u0E7F\u4E00-\u9FFF\u3040-\u309F\u30A0-\u30FF\uAC00-\uD7AF\u0900-\u097F\u0980-\u09FF]', '', text)

        # Keep only allowed characters
        allowed_pattern = r'[\u0590-\u05FF0-9\s\.,;:!?\-\"\'\(\)\[\]<>/=a-zA-Z_#&%@\n\r\t\u00B0\u2013\u2014\u2018\u2019\u201C\u201D]+'
        cleaned_parts = re.findall(allowed_pattern, text)
        return ''.join(cleaned_parts)

    def _validate_content_before_publish(self, article: Article) -> Dict[str, Any]:
        """
        Validate article content before publishing to WordPress.
        This is the final gate to ensure no foreign characters slip through.

        Returns:
            Dictionary with validation result
        """
        fields_to_check = [
            ("title", article.title),
            ("content_html", article.content_html),
            ("meta_description", article.meta_description),
            ("excerpt", article.excerpt),
            ("meta_title", article.meta_title),
        ]

        all_foreign = []
        all_scripts = set()

        for field_name, field_value in fields_to_check:
            if field_value:
                result = self._detect_foreign_characters(field_value)
                if result["has_foreign"]:
                    all_foreign.append({
                        "field": field_name,
                        "chars": result["chars"],
                        "scripts": result["scripts"]
                    })
                    all_scripts.update(result["scripts"])

        passed = len(all_foreign) == 0

        if not passed:
            print(f"[WordPress] PRE-PUBLISH VALIDATION FAILED!")
            print(f"[WordPress] Foreign scripts detected: {list(all_scripts)}")
            for item in all_foreign:
                print(f"[WordPress]   - Field '{item['field']}': {item['scripts']}")

        return {
            "passed": passed,
            "details": all_foreign,
            "scripts": list(all_scripts)
        }

    def _clean_article_content(self, article: Article) -> None:
        """
        Clean all text fields in an article to remove foreign characters.
        Modifies the article object in place.
        """
        if article.title:
            article.title = self._clean_text_hebrew_only(article.title)
        if article.content_html:
            article.content_html = self._clean_text_hebrew_only(article.content_html)
        if article.meta_description:
            article.meta_description = self._clean_text_hebrew_only(article.meta_description)
        if article.excerpt:
            article.excerpt = self._clean_text_hebrew_only(article.excerpt)
        if article.meta_title:
            article.meta_title = self._clean_text_hebrew_only(article.meta_title)

        print(f"[WordPress] Article {article.id} content cleaned")
