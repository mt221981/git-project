from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from app.models.article import PublishStatus


class ArticleBase(BaseModel):
    """Base schema for Article with common fields."""
    title: Optional[str] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    focus_keyword: Optional[str] = None
    category_primary: Optional[str] = None


class ArticleResponse(BaseModel):
    """Schema for article response."""
    id: int
    verdict_id: int

    # SEO
    title: str
    slug: str
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None

    # Content
    content_html: str
    excerpt: Optional[str] = None

    # Keywords
    focus_keyword: Optional[str] = None
    secondary_keywords: Optional[List[str]] = None
    long_tail_keywords: Optional[List[str]] = None

    # Metrics
    word_count: Optional[int] = None
    reading_time_minutes: Optional[int] = None

    # Structured content
    faq_items: Optional[List[Dict[str, Any]]] = None
    common_mistakes: Optional[List[Dict[str, Any]]] = None

    # Schema markup
    schema_article: Optional[Dict[str, Any]] = None
    schema_faq: Optional[Dict[str, Any]] = None

    # Links
    internal_links: Optional[List[Dict[str, Any]]] = None
    external_links: Optional[List[Dict[str, Any]]] = None

    # Categorization
    category_primary: Optional[str] = None
    categories_secondary: Optional[List[str]] = None
    tags: Optional[List[str]] = None

    # Featured image
    featured_image_prompt: Optional[str] = None
    featured_image_alt: Optional[str] = None

    # Quality scores
    content_score: int
    seo_score: int
    readability_score: int
    eeat_score: int
    overall_score: int
    quality_issues: Optional[List[Dict[str, Any]]] = None

    # Publishing
    publish_status: PublishStatus
    wordpress_post_id: Optional[int] = None
    wordpress_url: Optional[str] = None
    published_at: Optional[datetime] = None

    # Timestamps
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator('quality_issues', mode='before')
    @classmethod
    def convert_quality_issues(cls, v):
        """Convert old string format to new dict format for backward compatibility."""
        if v is None:
            return None
        result = []
        for item in v:
            if isinstance(item, str):
                # Old format: just a string message
                result.append({"type": "warning", "message": item})
            elif isinstance(item, dict):
                # New format: already a dict
                result.append(item)
            else:
                # Unknown format, skip
                continue
        return result


class ArticleListResponse(BaseModel):
    """Schema for article list item (lighter than full response)."""
    id: int
    verdict_id: int
    title: str
    slug: str
    excerpt: Optional[str] = None
    category_primary: Optional[str] = None
    word_count: Optional[int] = None
    overall_score: int
    publish_status: PublishStatus
    published_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ArticleGenerationResponse(BaseModel):
    """Response after generating an article."""
    message: str
    article_id: int
    verdict_id: int
    title: str
    slug: str
    overall_score: int
    publish_status: PublishStatus
