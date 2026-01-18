from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Enum
from sqlalchemy.dialects.postgresql import JSON
from datetime import datetime
import enum

from app.database import Base


class SEOPlugin(str, enum.Enum):
    YOAST = "yoast"
    RANKMATH = "rankmath"
    NONE = "none"


class WordPressSite(Base):
    __tablename__ = "wordpress_sites"

    id = Column(Integer, primary_key=True, index=True)

    # Site information
    site_name = Column(String(200), nullable=False)
    site_url = Column(String(500), nullable=False)

    # API credentials
    api_username = Column(String(200), nullable=False)
    api_password_encrypted = Column(Text, nullable=False)

    # Configuration
    seo_plugin = Column(Enum(SEOPlugin), default=SEOPlugin.NONE, nullable=False)
    default_category_id = Column(Integer)
    default_author_id = Column(Integer)
    categories_map = Column(JSON)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
