"""VerdictAnalyzer - Core service for analyzing legal verdicts using Claude API."""

import json
from typing import Dict, Any, Optional
from anthropic import Anthropic
from app.config import settings


class AnalyzerError(Exception):
    """Exception raised when analysis fails."""
    pass


class VerdictAnalyzer:
    """
    Core service for analyzing Hebrew legal verdicts using Claude API.

    Extracts structured data including:
    - Court metadata (name, level, case number, date, judge)
    - Legal categorization (area, sub-area, case type)
    - Content analysis (facts, questions, summary, principles)
    - Legal references (laws, precedents)
    - Financial data (compensation amounts and breakdown)
    - Insights and reader questions
    """

    SYSTEM_PROMPT = """אתה מומחה משפטי ישראלי המתמחה בניתוח וחילוץ מידע מפסקי דין.

תפקידך: לחלץ מידע מובנה מפסק דין בצורה מדויקת ומקצועית.

## עקרונות עבודה:
✓ דיוק מוחלט - כל מידע חייב להיות מבוסס על פסק הדין
✓ שפה משפטית מדויקת - השתמש בטרמינולוגיה משפטית נכונה
✓ מבנה ברור - הצג מידע בפורמט JSON מסודר
✓ מקיף - כלול את כל המידע הרלוונטי, אל תדלג

## סוגי מידע לחילוץ:

### 1. מטא-דאטה של בית המשפט
- שם בית המשפט (מלא ומדויק)
- דרגת בית המשפט (עליון/מחוזי/שלום)
- מספר תיק (כפי שמופיע בפסק הדין)
- תאריך מתן פסק הדין
- שם השופט/ים

### 2. סיווג משפטי
- תחום משפטי ראשי: נזיקין/חוזים/עבודה/ביטוח/מקרקעין/משפחה/צרכנות/מנהלי/פלילי/אחר
- תת-תחום משפטי (ספציפי יותר)
- סוג ההליך: תביעה/ערעור/בקשה

### 3. תוכן משפטי
- עובדות מהותיות (5-8): התרחישות מרכזיות, זמנים, מקומות, צדדים
- שאלות משפטיות (2-4): הסוגיות שבית המשפט נדרש להכריע בהן
- תקציר פסק הדין (2-3 משפטים): מה קרה ומה הוכרע
- עקרונות משפטיים (3-5): כללים והלכות שהופעלו או נקבעו

### 4. מקורות משפטיים
- חוקים רלוונטיים: שם החוק, מספר סעיף, הסבר קצר
- תקדימים שצוטטו: שם התיק, העיקרון שנקבע

### 5. פיצויים (אם רלוונטי)
- סכום כולל
- פירוט לפי קטגוריות (נזק, עוגמת נפש, הוצאות, וכו')

### 6. תובנות מעשיות ושאלות
- לקחים מעשיים (3-5): מה ניתן ללמוד, נקודות חשובות
- שאלות לקורא (4-6): שאלות נפוצות שעולות מהתיק

## פורמט הפלט:
החזר JSON תקין בלבד, ללא טקסט הקדמה או הסבר."""

    def __init__(self, api_key: str = None):
        """
        Initialize VerdictAnalyzer.

        Args:
            api_key: Anthropic API key (uses settings.ANTHROPIC_API_KEY if not provided)
        """
        self.api_key = api_key or settings.ANTHROPIC_API_KEY
        if not self.api_key or self.api_key == "your-key-here":
            raise ValueError("ANTHROPIC_API_KEY not configured. Set it in .env file.")

        self.client = Anthropic(api_key=self.api_key)

    def analyze(self, anonymized_text: str) -> Dict[str, Any]:
        """
        Analyze anonymized verdict text and extract structured data.

        Args:
            anonymized_text: The anonymized verdict text in Hebrew

        Returns:
            Dictionary with all extracted data:
            {
                "court_name": str,
                "court_level": str,  # "עליון"/"מחוזי"/"שלום"
                "case_number_display": str,
                "verdict_date": str,  # "YYYY-MM-DD" or text
                "judge_name": str,
                "legal_area": str,  # נזיקין/חוזים/עבודה/...
                "legal_sub_area": str,
                "case_type": str,  # תביעה/ערעור/בקשה
                "key_facts": List[str],  # 5-8 items
                "legal_questions": List[str],  # 2-4 items
                "verdict_summary": str,
                "legal_principles": List[str],  # 3-5 items
                "relevant_laws": List[Dict],  # [{name, section, explanation}, ...]
                "precedents_cited": List[Dict],  # [{case_name, key_holding}, ...]
                "compensation_amount": Optional[float],
                "compensation_breakdown": Optional[Dict],
                "practical_insights": List[str],  # 3-5 items
                "reader_questions": List[str]  # 4-6 items
            }

        Raises:
            AnalyzerError: If analysis fails
        """
        if not anonymized_text or not anonymized_text.strip():
            raise AnalyzerError("Anonymized text cannot be empty")

        # Build prompt
        user_prompt = self._build_prompt(anonymized_text)

        try:
            # Call Claude API
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                temperature=0,  # Deterministic for structured extraction
                system=self.SYSTEM_PROMPT,
                messages=[{
                    "role": "user",
                    "content": user_prompt
                }]
            )

            # Extract text from response
            response_text = response.content[0].text

            # Parse JSON
            result = self._parse_response(response_text)

            # Validate and normalize
            return self._validate_result(result)

        except json.JSONDecodeError as e:
            raise AnalyzerError(f"Failed to parse Claude response as JSON: {e}")
        except Exception as e:
            raise AnalyzerError(f"Analysis failed: {e}")

    def _build_prompt(self, text: str) -> str:
        """Build the user prompt for Claude."""
        return f"""נתח את פסק הדין המאונונם הבא והחזר את כל המידע בפורמט JSON מובנה.

**חשוב מאוד**: החזר JSON תקין בלבד, ללא טקסט לפני או אחרי!

פורמט הפלט הדרוש:

```json
{{
  "court_name": "בית המשפט המחוזי בתל אביב-יפו",
  "court_level": "מחוזי",
  "case_number_display": "12345-01-20",
  "verdict_date": "2021-03-15",
  "judge_name": "השופט/ת...",

  "legal_area": "עבודה",
  "legal_sub_area": "פיטורים",
  "case_type": "תביעה",

  "key_facts": [
    "התובע עבד 5 שנים אצל הנתבע",
    "פוטר ביום X ללא הודעה מוקדמת",
    "טענת הנתבע: הפרת חוזה עבודה",
    "התובע דורש פיצויי פיטורים + הודעה מוקדמת"
  ],

  "legal_questions": [
    "האם הפיטורים היו כדין?",
    "האם התובע זכאי לפיצויי פיטורים?",
    "האם התובע זכאי לפיצוי בגין אי-מתן הודעה מוקדמת?"
  ],

  "verdict_summary": "בית המשפט קיבל את התביעה חלקית. נקבע כי הפיטורים היו שלא כדין, והנתבע חויב בפיצויי פיטורים מלאים ובפיצוי נוסף בגין אי-מתן הודעה מוקדמת.",

  "legal_principles": [
    "חובת מעביד לתת הודעה מוקדמת לפני פיטורים - סעיף 5 לחוק עבודה",
    "פיטורים ללא הצדקה מהווים הפרה יסודית של חוזה העבודה",
    "נטל ההוכחה על המעביד להוכיח הצדקה לפיטורים"
  ],

  "relevant_laws": [
    {{
      "name": "חוק עבודה תשל\\"ח-1978",
      "section": "סעיף 5",
      "explanation": "קובע חובת מתן הודעה מוקדמת או תשלום במקומה"
    }},
    {{
      "name": "חוק פיצויי פיטורים תשכ\\"ג-1963",
      "section": "סעיף 11",
      "explanation": "קובע זכאות לפיצויי פיטורים מלאים במקרה של פיטורים שלא כדין"
    }}
  ],

  "precedents_cited": [
    {{
      "case_name": "כהן נגד משרד החינוך (ע\\"ע 567/85)",
      "key_holding": "פיטורים ללא הצדקה מספקת מהווים הפרה יסודית ומזכים בפיצויי פיטורים מלאים"
    }}
  ],

  "compensation_amount": 120000.0,
  "compensation_breakdown": {{
    "פיצויי_פיטורים": 95000.0,
    "הודעה_מוקדמת": 15000.0,
    "הוצאות_משפט": 10000.0
  }},

  "practical_insights": [
    "מעסיקים חייבים להוכיח בראיות מוצקות כל טענה להפרת חוזה עבודה",
    "פיטורים ללא הודעה מוקדמת מחייבים הצדקה חזקה ביותר",
    "עובדים שפוטרו שלא כדין זכאים לפיצויים מלאים ולפיצוי נוסף"
  ],

  "reader_questions": [
    "מהי הודעה מוקדמת ומתי חובה לתת אותה?",
    "מה ההבדל בין פיטורים כדין לפיטורים שלא כדין?",
    "כיצד מחושבים פיצויי פיטורים?",
    "מה נדרש כדי להוכיח הצדקה לפיטורים?"
  ]
}}
```

**הנחיות חשובות**:
1. תחום משפטי חייב להיות אחד מהבאים: נזיקין/חוזים/עבודה/ביטוח/מקרקעין/משפחה/צרכנות/מנהלי/פלילי/אחר
2. דרגת בית משפט: עליון/מחוזי/שלום
3. סוג הליך: תביעה/ערעור/בקשה
4. אם אין פיצויים כספיים, השתמש ב-null
5. כל הטקסט בעברית
6. JSON תקין בלבד!

---

פסק הדין לניתוח:

{text}

---

החזר JSON בלבד:"""

    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """Parse Claude's JSON response."""
        # Try to extract JSON from response
        response_text = response_text.strip()

        # Remove markdown code blocks if present
        if response_text.startswith("```"):
            # Find the actual JSON content
            lines = response_text.split("\n")
            json_lines = []
            in_json = False
            for line in lines:
                if line.strip().startswith("```"):
                    in_json = not in_json
                    continue
                if in_json or (line.strip().startswith("{") or json_lines):
                    json_lines.append(line)
                    if line.strip().endswith("}") and json_lines[0].strip().startswith("{"):
                        break
            response_text = "\n".join(json_lines)

        # Parse JSON
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            # Try to find JSON object in text
            start = response_text.find("{")
            end = response_text.rfind("}") + 1
            if start != -1 and end > start:
                return json.loads(response_text[start:end])
            raise

    def _validate_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize the analysis result."""
        # Ensure all required fields exist
        required_fields = [
            "court_name", "court_level", "case_number_display", "verdict_date",
            "judge_name", "legal_area", "legal_sub_area", "case_type",
            "key_facts", "legal_questions", "verdict_summary", "legal_principles",
            "relevant_laws", "precedents_cited", "practical_insights", "reader_questions"
        ]

        for field in required_fields:
            if field not in result:
                result[field] = [] if field.endswith("s") or field in ["key_facts", "legal_questions", "legal_principles", "relevant_laws", "precedents_cited", "practical_insights", "reader_questions"] else ""

        # Normalize optional fields
        if "compensation_amount" not in result:
            result["compensation_amount"] = None
        if "compensation_breakdown" not in result:
            result["compensation_breakdown"] = None

        # Validate legal_area
        valid_areas = ["נזיקין", "חוזים", "עבודה", "ביטוח", "מקרקעין", "משפחה", "צרכנות", "מנהלי", "פלילי", "אחר"]
        if result["legal_area"] not in valid_areas:
            result["legal_area"] = "אחר"

        # Validate court_level
        valid_levels = ["עליון", "מחוזי", "שלום", "אחר"]
        if result.get("court_level") not in valid_levels:
            # Try to infer from court_name
            court_name = result.get("court_name", "").lower()
            if "עליון" in court_name:
                result["court_level"] = "עליון"
            elif "מחוזי" in court_name:
                result["court_level"] = "מחוזי"
            elif "שלום" in court_name:
                result["court_level"] = "שלום"
            else:
                result["court_level"] = "אחר"

        # Validate case_type
        valid_types = ["תביעה", "ערעור", "בקשה", "אחר"]
        if result.get("case_type") not in valid_types:
            result["case_type"] = "תביעה"  # Default

        return result
