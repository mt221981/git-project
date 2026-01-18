from pydantic import BaseModel, Field, ConfigDict, HttpUrl
from typing import Optional, Dict, Any, List
from datetime import datetime
from app.models.wordpress_site import SEOPlugin


class WordPressSiteCreate(BaseModel):
    """Schema for creating a WordPress site."""
    site_name: str = Field(..., min_length=1, max_length=200)
    site_url: HttpUrl
    api_username: str = Field(..., min_length=1, max_length=200)
    api_password: str = Field(..., min_length=1)
    seo_plugin: SEOPlugin = SEOPlugin.NONE
    default_category_id: Optional[int] = None
    default_author_id: Optional[int] = None
    categories_map: Optional[Dict[str, int]] = None


class WordPressSiteUpdate(BaseModel):
    """Schema for updating a WordPress site."""
    site_name: Optional[str] = Field(None, min_length=1, max_length=200)
    site_url: Optional[HttpUrl] = None
    api_username: Optional[str] = Field(None, min_length=1, max_length=200)
    api_password: Optional[str] = Field(None, min_length=1)
    seo_plugin: Optional[SEOPlugin] = None
    default_category_id: Optional[int] = None
    default_author_id: Optional[int] = None
    categories_map: Optional[Dict[str, int]] = None
    is_active: Optional[bool] = None


class WordPressSiteResponse(BaseModel):
    """Schema for WordPress site response."""
    id: int
    site_name: str
    site_url: str
    api_username: str
    seo_plugin: SEOPlugin
    default_category_id: Optional[int] = None
    default_author_id: Optional[int] = None
    categories_map: Optional[Dict[str, int]] = None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WordPressCategory(BaseModel):
    """WordPress category."""
    id: int
    name: str
    slug: str
    description: Optional[str] = None
    parent: Optional[int] = None


class WordPressTag(BaseModel):
    """WordPress tag."""
    id: int
    name: str
    slug: str
    description: Optional[str] = None


class WordPressPublishRequest(BaseModel):
    """Request to publish an article to WordPress."""
    site_id: int
    status: str = Field(default="draft", pattern="^(draft|publish)$")
    author_id: Optional[int] = None
    category_ids: Optional[list[int]] = None
    tag_names: Optional[list[str]] = None


class WordPressPublishResponse(BaseModel):
    """Response after publishing to WordPress."""
    message: str
    article_id: int
    wordpress_post_id: int
    wordpress_url: str
    published_at: Optional[datetime] = None


class WordPressSiteTestResponse(BaseModel):
    """Response from testing WordPress connection."""
    success: bool
    message: str
    site_info: Optional[Dict[str, Any]] = None


class BatchPublishRequest(BaseModel):
    """Request to publish multiple articles to WordPress."""
    article_ids: List[int] = Field(..., min_length=1, max_length=100, description="List of article IDs to publish (max 100)")
    site_id: int = Field(..., description="WordPress site ID")
    status: str = Field(default="draft", pattern="^(draft|publish|private)$", description="Publish status")
    stop_on_error: Optional[bool] = Field(default=False, description="Stop processing if an article fails")


class BatchPublishProgress(BaseModel):
    """Progress information for batch publishing."""
    status: str = Field(..., description="Status: processing, completed, or error")
    current: int = Field(..., description="Current article index")
    total: int = Field(..., description="Total number of articles")
    successful: List[int] = Field(default_factory=list, description="IDs of successfully published articles")
    failed: List[Dict[str, Any]] = Field(default_factory=list, description="Failed articles with errors")
    current_article_id: Optional[int] = Field(None, description="Article ID currently being processed")


class BatchPublishResponse(BaseModel):
    """Response from initiating batch publishing."""
    batch_id: str = Field(..., description="Unique batch identifier for tracking progress")
    status: str = Field(..., description="Initial status")
    total: int = Field(..., description="Total articles to process")
