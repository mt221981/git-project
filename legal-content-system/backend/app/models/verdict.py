from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, Enum
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database import Base


class CourtLevel(str, enum.Enum):
    SHALOM = "שלום"
    MEHOZI = "מחוזי"
    ELION = "עליון"
    AVODA = "עבודה"
    MISHPACHA = "משפחה"


class PrivacyRiskLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class VerdictStatus(str, enum.Enum):
    NEW = "new"
    EXTRACTING = "extracting"
    EXTRACTED = "extracted"
    ANONYMIZING = "anonymizing"
    ANONYMIZED = "anonymized"
    ANALYZING = "analyzing"
    ANALYZED = "analyzed"
    ARTICLE_CREATED = "article_created"
    PUBLISHED = "published"
    FAILED = "failed"


class Verdict(Base):
    __tablename__ = "verdicts"

    id = Column(Integer, primary_key=True, index=True)

    # File and case identification
    file_hash = Column(String(64), unique=True, nullable=False, index=True)
    case_number = Column(String(100), index=True)
    case_number_display = Column(String(100))

    # Court information
    court_name = Column(String(200))
    court_level = Column(Enum(CourtLevel), nullable=True)
    judge_name = Column(String(200))
    verdict_date = Column(DateTime, nullable=True)

    # Case categorization
    case_type = Column(String(100))
    legal_area = Column(String(100))
    legal_sub_area = Column(String(100))

    # Text content
    original_text = Column(Text, nullable=False)
    cleaned_text = Column(Text)
    anonymized_text = Column(Text)
    anonymization_report = Column(JSON)

    # Privacy
    privacy_risk_level = Column(Enum(PrivacyRiskLevel), default=PrivacyRiskLevel.LOW)

    # Structured analysis
    key_facts = Column(JSON)
    legal_questions = Column(JSON)
    legal_principles = Column(JSON)

    # Financial information
    compensation_amount = Column(Float)
    compensation_breakdown = Column(JSON)

    # Legal references
    relevant_laws = Column(JSON)
    precedents_cited = Column(JSON)
    practical_insights = Column(JSON)

    # Status and review
    status = Column(Enum(VerdictStatus), default=VerdictStatus.NEW, nullable=False, index=True)
    requires_manual_review = Column(Boolean, default=False)
    review_notes = Column(Text)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    articles = relationship("Article", back_populates="verdict", cascade="all, delete-orphan")
