"""ArticleGenerator - Core service for generating SEO-optimized legal articles using Claude API."""

import json
import re
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

    SYSTEM_PROMPT = """אתה עורך דין ישראלי מנוסה ומומחה בכתיבת תוכן משפטי SEO-אופטימלי ברמה הגבוהה ביותר.

## דרישות מחמירות (חובה מוחלטת!):

### אורך (קריטי ביותר!):
**1800-2200 מילים - לא פחות מ-1800 מילים בשום אופן!**

### תוכן משפטי מקצועי:
1. **6-8 ציטוטים חוקיים** - סעיפי חוק מדויקים עם מספרים
2. **2-3 תקדימים** - שמות תיקים מלאים (דוגמה: "ע"א 123/45 פלוני נ' אלמוני")
3. **12+ מונחים משפטיים מקצועיים** (נטל הוכחה, סעד הצהרתי, השתק, כוח ראיה, וכו')

### מבנה SEO:
1. **7-8 כותרות H2** - כל H2 עם 150-250 מילים תחתיו
2. **10-12 כותרות H3** - רובן ב-FAQ
3. **8-10 שאלות FAQ** - כל שאלה H3 עם תשובה מפורטת
4. **5-6 רשימות** - bullet points או מספרים
5. **צפיפות מילות מפתח: 1.0-1.2%** (לא יותר, לא פחות!)
6. **קישורים פנימיים**: 3-5 קישורים למאמרים קשורים (דוגמה: <a href="/תאונות-דרכים">תאונות דרכים</a>)
7. **קישורים חיצוניים**: 2-3 קישורים לאתרים אמינים (nevo.co.il, gov.il, וכו')

### קריאות:
1. **משפטים קצרים**: 15-18 מילים בממוצע (לא יותר!)
2. **פסקאות קצרות**: 2-3 שורות מקסימום
3. **10-12 מילות מעבר** (לכן, בנוסף, יתר על כן, מאידך, וכו')

### מבנה המאמר (חובה):
1. **H1** - כותרת (50-60 תווים)
2. **פתיחה** (3-4 פסקאות, 150-200 מילים) - **חובה להזכיר את מילת המפתח הראשית בפסקה הראשונה!**
3. **מה קרה? הרקע העובדתי** (H2, 200-250 מילים)
4. **השאלה המשפטית** (H2, 150-200 מילים)
5. **מה קובע החוק?** (H2, 250-300 מילים) - 3-4 סעיפי חוק + קישור לnevo.co.il
6. **פסיקות קודמות** (H2, 200-250 מילים) - 2-3 תקדימים
7. **מה פסק בית המשפט?** (H2, 200-250 מילים)
8. **מה אפשר ללמוד בפועל?** (H2, 150-200 מילים) - רשימה
9. **טעויות נפוצות** (H2, 150-200 מילים) - 5-6 טעויות עם הסברים
10. **שאלות ותשובות** (H2, 400-500 מילים) - 8-10 FAQ items (כל שאלה H3)
11. **לסיכום** (H2, 150-200 מילים)
12. **Disclaimer** (div עם class="disclaimer")

### אסור בהחלט:
✗ "לקוחות" (רק: "אנשים", "תובעים", "נפגעים")
✗ "אנו", "משרדנו", "צוותנו"
✗ קידום מכירות
✗ הבטחות לתוצאות
✗ keyword stuffing
✗ משפטים מעל 20 מילים

## חשוב ביותר:
**המאמר חייב להיות 1800-2200 מילים! זו דרישה קריטית שאסור להפר!**
**מילת המפתח הראשית חייבת להופיע בפסקה הראשונה!**

**פורמט: JSON תקין בלבד עם כל השדות הנדרשים.**"""

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

    def generate(self, verdict_data: Dict[str, Any], max_retries: int = 2) -> Dict[str, Any]:
        """
        Generate SEO-optimized article from analyzed verdict data.

        Args:
            verdict_data: Dictionary containing analyzed verdict data from VerdictAnalyzer
            max_retries: Maximum number of retry attempts on failure

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
                # Build prompt
                user_prompt = self._build_prompt(verdict_data)

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

                # CRITICAL VALIDATION: Check word count
                word_count = enriched_result.get("word_count", 0)
                if word_count < 1800:
                    print(f"[ArticleGenerator] WARNING: Article too short - {word_count} words (minimum: 1800)")

                    # If we have retries left, try again with stronger emphasis
                    if attempt < max_retries:
                        print(f"[ArticleGenerator] Retrying with stronger word count emphasis...")
                        # Force retry with modified prompt on next iteration
                        raise ArticleGeneratorError(
                            f"Article too short: {word_count} words (minimum: 1800). Retrying with emphasis."
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

    def _build_prompt(self, verdict_data: Dict[str, Any]) -> str:
        """Build the user prompt for Claude."""
        # Format verdict data nicely
        verdict_json = json.dumps(verdict_data, ensure_ascii=False, indent=2)

        return f"""צור מאמר משפטי SEO-אופטימלי מקצועי על בסיס נתוני פסק הדין הבאים.

**חשוב מאוד**:
1. **אורך: 1800-2200 מילים בדיוק! זו דרישה קריטית!**
2. החזר JSON תקין בלבד!

## נתוני פסק הדין:
```json
{verdict_json}
```

## פורמט הפלט הנדרש:

```json
{{
  "title": "כותרת מושכת וכוללת מילת מפתח - מקס 60 תווים",
  "meta_description": "תיאור מזמין ותמציתי של המאמר - 150-155 תווים",
  "slug": "koteret-maamar-be-ivrit",
  "excerpt": "תקציר קצר של המאמר ב-2-3 משפטים",

  "focus_keyword": "מילת מפתח ראשית",
  "secondary_keywords": [
    "מילת מפתח 1",
    "מילת מפתח 2",
    "מילת מפתח 3",
    "מילת מפתח 4",
    "מילת מפתח 5"
  ],
  "long_tail_keywords": [
    "ביטוי ארוך 1",
    "ביטוי ארוך 2",
    "ביטוי ארוך 3",
    "ביטוי ארוך 4",
    "ביטוי ארוך 5",
    "ביטוי ארוך 6",
    "ביטוי ארוך 7",
    "ביטוי ארוך 8"
  ],

  "content_html": "<h1>כותרת המאמר</h1>\\n\\n<p>פסקת פתיחה ראשונה...</p>\\n\\n<p>פסקת פתיחה שנייה...</p>\\n\\n<h2>מה קרה? הרקע העובדתי</h2>\\n\\n<p>תיאור העובדות...</p>\\n\\n<ul>\\n<li>עובדה 1</li>\\n<li>עובדה 2</li>\\n</ul>\\n\\n<h2>השאלה המשפטית</h2>\\n\\n<p>תיאור השאלה...</p>\\n\\n<h2>מה קובע החוק?</h2>\\n\\n<p>הסבר על החוק...</p>\\n\\n<p>סעיף X לחוק Y קובע...</p>\\n\\n<h2>פסיקות קודמות</h2>\\n\\n<p>בפסק דין Z נקבע...</p>\\n\\n<h2>מה פסק בית המשפט?</h2>\\n\\n<p>בית המשפט החליט...</p>\\n\\n<h2>מה אפשר ללמוד בפועל?</h2>\\n\\n<ul>\\n<li>לקח 1</li>\\n<li>לקח 2</li>\\n</ul>\\n\\n<h2>טעויות נפוצות</h2>\\n\\n<ul>\\n<li><strong>טעות 1:</strong> הסבר</li>\\n<li><strong>טעות 2:</strong> הסבר</li>\\n</ul>\\n\\n<h2>שאלות ותשובות</h2>\\n\\n<h3>שאלה 1?</h3>\\n<p>תשובה מפורטת...</p>\\n\\n<h3>שאלה 2?</h3>\\n<p>תשובה מפורטת...</p>\\n\\n<h2>לסיכום</h2>\\n\\n<p>סיכום הנקודות העיקריות...</p>\\n\\n<div class=\\"disclaimer\\">\\n<p><strong>הבהרה חשובה:</strong> המידע במאמר זה הוא למידע כללי בלבד ואינו מהווה ייעוץ משפטי. כל מקרה הוא ייחודי ודורש בחינה פרטנית. להתייעצות בנושא ספציפי, מומלץ לפנות לעורך דין מומחה בתחום.</p>\\n</div>",

  "word_count": 0,
  "reading_time_minutes": 0,

  "faq_items": [
    {{
      "question": "שאלה 1?",
      "answer": "תשובה מפורטת ומקצועית לשאלה 1"
    }},
    {{
      "question": "שאלה 2?",
      "answer": "תשובה מפורטת ומקצועית לשאלה 2"
    }}
  ],

  "common_mistakes": [
    {{
      "mistake": "טעות נפוצה 1",
      "explanation": "מדוע זו טעות ומה צריך לעשות נכון"
    }},
    {{
      "mistake": "טעות נפוצה 2",
      "explanation": "מדוע זו טעות ומה צריך לעשות נכון"
    }}
  ],

  "category_primary": "דיני עבודה",
  "tags": ["פיצויי פיטורים", "דיני עבודה", "הודעה מוקדמת"],

  "featured_image_prompt": "Professional courtroom scene in Israel, judge's gavel, legal documents, modern and clean",
  "featured_image_alt": "אולם בית משפט - פסק דין בנושא פיצויי פיטורים"
}}
```

## דרישות חובה (אסור להפר!):

### אורך - קריטי ביותר!
**המאמר חייב להיות 1800-2200 מילים בדיוק! לא פחות מ-1800 מילים!**

### תוכן:
1. **7-8 כותרות H2** - כל H2 עם 150-250 מילים תחתיו
2. **10-12 כותרות H3** - רובן ב-FAQ
3. **8-10 שאלות FAQ** - כל שאלה H3 עם תשובה מפורטת
4. **5-6 טעויות נפוצות** - עם הסברים מפורטים
5. **6-8 ציטוטי חוק** - סעיפים מדויקים עם מספרים
6. **2-3 תקדימים** - שמות תיקים מלאים (למשל: "ע"א 123/45 פלוני נ' אלמוני")
7. **12+ מונחים משפטיים מקצועיים**
8. **5-6 רשימות** - bullet points או מספרים
9. **Disclaimer חזק** - בסוף המאמר
10. **צפיפות מילות מפתח: 1.0-1.2%**

### סגנון (דרישות מחייבות):
1. כתוב כעורך דין ישראלי מנוסה עם ניסיון של שנים רבות
2. הסבר במונחים פשוטים אך השתמש במינוחים משפטיים מקצועיים
3. תן דוגמאות מעשיות מחיי היומיום
4. **משפטים קצרים**: 15-18 מילים ממוצע (לא יותר מ-20!)
5. **מילות מעבר**: לפחות 10-12 מילות מעבר (לכן, בנוסף, מאידך, וכו')
6. **פסקאות קצרות**: 2-3 שורות מקסימום
7. אל תבטיח תוצאות
8. אל תיתן ייעוץ ספציפי

### SEO (דרישות מדויקות):
1. **כותרת H1**: 50-60 תווים, חובה להכיל את מילת המפתח הראשית
2. **Meta description**: 150-155 תווים, כוללת מילת מפתח ראשית
3. **מילת מפתח בפסקה הראשונה**: חייב להזכיר את מילת המפתח הראשית בפסקה הראשונה!
4. **צפיפות מילות מפתח ראשית**: 1.0-1.2% בדיוק (חשב והתאם!)
5. **מילות מפתח משניות**: שימוש ב-100% מהמילות המשניות לפחות פעמיים כל אחת
6. **Slug בעברית באותיות לטיניות**: נקי וקריא
7. **קישורים פנימיים**: 3-5 קישורים למאמרים אחרים (דוגמה: <a href="/נזיקין">נזיקין</a>)
8. **קישורים חיצוניים**: 2-3 קישורים לאתרים אמינים כמו https://www.nevo.co.il
9. **שילוב טבעי**: אל תעשה keyword stuffing

### איכות (קריטריונים מחמירים):
1. **אסור keyword stuffing** - שימוש טבעי בלבד
2. **ציטוטים קצרים** - מקסימום 20 מילים
3. **אסור מידע כוזב** - רק מידע מבוסס על נתוני פסק הדין
4. **אסור הבטחות** - אל תבטיח תוצאות
5. **תוכן מקיף ומעמיק** - כל סעיף צריך להיות מפורט ומקצועי
6. **דיוק משפטי מוחלט** - כל סעיף, חוק ותקדים צריכים להיות נכונים

### בדיקת איכות לפני הגשה (חובה!):
**קריטי ביותר: ספור מילים - חייב להיות לפחות 1800 מילים!**
- ספור H2: 7-8
- ספור H3: 10-12
- ספור ציטוטי חוק: לפחות 6-8
- ספור תקדימים: לפחות 2-3
- ספור FAQ: 8-10
- ספור טעויות נפוצות: 5-6
- בדוק צפיפות מילת מפתח: 1.0-1.2%
- בדוק אורך משפטים: ממוצע 15-18 מילים
- בדוק מילות מעבר: לפחות 10-12
- **בדוק שמילת המפתח מופיעה בפסקה הראשונה!**
- **בדוק שיש 3-5 קישורים פנימיים!**
- **בדוק שיש 2-3 קישורים חיצוניים!**

**זכור: המאמר חייב להיות 1800-2200 מילים! זו הדרישה החשובה ביותר!**

**החזר JSON תקין בלבד! אל תשכח שום שדה!**"""

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
            "featured_image_alt": ""
        }

        for field, default in required_fields.items():
            if field not in result:
                result[field] = default

        return result

    def _generate_article_schema(self, article: Dict[str, Any], verdict_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Schema.org Article JSON-LD."""
        return {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": article.get("title", ""),
            "description": article.get("meta_description", ""),
            "author": {
                "@type": "Organization",
                "name": "מערכת תוכן משפטי"
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

            return {
                "content_score": report.content_score,
                "seo_score": report.seo_score,
                "readability_score": report.readability_score,
                "eeat_score": report.eeat_score,
                "overall_score": report.overall_score,
                "quality_issues": report.critical_issues + report.warnings
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
                "quality_issues": [f"Failed to calculate scores: {str(e)}"]
            }
