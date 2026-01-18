# Core Services Documentation

This document describes the core file processing and anonymization services.

## FileProcessor Service

The `FileProcessor` service handles document processing tasks including text extraction, hash calculation, and text cleaning.

### Location
`app/services/file_processor.py`

### Features

#### 1. Hash Calculation
```python
from app.services import FileProcessor

processor = FileProcessor()
file_hash = processor.calculate_hash(file_content)  # Returns SHA-256 hash
```

**Purpose**: Calculate unique hash for duplicate detection

**Returns**: 64-character hexadecimal string

#### 2. Text Extraction
```python
text = processor.extract_text(file_content, '.pdf')
```

**Supported file types**:
- `.pdf` - Uses PyPDF2
- `.docx` - Uses python-docx
- `.doc` - Attempts DOCX parser
- `.txt` - UTF-8 and Hebrew encodings

**Encoding support for TXT files**:
- UTF-8
- UTF-8 with BOM
- Windows-1255 (Hebrew)
- ISO-8859-8 (Hebrew)
- CP1255 (Hebrew code page)
- Latin-1 (fallback)

**Returns**: Extracted text as string

**Raises**: `FileProcessingError` if extraction fails

#### 3. Text Cleaning
```python
cleaned_text = processor.clean_text(raw_text)
```

**Cleaning operations**:
- Removes page numbers (standalone numbers on lines)
- Removes common headers/footers ("עמוד X מתוך Y")
- Removes repeated header patterns
- Fixes broken lines (joins mid-sentence splits)
- Normalizes Hebrew text:
  - Removes nikud (vowel points)
  - Normalizes quotes (״ → ")
  - Normalizes dashes
  - Removes zero-width characters
- Removes extra whitespace
- Normalizes line breaks (max 2 consecutive)

**Returns**: Cleaned text string

#### 4. Text Statistics
```python
stats = processor.get_text_stats(text)
```

**Returns**:
```python
{
    'char_count': int,
    'word_count': int,
    'line_count': int,
    'paragraph_count': int,
    'has_hebrew': bool,
    'has_english': bool
}
```

### Example Usage

```python
from app.services import FileProcessor, FileProcessingError

processor = FileProcessor()

try:
    # Calculate hash for duplicate check
    file_hash = processor.calculate_hash(file_content)

    # Extract text from uploaded file
    raw_text = processor.extract_text(file_content, '.pdf')

    # Clean the text
    cleaned_text = processor.clean_text(raw_text)

    # Get statistics
    stats = processor.get_text_stats(cleaned_text)
    print(f"Extracted {stats['word_count']} words")

except FileProcessingError as e:
    print(f"Processing failed: {e}")
```

---

## Anonymizer Service

The `Anonymizer` service uses Claude API to identify and replace personal information in Hebrew legal documents.

### Location
`app/services/anonymizer.py`

### Features

#### Anonymization Categories

1. **person_name** - Names of people
   - Plaintiffs, defendants, witnesses
   - Family members
   - Minors (especially important!)
   - Replacements: "התובע", "הנתבע", "העד מס' 1", "הקטין"

2. **official_id** - Official identification
   - ID numbers (ת.ז.)
   - Passport numbers
   - Business licenses
   - Replacements: "ת.ז. ***123" (last 3 digits)

3. **contact_info** - Contact details
   - Phone numbers
   - Email addresses
   - Replacements: "[טלפון הוסר]", "[אימייל הוסר]"

4. **property_details** - Property information
   - Full addresses
   - Vehicle numbers
   - Bank account numbers
   - Replacements: "[כתובת הוסרה]", "חשבון בנק ***456"

5. **sensitive_info** - Sensitive information
   - Medical details
   - Ages of minors
   - Intimate details
   - Replacements: "[מידע רפואי הוסר]", "קטין בן X"

#### What is NOT Anonymized

- Judge names (public information)
- Lawyer names (public information)
- Large company names
- Case numbers
- Court names
- Law citations
- Monetary amounts
- Dates (unless identifying minors)

### API

#### Initialize
```python
from app.services import Anonymizer

anonymizer = Anonymizer()  # Uses ANTHROPIC_API_KEY from settings
# or
anonymizer = Anonymizer(api_key="your-api-key")
```

#### Anonymize Text
```python
result = anonymizer.anonymize(hebrew_legal_text)
```

**Returns**:
```python
{
    "anonymized_text": str,       # Full anonymized text
    "report": [                   # List of identified items
        {
            "original": str,           # Original text
            "category": str,           # Category (see above)
            "confidence": str,         # "high"|"medium"|"low"
            "replacement": str,        # Replacement text
            "reasoning": str          # Explanation
        }
    ],
    "risk_level": str,            # "low"|"medium"|"high"
    "requires_review": bool,      # Manual review needed?
    "review_notes": str          # Notes for reviewer
}
```

#### Get Statistics
```python
stats = anonymizer.get_stats(result['report'])
```

**Returns**:
```python
{
    'total_items': int,
    'by_category': {              # Count per category
        'person_name': int,
        'official_id': int,
        ...
    },
    'by_confidence': {            # Count per confidence level
        'high': int,
        'medium': int,
        'low': int
    },
    'high_risk_count': int        # Sensitive items count
}
```

### Risk Levels

**Low Risk**:
- No sensitive information
- Fully anonymized
- Only public information removed

**Medium Risk**:
- Regular personal information
- Moderate identification potential
- Standard review recommended

**High Risk**:
- Very sensitive information (medical, minors, ID numbers)
- High identification potential
- **Manual review required**

### Confidence Levels

**High**: Definitely personal identifying information
- Full names, ID numbers, phone numbers

**Medium**: Likely personal information
- First names only, partial addresses

**Low**: Possibly personal information
- Uncertain context

### Manual Review Triggers

The system flags for manual review when:
- Medical or intimate information found
- Minors involved
- ID numbers or bank details found
- Multiple identifying details together
- Uncertain items found

### Example Usage

```python
from app.services import Anonymizer, AnonymizationError

anonymizer = Anonymizer()

legal_text = """
פסק דין

תובע: ישראל ישראלי, ת.ז. 123456789
כתובת: רחוב הרצל 10, תל אביב
טלפון: 052-1234567

נתבע: דוד כהן

העובדות: התובע, מר ישראל ישראלי, עבד...
"""

try:
    result = anonymizer.anonymize(legal_text)

    # Check result
    print(f"Risk level: {result['risk_level']}")
    print(f"Items found: {len(result['report'])}")
    print(f"Requires review: {result['requires_review']}")

    # Get statistics
    stats = anonymizer.get_stats(result['report'])
    print(f"Names found: {stats['by_category'].get('person_name', 0)}")
    print(f"IDs found: {stats['by_category'].get('official_id', 0)}")

    # Use anonymized text
    anonymized = result['anonymized_text']
    # "התובע, ת.ז. ***789..." instead of "ישראל ישראלי, ת.ז. 123456789..."

    # Show what was changed
    for item in result['report']:
        print(f"{item['category']}: {item['original']} → {item['replacement']}")

except AnonymizationError as e:
    print(f"Anonymization failed: {e}")
```

### Best Practices

1. **Always check risk level**
   ```python
   if result['risk_level'] == 'high' or result['requires_review']:
       # Send for manual review
       pass
   ```

2. **Verify critical items**
   ```python
   for item in result['report']:
       if item['category'] == 'official_id' and item['confidence'] == 'high':
           # Extra verification for ID numbers
           pass
   ```

3. **Keep original text**
   ```python
   # Store both original and anonymized
   verdict.original_text = original
   verdict.anonymized_text = result['anonymized_text']
   verdict.anonymization_report = result['report']
   ```

4. **Handle errors gracefully**
   ```python
   try:
       result = anonymizer.anonymize(text)
   except AnonymizationError as e:
       # Log error, retry, or alert admin
       logger.error(f"Anonymization failed: {e}")
       verdict.status = "anonymization_failed"
   ```

---

## Testing

Run the test script to validate both services:

```bash
cd backend
python test_services.py
```

The test script validates:
- Hash calculation
- Text extraction from TXT files
- Text cleaning and normalization
- Hebrew text handling
- Anonymization with Claude API
- Statistics generation

**Note**: Anonymizer tests require `ANTHROPIC_API_KEY` in `.env` file.

---

## Error Handling

### FileProcessingError

Raised when:
- Unsupported file type
- PDF is password protected
- No text extracted from file
- Encoding detection failed (TXT files)
- File is corrupted

### AnonymizationError

Raised when:
- Text is empty
- Claude API call fails
- Response is not valid JSON
- Required fields missing in response
- API key not configured

---

## Integration with Verdict Processing

These services are used in the verdict processing workflow:

```python
from app.services import FileProcessor, Anonymizer

# 1. Upload and extract
processor = FileProcessor()
file_hash = processor.calculate_hash(file_content)
raw_text = processor.extract_text(file_content, file_extension)
cleaned_text = processor.clean_text(raw_text)

# 2. Store in database
verdict.file_hash = file_hash
verdict.original_text = raw_text
verdict.cleaned_text = cleaned_text
verdict.status = "extracted"

# 3. Anonymize
anonymizer = Anonymizer()
result = anonymizer.anonymize(cleaned_text)

verdict.anonymized_text = result['anonymized_text']
verdict.anonymization_report = result['report']
verdict.privacy_risk_level = result['risk_level']
verdict.requires_manual_review = result['requires_review']
verdict.status = "anonymized"
```

---

## Configuration

### Environment Variables

Required in `.env`:

```bash
# For Anonymizer service
ANTHROPIC_API_KEY=sk-ant-...

# Optional
MAX_UPLOAD_SIZE_MB=50
ALLOWED_FILE_EXTENSIONS=[".pdf", ".txt", ".doc", ".docx"]
```

### Dependencies

From `requirements.txt`:

```
PyPDF2==3.0.1           # PDF extraction
python-docx==1.1.0      # DOCX extraction
anthropic==0.18.1       # Claude API
```

---

## Performance Considerations

### FileProcessor
- **PDF extraction**: ~1-5 seconds for 10-page document
- **Text cleaning**: < 1 second for most documents
- **Memory**: Loads entire file in memory

### Anonymizer
- **API call**: ~5-15 seconds depending on text length
- **Token limit**: ~100k tokens (~75k words)
- **Cost**: ~$0.03 per 1000 tokens (Claude Sonnet)
- **Rate limits**: Anthropic API limits apply

### Optimization Tips

1. **Cache file hashes** to avoid re-processing duplicates
2. **Clean text before anonymization** to reduce token count
3. **Batch process** if possible to optimize API usage
4. **Monitor API usage** to track costs

---

## Security Notes

1. **API Keys**: Never commit `.env` file, always use environment variables
2. **Original Text**: Store securely, restrict access after anonymization
3. **Anonymization Report**: Contains original values - protect carefully
4. **Manual Review**: Always review high-risk cases before publishing
5. **Logging**: Don't log original personal information

---

## Support

For issues or questions:
1. Check error messages carefully
2. Verify `.env` configuration
3. Test with `test_services.py`
4. Check Claude API status if anonymization fails
5. Review SERVICES.md documentation
