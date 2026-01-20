"""Verdict analysis service using Claude API."""

import json
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.verdict import Verdict, VerdictStatus
from app.services.verdict_analyzer import VerdictAnalyzer, AnalysisError as AnalyzerError


class AnalysisError(Exception):
    """Exception raised when analysis fails."""
    pass


class AnalysisService:
    """
    Service for analyzing legal verdicts using Claude API.

    Extracts:
    - Key facts
    - Legal questions
    - Legal principles
    - Compensation details
    - Relevant laws
    - Cited precedents
    - Practical insights
    """

    def __init__(self, db: Session, analyzer: Optional[VerdictAnalyzer] = None):
        """
        Initialize analysis service.

        Args:
            db: Database session
            analyzer: Optional VerdictAnalyzer instance (creates default if not provided)
        """
        self.db = db
        self.analyzer = analyzer or VerdictAnalyzer()

    def analyze_text(self, text: str) -> Dict[str, Any]:
        """
        Analyze verdict text using Claude API.

        Args:
            text: Verdict text to analyze (should be anonymized)

        Returns:
            Dictionary with analysis results

        Raises:
            AnalysisError: If analysis fails
        """
        try:
            # Use new VerdictAnalyzer service
            result = self.analyzer.analyze(text)
            return result

        except AnalyzerError as e:
            raise AnalysisError(f"Analysis failed: {str(e)}")
        except Exception as e:
            raise AnalysisError(f"Analysis failed: {str(e)}")

    def analyze_verdict(self, verdict_id: int) -> Verdict:
        """
        Analyze a verdict and update it in the database.

        Args:
            verdict_id: ID of verdict to analyze

        Returns:
            Updated verdict

        Raises:
            ValueError: If verdict not found or in wrong status
            AnalysisError: If analysis fails
        """
        verdict = self.db.query(Verdict).filter(Verdict.id == verdict_id).first()

        if not verdict:
            raise ValueError(f"Verdict with ID {verdict_id} not found")

        # Check if verdict has been extracted (ANALYZING is also allowed - set by endpoint before background task)
        if verdict.status not in [VerdictStatus.EXTRACTED, VerdictStatus.ANALYZED, VerdictStatus.ANALYZING]:
            raise ValueError(
                f"Verdict must be extracted before analysis. Current status: {verdict.status}"
            )

        # Update status to analyzing (only if not already set by endpoint)
        if verdict.status != VerdictStatus.ANALYZING:
            verdict.status = VerdictStatus.ANALYZING
            self.db.commit()

        try:
            # Set initial progress
            verdict.processing_progress = 35
            verdict.processing_message = "מתחיל ניתוח משפטי..."
            self.db.commit()

            # Use cleaned or original text for analysis (skip anonymization)
            text_to_analyze = verdict.cleaned_text or verdict.original_text

            # Step 1: Extract legal basis (35-45%)
            verdict.processing_progress = 40
            verdict.processing_message = "מחלץ בסיס משפטי וסעיפי חוק..."
            self.db.commit()

            # Perform analysis
            result = self.analyze_text(text_to_analyze)

            # Step 2: Extract key issues (45-55%)
            verdict.processing_progress = 50
            verdict.processing_message = "מזהה נושאים מרכזיים..."
            self.db.commit()

            # Update verdict with analysis results
            verdict.key_facts = result.get("key_facts", [])
            verdict.legal_questions = result.get("legal_questions", [])
            verdict.legal_principles = result.get("legal_principles", [])

            # Step 3: Extract decision (55-60%)
            verdict.processing_progress = 55
            verdict.processing_message = "מחלץ החלטת בית המשפט..."
            self.db.commit()

            # Update compensation if found in analysis
            if result.get("compensation_amount"):
                verdict.compensation_amount = result["compensation_amount"]

            if result.get("compensation_breakdown"):
                verdict.compensation_breakdown = result["compensation_breakdown"]

            # Update legal references
            if result.get("relevant_laws"):
                verdict.relevant_laws = result["relevant_laws"]

            if result.get("precedents_cited"):
                verdict.precedents_cited = result["precedents_cited"]

            # Step 4: Generate keywords and finalize (60-65%)
            verdict.processing_progress = 60
            verdict.processing_message = "מייצר מילות מפתח SEO..."
            self.db.commit()

            # Update practical insights
            if result.get("practical_insights"):
                verdict.practical_insights = result["practical_insights"]

            # Mark as analyzed
            verdict.status = VerdictStatus.ANALYZED
            verdict.processing_progress = 65
            verdict.processing_message = "ניתוח משפטי הושלם בהצלחה"
            self.db.commit()
            self.db.refresh(verdict)

            return verdict

        except Exception as e:
            # Revert status on error
            verdict.status = VerdictStatus.FAILED
            verdict.processing_progress = 35
            verdict.processing_message = f"שגיאה בניתוח: {str(e)}"
            verdict.review_notes = f"Analysis failed: {str(e)}"
            self.db.commit()
            raise AnalysisError(f"Failed to analyze verdict: {str(e)}")

    def re_analyze_verdict(self, verdict_id: int) -> Verdict:
        """
        Re-analyze a verdict (useful if analysis needs updating).

        Args:
            verdict_id: ID of verdict to re-analyze

        Returns:
            Updated verdict

        Raises:
            ValueError: If verdict not found
            AnalysisError: If re-analysis fails
        """
        verdict = self.db.query(Verdict).filter(Verdict.id == verdict_id).first()

        if not verdict:
            raise ValueError(f"Verdict with ID {verdict_id} not found")

        # Clear previous analysis
        verdict.key_facts = None
        verdict.legal_questions = None
        verdict.legal_principles = None
        verdict.practical_insights = None
        verdict.status = VerdictStatus.ANONYMIZED
        self.db.commit()

        # Re-analyze
        return self.analyze_verdict(verdict_id)

    def get_analysis_stats(self) -> Dict[str, Any]:
        """
        Get analysis statistics.

        Returns:
            Dictionary with statistics
        """
        from sqlalchemy import func

        total_analyzed = self.db.query(func.count(Verdict.id)).filter(
            Verdict.status.in_([
                VerdictStatus.ANALYZED,
                VerdictStatus.ARTICLE_CREATED,
                VerdictStatus.PUBLISHED
            ])
        ).scalar()

        # Count verdicts with compensation
        with_compensation = self.db.query(func.count(Verdict.id)).filter(
            Verdict.compensation_amount.isnot(None)
        ).scalar()

        # Average compensation (excluding nulls)
        avg_compensation = self.db.query(
            func.avg(Verdict.compensation_amount)
        ).filter(
            Verdict.compensation_amount.isnot(None)
        ).scalar()

        # Count by legal area
        legal_areas = self.db.query(
            Verdict.legal_area,
            func.count(Verdict.id)
        ).filter(
            Verdict.legal_area.isnot(None)
        ).group_by(Verdict.legal_area).all()

        legal_area_counts = {area: count for area, count in legal_areas if area}

        return {
            "total_analyzed": total_analyzed,
            "with_compensation": with_compensation,
            "average_compensation": float(avg_compensation) if avg_compensation else None,
            "by_legal_area": legal_area_counts
        }
