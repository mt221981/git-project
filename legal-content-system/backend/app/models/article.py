from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database import Base


class PublishStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    READY = "ready"
    PUBLISHED = "published"
    FAILED = "failed"


class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    verdict_id = Column(Integer, ForeignKey("verdicts.id"), nullable=False, index=True)

    # SEO and metadata
    title = Column(String(70), nullable=False)
    slug = Column(String(200), unique=True, index=True)
    meta_title = Column(String(70))
    meta_description = Column(String(160))

    # Content
    content_html = Column(Text, nullable=False)
    excerpt = Column(Text)

    # Keywords
    focus_keyword = Column(String(100))
    secondary_keywords = Column(JSON)
    long_tail_keywords = Column(JSON)

    # Metrics
    word_count = Column(Integer)
    reading_time_minutes = Column(Integer)

    # Structured content
    faq_items = Column(JSON)
    common_mistakes = Column(JSON)

    # Schema markup
    schema_article = Column(JSON)
    schema_faq = Column(JSON)

    # Links
    internal_links = Column(JSON)
    external_links = Column(JSON)

    # Categorization
    category_primary = Column(String(100))
    categories_secondary = Column(JSON)
    tags = Column(JSON)

    # Featured image
    featured_image_prompt = Column(Text)
    featured_image_alt = Column(String(200))

    # Author
    author_name = Column(String(100), default="עו\"ד משה טייב")

    # Quality scores
    content_score = Column(Integer, default=0)
    seo_score = Column(Integer, default=0)
    readability_score = Column(Integer, default=0)
    eeat_score = Column(Integer, default=0)
    overall_score = Column(Integer, default=0)
    quality_issues = Column(JSON)

    # Publishing
    publish_status = Column(Enum(PublishStatus), default=PublishStatus.DRAFT, nullable=False, index=True)
    wordpress_post_id = Column(Integer)
    wordpress_url = Column(String(500))
    published_at = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    verdict = relationship("Verdict", back_populates="articles")
