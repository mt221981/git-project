# Phase 3: API Integration Documentation

This document describes the integration of FileProcessor and Anonymizer services into the API endpoints.

## Overview

Phase 3 integrates the core services (FileProcessor and Anonymizer) from Phase 2 into the existing API infrastructure, creating a complete upload and anonymization workflow.

## Architecture

```
User Upload
    ↓
┌─────────────────────────────────────────┐
│   POST /api/verdicts/upload             │
│   (verdicts.py router)                  │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│   VerdictService.process_file_upload()  │
│   Uses: FileProcessor                   │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│   FileProcessor                         │
│   • calculate_hash()                    │
│   • extract_text()                      │
│   • clean_text()                        │
│   • get_text_stats()                    │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│   Verdict saved to DB                   │
│   Status: EXTRACTED                     │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│   POST /api/verdicts/{id}/anonymize     │
│   (verdicts.py router)                  │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│   AnonymizationService                  │
│     .anonymize_verdict()                │
│   Uses: Anonymizer                      │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│   Anonymizer                            │
│   • anonymize()                         │
│   • Identify PII                        │
│   • Replace with placeholders           │
│   • Assess risk                         │
│   • Generate report                     │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│   Verdict updated in DB                 │
│   Status: ANONYMIZED                    │
│   Privacy risk assessed                 │
└─────────────────────────────────────────┘
```

## Changes Made

### 1. VerdictService (`app/services/verdict_service.py`)

**Updated `__init__`**:
```python
def __init__(
    self,
    db: Session,
    file_storage: Optional[FileStorageService] = None,
    file_processor: Optional[FileProcessor] = None  # NEW
):
    self.db = db
    self.file_storage = file_storage or FileStorageService()
    self.file_processor = file_processor or FileProcessor()  # NEW
```

**Updated `process_file_upload`**:
- ✅ Uses `FileProcessor.calculate_hash()` instead of old `calculate_file_hash()`
- ✅ Uses `FileProcessor.extract_text()` instead of old `extract_text_from_file()`
- ✅ Uses `FileProcessor.clean_text()` instead of old `clean_text()`
- ✅ Calls `FileProcessor.get_text_stats()` and stores in verdict.metadata
- ✅ Raises `FileProcessingError` instead of old `TextExtractionError`

**Benefits**:
- Better Hebrew text handling (6 encoding types)
- Improved text cleaning (nikud removal, header detection)
- Consistent text processing
- Text statistics available

### 2. AnonymizationService (`app/services/anonymization_service.py`)

**Updated `__init__`**:
```python
def __init__(self, db: Session, anonymizer: Optional[Anonymizer] = None):
    self.db = db
    self.anonymizer = anonymizer or Anonymizer()  # NEW
```

**Updated `anonymize_text`**:
- ✅ Uses `Anonymizer.anonymize()` instead of direct Claude API calls
- ✅ Transforms result to match expected format
- ✅ Simplified - no longer needs separate parsing/validation

**Removed methods**:
- ❌ `_parse_anonymization_response()` - Now handled by Anonymizer
- ❌ `assess_privacy_risk()` - Now integrated into Anonymizer

**Updated `anonymize_verdict`**:
- ✅ Simplified risk assessment (built into Anonymizer)
- ✅ No separate risk assessment call needed
- ✅ Cleaner code, fewer API calls

**Benefits**:
- More accurate PII detection (5 categories)
- Consistent replacements across document
- Confidence levels for each item
- Integrated risk assessment
- Hebrew-optimized prompts

### 3. Verdicts Router (`app/routers/verdicts.py`)

**Updated imports**:
```python
from app.services.file_processor import FileProcessingError  # NEW
# Removed: from app.utils import TextExtractionError
```

**Updated exception handling in `/upload`**:
```python
except FileProcessingError as e:  # Changed from TextExtractionError
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=f"Failed to process file: {str(e)}"
    )
```

**No changes needed to**:
- `/anonymize` endpoint - Already used AnonymizationService
- Other endpoints - Not affected

## API Endpoints

### Upload Verdict

**Endpoint**: `POST /api/verdicts/upload`

**Request**:
```http
POST /api/verdicts/upload
Content-Type: multipart/form-data

file: <PDF|TXT|DOCX file>
```

**Response**:
```json
{
  "message": "File uploaded and processed successfully",
  "verdict_id": 1,
  "file_hash": "a1b2c3...",
  "status": "extracted"
}
```

**Process**:
1. Validates file size (< 50MB)
2. Validates file type (.pdf, .txt, .doc, .docx)
3. Calculates hash (SHA-256)
4. Checks for duplicates
5. Extracts text (multi-encoding support)
6. Cleans text (removes headers, nikud, etc.)
7. Gets text statistics
8. Extracts metadata (case number, court, judge)
9. Stores file
10. Creates verdict record (status: EXTRACTED)

**Possible Errors**:
- `413`: File too large (> 50MB)
- `400`: Unsupported file type
- `409`: Duplicate file
- `422`: Failed to process file
- `500`: Server error

### Anonymize Verdict

**Endpoint**: `POST /api/verdicts/{verdict_id}/anonymize`

**Request**:
```http
POST /api/verdicts/1/anonymize
```

**Response**:
```json
{
  "id": 1,
  "status": "anonymized",
  "privacy_risk_level": "medium",
  "requires_manual_review": false,
  "anonymized_text": "התובע, ת.ז. ***789...",
  "anonymization_report": {
    "changes": [
      {
        "original": "ישראל ישראלי",
        "category": "person_name",
        "confidence": "high",
        "replacement": "התובע",
        "reasoning": "שם מלא של תובע"
      }
    ],
    "change_count": 12,
    "risk_explanation": "Risk level: medium",
    "review_notes": ""
  }
}
```

**Process**:
1. Validates verdict exists
2. Validates status is EXTRACTED
3. Sets status to ANONYMIZING
4. Gets text (cleaned_text or original_text)
5. Calls Anonymizer to anonymize text
6. Parses result
7. Maps risk level to enum
8. Stores anonymized text and report
9. Updates status to ANONYMIZED
10. Flags for manual review if needed

**Possible Errors**:
- `400`: Verdict not found or wrong status
- `422`: Anonymization failed
- `500`: Server error

### Re-Anonymize Verdict

**Endpoint**: `POST /api/verdicts/{verdict_id}/re-anonymize`

Useful if previous anonymization was incorrect. Clears old anonymization and performs it again.

## Data Flow

### Upload Flow

```
File Bytes
    ↓
Calculate Hash → Check Duplicate
    ↓
Extract Text (PyPDF2/python-docx)
    ↓
Clean Text
    - Remove page numbers
    - Remove headers/footers
    - Fix broken lines
    - Remove nikud
    - Normalize quotes/dashes
    - Remove extra whitespace
    ↓
Get Statistics
    - Word count
    - Character count
    - Language detection
    ↓
Extract Metadata
    - Case number
    - Court name
    - Judge name
    ↓
Store in Database
    - original_text
    - cleaned_text
    - metadata (with stats)
    - status: EXTRACTED
```

### Anonymization Flow

```
Cleaned Text
    ↓
Anonymizer.anonymize()
    ↓
Claude API Request
    - System prompt (Hebrew instructions)
    - User prompt (text to anonymize)
    ↓
Claude Response (JSON)
    - anonymized_text
    - identified_items[]
    - overall_risk
    - requires_manual_review
    - review_notes
    ↓
Transform Result
    - Rename fields to match service format
    ↓
Update Database
    - anonymized_text
    - anonymization_report
    - privacy_risk_level
    - requires_manual_review
    - status: ANONYMIZED
```

## Testing

### Unit Tests

**File Processor**:
```bash
python backend/test_services.py
```

Tests:
- Hash calculation
- Text extraction (PDF, DOCX, TXT)
- Text cleaning
- Hebrew encoding detection
- Statistics generation

**Anonymizer**:
```bash
python backend/test_services.py
```

Tests:
- Anonymization with Claude API
- Category detection (5 types)
- Risk assessment
- Confidence levels
- Statistics generation

**Note**: Requires `ANTHROPIC_API_KEY` in `.env`

### Integration Tests

**Complete Workflow**:
```bash
python backend/test_integration.py
```

Tests:
- File upload and processing
- Duplicate detection
- Text extraction and cleaning
- Anonymization
- Risk assessment
- Database updates
- Statistics

Creates an in-memory database and tests the complete flow from upload to anonymization.

## Configuration

### Environment Variables

Required in `.env`:

```bash
# Database
DATABASE_URL=sqlite:///./legal_content.db

# AI Services
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Security
SECRET_KEY=your-secret-key-here

# File Upload
MAX_UPLOAD_SIZE_MB=50
ALLOWED_FILE_EXTENSIONS=[".pdf", ".txt", ".doc", ".docx"]

# CORS
ALLOWED_ORIGINS=["http://localhost:3000", "http://localhost:5173"]
```

## Usage Examples

### Python Client

```python
import requests

# Upload file
with open('verdict.pdf', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/verdicts/upload',
        files={'file': f}
    )
verdict = response.json()
print(f"Uploaded: {verdict['verdict_id']}")

# Anonymize
response = requests.post(
    f"http://localhost:8000/api/verdicts/{verdict['verdict_id']}/anonymize"
)
anonymized = response.json()
print(f"Anonymized: {len(anonymized['anonymization_report']['changes'])} items")
print(f"Risk: {anonymized['privacy_risk_level']}")
```

### cURL

```bash
# Upload file
curl -X POST http://localhost:8000/api/verdicts/upload \
  -F "file=@verdict.pdf"

# Anonymize
curl -X POST http://localhost:8000/api/verdicts/1/anonymize
```

### Frontend Integration

```typescript
// Upload file
const formData = new FormData();
formData.append('file', file);

const uploadResponse = await verdictApi.upload(formData);
const verdictId = uploadResponse.data.verdict_id;

// Anonymize
const anonymizeResponse = await verdictApi.anonymize(verdictId);
console.log('Risk:', anonymizeResponse.data.privacy_risk_level);
```

## Performance

### File Processing

- **Small files** (< 1MB): ~1-2 seconds
- **Medium files** (1-10MB): ~2-5 seconds
- **Large files** (10-50MB): ~5-15 seconds

**Bottlenecks**:
- PDF extraction (PyPDF2)
- Text cleaning (regex operations)

### Anonymization

- **Short texts** (< 1000 words): ~3-5 seconds
- **Medium texts** (1000-5000 words): ~5-10 seconds
- **Long texts** (5000-10000 words): ~10-20 seconds

**Bottlenecks**:
- Claude API call (~80% of time)
- Network latency

**Cost**:
- ~$0.003 per 1000 input tokens
- ~$0.015 per 1000 output tokens
- Average verdict: ~$0.10-$0.30

## Error Handling

### File Processing Errors

**Unsupported file type**:
```json
{
  "detail": "Unsupported file type. Allowed: pdf, txt, doc, docx"
}
```

**File too large**:
```json
{
  "detail": "File too large. Maximum size: 50MB"
}
```

**Duplicate file**:
```json
{
  "detail": "File already uploaded. Verdict ID: 5. Use the existing verdict instead of uploading duplicate."
}
```

**Extraction failed**:
```json
{
  "detail": "Failed to process file: PDF is password protected"
}
```

### Anonymization Errors

**Wrong status**:
```json
{
  "detail": "Verdict must be extracted before anonymization"
}
```

**API failure**:
```json
{
  "detail": "Anonymization failed: API rate limit exceeded"
}
```

**No API key**:
```json
{
  "detail": "Anonymization failed: ANTHROPIC_API_KEY not configured"
}
```

## Security Considerations

1. **File Upload**:
   - Validate file type and size
   - Calculate hash before processing
   - Store files with hash-based names
   - Don't trust user-supplied filenames

2. **Personal Information**:
   - Original text contains PII - restrict access
   - Anonymization report contains original values - protect carefully
   - Only show anonymized text to non-authorized users
   - Log access to original texts

3. **API Keys**:
   - Never commit `.env` file
   - Rotate API keys periodically
   - Monitor API usage for anomalies

4. **Manual Review**:
   - Always review high-risk cases before publishing
   - Don't skip review flags
   - Verify critical anonymizations (ID numbers, minors)

## Monitoring

### Metrics to Track

1. **Upload Success Rate**:
   - Failed extractions
   - File type distribution
   - Average file size

2. **Anonymization Metrics**:
   - Success rate
   - Average items per verdict
   - Risk level distribution
   - Manual review rate

3. **Performance**:
   - Processing time per file size
   - API response time
   - Database query time

4. **Costs**:
   - API token usage
   - Cost per verdict
   - Monthly totals

### Logging

```python
import logging

logger = logging.getLogger(__name__)

# Log file uploads
logger.info(f"File uploaded: {verdict_id}, hash: {file_hash}")

# Log anonymization
logger.info(f"Anonymized verdict {verdict_id}: {item_count} items, risk: {risk}")

# Log failures
logger.error(f"Anonymization failed for {verdict_id}: {error}")
```

## Troubleshooting

### File Upload Issues

**Problem**: "Failed to extract text from file"

**Solutions**:
1. Check file is not corrupted
2. Verify PDF is not password-protected
3. Try converting DOC to DOCX
4. Check file encoding for TXT files

### Anonymization Issues

**Problem**: "Anonymization failed"

**Solutions**:
1. Check ANTHROPIC_API_KEY is set
2. Verify API key is valid
3. Check API rate limits
4. Review text length (< 100k tokens)

### Duplicate Detection

**Problem**: False positive duplicate detection

**Solutions**:
1. Verify files are actually different
2. Check hash calculation
3. Review database for hash collisions (extremely rare)

## Next Steps

After Phase 3, the system supports:
- ✅ File upload with multi-format support
- ✅ Duplicate detection
- ✅ Text extraction and cleaning
- ✅ Hebrew text handling
- ✅ Anonymization with Claude API
- ✅ Risk assessment
- ✅ Manual review flagging

**Ready for**:
- Phase 4: AI analysis and article generation
- Phase 5: WordPress publishing
- Phase 6: Frontend integration

## Support

For issues:
1. Run unit tests: `python backend/test_services.py`
2. Run integration tests: `python backend/test_integration.py`
3. Check logs for errors
4. Verify configuration in `.env`
5. Review SERVICES.md for service details
