"""Anonymization service using Claude API."""

import json
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.verdict import Verdict, VerdictStatus, PrivacyRiskLevel
from app.services.anonymizer import Anonymizer, AnonymizationError as AnonymizerError


class AnonymizationError(Exception):
    """Exception raised when anonymization fails."""
    pass


class AnonymizationService:
    """
    Service for anonymizing legal text using Claude API.

    Handles:
    - Identification of personal information
    - Replacement with anonymous placeholders
    - Privacy risk assessment
    - Anonymization reporting
    """

    def __init__(self, db: Session, anonymizer: Optional[Anonymizer] = None):
        """
        Initialize anonymization service.

        Args:
            db: Database session
            anonymizer: Optional Anonymizer instance (creates default if not provided)
        """
        self.db = db
        self.anonymizer = anonymizer or Anonymizer()

    def anonymize_text(self, text: str) -> Dict[str, Any]:
        """
        Anonymize text using Claude API.

        Args:
            text: Text to anonymize

        Returns:
            Dictionary with anonymization results:
            {
                "anonymized_text": str,
                "changes": List[Dict],  # Renamed from 'report'
                "overall_risk_assessment": str,  # Renamed from 'risk_level'
                "risk_explanation": str,
                "requires_manual_review": bool,  # Renamed from 'requires_review'
                "review_notes": str
            }

        Raises:
            AnonymizationError: If anonymization fails
        """
        try:
            # Use new Anonymizer service
            result = self.anonymizer.anonymize(text)

            # Transform result to match expected format
            # (Anonymizer uses: report, risk_level, requires_review)
            # (Service expects: changes, overall_risk_assessment, requires_manual_review)
            return {
                "anonymized_text": result["anonymized_text"],
                "changes": result["report"],  # Rename 'report' to 'changes'
                "overall_risk_assessment": result["risk_level"],  # Rename 'risk_level'
                "risk_explanation": f"Risk level: {result['risk_level']}",
                "requires_manual_review": result["requires_review"],  # Rename 'requires_review'
                "review_notes": result.get("review_notes", "")
            }

        except AnonymizerError as e:
            raise AnonymizationError(f"Anonymization failed: {str(e)}")
        except Exception as e:
            raise AnonymizationError(f"Anonymization failed: {str(e)}")

    def anonymize_verdict(self, verdict_id: int) -> Verdict:
        """
        Anonymize a verdict and update it in the database.

        Args:
            verdict_id: ID of verdict to anonymize

        Returns:
            Updated verdict

        Raises:
            ValueError: If verdict not found or in wrong status
            AnonymizationError: If anonymization fails
        """
        verdict = self.db.query(Verdict).filter(Verdict.id == verdict_id).first()

        if not verdict:
            raise ValueError(f"Verdict with ID {verdict_id} not found")

        # Check if verdict status is valid for anonymization
        # Allow ANONYMIZING status (set by endpoint before background task)
        if verdict.status == VerdictStatus.NEW:
            raise ValueError("Verdict must be extracted before anonymization")

        if verdict.status == VerdictStatus.ANONYMIZED:
            raise ValueError("Verdict is already anonymized")

        # Set status to anonymizing if not already
        if verdict.status != VerdictStatus.ANONYMIZING:
            verdict.status = VerdictStatus.ANONYMIZING
            self.db.commit()

        try:
            # Use cleaned text if available, otherwise use original
            text_to_anonymize = verdict.cleaned_text or verdict.original_text

            # Create progress callback to update DB
            def _update_progress(progress: int, message: str):
                """Update progress in database."""
                verdict.processing_progress = progress
                verdict.processing_message = message
                self.db.commit()

            # Perform anonymization using new Anonymizer service with progress tracking
            result = self.anonymizer.anonymize(
                text_to_anonymize,
                progress_callback=_update_progress
            )

            # Transform result to match expected format
            result = {
                "anonymized_text": result["anonymized_text"],
                "changes": result["report"],
                "overall_risk_assessment": result["risk_level"],
                "risk_explanation": f"Risk level: {result['risk_level']}",
                "requires_manual_review": result["requires_review"],
                "review_notes": result.get("review_notes", "")
            }

            # Map risk level string to enum
            risk_map = {
                "low": PrivacyRiskLevel.LOW,
                "medium": PrivacyRiskLevel.MEDIUM,
                "high": PrivacyRiskLevel.HIGH
            }

            # Update verdict with results
            verdict.anonymized_text = result["anonymized_text"]
            verdict.anonymization_report = {
                "changes": result["changes"],
                "change_count": len(result["changes"]),
                "risk_explanation": result.get("risk_explanation", ""),
                "review_notes": result.get("review_notes", "")
            }
            verdict.privacy_risk_level = risk_map.get(
                result["overall_risk_assessment"],
                PrivacyRiskLevel.MEDIUM
            )
            verdict.requires_manual_review = (
                result["requires_manual_review"] or
                verdict.privacy_risk_level == PrivacyRiskLevel.HIGH
            )

            if verdict.requires_manual_review and result.get("review_notes"):
                verdict.review_notes = result["review_notes"]

            verdict.status = VerdictStatus.ANONYMIZED
            self.db.commit()
            self.db.refresh(verdict)

            return verdict

        except Exception as e:
            # Revert status to previous state on error
            verdict.status = VerdictStatus.EXTRACTED
            verdict.review_notes = f"Anonymization failed: {str(e)}"
            self.db.commit()
            raise AnonymizationError(f"Failed to anonymize verdict: {str(e)}")

    def re_anonymize_verdict(self, verdict_id: int) -> Verdict:
        """
        Re-anonymize a verdict (useful if anonymization was incorrect).

        Args:
            verdict_id: ID of verdict to re-anonymize

        Returns:
            Updated verdict

        Raises:
            ValueError: If verdict not found
            AnonymizationError: If re-anonymization fails
        """
        verdict = self.db.query(Verdict).filter(Verdict.id == verdict_id).first()

        if not verdict:
            raise ValueError(f"Verdict with ID {verdict_id} not found")

        # Clear previous anonymization
        verdict.anonymized_text = None
        verdict.anonymization_report = None
        verdict.privacy_risk_level = PrivacyRiskLevel.LOW
        verdict.status = VerdictStatus.EXTRACTED
        self.db.commit()

        # Re-anonymize
        return self.anonymize_verdict(verdict_id)

    def get_anonymization_stats(self) -> Dict[str, Any]:
        """
        Get anonymization statistics.

        Returns:
            Dictionary with statistics
        """
        from sqlalchemy import func

        total_anonymized = self.db.query(func.count(Verdict.id)).filter(
            Verdict.status.in_([VerdictStatus.ANONYMIZED, VerdictStatus.ANALYZED,
                               VerdictStatus.ARTICLE_CREATED, VerdictStatus.PUBLISHED])
        ).scalar()

        risk_counts = {}
        for risk_level in PrivacyRiskLevel:
            count = self.db.query(func.count(Verdict.id)).filter(
                Verdict.privacy_risk_level == risk_level
            ).scalar()
            risk_counts[risk_level.value] = count

        pending_review = self.db.query(func.count(Verdict.id)).filter(
            Verdict.requires_manual_review == True,
            Verdict.review_notes.isnot(None)
        ).scalar()

        return {
            "total_anonymized": total_anonymized,
            "by_risk_level": risk_counts,
            "pending_manual_review": pending_review
        }
