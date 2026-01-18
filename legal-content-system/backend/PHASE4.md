## Phase 4: AI Analysis and Article Generation

Complete documentation for AI-powered verdict analysis and SEO article generation.

---

## 📋 Overview

Phase 4 adds intelligent content creation capabilities to the legal content system:
1. **AI Analysis**: Extract structured information from anonymized verdicts
2. **Article Generation**: Create SEO-optimized articles from analysis
3. **Quality Scoring**: Automatic content and SEO quality assessment

---

## 🏗️ Architecture

```
Anonymized Verdict
    ↓
┌─────────────────────────────────────────┐
│   POST /api/articles/verdicts/{id}/analyze │
│   (articles.py router)                  │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│   AnalysisService.analyze_verdict()    │
│   Uses: VerdictAnalyzer                 │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│   VerdictAnalyzer                       │
│   • analyze()                           │
│   • Extract structured data             │
│   • Parse Claude response               │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│   Verdict updated in DB                 │
│   Status: ANALYZED                      │
│   • key_facts                           │
│   • legal_questions                     │
│   • legal_principles                    │
│   • compensation_amount                 │
│   • relevant_laws                       │
│   • precedents_cited                    │
│   • practical_insights                  │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│   POST /api/articles/generate/{id}      │
│   (articles.py router)                  │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│   ArticleService.generate_article...()  │
│   Uses: ArticleGenerator                │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│   ArticleGenerator                      │
│   • generate()                          │
│   • calculate_scores()                  │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│   Article saved to DB                   │
│   • SEO-optimized content               │
│   • Quality scores                      │
│   • Keywords & tags                     │
│   • FAQ section                         │
└─────────────────────────────────────────┘
```

---

## 🔧 Core Services

### 1. VerdictAnalyzer (`app/services/verdict_analyzer.py`)

**Purpose**: Extract structured information from legal verdicts using Claude API.

**Key Method**:
```python
def analyze(text: str) -> Dict[str, Any]:
    """
    Analyze verdict text and extract structured information.

    Returns:
        {
            "key_facts": List[str],           # 5-8 key facts
            "legal_questions": List[str],     # 2-4 legal questions
            "legal_principles": List[str],    # 2-5 legal principles
            "compensation_amount": float,     # Total compensation
            "compensation_breakdown": {
                "total": float,
                "description": str,
                "items": [...]
            },
            "relevant_laws": List[Dict],      # Laws cited
            "precedents_cited": List[Dict],   # Precedents cited
            "practical_insights": List[str],  # 3-5 insights
            "case_type": str,                 # Type of case
            "outcome": str                    # Verdict outcome
        }
    """
```

**Features**:
- ✅ Extracts 7 types of structured data
- ✅ Hebrew-optimized prompts
- ✅ JSON parsing with error handling
- ✅ Field validation and enrichment
- ✅ Summary generation

**Example**:
```python
from app.services import VerdictAnalyzer

analyzer = VerdictAnalyzer()
result = analyzer.analyze(anonymized_text)

print(f"Case type: {result['case_type']}")
print(f"Key facts: {len(result['key_facts'])} items")
print(f"Compensation: ₪{result['compensation_amount']:,.0f}")
```

---

### 2. ArticleGenerator (`app/services/article_generator.py`)

**Purpose**: Generate SEO-optimized articles from analyzed verdicts.

**Key Method**:
```python
def generate(
    verdict_metadata: Dict[str, Any],
    analysis_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate SEO-optimized article.

    Returns:
        {
            "title": str,                     # SEO title (≤70 chars)
            "meta_title": str,                # Meta title
            "meta_description": str,          # Meta description
            "focus_keyword": str,             # Primary keyword
            "secondary_keywords": List[str],  # Secondary keywords
            "excerpt": str,                   # Brief summary
            "content_html": str,              # Full HTML content
            "word_count": int,                # Word count
            "category_primary": str,          # Main category
            "categories_secondary": List[str],# Secondary categories
            "tags": List[str],                # Tags
            "faq_items": List[Dict],          # FAQ section
            "common_mistakes": List[Dict],    # Common mistakes
            "internal_links": List[Dict],     # Internal links
            "external_links": List[Dict]      # External links
        }
    """
```

**Features**:
- ✅ Creates 1500-2500 word articles
- ✅ SEO-optimized (keywords, meta tags)
- ✅ Structured HTML (H2, H3, lists)
- ✅ FAQ generation (5-8 questions)
- ✅ Common mistakes section
- ✅ Internal/external links
- ✅ Automatic word count

**Quality Scoring**:
```python
def calculate_scores(article: Dict[str, Any]) -> Dict[str, int]:
    """
    Calculate quality scores (0-100).

    Returns:
        {
            "content_score": int,      # Content quality
            "seo_score": int,          # SEO optimization
            "readability_score": int,  # Readability
            "eeat_score": int,         # E-E-A-T compliance
            "overall_score": int       # Weighted average
        }
    """
```

**Example**:
```python
from app.services import ArticleGenerator

generator = ArticleGenerator()

metadata = {
    "case_number": "12345-01-20",
    "court_name": "בית המשפט המחוזי",
    "judge_name": "יצחק גרוס"
}

article = generator.generate(metadata, analysis_result)
scores = generator.calculate_scores(article)

print(f"Title: {article['title']}")
print(f"Word count: {article['word_count']}")
print(f"Overall score: {scores['overall_score']}/100")
```

---

## 🔄 Integration with Existing Services

### AnalysisService Updates

**Before** (Phase 3):
```python
def __init__(self, db: Session, anthropic_client: Optional[AnthropicClient] = None):
    self.db = db
    self.client = anthropic_client or AnthropicClient()

def analyze_text(self, text: str) -> Dict[str, Any]:
    # Direct Claude API call
    prompt = VERDICT_ANALYSIS_USER_PROMPT.format(text=text)
    response = self.client.create_structured_message(...)
    result = self._parse_analysis_response(response)
    return result
```

**After** (Phase 4):
```python
def __init__(self, db: Session, analyzer: Optional[VerdictAnalyzer] = None):
    self.db = db
    self.analyzer = analyzer or VerdictAnalyzer()  # NEW

def analyze_text(self, text: str) -> Dict[str, Any]:
    # Use VerdictAnalyzer service
    result = self.analyzer.analyze(text)
    return result
```

**Benefits**:
- ✅ Cleaner code (removed `_parse_analysis_response`)
- ✅ Better error handling
- ✅ Improved prompts
- ✅ More structured output

### ArticleService Updates

**Before** (Phase 3):
```python
def __init__(self, db: Session, anthropic_client: Optional[AnthropicClient] = None):
    self.db = db
    self.client = anthropic_client or AnthropicClient()

def generate_article_content(...) -> Dict[str, Any]:
    # Direct Claude API call
    prompt = ARTICLE_GENERATION_USER_PROMPT.format(...)
    response = self.client.create_message(...)
    result = self._parse_article_response(response)
    return result

def score_article(...) -> Dict[str, Any]:
    # Another Claude API call for scoring
    prompt = SEO_SCORING_PROMPT.format(...)
    response = self.client.create_structured_message(...)
    return json.loads(response)
```

**After** (Phase 4):
```python
def __init__(self, db: Session, generator: Optional[ArticleGenerator] = None):
    self.db = db
    self.generator = generator or ArticleGenerator()  # NEW

def generate_article_content(...) -> Dict[str, Any]:
    # Use ArticleGenerator service
    result = self.generator.generate(verdict_metadata, analysis_data)
    return result

def score_article(...) -> Dict[str, Any]:
    # Use ArticleGenerator's calculate_scores
    scores = self.generator.calculate_scores(article_content)
    return scores
```

**Benefits**:
- ✅ Single source of truth for article generation
- ✅ Cleaner scoring (no additional API call)
- ✅ Removed `_parse_article_response`
- ✅ Better separation of concerns

---

## 📊 Data Structures

### Analysis Result
```python
{
    "key_facts": [
        "התובע עבד 5 שנים בחברה",
        "פוטר ללא הודעה מוקדמת",
        "הנתבע טען להפרת חוזה"
    ],
    "legal_questions": [
        "האם הפיטורים היו מוצדקים?",
        "האם התובע זכאי לפיצויים?"
    ],
    "legal_principles": [
        "חובת מתן הודעה מוקדמת - סעיף 5 לחוק עבודה",
        "פיטורים ללא הצדקה - הפרה יסודית"
    ],
    "compensation_amount": 120000.0,
    "compensation_breakdown": {
        "total": 120000.0,
        "description": "פיצויי פיטורים והוצאות משפט",
        "items": [
            {
                "category": "פיצויי פיטורים",
                "amount": 95000.0,
                "description": "פיצויי פיטורים מלאים"
            },
            {
                "category": "הודעה מוקדמת",
                "amount": 15000.0,
                "description": "פיצוי בגין אי-מתן הודעה"
            },
            {
                "category": "הוצאות משפט",
                "amount": 10000.0,
                "description": "הוצאות משפט"
            }
        ]
    },
    "relevant_laws": [
        {
            "name": "חוק עבודה תשל\"ח-1978",
            "section": "סעיף 5",
            "description": "חובת מתן הודעה מוקדמת",
            "quote": "עובד זכאי להודעה מוקדמת..."
        }
    ],
    "precedents_cited": [
        {
            "case_name": "כהן נגד משרד החינוך",
            "case_number": "ע\"ע 567/85",
            "court": "בית המשפט העליון",
            "year": "1985",
            "relevance": "פיטורים ללא הצדקה",
            "principle": "חובת הנמקה בפיטורים"
        }
    ],
    "practical_insights": [
        "מעסיקים חייבים להוכיח בראיות ברורות כל טענה להפרת חוזה",
        "פיטורים ללא הודעה דורשים הצדקה חזקה במיוחד",
        "עובדים זכאים לפיצויים מלאים בפיטורים שלא כדין"
    ],
    "case_type": "דיני עבודה",
    "outcome": "התביעה התקבלה חלקית"
}
```

### Article Result
```python
{
    "title": "פיטורים שלא כדין: מדריך מלא לזכויותיך והפיצויים המגיעים לך",
    "meta_title": "פיטורים שלא כדין - זכויות ופיצויים | מדריך 2024",
    "meta_description": "נפטרת ללא הודעה מוקדמת? גלה את זכויותיך, הפיצויים המגיעים לך וכיצד להגיש תביעה. מדריך מקיף מבוסס פסיקה.",
    "focus_keyword": "פיטורים שלא כדין",
    "secondary_keywords": [
        "פיצויי פיטורים",
        "הודעה מוקדמת",
        "זכויות עובדים"
    ],
    "excerpt": "מדריך מקיף על פיטורים שלא כדין, הזכויות המגיעות לעובד שפוטר, הפיצויים שניתן לתבוע והדרך להגשת תביעה בבית הדין לעבודה.",
    "content_html": "<h2>רקע עובדתי</h2><p>במקרה זה...</p>",
    "word_count": 1847,
    "category_primary": "דיני עבודה",
    "categories_secondary": ["פיטורים", "זכויות עובדים"],
    "tags": [
        "פיטורים",
        "הודעה מוקדמת",
        "פיצויי פיטורים",
        "חוק עבודה",
        "בית דין לעבודה"
    ],
    "faq_items": [
        {
            "question": "מה הפיצויים המגיעים לעובד שפוטר שלא כדין?",
            "answer": "עובד שפוטר שלא כדין זכאי לפיצויי פיטורים מלאים..."
        },
        {
            "question": "כמה זמן יש להגיש תביעה על פיטורים שלא כדין?",
            "answer": "יש להגיש תביעה תוך שנה מיום הפיטורים..."
        }
    ],
    "common_mistakes": [
        {
            "mistake": "לחתום על הסכם פשרה מיד לאחר הפיטורים",
            "explanation": "רבים חותמים מיד מתוך לחץ כלכלי",
            "correct_approach": "יש להתייעץ עם עורך דין לפני חתימה"
        }
    ],
    "internal_links": [
        {
            "anchor_text": "פיצויי פיטורים - מדריך מלא",
            "url": "/pitzuyei-piturim-madrich",
            "relevance": "מסביר את חישוב הפיצויים בפירוט"
        }
    ],
    "external_links": [
        {
            "anchor_text": "חוק פיצויי פיטורים",
            "url": "https://www.nevo.co.il/law_html/law01/...",
            "description": "טקסט מלא של חוק פיצויי פיטורים"
        }
    ]
}
```

### Quality Scores
```python
{
    "content_score": 85,       # Content quality (structure, depth, value)
    "seo_score": 78,           # SEO optimization (keywords, meta, links)
    "readability_score": 82,   # Readability (structure, language, flow)
    "eeat_score": 88,          # E-E-A-T (expertise, authority, trust)
    "overall_score": 83        # Weighted average
}
```

---

## 🚀 API Endpoints

### Analyze Verdict

**Endpoint**: `POST /api/articles/verdicts/{verdict_id}/analyze`

**Purpose**: Extract structured information from anonymized verdict.

**Requirements**:
- Verdict must be in ANONYMIZED status
- Uses anonymized_text field

**Request**:
```http
POST /api/articles/verdicts/1/analyze
```

**Response**:
```json
{
  "id": 1,
  "status": "analyzed",
  "key_facts": ["עובדה 1", "עובדה 2"],
  "legal_questions": ["שאלה 1", "שאלה 2"],
  "legal_principles": ["עקרון 1", "עקרון 2"],
  "compensation_amount": 120000.0,
  "compensation_breakdown": {...},
  "relevant_laws": [...],
  "precedents_cited": [...],
  "practical_insights": [...]
}
```

**Process**:
1. Validates verdict exists and is anonymized
2. Sets status to ANALYZING
3. Calls VerdictAnalyzer.analyze()
4. Updates verdict with analysis data
5. Sets status to ANALYZED

---

### Generate Article

**Endpoint**: `POST /api/articles/generate/{verdict_id}`

**Purpose**: Generate SEO-optimized article from analyzed verdict.

**Requirements**:
- Verdict must be in ANALYZED status
- Must have analysis data (key_facts, etc.)

**Request**:
```http
POST /api/articles/generate/1
```

**Response**:
```json
{
  "article_id": 1,
  "title": "פיטורים שלא כדין: מדריך מלא לזכויותיך",
  "overall_score": 83,
  "word_count": 1847,
  "message": "Article generated successfully"
}
```

**Process**:
1. Validates verdict is analyzed
2. Gathers verdict metadata
3. Gathers analysis data
4. Calls ArticleGenerator.generate()
5. Calculates quality scores
6. Creates Article record in DB
7. Returns article ID

---

## 🧪 Testing

### Unit Tests

**Test VerdictAnalyzer**:
```bash
python backend/test_phase4.py
```

Tests:
- Text analysis with Claude API
- JSON parsing and validation
- Field extraction
- Error handling

**Test ArticleGenerator**:
```bash
python backend/test_phase4.py
```

Tests:
- Article generation with Claude API
- SEO optimization
- Quality scoring
- HTML structure validation

### Integration Tests

**Complete Workflow**:
```bash
python backend/test_phase4.py
```

Tests:
1. Create verdict with anonymized text
2. Run analysis (VerdictAnalyzer)
3. Validate analysis data
4. Generate article (ArticleGenerator)
5. Validate article structure
6. Calculate scores
7. Verify database updates

**Note**: Requires `ANTHROPIC_API_KEY` in `.env`

---

## 📈 Performance

### Analysis Performance
- **Short verdicts** (< 1000 words): ~3-5 seconds
- **Medium verdicts** (1000-5000 words): ~5-10 seconds
- **Long verdicts** (5000+ words): ~10-20 seconds

**Bottleneck**: Claude API call (~80% of time)

### Article Generation Performance
- **With analysis data**: ~8-15 seconds
- **Token usage**: ~3000-5000 tokens (input + output)

**Bottleneck**: Claude API call for content generation

### Cost Estimation
- **Analysis**: ~$0.05-$0.15 per verdict
- **Article Generation**: ~$0.10-$0.30 per article
- **Total per verdict**: ~$0.15-$0.45

---

## 💡 Best Practices

### 1. Analysis

✅ **Do**:
- Always use anonymized text for analysis
- Validate analysis results before article generation
- Store all analysis data in database
- Handle API errors gracefully

❌ **Don't**:
- Analyze original (non-anonymized) text
- Skip validation of required fields
- Generate articles without analysis
- Ignore API rate limits

### 2. Article Generation

✅ **Do**:
- Include all available analysis data
- Validate HTML structure
- Check word count (aim for 1500-2500)
- Review quality scores
- Test internal/external links

❌ **Don't**:
- Generate without proper metadata
- Skip SEO optimization
- Ignore quality scores below 70
- Publish without manual review for low scores

### 3. Quality Control

**Minimum Standards**:
- Overall score: ≥ 70
- Word count: ≥ 1500
- FAQ items: ≥ 5
- Key facts: ≥ 5
- Legal questions: ≥ 2

**Manual Review Required If**:
- Overall score < 70
- SEO score < 65
- Missing critical information
- Suspicious content

---

## 🔧 Configuration

### Environment Variables

Required in `.env`:
```bash
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### API Rate Limits

**Anthropic API**:
- Model: claude-3-5-sonnet-20241022
- Rate limit: Varies by plan
- Token limit: 200k tokens/request

**Recommendations**:
- Implement retry logic
- Add exponential backoff
- Monitor usage
- Cache results when possible

---

## 🐛 Troubleshooting

### Analysis Fails

**Problem**: "Analysis failed: Invalid JSON"

**Solutions**:
1. Check verdict text is valid Hebrew
2. Verify API key is correct
3. Check API rate limits
4. Review error logs for details

### Article Generation Fails

**Problem**: "Article generation failed"

**Solutions**:
1. Ensure verdict is analyzed first
2. Verify analysis data exists
3. Check API key and rate limits
4. Review token usage (stay under limits)

### Low Quality Scores

**Problem**: Overall score < 70

**Solutions**:
1. Check word count (should be 1500+)
2. Verify FAQ section has 5+ items
3. Ensure H2/H3 structure is correct
4. Review keyword usage
5. Consider re-generating article

---

## 🎯 Next Steps

After Phase 4:
- ✅ Upload verdicts (Phase 2-3)
- ✅ Anonymize content (Phase 3)
- ✅ Analyze verdicts (Phase 4)
- ✅ Generate articles (Phase 4)
- ⏭️  Publish to WordPress (Phase 5)
- ⏭️  Frontend integration (Phase 6)

---

## 📚 Additional Resources

- VerdictAnalyzer source: `backend/app/services/verdict_analyzer.py`
- ArticleGenerator source: `backend/app/services/article_generator.py`
- Tests: `backend/test_phase4.py`
- API routes: `backend/app/routers/articles.py`

---

**Phase 4 Complete!** 🎉

The system can now automatically analyze legal verdicts and generate professional SEO-optimized articles.
