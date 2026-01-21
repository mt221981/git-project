"""ArticleGenerator - Core service for generating SEO-optimized legal articles using Claude API."""

import json
import re
import random
from typing import Dict, Any
from anthropic import Anthropic
from app.config import settings
from app.utils.json_repair import safe_parse_json
from app.services.quality_checker import QualityChecker


class ArticleGeneratorError(Exception):
    """Exception raised when article generation fails."""
    pass


class ArticleGenerator:
    """
    Core service for generating SEO-optimized articles from analyzed verdicts.

    Creates comprehensive, E-E-A-T compliant articles with:
    - Proper SEO structure and meta tags
    - Structured H2 sections
    - FAQ section with Schema.org markup
    - Common mistakes section
    - Legal disclaimers
    - All written as experienced Israeli lawyer
    """

    SYSTEM_PROMPT = """אתה עורך דין ישראלי מנוסה הכותב מאמרים משפטיים מקצועיים לאתר SEO.

**חשוב מאוד:** המאמר חייב להתבסס על פסק הדין שיסופק לך - לא מאמר גנרי!

## דרישות תוכן:
1. השתמש בעובדות, בנימוקים ובהחלטה מפסק הדין הספציפי
2. צטט 6-8 סעיפי חוק מדויקים (סעיף X לחוק Y)
3. הסבר את העקרונות המשפטיים שבית המשפט יישם
4. תובנות מעשיות - מה אפשר ללמוד מפסק הדין

## דרישות SEO:
- אורך: 1800-2200 מילים (חובה!)
- מבנה: H1 + 7 H2 + 5 H3
- מילת מפתח: 10-15 הזכרות טבעיות (1-2% צפיפות)
- FAQ: 8-10 שאלות רלוונטיות לפסק הדין הספציפי

## דרישות עיצוב:
- פסקאות: 3-5 משפטים, עד 150 מילים
- משפטים: עד 25 מילים בממוצע
- רשימות: 2+ רשימות ממוספרות או עם תבליטים
- מילות קישור: השתמש ב-8+ (לכן, אולם, בנוסף, כמו כן, למרות, יתרה מזאת, ראשית, שנית, לבסוף)

## E-E-A-T חובה:
- מונחים משפטיים: השתמש ב-10+ מונחים (פיצויים, נזק, אחריות, רשלנות, סמכות, ערעור, פסק דין, בית משפט, תובע, נתבע, התיישנות, עדות)
- disclaimer בסוף: "אין באמור לעיל משום ייעוץ משפטי. מומלץ להתייעץ עם עורך דין מומחה בתחום."
- CTA בסוף: "לייעוץ משפטי בנושא, צרו קשר עם עורך דין מומחה."

## כותרת (title):
- מקסימום 55 תווים
- חובה לכלול את מילת המפתח
- ללא קיצורים או מילים חתוכות

## meta_description:
- 120-160 תווים בדיוק
- חובה לכלול את מילת המפתח

## איסורים:
- אסור מספרי תיקים (ע"א/ת"א)
- אסור שמות בעלי דין
- אסור "משרדנו/לקוחותינו"
- אסור "פסק דין חדשני/תקדימי/פורץ דרך"

החזר JSON בלבד:
{"title", "meta_title", "meta_description", "content_html", "excerpt", "focus_keyword", "secondary_keywords", "faq_items", "external_links", "category_primary", "tags"}
"""

    def __init__(self, api_key: str = None):
        """
        Initialize ArticleGenerator.

        Args:
            api_key: Anthropic API key (uses settings.ANTHROPIC_API_KEY if not provided)
        """
        self.api_key = api_key or settings.ANTHROPIC_API_KEY
        if not self.api_key or self.api_key == "your-key-here":
            raise ValueError("ANTHROPIC_API_KEY not configured. Set it in .env file.")

        self.client = Anthropic(api_key=self.api_key)

    def generate(self, verdict_data: Dict[str, Any], max_retries: int = 1, improvement_hints: str = None) -> Dict[str, Any]:
        """
        Generate SEO-optimized article from analyzed verdict data.

        Args:
            verdict_data: Dictionary containing analyzed verdict data from VerdictAnalyzer
            max_retries: Maximum number of retry attempts on failure
            improvement_hints: Optional specific improvement instructions from quality scoring

        Returns:
            Dictionary with complete article data:
            {
                "title": str,  # max 60 chars
                "meta_description": str,  # max 155 chars
                "slug": str,
                "excerpt": str,
                "focus_keyword": str,
                "secondary_keywords": List[str],  # 5-8 items
                "long_tail_keywords": List[str],  # 8-12 items
                "content_html": str,  # 1500-2500 words with full structure
                "word_count": int,
                "reading_time_minutes": int,
                "faq_items": List[Dict],  # [{question, answer}, ...]
                "common_mistakes": List[Dict],  # [{mistake, explanation}, ...]
                "category_primary": str,
                "tags": List[str],
                "featured_image_prompt": str,
                "featured_image_alt": str,
                "schema_article": Dict,  # JSON-LD
                "schema_faq": Dict  # JSON-LD
            }

        Raises:
            ArticleGeneratorError: If generation fails after all retries
        """
        if not verdict_data:
            raise ArticleGeneratorError("Verdict data cannot be empty")

        last_error = None

        for attempt in range(max_retries + 1):
            try:
                # Build prompt (with improvement hints if provided)
                user_prompt = self._build_prompt(verdict_data, improvement_hints)

                # Call Claude API
                response = self.client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=16384,  # Increased for complete article with all fields
                    temperature=0.7,  # Some creativity for natural writing
                    system=self.SYSTEM_PROMPT,
                    messages=[{
                        "role": "user",
                        "content": user_prompt
                    }]
                )

                # Extract text from response and log stop reason
                response_text = response.content[0].text
                stop_reason = response.stop_reason
                usage = response.usage
                print(f"[ArticleGenerator] API response - stop_reason: {stop_reason}, input_tokens: {usage.input_tokens}, output_tokens: {usage.output_tokens}, response_length: {len(response_text)}")

                # Parse JSON with repair logic
                result = self._parse_response(response_text)

                # Validate and enrich
                enriched_result = self._validate_and_enrich(result, verdict_data)

                # CRITICAL VALIDATION: Check word count (lowered to 700 for testing)
                word_count = enriched_result.get("word_count", 0)
                if word_count < 700:
                    print(f"[ArticleGenerator] WARNING: Article too short - {word_count} words (minimum: 700)")

                    # If we have retries left, try again with stronger emphasis
                    if attempt < max_retries:
                        print(f"[ArticleGenerator] Retrying with stronger word count emphasis...")
                        # Force retry with modified prompt on next iteration
                        raise ArticleGeneratorError(
                            f"Article too short: {word_count} words (minimum: 700). Retrying with emphasis."
                        )
                    else:
                        # Last attempt failed - log warning but return result
                        print(f"[ArticleGenerator] WARNING: Final attempt produced only {word_count} words (target: 1800-2200)")

                return enriched_result

            except (ArticleGeneratorError, json.JSONDecodeError) as e:
                last_error = e
                if attempt < max_retries:
                    print(f"[ArticleGenerator] Attempt {attempt + 1} failed: {str(e)[:100]}. Retrying...")
                    continue

            except Exception as e:
                last_error = e
                if attempt < max_retries:
                    print(f"[ArticleGenerator] Attempt {attempt + 1} failed: {str(e)[:100]}. Retrying...")
                    continue

        raise ArticleGeneratorError(f"Article generation failed after {max_retries + 1} attempts: {str(last_error)}")

    def _build_prompt(self, verdict_data: Dict[str, Any], improvement_hints: str = None) -> str:
        """Build comprehensive prompt with actual verdict content."""

        legal_area = verdict_data.get("legal_area") or "משפט אזרחי"
        focus_keyword = verdict_data.get("focus_keyword") or legal_area

        # Format key facts
        key_facts = verdict_data.get("key_facts", [])
        facts_text = "\n".join(f"- {f}" for f in key_facts[:8]) if key_facts else "לא סופקו"

        # Format legal principles
        principles = verdict_data.get("legal_principles", [])
        principles_text = "\n".join(f"- {p}" for p in principles[:5]) if principles else "לא סופקו"

        # Format relevant laws
        laws = verdict_data.get("relevant_laws", [])
        laws_text = ""
        if laws:
            for law in laws[:8]:
                if isinstance(law, dict):
                    laws_text += f"- {law.get('name', '')} {law.get('section', '')}\n"
                else:
                    laws_text += f"- {law}\n"
        else:
            laws_text = "לא סופקו"

        # Format insights
        insights = verdict_data.get("practical_insights", [])
        insights_text = "\n".join(f"- {i}" for i in insights[:5]) if insights else "לא סופקו"

        # Get verdict text
        verdict_text = verdict_data.get("verdict_text", "")[:5000]
        summary = verdict_data.get("summary", "")

        # Compensation
        comp = verdict_data.get("compensation_amount")
        comp_text = f"\n## פיצוי שנפסק: {comp:,.0f} ש\"ח" if comp else ""

        hint_section = f"\n\n**שיפורים נדרשים:** {improvement_hints}" if improvement_hints else ""

        return f"""כתוב מאמר משפטי SEO בעברית המבוסס על פסק הדין הבא:{hint_section}

## מילת מפתח: {focus_keyword}
## תחום: {legal_area}{comp_text}

## תקציר:
{summary if summary else "ראה עובדות למטה"}

## עובדות מרכזיות:
{facts_text}

## עקרונות משפטיים:
{principles_text}

## חוקים וסעיפים (חובה לצטט!):
{laws_text}

## תובנות מעשיות:
{insights_text}

## קטע מפסק הדין:
{verdict_text if verdict_text else "לא סופק"}

---
## דרישות חובה לציון 80+:

### תוכן:
- 1800-2200 מילים
- 7 כותרות H2 + 5 כותרות H3
- 16+ פסקאות (3-5 משפטים כל אחת)
- 8+ שאלות FAQ
- 2+ רשימות

### SEO:
- כותרת עד 55 תווים עם "{focus_keyword}"
- meta_description: 120-160 תווים עם "{focus_keyword}"
- "{focus_keyword}" בפסקה הראשונה
- 10-15 הזכרות טבעיות של מילת המפתח

### קריאות:
- משפטים קצרים (עד 25 מילים)
- פסקאות עד 150 מילים
- 8+ מילות קישור: לכן, אולם, בנוסף, כמו כן, למרות, יתרה מזאת, ראשית, שנית, לבסוף

### E-E-A-T (חובה!):
- 6+ ציטוטי חוק (סעיף X לחוק Y)
- 10+ מונחים משפטיים: פיצויים, נזק, אחריות, רשלנות, סמכות, ערעור, פסק דין, בית משפט, תובע, נתבע
- בסוף המאמר disclaimer: "אין באמור לעיל משום ייעוץ משפטי. מומלץ להתייעץ עם עורך דין."
- בסוף המאמר CTA: "לייעוץ משפטי, צרו קשר."

### איסורים:
- אסור "פסק דין חדשני/תקדימי/פורץ דרך"
- אסור מספרי תיקים

החזר JSON בלבד."""

    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """Parse Claude's JSON response with robust repair logic."""
        result = safe_parse_json(response_text)

        if result is None:
            # Log the problematic response for debugging
            print(f"[ArticleGenerator] Failed to parse JSON. First 500 chars: {response_text[:500]}")
            raise ArticleGeneratorError(
                "Failed to parse Claude response as JSON after repair attempts"
            )

        return result

    def _validate_and_enrich(self, result: Dict[str, Any], verdict_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and enrich the article data."""
        # Calculate word count from HTML
        if "content_html" in result:
            text = re.sub(r'<[^>]+>', '', result["content_html"])
            result["word_count"] = len(text.split())
            result["reading_time_minutes"] = max(1, result["word_count"] // 200)

        # Generate Schema.org JSON-LD
        result["schema_article"] = self._generate_article_schema(result, verdict_data)
        result["schema_faq"] = self._generate_faq_schema(result.get("faq_items", []))

        # Ensure all required fields
        required_fields = {
            "title": "",
            "meta_description": "",
            "slug": "",
            "excerpt": "",
            "focus_keyword": "",
            "secondary_keywords": [],
            "long_tail_keywords": [],
            "content_html": "",
            "word_count": 0,
            "reading_time_minutes": 0,
            "faq_items": [],
            "common_mistakes": [],
            "category_primary": verdict_data.get("legal_area", "משפטי"),
            "tags": [],
            "featured_image_prompt": "",
            "featured_image_alt": "",
            "author_name": self._get_random_author()
        }

        for field, default in required_fields.items():
            if field not in result:
                result[field] = default

        return result

    # Authors list for random selection
    AUTHORS = [
        "עו\"ד משה טייב",
        "עו\"ד מיכאל לב"
    ]

    def _get_random_author(self) -> str:
        """Get a random author name from the predefined list."""
        return random.choice(self.AUTHORS)

    def _generate_article_schema(self, article: Dict[str, Any], verdict_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Schema.org Article JSON-LD."""
        author_name = article.get("author_name") or self._get_random_author()
        return {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": article.get("title", ""),
            "description": article.get("meta_description", ""),
            "author": {
                "@type": "Person",
                "name": author_name,
                "jobTitle": "עורך דין"
            },
            "publisher": {
                "@type": "Organization",
                "name": "לב-טייב עורכי דין",
                "url": "https://lt-law.co.il"
            },
            "datePublished": verdict_data.get("verdict_date", ""),
            "articleBody": re.sub(r'<[^>]+>', '', article.get("content_html", "")),
            "wordCount": article.get("word_count", 0),
            "inLanguage": "he",
            "about": {
                "@type": "Thing",
                "name": verdict_data.get("legal_area", "")
            }
        }

    def _generate_faq_schema(self, faq_items: list) -> Dict[str, Any]:
        """Generate Schema.org FAQPage JSON-LD."""
        if not faq_items:
            return {}

        return {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": item.get("question", ""),
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": item.get("answer", "")
                    }
                }
                for item in faq_items
            ]
        }

    def calculate_scores(self, article_content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate quality scores for an article using QualityChecker.

        Args:
            article_content: Article content dictionary

        Returns:
            Dictionary with quality scores:
            {
                "content_score": int,
                "seo_score": int,
                "readability_score": int,
                "eeat_score": int,
                "overall_score": int,
                "quality_issues": list[str]
            }
        """
        try:
            # Log what we're receiving
            print(f"[ArticleGenerator] calculate_scores called with keys: {list(article_content.keys())}")
            print(f"[ArticleGenerator] Has content_html: {'content_html' in article_content}")
            print(f"[ArticleGenerator] Has word_count: {'word_count' in article_content}")
            print(f"[ArticleGenerator] Has title: {'title' in article_content}")
            print(f"[ArticleGenerator] Has focus_keyword: {'focus_keyword' in article_content}")

            checker = QualityChecker()
            report = checker.check_all(article_content)

            print(f"[ArticleGenerator] QualityChecker returned scores:")
            print(f"  Content: {report.content_score}/100")
            print(f"  SEO: {report.seo_score}/100")
            print(f"  Readability: {report.readability_score}/100")
            print(f"  E-E-A-T: {report.eeat_score}/100")
            print(f"  Overall: {report.overall_score}/100")

            # Convert string issues to dict format for Pydantic schema compatibility
            quality_issues = []
            for issue in report.critical_issues:
                quality_issues.append({"type": "critical", "message": issue})
            for issue in report.warnings:
                quality_issues.append({"type": "warning", "message": issue})

            return {
                "content_score": report.content_score,
                "seo_score": report.seo_score,
                "readability_score": report.readability_score,
                "eeat_score": report.eeat_score,
                "overall_score": report.overall_score,
                "quality_issues": quality_issues
            }

        except Exception as e:
            # Log full traceback for debugging
            import traceback
            print(f"[ArticleGenerator] EXCEPTION in calculate_scores:")
            print(traceback.format_exc())

            # Return default scores if calculation fails
            return {
                "content_score": 70,
                "seo_score": 70,
                "readability_score": 70,
                "eeat_score": 70,
                "overall_score": 70,
                "quality_issues": [{"type": "error", "message": f"Failed to calculate scores: {str(e)}"}]
            }
