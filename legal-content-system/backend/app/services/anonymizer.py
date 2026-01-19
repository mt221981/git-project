"""Anonymizer service using Claude API for legal document anonymization."""

import json
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from anthropic import Anthropic
from app.config import settings
from app.utils.json_repair import safe_parse_json


class AnonymizationError(Exception):
    """Exception raised when anonymization fails."""
    pass


class Anonymizer:
    """
    Service for anonymizing legal documents using Claude API.

    Uses Claude to:
    - Identify personal information in Hebrew legal texts
    - Replace with consistent anonymous placeholders
    - Categorize each identified item
    - Assess privacy risk level
    - Flag cases requiring manual review
    """

    # System prompt for Claude
    SYSTEM_PROMPT = """אתה מומחה לאנונימיזציה של מסמכים משפטיים ישראליים.

תפקידך לזהות ולהחליף מידע מזהה אישי בטקסטים משפטיים, תוך שמירה על קריאות וזרימה טבעית.

## סוגי מידע לאנונימיזציה:

1. **שמות אנשים** (person_name):
   - שמות פרטיים ומשפחתיים של בעלי דין, עדים, נפגעים
   - שמות של קטינים (חשוב במיוחד!)
   - שמות של בני משפחה
   - התחליף: "התובע", "הנתבע", "העד מס' 1", "הקטין", "בן/בת הזוג"

2. **תעודות זהות** (official_id):
   - מספרי ת.ז.
   - מספרי דרכון
   - מספרי רישוי עסק
   - התחליף: "ת.ז. ***123" (3 ספרות אחרונות), "דרכון ***789"

3. **פרטי קשר** (contact_info):
   - מספרי טלפון
   - כתובות אימייל
   - התחליף: "[טלפון הוסר]", "[אימייל הוסר]"

4. **כתובות ונכסים** (property_details):
   - כתובות מגורים מלאות
   - מספרי רכב
   - מספרי חשבון בנק
   - התחליף: "[כתובת הוסרה]", "[מספר רכב הוסר]", "חשבון בנק ***456"

5. **מידע רגיש** (sensitive_info):
   - פרטים רפואיים מזהים
   - גילאים של קטינים
   - פרטים אינטימיים
   - התחליף: "[מידע רפואי הוסר]", "קטין בן X", "[פרטים הוסרו]"

## מה לא להחליף:

❌ אל תאנוניזם:
- שמות שופטים
- שמות עורכי דין (מידע ציבורי)
- שמות חברות גדולות וידועות
- מספרי תיקים משפטיים
- שמות בתי משפט
- ציטוטים מחוקים ופסיקות
- סכומי כסף
- תאריכים (אלא אם מזהים קטין)

## כללי עבודה:

1. **עקביות**: אותו שם תמיד יקבל אותו תחליף בכל המסמך
2. **קריאות**: הטקסט המאונוניזם חייב להישאר קריא וזורם
3. **דיוק**: תייג כל פריט עם רמת ביטחון (high/medium/low)
4. **הקשר**: שמור על ההקשר המשפטי - לא להסיר מידע משפטי חשוב

## רמות ביטחון (Confidence):

- **high**: ודאי שזה מידע אישי מזהה (שם מלא, ת.ז., טלפון)
- **medium**: סביר שזה מידע אישי (שם פרטי בלבד, כתובת חלקית)
- **low**: ייתכן שזה מידע אישי אבל לא בטוח

## הערכת סיכון (Risk Level):

- **low**: אין מידע רגיש, אנונימיזציה מלאה
- **medium**: מידע אישי רגיל, יש פוטנציאל זיהוי בינוני
- **high**: מידע רגיש מאוד (קטינים, פרטים רפואיים, מספרי ת.ז.)

## דגל לבדיקה ידנית (Manual Review):

סמן requires_manual_review = true אם:
- יש מידע רפואי או אינטימי
- מדובר בקטינים
- מצאת מספרי ת.ז. או פרטים בנקאיים
- יש שילוב של מספר פרטים מזהים
- יש פרטים שלא בטוח אם להחליף

החזר תמיד JSON תקין בפורמט המדויק שנדרש."""

    def __init__(self, api_key: str = None):
        """
        Initialize Anonymizer with Claude API.

        Args:
            api_key: Anthropic API key (uses settings if not provided)
        """
        self.api_key = api_key or settings.ANTHROPIC_API_KEY
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not configured")

        self.client = Anthropic(api_key=self.api_key)

    # Maximum characters per chunk for processing
    # Increased to 25000 to reduce number of API calls
    MAX_CHUNK_SIZE = 25000  # ~6250 tokens, still safe for Claude's context

    def anonymize(self, text: str, progress_callback=None) -> Dict[str, Any]:
        """
        Anonymize text using Claude API.

        Args:
            text: Hebrew legal text to anonymize
            progress_callback: Optional callback function(percent, message) for progress updates

        Returns:
            Dictionary with:
            {
                "anonymized_text": str,           # Full anonymized text
                "report": List[Dict],             # List of identified items
                "risk_level": str,                # "low"|"medium"|"high"
                "requires_review": bool           # True if manual review needed
            }

        Raises:
            AnonymizationError: If anonymization fails
        """
        if not text or not text.strip():
            raise AnonymizationError("Text cannot be empty")

        # Check if text needs to be chunked
        if len(text) > self.MAX_CHUNK_SIZE:
            return self._anonymize_chunked(text, progress_callback)
        else:
            if progress_callback:
                progress_callback(10, "מתחיל אנונימיזציה...")
            result = self._anonymize_single(text)
            if progress_callback:
                progress_callback(100, "הושלם")
            return result

    def _anonymize_single(self, text: str, max_retries: int = 2) -> Dict[str, Any]:
        """Anonymize a single chunk of text with retry logic."""
        user_prompt = self._build_user_prompt(text)
        last_error = None

        for attempt in range(max_retries + 1):
            try:
                response = self.client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=16000,
                    system=self.SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": user_prompt}]
                )

                response_text = response.content[0].text
                result = self._parse_response(response_text)
                return self._transform_result(result)

            except (AnonymizationError, json.JSONDecodeError) as e:
                last_error = e
                if attempt < max_retries:
                    print(f"[Anonymizer] Attempt {attempt + 1} failed: {str(e)[:100]}. Retrying...")
                    continue

            except Exception as e:
                last_error = e
                if attempt < max_retries:
                    print(f"[Anonymizer] Attempt {attempt + 1} failed: {str(e)[:100]}. Retrying...")
                    continue

        raise AnonymizationError(f"Anonymization failed after {max_retries + 1} attempts: {str(last_error)}")

    def _anonymize_chunked(self, text: str, progress_callback=None) -> Dict[str, Any]:
        """Anonymize large text by processing chunks sequentially for reliability."""
        chunks = self._split_into_chunks(text)
        total_chunks = len(chunks)

        print(f"[Anonymizer] Processing {total_chunks} chunks sequentially")

        all_reports = []
        anonymized_parts = []
        highest_risk = "low"
        needs_review = False
        review_notes = []

        # Process chunks one by one for reliability
        for chunk_idx, chunk in enumerate(chunks):
            # Update progress at start of each chunk
            if progress_callback:
                percent = int((chunk_idx / total_chunks) * 90) + 5
                progress_callback(percent, f"מעבד חלק {chunk_idx+1}/{total_chunks}...")

            print(f"[Anonymizer] Processing chunk {chunk_idx+1}/{total_chunks}")

            try:
                result = self._anonymize_single(chunk)

                anonymized_parts.append(result["anonymized_text"])
                all_reports.extend(result.get("report", []))

                # Update risk level (take highest)
                chunk_risk = result.get("risk_level", "low")
                if chunk_risk == "high" or (chunk_risk == "medium" and highest_risk == "low"):
                    highest_risk = chunk_risk

                if result.get("requires_review"):
                    needs_review = True
                    if result.get("review_notes"):
                        review_notes.append(f"חלק {chunk_idx+1}: {result['review_notes']}")

                print(f"[Anonymizer] Completed chunk {chunk_idx+1}/{total_chunks}")

            except Exception as e:
                print(f"[Anonymizer] Error in chunk {chunk_idx+1}: {str(e)}")
                # Keep original text for failed chunks
                anonymized_parts.append(chunk)
                needs_review = True
                review_notes.append(f"חלק {chunk_idx+1}: שגיאה בעיבוד - {str(e)}")

        if progress_callback:
            progress_callback(100, "הושלם")

        return {
            "anonymized_text": "\n\n".join(anonymized_parts),
            "report": all_reports,
            "risk_level": highest_risk,
            "requires_review": needs_review,
            "review_notes": "\n".join(review_notes) if review_notes else ""
        }

    def _split_into_chunks(self, text: str) -> List[str]:
        """Split text into chunks at paragraph boundaries."""
        import re

        # Normalize line endings and split on various paragraph separators
        # Handle \r\r, \r\n\r\n, \n\n patterns
        normalized = text.replace('\r\n', '\n').replace('\r', '\n')
        # Split on double newlines or multiple newlines
        paragraphs = re.split(r'\n\s*\n', normalized)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        # If still no good paragraphs, force split by character count
        if len(paragraphs) <= 1 and len(text) > self.MAX_CHUNK_SIZE:
            print(f"[Anonymizer] No paragraph breaks found, splitting by size")
            return self._force_split_by_size(text)

        chunks = []
        current_chunk = []
        current_size = 0

        for para in paragraphs:
            para_size = len(para)

            # If a single paragraph is too large, force split it
            if para_size > self.MAX_CHUNK_SIZE:
                if current_chunk:
                    chunks.append('\n\n'.join(current_chunk))
                    current_chunk = []
                    current_size = 0
                # Split large paragraph by sentences or force by size
                chunks.extend(self._force_split_by_size(para))
            elif current_size + para_size > self.MAX_CHUNK_SIZE and current_chunk:
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = [para]
                current_size = para_size
            else:
                current_chunk.append(para)
                current_size += para_size + 2  # +2 for \n\n

        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))

        return chunks if chunks else [text]

    def _force_split_by_size(self, text: str) -> List[str]:
        """Force split text by size when no paragraph breaks exist."""
        import re

        chunks = []
        # Try to split at sentence boundaries first
        sentences = re.split(r'(?<=[.!?])\s+', text)

        current_chunk = []
        current_size = 0

        for sentence in sentences:
            sentence_size = len(sentence)

            if sentence_size > self.MAX_CHUNK_SIZE:
                # Even a single sentence is too large, split by words
                if current_chunk:
                    chunks.append(' '.join(current_chunk))
                    current_chunk = []
                    current_size = 0
                # Split sentence by character limit
                words = sentence.split()
                word_chunk = []
                word_size = 0
                for word in words:
                    if word_size + len(word) + 1 > self.MAX_CHUNK_SIZE and word_chunk:
                        chunks.append(' '.join(word_chunk))
                        word_chunk = [word]
                        word_size = len(word)
                    else:
                        word_chunk.append(word)
                        word_size += len(word) + 1
                if word_chunk:
                    chunks.append(' '.join(word_chunk))
            elif current_size + sentence_size > self.MAX_CHUNK_SIZE and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = [sentence]
                current_size = sentence_size
            else:
                current_chunk.append(sentence)
                current_size += sentence_size + 1

        if current_chunk:
            chunks.append(' '.join(current_chunk))

        return chunks if chunks else [text]

    def _build_user_prompt(self, text: str) -> str:
        """
        Build user prompt for Claude.

        Args:
            text: Text to anonymize

        Returns:
            Formatted prompt
        """
        return f"""אנא אנוניזם את הטקסט המשפטי הבא.

זהה כל מידע אישי מזהה והחלף אותו בתחליפים אנונימיים עקביים.

**חשוב**: שמור על עקביות - אותו שם תמיד מקבל אותו תחליף!

החזר JSON בפורמט הבא בלבד (ללא טקסט נוסף):

```json
{{
  "anonymized_text": "הטקסט המלא המאונוניזם כאן",
  "identified_items": [
    {{
      "original": "הטקסט המקורי",
      "category": "person_name|official_id|contact_info|property_details|sensitive_info",
      "confidence": "high|medium|low",
      "replacement": "התחליף",
      "reasoning": "הסבר קצר למה זוהה"
    }}
  ],
  "overall_risk": "low|medium|high",
  "requires_manual_review": true/false,
  "review_notes": "הערות חשובות אם נדרשת בדיקה ידנית"
}}
```

הטקסט לאנונימיזציה:

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
            AnonymizationError: If JSON cannot be parsed
        """
        # Log response for debugging
        print(f"[Anonymizer] Response length: {len(response_text)}")
        print(f"[Anonymizer] Response preview: {response_text[:300]}...")

        # Use the robust JSON parser
        result = safe_parse_json(response_text)

        if result is None:
            # If parsing completely fails, create a fallback response
            print(f"[Anonymizer] JSON parsing failed, using fallback")
            return {
                "anonymized_text": response_text if response_text else "אירעה שגיאה באנונימיזציה",
                "identified_items": [],
                "overall_risk": "high",
                "requires_manual_review": True,
                "review_notes": "לא התקבל JSON תקין מהמודל - נדרשת בדיקה ידנית"
            }

        return result

    def _transform_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform Claude's response to required format.

        Args:
            result: Parsed JSON from Claude

        Returns:
            Transformed result dictionary

        Raises:
            AnonymizationError: If required fields are missing
        """
        # Validate required fields
        required_fields = ["anonymized_text", "identified_items", "overall_risk", "requires_manual_review"]

        for field in required_fields:
            if field not in result:
                raise AnonymizationError(f"Missing required field in response: {field}")

        # Validate risk level
        valid_risks = ["low", "medium", "high"]
        if result["overall_risk"] not in valid_risks:
            result["overall_risk"] = "medium"  # Default to medium if invalid

        # Validate identified items structure
        for item in result.get("identified_items", []):
            required_item_fields = ["original", "category", "confidence", "replacement"]
            for field in required_item_fields:
                if field not in item:
                    raise AnonymizationError(f"Missing field '{field}' in identified item")

        # Transform to required format
        return {
            "anonymized_text": result["anonymized_text"],
            "report": result["identified_items"],  # Rename to 'report'
            "risk_level": result["overall_risk"],  # Rename to 'risk_level'
            "requires_review": result["requires_manual_review"],  # Rename to 'requires_review'
            "review_notes": result.get("review_notes", "")
        }

    def get_stats(self, report: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get statistics from anonymization report.

        Args:
            report: List of identified items from anonymize()

        Returns:
            Dictionary with statistics:
            {
                'total_items': int,
                'by_category': dict,
                'by_confidence': dict,
                'high_risk_count': int
            }
        """
        if not report:
            return {
                'total_items': 0,
                'by_category': {},
                'by_confidence': {},
                'high_risk_count': 0
            }

        # Count by category
        by_category = {}
        for item in report:
            category = item.get("category", "unknown")
            by_category[category] = by_category.get(category, 0) + 1

        # Count by confidence
        by_confidence = {}
        for item in report:
            confidence = item.get("confidence", "unknown")
            by_confidence[confidence] = by_confidence.get(confidence, 0) + 1

        # Count high-risk items (sensitive_info or official_id with high confidence)
        high_risk_count = sum(
            1 for item in report
            if item.get("category") in ["sensitive_info", "official_id"]
            and item.get("confidence") == "high"
        )

        return {
            'total_items': len(report),
            'by_category': by_category,
            'by_confidence': by_confidence,
            'high_risk_count': high_risk_count
        }
