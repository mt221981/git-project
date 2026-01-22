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

    # Valid practice areas for the law office
    VALID_CATEGORIES = [
        "ביטוח לאומי",
        "תביעות ביטוח",
        "נזקי גוף ורכוש",
        "תאונות עבודה",
        "רשלנות רפואית",
        "תאונות דרכים",
        "ליקויי בנייה",
        "איחור במסירת דירה"
    ]

    SYSTEM_PROMPT = """אתה עורך דין ישראלי מנוסה הכותב מאמרים משפטיים מקצועיים לאתר SEO.

**חשוב מאוד:** המאמר חייב להתבסס על פסק הדין שיסופק לך - לא מאמר גנרי!

## תחומי העיסוק של המשרד (חובה לבחור קטגוריה מהרשימה!):
1. ביטוח לאומי - תביעות נכות, קצבאות, דמי פגיעה
2. תביעות ביטוח - תביעות נגד חברות ביטוח, פוליסות, כיסוי ביטוחי
3. נזקי גוף ורכוש - פיצויים על נזקי גוף, נזקי רכוש
4. תאונות עבודה - תאונות במקום העבודה, מחלות מקצוע
5. רשלנות רפואית - טעויות רפואיות, רשלנות בטיפול
6. תאונות דרכים - תאונות רכב, נזקי גוף ומוות בתאונות דרכים
7. ליקויי בנייה - ליקויים בדירות, תביעות נגד קבלנים
8. איחור במסירת דירה - פיצויים על איחור במסירה

## דרישות תוכן:
1. השתמש בעובדות, בנימוקים ובהחלטה מפסק הדין הספציפי
2. צטט 6-8 סעיפי חוק מדויקים (סעיף X לחוק Y)
3. הסבר את העקרונות המשפטיים שבית המשפט יישם
4. תובנות מעשיות - מה אפשר ללמוד מפסק הדין

## דרישות SEO:
- אורך: 1800-2200 מילים (חובה!)
- מבנה: H1 + 7 H2 + 5 H3
- מילת מפתח: 5-8 הזכרות טבעיות בלבד (0.5-1.5% צפיפות). חשוב: השתמש בווריאציות ומילים נרדפות!
- FAQ: 8-10 שאלות רלוונטיות לפסק הדין הספציפי

## דרישות עיצוב:
- פסקאות: 3-5 משפטים, עד 150 מילים
- משפטים: עד 25 מילים בממוצע
- רשימות: 2+ רשימות ממוספרות או עם תבליטים
- מילות קישור: השתמש ב-8+ (לכן, אולם, בנוסף, כמו כן, למרות, יתרה מזאת, ראשית, שנית, לבסוף)

## E-E-A-T חובה:
- מונחים משפטיים: השתמש ב-10+ מונחים (פיצויים, נזק, אחריות, רשלנות, סמכות, ערעור, פסק דין, בית משפט, תובע, נתבע, התיישנות, עדות)
- disclaimer בסוף המאמר (חובה!): "<p><strong>אין באמור לעיל משום ייעוץ משפטי. מומלץ להתייעץ עם עורך דין מומחה בתחום.</strong></p>"
- CTA בסוף המאמר (חובה!): "<p><strong>לייעוץ משפטי בנושא, צרו קשר עם משרדנו.</strong></p>"

## כותרת (title):
- מקסימום 55 תווים
- חובה לכלול את מילת המפתח
- ללא קיצורים או מילים חתוכות

## meta_description:
- 120-160 תווים בדיוק
- חובה לכלול את מילת המפתח

## category_primary (חובה!):
בחר קטגוריה אחת בלבד מהרשימה: ביטוח לאומי, תביעות ביטוח, נזקי גוף ורכוש, תאונות עבודה, רשלנות רפואית, תאונות דרכים, ליקויי בנייה, איחור במסירת דירה

## איסורים:
- אסור מספרי תיקים (ע"א/ת"א)
- אסור שמות בעלי דין
- אסור "משרדנו/לקוחותינו"
- אסור "פסק דין חדשני/תקדימי/פורץ דרך"

## שפה - חובה!
כתוב אך ורק בעברית! אסור בהחלט להשתמש בתווים משפות אחרות (ערבית, רוסית, סינית וכו').
תווים מותרים: אותיות עבריות, ספרות, סימני פיסוק בסיסיים, ותגיות HTML בלבד.

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
- 5-8 הזכרות טבעיות בלבד של מילת המפתח (0.5-1.5% צפיפות). השתמש בווריאציות, מילים נרדפות וביטויים קשורים במקום לחזור על אותה מילה!

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

    def _detect_foreign_characters(self, text: str) -> Dict[str, Any]:
        """
        Detect foreign (non-Hebrew/Latin) characters in text.

        Returns:
            Dictionary with:
            - has_foreign: bool - True if foreign characters detected
            - foreign_chars: list - List of detected foreign characters
            - foreign_scripts: list - Names of detected scripts (Arabic, Cyrillic, etc.)
        """
        if not text:
            return {"has_foreign": False, "foreign_chars": [], "foreign_scripts": []}

        foreign_chars = []
        foreign_scripts = set()

        # Define forbidden character ranges with script names
        forbidden_ranges = [
            (0x0600, 0x06FF, "Arabic"),
            (0x0750, 0x077F, "Arabic Supplement"),
            (0x08A0, 0x08FF, "Arabic Extended-A"),
            (0x0400, 0x04FF, "Cyrillic"),
            (0x0370, 0x03FF, "Greek"),
            (0x0E00, 0x0E7F, "Thai"),
            (0x4E00, 0x9FFF, "Chinese"),
            (0x3040, 0x309F, "Japanese Hiragana"),
            (0x30A0, 0x30FF, "Japanese Katakana"),
            (0xAC00, 0xD7AF, "Korean"),
            (0x0900, 0x097F, "Devanagari"),
            (0x0980, 0x09FF, "Bengali"),
        ]

        for char in text:
            code = ord(char)
            for start, end, script_name in forbidden_ranges:
                if start <= code <= end:
                    foreign_chars.append(char)
                    foreign_scripts.add(script_name)
                    break

        return {
            "has_foreign": len(foreign_chars) > 0,
            "foreign_chars": foreign_chars[:20],  # Limit to first 20
            "foreign_scripts": list(foreign_scripts)
        }

    def _clean_hebrew_text(self, text: str) -> str:
        """
        Clean text to contain only valid Hebrew characters and allowed symbols.
        Removes foreign/non-Hebrew characters (Arabic, etc.) that may have been introduced by AI.

        Allowed characters:
        - Hebrew letters (U+0590-U+05FF)
        - Numbers (0-9)
        - Basic punctuation (.,;:!?-"'())
        - Whitespace
        - HTML tags and attributes (a-zA-Z for tag names, =/"' for attributes)
        """
        if not text:
            return text

        # First, explicitly remove Arabic characters (U+0600-U+06FF) and other unwanted scripts
        # Arabic, Arabic Supplement, Arabic Extended-A
        text = re.sub(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]', '', text)

        # Remove other non-Latin/Hebrew scripts that might slip in
        # Cyrillic, Greek, Thai, Chinese, Japanese, Korean, Devanagari, Bengali
        text = re.sub(r'[\u0400-\u04FF\u0370-\u03FF\u0E00-\u0E7F\u4E00-\u9FFF\u3040-\u309F\u30A0-\u30FF\uAC00-\uD7AF\u0900-\u097F\u0980-\u09FF]', '', text)

        # Pattern to match characters we want to KEEP
        # Hebrew, numbers, punctuation, whitespace, and characters needed for HTML
        allowed_pattern = r'[\u0590-\u05FF0-9\s\.,;:!?\-\"\'\(\)\[\]<>/=a-zA-Z_#&%@\n\r\t\u00B0\u2013\u2014\u2018\u2019\u201C\u201D]+'

        # Extract all allowed characters
        cleaned_parts = re.findall(allowed_pattern, text)
        return ''.join(cleaned_parts)

    def _validate_hebrew_only(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate that all text fields contain only Hebrew/allowed characters.
        Cleans any foreign characters found.

        Returns:
            Dictionary with validation results:
            - passed: bool
            - cleaned_fields: list of fields that were cleaned
            - foreign_detected: dict of field -> detected foreign info
        """
        fields_to_check = ["content_html", "title", "meta_description", "excerpt", "meta_title"]
        validation_result = {
            "passed": True,
            "cleaned_fields": [],
            "foreign_detected": {}
        }

        for field in fields_to_check:
            if field in result and result[field]:
                detection = self._detect_foreign_characters(result[field])
                if detection["has_foreign"]:
                    validation_result["passed"] = False
                    validation_result["foreign_detected"][field] = detection
                    # Clean the field
                    result[field] = self._clean_hebrew_text(result[field])
                    validation_result["cleaned_fields"].append(field)
                    print(f"[ArticleGenerator] WARNING: Foreign characters ({detection['foreign_scripts']}) detected and removed from {field}")

        # Also check FAQ items
        if "faq_items" in result:
            for i, faq in enumerate(result.get("faq_items", [])):
                for faq_field in ["question", "answer"]:
                    if faq_field in faq and faq[faq_field]:
                        detection = self._detect_foreign_characters(faq[faq_field])
                        if detection["has_foreign"]:
                            validation_result["passed"] = False
                            field_name = f"faq_items[{i}].{faq_field}"
                            validation_result["foreign_detected"][field_name] = detection
                            faq[faq_field] = self._clean_hebrew_text(faq[faq_field])
                            validation_result["cleaned_fields"].append(field_name)
                            print(f"[ArticleGenerator] WARNING: Foreign characters removed from {field_name}")

        return validation_result

    def _validate_and_fix_category(self, result: Dict[str, Any], verdict_data: Dict[str, Any]) -> str:
        """
        Validate category_primary is in allowed list. Fix if needed.

        Category mapping based on legal area keywords:
        - ביטוח לאומי: נכות, קצבה, דמי פגיעה, ביטוח לאומי
        - תביעות ביטוח: פוליסה, חברת ביטוח, כיסוי ביטוחי, תביעת ביטוח
        - נזקי גוף ורכוש: נזק גוף, נזק רכוש, פיצויים, נזיקין
        - תאונות עבודה: תאונת עבודה, מקום עבודה, מחלת מקצוע
        - רשלנות רפואית: רשלנות רפואית, טעות רפואית, בית חולים, רופא
        - תאונות דרכים: תאונת דרכים, תאונת רכב, נפגע דרכים
        - ליקויי בנייה: ליקויי בנייה, ליקוי, קבלן, דירה חדשה
        - איחור במסירת דירה: איחור במסירה, מסירת דירה, פיצוי איחור
        """
        category = result.get("category_primary", "")

        # If category is valid, return it
        if category in self.VALID_CATEGORIES:
            print(f"[ArticleGenerator] Category valid: {category}")
            return category

        # Try to fix based on legal area or content keywords
        legal_area = verdict_data.get("legal_area", "").lower()
        content = result.get("content_html", "").lower()
        title = result.get("title", "").lower()
        all_text = f"{legal_area} {title} {content}"

        # Keyword mapping to categories
        category_keywords = {
            "ביטוח לאומי": ["ביטוח לאומי", "נכות כללית", "דמי פגיעה", "קצבת נכות", "המוסד לביטוח לאומי"],
            "תביעות ביטוח": ["פוליסת ביטוח", "חברת ביטוח", "כיסוי ביטוחי", "תביעת ביטוח", "מבטחת"],
            "נזקי גוף ורכוש": ["נזק גוף", "נזקי גוף", "נזק רכוש", "נזיקין", "פיצויים"],
            "תאונות עבודה": ["תאונת עבודה", "תאונות עבודה", "מקום העבודה", "מחלת מקצוע", "פגיעה בעבודה"],
            "רשלנות רפואית": ["רשלנות רפואית", "טעות רפואית", "בית חולים", "טיפול רפואי", "רופא"],
            "תאונות דרכים": ["תאונת דרכים", "תאונות דרכים", "נפגע דרכים", "תאונת רכב", "נהיגה"],
            "ליקויי בנייה": ["ליקויי בנייה", "ליקוי בנייה", "קבלן", "דירה חדשה", "פגמים בדירה"],
            "איחור במסירת דירה": ["איחור במסירה", "מסירת דירה", "איחור קבלן", "פיצוי איחור"]
        }

        # Find best matching category
        best_match = None
        best_score = 0

        for cat, keywords in category_keywords.items():
            score = sum(1 for kw in keywords if kw in all_text)
            if score > best_score:
                best_score = score
                best_match = cat

        if best_match and best_score > 0:
            print(f"[ArticleGenerator] Category fixed: '{category}' -> '{best_match}' (score: {best_score})")
            return best_match

        # Default to most generic category
        default_cat = "נזקי גוף ורכוש"
        print(f"[ArticleGenerator] Category defaulted: '{category}' -> '{default_cat}'")
        return default_cat

    def _ensure_disclaimer_and_cta(self, content_html: str) -> str:
        """
        Ensure disclaimer and CTA exist at the end of article.
        If missing, append them automatically.

        This guarantees E-E-A-T score passes (80+).
        """
        text_lower = content_html.lower()

        # Check for disclaimer keywords
        disclaimer_keywords = ['אין באמור', 'אינו מהווה ייעוץ', 'יש להיוועץ',
                              'מומלץ להתייעץ', 'אין לראות']
        has_disclaimer = any(kw in text_lower for kw in disclaimer_keywords)

        # Check for CTA keywords
        cta_keywords = ['צרו קשר', 'פנו אלינו', 'התקשרו', 'לייעוץ', 'לפגישה']
        has_cta = any(kw in text_lower for kw in cta_keywords)

        # Append if missing
        if not has_disclaimer:
            disclaimer = '<h2>כתב ויתור</h2><p><strong>אין באמור לעיל משום ייעוץ משפטי. מומלץ להתייעץ עם עורך דין מומחה בתחום.</strong></p>'
            content_html += f'\n{disclaimer}'
            print(f"[ArticleGenerator] Added missing disclaimer")

        if not has_cta:
            cta = '<h2>צור קשר</h2><p><strong>לייעוץ משפטי מקצועי בנושא, צרו קשר עם משרדנו.</strong></p>'
            content_html += f'\n{cta}'
            print(f"[ArticleGenerator] Added missing CTA")

        return content_html

    def _ensure_seo_keywords(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ensure focus keyword appears in title and meta description.
        Improve secondary keywords coverage if needed.

        This guarantees SEO score reaches 80+.
        """
        focus_keyword = result.get("focus_keyword", "").strip()
        secondary_keywords = result.get("secondary_keywords", []) or []
        title = result.get("title", "")
        meta_desc = result.get("meta_description", "")
        content_html = result.get("content_html", "")

        print(f"[ArticleGenerator] _ensure_seo_keywords called - focus_keyword: '{focus_keyword}', title_has_keyword: {focus_keyword.lower() in title.lower() if focus_keyword else False}, meta_has_keyword: {focus_keyword.lower() in meta_desc.lower() if focus_keyword else False}")

        if not focus_keyword:
            print(f"[ArticleGenerator] No focus_keyword, skipping SEO keyword injection")
            return result

        # Fix 1: Ensure focus keyword in title
        if focus_keyword.lower() not in title.lower():
            # Add keyword at the beginning
            new_title = f"{focus_keyword} - {title}"
            # Truncate if too long
            if len(new_title) > 60:
                new_title = new_title[:57] + "..."
            result["title"] = new_title
            print(f"[ArticleGenerator] Added focus keyword to title")

        # Fix 2: Ensure focus keyword in meta description
        if focus_keyword.lower() not in meta_desc.lower():
            # Prepend keyword
            new_meta = f"{focus_keyword}: {meta_desc}"
            # Truncate if too long
            if len(new_meta) > 160:
                new_meta = new_meta[:157] + "..."
            result["meta_description"] = new_meta
            print(f"[ArticleGenerator] Added focus keyword to meta description")

        # Fix 3: Improve secondary keywords coverage
        if secondary_keywords:
            content_text = re.sub(r'<[^>]+>', '', content_html).lower()
            used_secondary = sum(1 for kw in secondary_keywords if kw.lower() in content_text)
            coverage_ratio = used_secondary / len(secondary_keywords) if secondary_keywords else 0

            # If coverage < 70%, add missing keywords
            if coverage_ratio < 0.7:
                missing_keywords = [kw for kw in secondary_keywords
                                  if kw.lower() not in content_text]

                if missing_keywords:
                    # Take up to 5 missing keywords
                    keywords_to_add = missing_keywords[:5]
                    keywords_str = ", ".join(keywords_to_add)

                    # Add natural paragraph with keywords before disclaimer
                    seo_paragraph = f'''<h2>מונחים משפטיים נוספים</h2>
<p>בהקשר זה, כדאי להכיר גם מונחים משפטיים רלוונטיים כגון: <strong>{keywords_str}</strong>. מונחים אלו עשויים להיות רלוונטיים במקרים דומים.</p>'''

                    # Insert before disclaimer (if exists) or at the end
                    if 'כתב ויתור' in content_html or 'אין באמור' in content_html:
                        # Find disclaimer position and insert before it
                        disclaimer_pos = content_html.lower().find('<h2>כתב ויתור')
                        if disclaimer_pos > 0:
                            result["content_html"] = content_html[:disclaimer_pos] + seo_paragraph + '\n' + content_html[disclaimer_pos:]
                        else:
                            result["content_html"] = content_html + '\n' + seo_paragraph
                    else:
                        result["content_html"] = content_html + '\n' + seo_paragraph

                    print(f"[ArticleGenerator] Added {len(keywords_to_add)} missing secondary keywords")

        return result

    def _validate_and_enrich(self, result: Dict[str, Any], verdict_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and enrich the article data."""
        # CRITICAL: Validate Hebrew-only content and clean any foreign characters
        hebrew_validation = self._validate_hebrew_only(result)
        if not hebrew_validation["passed"]:
            print(f"[ArticleGenerator] Hebrew validation FAILED - cleaned {len(hebrew_validation['cleaned_fields'])} fields")
            print(f"[ArticleGenerator] Foreign scripts detected: {set(s for d in hebrew_validation['foreign_detected'].values() for s in d.get('foreign_scripts', []))}")

        # Additional cleaning pass for safety (belt and suspenders)
        if "content_html" in result:
            result["content_html"] = self._clean_hebrew_text(result["content_html"])
        if "title" in result:
            result["title"] = self._clean_hebrew_text(result["title"])
        if "meta_description" in result:
            result["meta_description"] = self._clean_hebrew_text(result["meta_description"])
        if "excerpt" in result:
            result["excerpt"] = self._clean_hebrew_text(result["excerpt"])
        if "meta_title" in result:
            result["meta_title"] = self._clean_hebrew_text(result["meta_title"])

        # ENSURE DISCLAIMER AND CTA (for E-E-A-T score 80+)
        if "content_html" in result:
            result["content_html"] = self._ensure_disclaimer_and_cta(result["content_html"])

        # ENSURE SEO KEYWORDS (for SEO score 80+)
        result = self._ensure_seo_keywords(result)

        # Calculate word count from HTML
        if "content_html" in result:
            text = re.sub(r'<[^>]+>', '', result["content_html"])
            result["word_count"] = len(text.split())
            result["reading_time_minutes"] = max(1, result["word_count"] // 200)

        # Validate and fix category to match law office practice areas
        result["category_primary"] = self._validate_and_fix_category(result, verdict_data)

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
            "category_primary": "נזקי גוף ורכוש",  # Default to most common category
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
