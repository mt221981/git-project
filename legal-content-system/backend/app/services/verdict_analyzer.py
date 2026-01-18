"""Verdict analyzer service using Claude API for structured data extraction."""

import json
from typing import Dict, Any, Optional, List
from anthropic import Anthropic
from app.config import settings
from app.utils.json_repair import safe_parse_json


class AnalysisError(Exception):
    """Exception raised when analysis fails."""
    pass


class VerdictAnalyzer:
    """
    Core service for analyzing legal verdicts using Claude API.

    Extracts structured information including:
    - Key facts
    - Legal questions
    - Legal principles
    - Compensation details
    - Relevant laws
    - Cited precedents
    - Practical insights
    """

    # System prompt for Claude
    SYSTEM_PROMPT = """אתה מומחה משפטי ישראלי המתמחה בניתוח פסקי דין.

תפקידך לחלץ מידע מובנה מפסקי דין בצורה מדויקת ושיטתית.

## יכולות הניתוח שלך:

### 1. חילוץ עובדות מהותיות (Key Facts)
זהה את העובדות המרכזיות והרלוונטיות לפסק הדין:
- מי הצדדים למחלוקת
- מה אירע (התרחישות)
- מתי ואיפה התרחשו האירועים
- מה הסכסוך המרכזי

### 2. זיהוי שאלות משפטיות (Legal Questions)
חלץ את השאלות המשפטיות שנדונו:
- השאלות שבית המשפט התמודד איתן
- סוגיות משפטיות מרכזיות
- סעיפי חוק שנבחנו

### 3. עקרונות משפטיים (Legal Principles)
זהה עקרונות משפטיים שהוחלו או נקבעו:
- כללים משפטיים שהופעלו
- פרשנויות חוקיות
- סטנדרטים משפטיים

### 4. פיצויים (Compensation)
חלץ פרטים על פיצויים כספיים:
- סכום כולל
- פירוט לפי קטגוריות (נזק ישיר, עוגמת נפש, הוצאות, וכו')
- הצדקה לכל סכום

### 5. חוקים רלוונטיים (Relevant Laws)
זהה חוקים שצוטטו או הוזכרו:
- שם החוק
- סעיף ספציפי
- רלוונטיות למקרה
- ציטוטים רלוונטיים

### 6. תקדימים (Precedents)
חלץ תקדימים שהוזכרו:
- שם התיק
- מספר תיק
- בית המשפט
- שנה
- העקרון שנקבע
- רלוונטיות למקרה הנוכחי

### 7. תובנות מעשיות (Practical Insights)
הפק לקחים ותובנות:
- מה ניתן ללמוד מהתיק
- נקודות חשובות למקרים דומים
- המלצות מעשיות

## עקרונות עבודה:

✓ דיוק: וודא שכל המידע מדויק ומבוסס על פסק הדין
✓ מובנה: הצג מידע בפורמט JSON מובנה וברור
✓ ממוקד: התמקד במידע המהותי והרלוונטי
✓ מקצועי: השתמש בטרמינולוגיה משפטית מדויקת
✓ מלא: כלול את כל המידע החשוב, אל תדלג על פרטים

## פלט:

החזר תמיד JSON תקין בלבד, ללא טקסט נוסף."""

    def __init__(self, api_key: str = None):
        """
        Initialize VerdictAnalyzer with Claude API.

        Args:
            api_key: Anthropic API key (uses settings if not provided)
        """
        self.api_key = api_key or settings.ANTHROPIC_API_KEY
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not configured")

        self.client = Anthropic(api_key=self.api_key)

    def analyze(self, text: str, max_retries: int = 2) -> Dict[str, Any]:
        """
        Analyze verdict text and extract structured information.

        Args:
            text: Hebrew legal verdict text (should be anonymized)
            max_retries: Maximum number of retry attempts on failure

        Returns:
            Dictionary with:
            {
                "key_facts": List[str],
                "legal_questions": List[str],
                "legal_principles": List[str],
                "compensation_amount": Optional[float],
                "compensation_breakdown": Dict,
                "relevant_laws": List[Dict],
                "precedents_cited": List[Dict],
                "practical_insights": List[str],
                "case_type": str,
                "outcome": str
            }

        Raises:
            AnalysisError: If analysis fails after all retries

        Example:
            >>> analyzer = VerdictAnalyzer()
            >>> result = analyzer.analyze(anonymized_text)
            >>> print(result["key_facts"])
            ['התובע עבד 5 שנים', 'פוטר ללא הודעה', ...]
        """
        if not text or not text.strip():
            raise AnalysisError("Text cannot be empty")

        last_error = None

        for attempt in range(max_retries + 1):
            try:
                # Build user prompt
                user_prompt = self._build_user_prompt(text)

                # Call Claude API
                response = self.client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=4096,
                    system=self.SYSTEM_PROMPT,
                    messages=[
                        {
                            "role": "user",
                            "content": user_prompt
                        }
                    ]
                )

                # Extract response text
                response_text = response.content[0].text

                # Parse JSON response with repair logic
                result = self._parse_response(response_text)

                # Validate and enrich
                return self._validate_and_enrich(result)

            except (AnalysisError, json.JSONDecodeError) as e:
                last_error = e
                if attempt < max_retries:
                    print(f"[VerdictAnalyzer] Attempt {attempt + 1} failed: {str(e)[:100]}. Retrying...")
                    continue

            except Exception as e:
                last_error = e
                if attempt < max_retries:
                    print(f"[VerdictAnalyzer] Attempt {attempt + 1} failed: {str(e)[:100]}. Retrying...")
                    continue

        raise AnalysisError(f"Analysis failed after {max_retries + 1} attempts: {str(last_error)}")

    def _build_user_prompt(self, text: str) -> str:
        """
        Build user prompt for Claude.

        Args:
            text: Verdict text to analyze

        Returns:
            Formatted prompt
        """
        return f"""נתח את פסק הדין הבא והחזר ניתוח מובנה בפורמט JSON.

**חשוב**: החזר JSON תקין בלבד, ללא טקסט הסבר לפני או אחרי.

פורמט הפלט:

```json
{{
  "key_facts": [
    "עובדה מהותית 1",
    "עובדה מהותית 2",
    "עובדה מהותית 3"
  ],
  "legal_questions": [
    "שאלה משפטית 1",
    "שאלה משפטית 2"
  ],
  "legal_principles": [
    "עקרון משפטי 1 + הסבר קצר",
    "עקרון משפטי 2 + הסבר קצר"
  ],
  "compensation_amount": 120000.0,
  "compensation_breakdown": {{
    "total": 120000.0,
    "description": "תיאור כללי של הפיצוי",
    "items": [
      {{
        "category": "פיצויי פיטורים",
        "amount": 95000.0,
        "description": "פיצויי פיטורים מלאים"
      }},
      {{
        "category": "הודעה מוקדמת",
        "amount": 15000.0,
        "description": "פיצוי בגין אי-מתן הודעה מוקדמת"
      }},
      {{
        "category": "הוצאות משפט",
        "amount": 10000.0,
        "description": "הוצאות משפט"
      }}
    ]
  }},
  "relevant_laws": [
    {{
      "name": "חוק עבודה",
      "section": "סעיף 5",
      "description": "חובת מתן הודעה מוקדמת",
      "quote": "ציטוט רלוונטי מהחוק אם יש"
    }}
  ],
  "precedents_cited": [
    {{
      "case_name": "כהן נגד משרד החינוך",
      "case_number": "ע\\"ע 567/85",
      "court": "בית המשפט העליון",
      "year": "1985",
      "relevance": "קבע כי פיטורים ללא הצדקה מהווים הפרה יסודית",
      "principle": "חובת הנמקה בפיטורים"
    }}
  ],
  "practical_insights": [
    "תובנה מעשית 1 - מה ניתן ללמוד",
    "תובנה מעשית 2 - נקודות חשובות",
    "תובנה מעשית 3 - המלצות למקרים דומים"
  ],
  "case_type": "תביעת עבודה",
  "outcome": "התביעה התקבלה חלקית"
}}
```

הנחיות:
- **key_facts**: 5-8 עובדות מרכזיות, ממוקדות וברורות
- **legal_questions**: 2-4 שאלות משפטיות עיקריות שנדונו
- **legal_principles**: 2-5 עקרונות משפטיים שהוחלו
- **compensation_amount**: סכום כולל כמספר (null אם אין)
- **compensation_breakdown**: פירוק מפורט של הפיצוי
- **relevant_laws**: חוקים שהוזכרו בפסק הדין
- **precedents_cited**: תקדימים שצוטטו (ריק אם אין)
- **practical_insights**: 3-5 תובנות מעשיות
- **case_type**: סוג התיק (עבודה, נזיקין, משפחה, וכו')
- **outcome**: התוצאה (התקבל/נדחה/התקבל חלקית)

פסק הדין לניתוח:

---
{text}
---

אנא החזר JSON תקין בלבד."""

    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse Claude's JSON response with robust repair logic.

        Args:
            response_text: Raw response from Claude

        Returns:
            Parsed JSON dictionary

        Raises:
            AnalysisError: If JSON cannot be parsed
        """
        result = safe_parse_json(response_text)

        if result is None:
            # Log the problematic response for debugging
            print(f"[VerdictAnalyzer] Failed to parse JSON. First 500 chars: {response_text[:500]}")
            raise AnalysisError(
                "Failed to parse Claude response as JSON after repair attempts"
            )

        return result

    def _validate_and_enrich(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and enrich analysis result.

        Args:
            result: Parsed JSON from Claude

        Returns:
            Validated and enriched result

        Raises:
            AnalysisError: If required fields are missing
        """
        # Required fields
        required_fields = ["key_facts", "legal_questions", "legal_principles"]

        for field in required_fields:
            if field not in result:
                raise AnalysisError(f"Missing required field: {field}")

        # Ensure lists are lists
        list_fields = [
            "key_facts", "legal_questions", "legal_principles",
            "relevant_laws", "precedents_cited", "practical_insights"
        ]

        for field in list_fields:
            if field not in result:
                result[field] = []
            elif not isinstance(result[field], list):
                result[field] = []

        # Ensure compensation_amount is float or None
        if "compensation_amount" in result:
            if result["compensation_amount"] is not None:
                try:
                    result["compensation_amount"] = float(result["compensation_amount"])
                except (ValueError, TypeError):
                    result["compensation_amount"] = None
        else:
            result["compensation_amount"] = None

        # Ensure compensation_breakdown exists
        if "compensation_breakdown" not in result or not result["compensation_breakdown"]:
            result["compensation_breakdown"] = {
                "total": result.get("compensation_amount", 0),
                "description": "",
                "items": []
            }

        # Ensure case_type and outcome exist
        if "case_type" not in result:
            result["case_type"] = "לא זוהה"

        if "outcome" not in result:
            result["outcome"] = "לא זוהה"

        return result

    def get_summary(self, analysis: Dict[str, Any]) -> str:
        """
        Generate a brief summary of the analysis.

        Args:
            analysis: Analysis result from analyze()

        Returns:
            Brief text summary
        """
        facts_count = len(analysis.get("key_facts", []))
        questions_count = len(analysis.get("legal_questions", []))
        principles_count = len(analysis.get("legal_principles", []))
        compensation = analysis.get("compensation_amount")

        summary_parts = [
            f"סוג תיק: {analysis.get('case_type', 'לא ידוע')}",
            f"תוצאה: {analysis.get('outcome', 'לא ידועה')}",
            f"עובדות מרכזיות: {facts_count}",
            f"שאלות משפטיות: {questions_count}",
            f"עקרונות משפטיים: {principles_count}"
        ]

        if compensation:
            summary_parts.append(f"פיצוי: ₪{compensation:,.0f}")

        return " | ".join(summary_parts)
