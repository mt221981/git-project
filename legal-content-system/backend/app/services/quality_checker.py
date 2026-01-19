"""
Quality Checker Service - Article quality validation and scoring.

This service performs comprehensive quality checks on articles including:
- Content quality (word count, structure, headings)
- SEO optimization (keywords, meta description, title)
- Readability (sentence length, paragraph structure)
- E-E-A-T signals (expertise, authority, trust indicators)
- Privacy/PII detection
"""

import re
from dataclasses import dataclass
from typing import Optional
from enum import Enum


class QualityLevel(str, Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    NEEDS_IMPROVEMENT = "needs_improvement"
    POOR = "poor"


@dataclass
class QualityCheck:
    """Individual quality check result."""
    name: str
    passed: bool
    score: int  # 0-100
    message: str
    category: str
    severity: str = "info"  # info, warning, error


@dataclass
class QualityReport:
    """Complete quality report for an article."""
    checks: list[QualityCheck]
    content_score: int
    seo_score: int
    readability_score: int
    eeat_score: int
    overall_score: int
    level: QualityLevel
    all_passed: bool
    ready_to_publish: bool
    critical_issues: list[str]
    warnings: list[str]
    suggestions: list[str]


class QualityChecker:
    """Article quality checker with comprehensive validation."""

    # Minimum thresholds
    MIN_WORD_COUNT = 1200
    TARGET_WORD_COUNT = 1800
    MAX_WORD_COUNT = 3500
    MIN_H2_COUNT = 5
    MIN_FAQ_COUNT = 5
    MIN_META_DESC_LENGTH = 120
    MAX_META_DESC_LENGTH = 160
    MAX_TITLE_LENGTH = 60

    # PII patterns to detect
    PII_PATTERNS = [
        (r'\b\d{9}\b', "Israeli ID number"),
        (r'\b\d{3}-?\d{7}\b', "ID number format"),
        (r'\b05\d-?\d{7}\b', "Israeli mobile phone"),
        (r'\b0[2-9]-?\d{7}\b', "Israeli landline"),
        (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', "Email address"),
        (r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', "IP address"),
        (r'\b[0-9]{4}[- ]?[0-9]{4}[- ]?[0-9]{4}[- ]?[0-9]{4}\b', "Credit card number"),
    ]

    def check_all(self, article: dict) -> QualityReport:
        """
        Run all quality checks on an article.

        Args:
            article: Dictionary containing article data with keys:
                - title: Article title
                - meta_description: Meta description
                - content_html: HTML content
                - word_count: Number of words
                - faq_items: List of FAQ items
                - focus_keyword: Primary keyword
                - secondary_keywords: List of secondary keywords
                - excerpt: Article excerpt

        Returns:
            QualityReport with all check results and scores
        """
        checks = []

        # Content checks
        checks.extend(self._check_content(article))

        # SEO checks
        checks.extend(self._check_seo(article))

        # Readability checks
        checks.extend(self._check_readability(article))

        # E-E-A-T checks
        checks.extend(self._check_eeat(article))

        # PII/Privacy checks
        checks.extend(self._check_privacy(article))

        # Calculate scores
        content_checks = [c for c in checks if c.category == "content"]
        seo_checks = [c for c in checks if c.category == "seo"]
        readability_checks = [c for c in checks if c.category == "readability"]
        eeat_checks = [c for c in checks if c.category == "eeat"]

        content_score = self._calculate_category_score(content_checks)
        seo_score = self._calculate_category_score(seo_checks)
        readability_score = self._calculate_category_score(readability_checks)
        eeat_score = self._calculate_category_score(eeat_checks)

        # Overall score (weighted average)
        overall_score = int(
            content_score * 0.30 +
            seo_score * 0.30 +
            readability_score * 0.20 +
            eeat_score * 0.20
        )

        # Determine quality level
        level = self._determine_level(overall_score)

        # Identify issues
        critical_issues = [c.message for c in checks if c.severity == "error" and not c.passed]
        warnings = [c.message for c in checks if c.severity == "warning" and not c.passed]
        suggestions = [c.message for c in checks if c.severity == "info" and not c.passed]

        # Ready to publish if no critical issues and score >= 95 (updated quality standard)
        all_passed = all(c.passed for c in checks if c.severity == "error")
        ready_to_publish = all_passed and overall_score >= 95

        return QualityReport(
            checks=checks,
            content_score=content_score,
            seo_score=seo_score,
            readability_score=readability_score,
            eeat_score=eeat_score,
            overall_score=overall_score,
            level=level,
            all_passed=all(c.passed for c in checks),
            ready_to_publish=ready_to_publish,
            critical_issues=critical_issues,
            warnings=warnings,
            suggestions=suggestions
        )

    def _check_content(self, article: dict) -> list[QualityCheck]:
        """Content quality checks."""
        checks = []
        content = article.get("content_html", "")
        word_count = article.get("word_count", 0)

        # Word count check
        if word_count >= self.TARGET_WORD_COUNT:
            score = 100
        elif word_count >= self.MIN_WORD_COUNT:
            score = int(70 + (word_count - self.MIN_WORD_COUNT) / (self.TARGET_WORD_COUNT - self.MIN_WORD_COUNT) * 30)
        else:
            score = int(word_count / self.MIN_WORD_COUNT * 70)

        checks.append(QualityCheck(
            name="word_count",
            passed=word_count >= self.MIN_WORD_COUNT,
            score=score,
            message=f"Word count: {word_count} (minimum: {self.MIN_WORD_COUNT})",
            category="content",
            severity="error" if word_count < self.MIN_WORD_COUNT else "info"
        ))

        # H2 headings check
        h2_count = len(re.findall(r'<h2[^>]*>', content, re.IGNORECASE))
        h2_score = min(100, h2_count * 15)
        checks.append(QualityCheck(
            name="h2_structure",
            passed=h2_count >= self.MIN_H2_COUNT,
            score=h2_score,
            message=f"H2 headings: {h2_count} (recommended: {self.MIN_H2_COUNT}+)",
            category="content",
            severity="warning" if h2_count < self.MIN_H2_COUNT else "info"
        ))

        # H3 headings check (for depth)
        h3_count = len(re.findall(r'<h3[^>]*>', content, re.IGNORECASE))
        h3_score = min(100, 50 + h3_count * 10)
        checks.append(QualityCheck(
            name="h3_structure",
            passed=h3_count >= 3,
            score=h3_score,
            message=f"H3 headings: {h3_count} (recommended: 3+)",
            category="content",
            severity="info"
        ))

        # Paragraph count
        p_count = len(re.findall(r'<p[^>]*>', content, re.IGNORECASE))
        p_score = min(100, p_count * 5)
        checks.append(QualityCheck(
            name="paragraph_count",
            passed=p_count >= 10,
            score=p_score,
            message=f"Paragraphs: {p_count}",
            category="content",
            severity="info"
        ))

        # FAQ items check
        faq_items = article.get("faq_items", [])
        faq_count = len(faq_items) if faq_items else 0
        faq_score = min(100, faq_count * 12)
        checks.append(QualityCheck(
            name="faq_count",
            passed=faq_count >= self.MIN_FAQ_COUNT,
            score=faq_score,
            message=f"FAQ items: {faq_count} (recommended: {self.MIN_FAQ_COUNT}+)",
            category="content",
            severity="warning" if faq_count < self.MIN_FAQ_COUNT else "info"
        ))

        # List items (ul/ol)
        list_count = len(re.findall(r'<[uo]l[^>]*>', content, re.IGNORECASE))
        list_score = min(100, 50 + list_count * 15)
        checks.append(QualityCheck(
            name="list_usage",
            passed=list_count >= 2,
            score=list_score,
            message=f"Lists used: {list_count}",
            category="content",
            severity="info"
        ))

        return checks

    def _check_seo(self, article: dict) -> list[QualityCheck]:
        """SEO optimization checks."""
        checks = []
        title = article.get("title", "")
        meta_desc = article.get("meta_description", "")
        content = article.get("content_html", "")
        focus_keyword = article.get("focus_keyword", "").lower()
        secondary_keywords = article.get("secondary_keywords", []) or []

        # Title length check
        title_len = len(title)
        title_passed = title_len <= self.MAX_TITLE_LENGTH and title_len > 0
        title_score = 100 if title_passed else (50 if title_len > 0 else 0)
        checks.append(QualityCheck(
            name="title_length",
            passed=title_passed,
            score=title_score,
            message=f"Title length: {title_len} characters (max: {self.MAX_TITLE_LENGTH})",
            category="seo",
            severity="warning" if not title_passed else "info"
        ))

        # Meta description length check
        meta_len = len(meta_desc)
        meta_passed = self.MIN_META_DESC_LENGTH <= meta_len <= self.MAX_META_DESC_LENGTH
        if meta_passed:
            meta_score = 100
        elif meta_len > 0:
            meta_score = 50
        else:
            meta_score = 0
        checks.append(QualityCheck(
            name="meta_description_length",
            passed=meta_passed,
            score=meta_score,
            message=f"Meta description: {meta_len} characters ({self.MIN_META_DESC_LENGTH}-{self.MAX_META_DESC_LENGTH} recommended)",
            category="seo",
            severity="warning" if not meta_passed else "info"
        ))

        # Keyword in title check
        keyword_in_title = focus_keyword.lower() in title.lower() if focus_keyword else False
        checks.append(QualityCheck(
            name="keyword_in_title",
            passed=keyword_in_title,
            score=100 if keyword_in_title else 0,
            message="Focus keyword in title" if keyword_in_title else "Focus keyword missing from title",
            category="seo",
            severity="warning" if not keyword_in_title else "info"
        ))

        # Keyword in meta description
        keyword_in_meta = focus_keyword.lower() in meta_desc.lower() if focus_keyword else False
        checks.append(QualityCheck(
            name="keyword_in_meta",
            passed=keyword_in_meta,
            score=100 if keyword_in_meta else 0,
            message="Focus keyword in meta description" if keyword_in_meta else "Focus keyword missing from meta description",
            category="seo",
            severity="info"
        ))

        # Keyword in first paragraph
        first_p_match = re.search(r'<p[^>]*>(.*?)</p>', content, re.IGNORECASE | re.DOTALL)
        first_p = first_p_match.group(1) if first_p_match else ""
        keyword_in_first_p = focus_keyword.lower() in first_p.lower() if focus_keyword else False
        checks.append(QualityCheck(
            name="keyword_in_intro",
            passed=keyword_in_first_p,
            score=100 if keyword_in_first_p else 0,
            message="Focus keyword in introduction" if keyword_in_first_p else "Focus keyword missing from introduction",
            category="seo",
            severity="warning" if not keyword_in_first_p else "info"
        ))

        # Keyword density (aim for 1-2%)
        content_text = re.sub(r'<[^>]+>', '', content).lower()
        word_count = len(content_text.split())
        if focus_keyword and word_count > 0:
            keyword_count = content_text.count(focus_keyword.lower())
            density = (keyword_count / word_count) * 100
            density_passed = 0.5 <= density <= 2.5
            density_score = 100 if density_passed else (50 if density > 0 else 0)
        else:
            density = 0
            density_passed = False
            density_score = 0
        checks.append(QualityCheck(
            name="keyword_density",
            passed=density_passed,
            score=density_score,
            message=f"Keyword density: {density:.1f}% (0.5-2.5% recommended)",
            category="seo",
            severity="info"
        ))

        # Secondary keywords usage
        if secondary_keywords:
            used_secondary = sum(1 for kw in secondary_keywords if kw.lower() in content_text)
            secondary_ratio = used_secondary / len(secondary_keywords) if secondary_keywords else 0
            secondary_score = int(secondary_ratio * 100)
        else:
            secondary_score = 50
        checks.append(QualityCheck(
            name="secondary_keywords",
            passed=secondary_score >= 70,
            score=secondary_score,
            message=f"Secondary keywords coverage: {secondary_score}%",
            category="seo",
            severity="info"
        ))

        # Slug check - for Hebrew content, just verify slug exists and is non-empty
        # For English focus keywords, verify keyword is in slug
        slug = article.get("slug", "")
        if focus_keyword:
            # Check if focus keyword contains Hebrew characters
            has_hebrew = any('\u0590' <= char <= '\u05FF' for char in focus_keyword)
            if has_hebrew:
                # For Hebrew keywords, just verify slug exists, is non-empty, and uses Latin chars
                slug_passed = bool(slug) and len(slug) >= 5 and slug.replace("-", "").isascii()
            else:
                # For English keywords, verify keyword is in slug
                slug_passed = focus_keyword.lower().replace(" ", "-") in slug.lower()
        else:
            slug_passed = bool(slug)
        checks.append(QualityCheck(
            name="slug_optimization",
            passed=slug_passed,
            score=100 if slug_passed else 50,
            message="URL slug is optimized" if slug_passed else "URL slug could be improved",
            category="seo",
            severity="info"
        ))

        return checks

    def _check_readability(self, article: dict) -> list[QualityCheck]:
        """Readability checks."""
        checks = []
        content = article.get("content_html", "")

        # Strip HTML tags for text analysis
        text = re.sub(r'<[^>]+>', '', content)

        # Average sentence length
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        if sentences:
            avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences)
            sentence_passed = avg_sentence_length <= 25
            sentence_score = 100 if avg_sentence_length <= 20 else (70 if avg_sentence_length <= 25 else 40)
        else:
            avg_sentence_length = 0
            sentence_passed = False
            sentence_score = 0
        checks.append(QualityCheck(
            name="sentence_length",
            passed=sentence_passed,
            score=sentence_score,
            message=f"Average sentence length: {avg_sentence_length:.1f} words (max 25 recommended)",
            category="readability",
            severity="info"
        ))

        # Paragraph length (check for long paragraphs)
        paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', content, re.IGNORECASE | re.DOTALL)
        long_paragraphs = sum(1 for p in paragraphs if len(p.split()) > 150)
        paragraph_passed = long_paragraphs == 0
        paragraph_score = 100 if long_paragraphs == 0 else max(0, 100 - long_paragraphs * 20)
        checks.append(QualityCheck(
            name="paragraph_length",
            passed=paragraph_passed,
            score=paragraph_score,
            message=f"Long paragraphs (150+ words): {long_paragraphs}",
            category="readability",
            severity="warning" if not paragraph_passed else "info"
        ))

        # Transition words (Hebrew)
        transition_words = [
            'לכן', 'אולם', 'עם זאת', 'בנוסף', 'כמו כן', 'לעומת זאת',
            'בהתאם', 'למרות', 'יתרה מזאת', 'בסיכום', 'לסיכום', 'ראשית',
            'שנית', 'לבסוף', 'מכאן', 'אם כן', 'כאמור', 'למעשה'
        ]
        transition_count = sum(1 for word in transition_words if word in text)
        transition_score = min(100, transition_count * 10)
        checks.append(QualityCheck(
            name="transition_words",
            passed=transition_count >= 5,
            score=transition_score,
            message=f"Transition words used: {transition_count}",
            category="readability",
            severity="info"
        ))

        # Reading time check
        reading_time = article.get("reading_time_minutes", 0)
        reading_passed = 5 <= reading_time <= 15
        reading_score = 100 if reading_passed else 70
        checks.append(QualityCheck(
            name="reading_time",
            passed=reading_passed,
            score=reading_score,
            message=f"Reading time: {reading_time} minutes",
            category="readability",
            severity="info"
        ))

        return checks

    def _check_eeat(self, article: dict) -> list[QualityCheck]:
        """E-E-A-T (Experience, Expertise, Authoritativeness, Trust) checks."""
        checks = []
        content = article.get("content_html", "")
        text = re.sub(r'<[^>]+>', '', content).lower()

        # Legal citations (expertise indicator)
        law_patterns = [
            r'חוק\s+\S+',
            r'סעיף\s+\d+',
            r'תקנה\s+\d+',
            r'פקודת\s+\S+',
        ]
        law_citations = sum(len(re.findall(p, text)) for p in law_patterns)
        law_score = min(100, law_citations * 15)
        checks.append(QualityCheck(
            name="legal_citations",
            passed=law_citations >= 3,
            score=law_score,
            message=f"Legal citations found: {law_citations}",
            category="eeat",
            severity="warning" if law_citations < 2 else "info"
        ))

        # Precedent citations (authority indicator)
        precedent_patterns = [
            r'ע"א\s+\d+',
            r'ע"ע\s+\d+',
            r'בג"ץ\s+\d+',
            r'ת"א\s+\d+',
            r'תיק\s+\d+',
        ]
        precedent_citations = sum(len(re.findall(p, text)) for p in precedent_patterns)
        precedent_score = min(100, 50 + precedent_citations * 15)
        checks.append(QualityCheck(
            name="precedent_citations",
            passed=precedent_citations >= 1,
            score=precedent_score,
            message=f"Precedent citations found: {precedent_citations}",
            category="eeat",
            severity="info"
        ))

        # Disclaimer presence (trust indicator)
        disclaimer_keywords = ['אין באמור', 'אינו מהווה ייעוץ', 'יש להיוועץ', 'מומלץ להתייעץ', 'אין לראות']
        has_disclaimer = any(kw in text for kw in disclaimer_keywords)
        checks.append(QualityCheck(
            name="disclaimer",
            passed=has_disclaimer,
            score=100 if has_disclaimer else 0,
            message="Legal disclaimer present" if has_disclaimer else "Legal disclaimer missing",
            category="eeat",
            severity="error" if not has_disclaimer else "info"
        ))

        # CTA presence (engagement indicator)
        cta_keywords = ['צרו קשר', 'פנו אלינו', 'התקשרו', 'לייעוץ', 'לפגישה']
        has_cta = any(kw in text for kw in cta_keywords)
        checks.append(QualityCheck(
            name="call_to_action",
            passed=has_cta,
            score=100 if has_cta else 50,
            message="Call to action present" if has_cta else "Consider adding a call to action",
            category="eeat",
            severity="info"
        ))

        # Expert terminology usage
        expert_terms = [
            'פיצויים', 'נזק', 'אחריות', 'רשלנות', 'התיישנות', 'סמכות',
            'ערעור', 'פסק דין', 'בית משפט', 'תובע', 'נתבע', 'עדות'
        ]
        terms_used = sum(1 for term in expert_terms if term in text)
        terms_score = min(100, terms_used * 10)
        checks.append(QualityCheck(
            name="expert_terminology",
            passed=terms_used >= 5,
            score=terms_score,
            message=f"Legal terms used: {terms_used}",
            category="eeat",
            severity="info"
        ))

        return checks

    def _check_privacy(self, article: dict) -> list[QualityCheck]:
        """Privacy and PII detection checks."""
        checks = []
        content = article.get("content_html", "")
        title = article.get("title", "")
        meta_desc = article.get("meta_description", "")

        # Check all text for PII
        all_text = f"{title} {meta_desc} {content}"

        pii_found = []
        for pattern, description in self.PII_PATTERNS:
            matches = re.findall(pattern, all_text)
            if matches:
                pii_found.append(f"{description}: {len(matches)} found")

        pii_clean = len(pii_found) == 0
        checks.append(QualityCheck(
            name="pii_check",
            passed=pii_clean,
            score=0 if not pii_clean else 100,
            message="No PII detected" if pii_clean else f"PII detected: {'; '.join(pii_found)}",
            category="privacy",
            severity="error" if not pii_clean else "info"
        ))

        # Check for placeholder markers that weren't replaced
        placeholder_patterns = [
            r'\[.*הוסר.*\]',
            r'\[.*REMOVED.*\]',
            r'פלוני|אלמוני',
            r'XXX',
        ]
        unresolved_placeholders = sum(
            len(re.findall(p, all_text, re.IGNORECASE))
            for p in placeholder_patterns
        )
        placeholder_check = unresolved_placeholders <= 5  # Some placeholders are expected
        checks.append(QualityCheck(
            name="placeholder_check",
            passed=placeholder_check,
            score=100 if placeholder_check else 50,
            message=f"Anonymization placeholders: {unresolved_placeholders}",
            category="privacy",
            severity="info"
        ))

        return checks

    def _calculate_category_score(self, checks: list[QualityCheck]) -> int:
        """Calculate average score for a category of checks."""
        if not checks:
            return 0
        return int(sum(c.score for c in checks) / len(checks))

    def _determine_level(self, score: int) -> QualityLevel:
        """Determine quality level based on overall score."""
        if score >= 85:
            return QualityLevel.EXCELLENT
        elif score >= 70:
            return QualityLevel.GOOD
        elif score >= 50:
            return QualityLevel.NEEDS_IMPROVEMENT
        else:
            return QualityLevel.POOR

    def to_dict(self, report: QualityReport) -> dict:
        """Convert QualityReport to dictionary for JSON serialization."""
        return {
            "checks": [
                {
                    "name": c.name,
                    "passed": c.passed,
                    "score": c.score,
                    "message": c.message,
                    "category": c.category,
                    "severity": c.severity
                }
                for c in report.checks
            ],
            "content_score": report.content_score,
            "seo_score": report.seo_score,
            "readability_score": report.readability_score,
            "eeat_score": report.eeat_score,
            "overall_score": report.overall_score,
            "level": report.level.value,
            "all_passed": report.all_passed,
            "ready_to_publish": report.ready_to_publish,
            "critical_issues": report.critical_issues,
            "warnings": report.warnings,
            "suggestions": report.suggestions
        }
