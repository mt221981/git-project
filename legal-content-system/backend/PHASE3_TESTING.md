# Phase 3: Anonymization Service - Testing Guide

## Overview

Phase 3 implements verdict anonymization using Claude API. The system identifies and replaces personal information while maintaining text readability and generating detailed reports.

## What Was Implemented

### 1. Anthropic Client Wrapper (`app/utils/anthropic_client.py`)
- Convenient wrapper for Claude API calls
- Support for structured output with lower temperature
- Token counting estimation

### 2. Anonymization Prompts (`app/services/prompts.py`)
- Hebrew-language prompts for anonymization
- Privacy risk assessment prompts
- Metadata extraction prompts (for future phases)

### 3. Anonymization Service (`app/services/anonymization_service.py`)
- Main anonymization logic using Claude API
- Privacy risk assessment (LOW/MEDIUM/HIGH)
- Detailed change tracking and reporting
- Manual review flagging

### 4. New API Endpoints

#### POST `/api/v1/verdicts/{verdict_id}/anonymize`
Anonymize a verdict for the first time.

#### POST `/api/v1/verdicts/{verdict_id}/re-anonymize`
Re-anonymize a verdict (clears previous anonymization).

#### GET `/api/v1/verdicts/statistics/anonymization`
Get anonymization statistics.

## Setup

1. Ensure you have your Anthropic API key in `.env`:
```bash
ANTHROPIC_API_KEY=your-api-key-here
```

2. Install/update dependencies:
```bash
pip install -r requirements.txt
```

3. Start the server:
```bash
python app/main.py
```

## Testing Workflow

### Step 1: Upload a Verdict

```bash
curl -X POST "http://localhost:8000/api/v1/verdicts/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@path/to/verdict.pdf"
```

Response:
```json
{
  "message": "File uploaded and processed successfully",
  "verdict_id": 1,
  "file_hash": "abc123...",
  "status": "extracted"
}
```

### Step 2: Anonymize the Verdict

```bash
curl -X POST "http://localhost:8000/api/v1/verdicts/1/anonymize"
```

This will:
1. Send the verdict text to Claude API
2. Identify personal information (names, IDs, addresses, etc.)
3. Replace with anonymous placeholders
4. Generate a detailed anonymization report
5. Assess privacy risk level
6. Flag for manual review if needed

Response includes:
```json
{
  "id": 1,
  "status": "anonymized",
  "anonymized_text": "...",
  "anonymization_report": {
    "changes": [
      {
        "type": "name",
        "original": "ישראל ישראלי",
        "replacement": "התובע",
        "context": "...",
        "risk_level": "medium"
      }
    ],
    "change_count": 15,
    "risk_explanation": "...",
    "review_notes": "..."
  },
  "privacy_risk_level": "medium",
  "requires_manual_review": true,
  ...
}
```

### Step 3: Review Anonymization

```bash
curl -X GET "http://localhost:8000/api/v1/verdicts/1"
```

Check:
- `anonymized_text` - The anonymized version
- `anonymization_report.changes` - What was changed
- `privacy_risk_level` - Risk assessment
- `requires_manual_review` - Whether manual review is needed
- `review_notes` - Notes for reviewer

### Step 4: Re-anonymize if Needed

If the anonymization wasn't satisfactory:

```bash
curl -X POST "http://localhost:8000/api/v1/verdicts/1/re-anonymize"
```

### Step 5: Check Statistics

```bash
curl -X GET "http://localhost:8000/api/v1/verdicts/statistics/anonymization"
```

Response:
```json
{
  "total_anonymized": 10,
  "by_risk_level": {
    "low": 3,
    "medium": 5,
    "high": 2
  },
  "pending_manual_review": 7
}
```

## Anonymization Features

### What Gets Anonymized

1. **Names** (first, last, full)
   - Original: "ישראל ישראלי"
   - Replacement: "התובע" / "הנתבע" / "העד מס' 1"

2. **ID Numbers**
   - Original: "123456789"
   - Replacement: "***456789" (last 3 digits kept)

3. **Addresses**
   - Original: "רחוב הרצל 10, תל אביב"
   - Replacement: "רחוב [X] מספר [Y], [עיר]"

4. **Phone Numbers**
   - Original: "050-1234567"
   - Replacement: "05X-XXX-XXXX"

5. **Email Addresses**
   - Original: "user@example.com"
   - Replacement: "[user]@[domain]"

6. **Other identifying information** as detected

### What Doesn't Get Anonymized

- Court names and judges
- Case numbers
- Law references and citations
- Amounts and dates
- Legal precedents

### Privacy Risk Levels

- **LOW**: No sensitive info, fully anonymized, safe to publish
- **MEDIUM**: Some identifying info, requires review
- **HIGH**: Highly sensitive, mandatory manual review before publishing

## Using via Python

```python
import requests

# Upload verdict
with open("verdict.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/v1/verdicts/upload",
        files={"file": f}
    )
verdict_id = response.json()["verdict_id"]

# Anonymize
response = requests.post(
    f"http://localhost:8000/api/v1/verdicts/{verdict_id}/anonymize"
)

result = response.json()
print(f"Status: {result['status']}")
print(f"Risk Level: {result['privacy_risk_level']}")
print(f"Needs Review: {result['requires_manual_review']}")
print(f"Changes Made: {len(result['anonymization_report']['changes'])}")
```

## Interactive API Documentation

Visit http://localhost:8000/docs to use the interactive Swagger UI for testing all endpoints.

## Troubleshooting

### Error: "Anthropic API error"
- Check that your `ANTHROPIC_API_KEY` is set correctly in `.env`
- Verify the API key is valid and has available credits

### Error: "Text too long for anonymization"
- The text exceeds ~100k tokens
- Solution: Split the verdict into smaller sections

### Error: "Verdict must be extracted before anonymization"
- The verdict status is 'new' instead of 'extracted'
- Ensure file upload completed successfully

### Anonymization seems incorrect
- Use the re-anonymize endpoint to try again
- Claude's responses can vary slightly between runs
- Check the anonymization_report for details on what was changed

## Next Steps

After Phase 3, you can proceed to:
- **Phase 4**: AI Analysis and Article Generation
- **Phase 5**: WordPress Publishing
- **Phase 6**: Frontend Interface

The anonymized text will be used in subsequent phases for article generation and publishing.
