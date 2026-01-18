from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.verdict import CourtLevel, PrivacyRiskLevel, VerdictStatus


class VerdictBase(BaseModel):
    """Base schema for Verdict with common fields."""
    case_number: Optional[str] = None
    case_number_display: Optional[str] = None
    court_name: Optional[str] = None
    court_level: Optional[CourtLevel] = None
    judge_name: Optional[str] = None
    verdict_date: Optional[datetime] = None
    case_type: Optional[str] = None
    legal_area: Optional[str] = None
    legal_sub_area: Optional[str] = None


class VerdictCreate(BaseModel):
    """Schema for creating a verdict (used internally after file upload)."""
    file_hash: str
    original_text: str
    case_number: Optional[str] = None
    case_number_display: Optional[str] = None
    court_name: Optional[str] = None
    court_level: Optional[CourtLevel] = None
    judge_name: Optional[str] = None
    verdict_date: Optional[datetime] = None
    case_type: Optional[str] = None
    legal_area: Optional[str] = None
    legal_sub_area: Optional[str] = None


class VerdictUpdate(BaseModel):
    """Schema for updating verdict fields."""
    case_number: Optional[str] = None
    case_number_display: Optional[str] = None
    court_name: Optional[str] = None
    court_level: Optional[CourtLevel] = None
    judge_name: Optional[str] = None
    verdict_date: Optional[datetime] = None
    case_type: Optional[str] = None
    legal_area: Optional[str] = None
    legal_sub_area: Optional[str] = None
    cleaned_text: Optional[str] = None
    anonymized_text: Optional[str] = None
    anonymization_report: Optional[Dict[str, Any]] = None
    privacy_risk_level: Optional[PrivacyRiskLevel] = None
    key_facts: Optional[List[str]] = None
    legal_questions: Optional[List[str]] = None
    legal_principles: Optional[List[str]] = None
    compensation_amount: Optional[float] = None
    compensation_breakdown: Optional[Dict[str, Any]] = None
    relevant_laws: Optional[List[Dict[str, Any]]] = None
    precedents_cited: Optional[List[Dict[str, Any]]] = None
    practical_insights: Optional[List[str]] = None
    requires_manual_review: Optional[bool] = None
    review_notes: Optional[str] = None


class VerdictStatusUpdate(BaseModel):
    """Schema for updating verdict status."""
    status: VerdictStatus


class VerdictResponse(BaseModel):
    """Schema for verdict response."""
    id: int
    file_hash: str
    case_number: Optional[str] = None
    case_number_display: Optional[str] = None
    court_name: Optional[str] = None
    court_level: Optional[CourtLevel] = None
    judge_name: Optional[str] = None
    verdict_date: Optional[datetime] = None
    case_type: Optional[str] = None
    legal_area: Optional[str] = None
    legal_sub_area: Optional[str] = None

    original_text: str
    cleaned_text: Optional[str] = None
    anonymized_text: Optional[str] = None
    anonymization_report: Optional[Dict[str, Any]] = None

    privacy_risk_level: PrivacyRiskLevel

    key_facts: Optional[List[str]] = None
    legal_questions: Optional[List[str]] = None
    legal_principles: Optional[List[str]] = None

    compensation_amount: Optional[float] = None
    compensation_breakdown: Optional[Dict[str, Any]] = None

    relevant_laws: Optional[List[Dict[str, Any]]] = None
    precedents_cited: Optional[List[Dict[str, Any]]] = None
    practical_insights: Optional[List[str]] = None

    status: VerdictStatus
    requires_manual_review: bool
    review_notes: Optional[str] = None

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VerdictListResponse(BaseModel):
    """Schema for verdict list item (lighter than full response)."""
    id: int
    file_hash: str
    case_number: Optional[str] = None
    case_number_display: Optional[str] = None
    court_name: Optional[str] = None
    court_level: Optional[CourtLevel] = None
    judge_name: Optional[str] = None
    verdict_date: Optional[datetime] = None
    case_type: Optional[str] = None
    legal_area: Optional[str] = None
    status: VerdictStatus
    requires_manual_review: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FileUploadResponse(BaseModel):
    """Schema for file upload response."""
    message: str
    verdict_id: int
    file_hash: str
    status: VerdictStatus
