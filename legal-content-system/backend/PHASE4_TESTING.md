# Phase 4: AI Analysis and Article Generation - Testing Guide

## Overview

Phase 4 implements verdict analysis and SEO article generation using Claude API. The system extracts structured information from verdicts and generates high-quality, SEO-optimized articles.

## What Was Implemented

### 1. Analysis Service (`app/services/analysis_service.py`)
Extracts structured information from verdicts:
- **Key facts**: 5-7 main facts of the case
- **Legal questions**: The legal issues discussed
- **Legal principles**: Legal principles applied
- **Compensation details**: Financial breakdown
- **Relevant laws**: Laws cited in the verdict
- **Precedents**: Court precedents referenced
- **Practical insights**: Actionable takeaways

### 2. Article Generation Service (`app/services/article_service.py`)
Creates SEO-optimized articles:
- Article content with proper HTML structure
- SEO metadata (title, meta description, keywords)
- FAQ items with schema markup
- Quality scoring (Content, SEO, Readability, E-E-A-T)
- Schema.org JSON-LD markup
- Internal and external link suggestions

### 3. Comprehensive Prompts (`app/services/prompts.py`)
- Hebrew-language analysis prompts
- Article generation with SEO guidelines
- Quality scoring criteria
- Schema markup generation

### 4. New API Endpoints

#### Analysis Endpoints
- `POST /api/v1/articles/verdicts/{id}/analyze` - Analyze verdict
- `POST /api/v1/articles/verdicts/{id}/re-analyze` - Re-analyze verdict
- `GET /api/v1/articles/verdicts/statistics/analysis` - Analysis statistics

#### Article Endpoints
- `POST /api/v1/articles/generate/{verdict_id}` - Generate article
- `GET /api/v1/articles` - List articles with pagination
- `GET /api/v1/articles/{id}` - Get article details
- `GET /api/v1/articles/by-verdict/{verdict_id}` - Get article by verdict
- `GET /api/v1/articles/statistics/overview` - Article statistics

## Complete Workflow: Upload to Article

### Step 1: Upload a Verdict

```bash
curl -X POST "http://localhost:8000/api/v1/verdicts/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@verdict.pdf"
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

Response: Verdict with `status: "anonymized"`

### Step 3: Analyze the Verdict

```bash
curl -X POST "http://localhost:8000/api/v1/articles/verdicts/1/analyze"
```

This extracts:
- Key facts from the case
- Legal questions and principles
- Compensation details
- Relevant laws and precedents
- Practical insights

Response:
```json
{
  "id": 1,
  "status": "analyzed",
  "key_facts": [
    "עובדה 1: התובע נפגע בתאונת דרכים...",
    "עובדה 2: הנתבע לא שמר על מרחק בטיחות..."
  ],
  "legal_questions": [
    "האם הנתבע פעל ברשלנות?",
    "מהו גובה הפיצוי המגיע לתובע?"
  ],
  "legal_principles": [
    "עקרון האחריות בנזיקין - כל הגורם נזק לזולתו חייב בפיצויו",
    "חובת שמירת מרחק בטיחות לפי תקנות התעבורה"
  ],
  "compensation_amount": 50000,
  "compensation_breakdown": {
    "total": 50000,
    "description": "פיצוי כולל בגין נזקים שונים",
    "items": [
      {"category": "נזק ישיר", "amount": 30000, "description": "הוצאות רפואיות"},
      {"category": "עוגמת נפש", "amount": 20000, "description": "פיצוי בגין כאב וסבל"}
    ]
  },
  "relevant_laws": [
    {
      "name": "פקודת הנזיקין",
      "section": "35",
      "description": "אחריות בנזיקין"
    }
  ],
  "precedents_cited": [
    {
      "case_name": "ע\"א 1234/20",
      "case_number": "1234/20",
      "court": "בית המשפט העליון",
      "relevance": "קביעת גובה פיצוי בתאונות דרכים"
    }
  ],
  "practical_insights": [
    "חשיבות תיעוד רפואי מיידי לאחר תאונה",
    "זכאות לפיצוי גם ללא נזק גופני ישיר",
    "המלצה לייעוץ משפטי מוקדם"
  ]
}
```

### Step 4: Generate SEO Article

```bash
curl -X POST "http://localhost:8000/api/v1/articles/generate/1"
```

This creates a complete SEO article:
- Title and meta tags optimized for search
- 1500-2500 word article with proper HTML structure
- FAQ section with schema markup
- Internal/external link suggestions
- Quality scores (content, SEO, readability, E-E-A-T)

Response:
```json
{
  "message": "Article generated successfully",
  "article_id": 1,
  "verdict_id": 1,
  "title": "פיצוי בתאונת דרכים: מדריך מקיף לזכויות הנפגעים",
  "slug": "piẓuy-btavnt-drkim-mdrik-mkip-lzkhuyut-hnpgym",
  "overall_score": 85,
  "publish_status": "draft"
}
```

### Step 5: Get the Complete Article

```bash
curl "http://localhost:8000/api/v1/articles/1"
```

Response includes:
```json
{
  "id": 1,
  "verdict_id": 1,
  "title": "פיצוי בתאונת דרכים: מדריך מקיף לזכויות הנפגעים",
  "slug": "...",
  "meta_title": "פיצוי תאונת דרכים 2026 - מה מגיע לך?",
  "meta_description": "גלה כמה פיצוי מגיע לך בתאונת דרכים. מדריך מקיף על זכויות, הליך התביעה, וטיפים מעשיים. ייעוץ משפטי חינם!",
  "focus_keyword": "פיצוי תאונת דרכים",
  "secondary_keywords": ["זכויות נפגעי תאונות", "תביעת פיצויים", "פגיעה בתאונה"],
  "content_html": "<h2>רקע עובדתי</h2><p>...</p>...",
  "word_count": 2150,
  "reading_time_minutes": 11,
  "faq_items": [
    {
      "question": "כמה זמן לוקח לקבל פיצוי בתאונת דרכים?",
      "answer": "הליך תביעת פיצויים יכול לקחת בין 6 חודשים לשנתיים, תלוי במורכבות התיק..."
    }
  ],
  "common_mistakes": [
    {
      "mistake": "אי דיווח מיידי למשטרה",
      "explanation": "הימנעות מדיווח עלולה לפגוע בתביעה",
      "correct_approach": "דווח תמיד למשטרה, גם בתאונות קלות"
    }
  ],
  "schema_article": {...},
  "schema_faq": {...},
  "category_primary": "נזיקין",
  "categories_secondary": ["תאונות דרכים", "פיצויים"],
  "tags": ["תאונת דרכים", "פיצוי", "נזיקין", "ביטוח", "זכויות"],
  "content_score": 88,
  "seo_score": 85,
  "readability_score": 82,
  "eeat_score": 90,
  "overall_score": 86,
  "quality_issues": [...],
  "publish_status": "draft"
}
```

## Understanding the Scores

### Content Score (0-100)
- Article length (1500+ words)
- Structure and hierarchy
- Value to reader
- Professional accuracy

### SEO Score (0-100)
- Keyword usage (title, H2, content)
- Keyword density (1-2%)
- Meta tags optimization
- Internal/external links

### Readability Score (0-100)
- Sentence clarity
- Paragraph balance
- Use of lists and structure
- Avoiding jargon

### E-E-A-T Score (0-100)
Experience, Expertise, Authority, Trust:
- Legal expertise demonstration
- Citation of reliable sources
- Factual accuracy
- Professional tone

### Overall Score
Weighted average of all scores.

## Article Structure

Generated articles follow this structure:

```html
<h2>פתיחה</h2>
<p>פסקה פתיחה חזקה (150-200 מילים) המסכמת את המקרה ומה ניתן ללמוד ממנו</p>

<h2>רקע עובדתי</h2>
<p>העובדות של התיק באופן קליט וברור...</p>

<h2>השאלות המשפטיות</h2>
<p>אילו שאלות משפטיות נדונו...</p>

<h2>ההכרעה וההנמקה</h2>
<p>מה בית המשפט הכריע ומדוע...</p>

<h2>פירוט הפיצוי</h2>
<ul>
  <li>נזק ישיר: 30,000 ₪</li>
  <li>עוגמת נפש: 20,000 ₪</li>
</ul>

<h2>משמעות המקרה</h2>
<p>מה ניתן ללמוד מפסק דין זה...</p>

<h2>תובנות מעשיות</h2>
<ul>
  <li>טיפ 1</li>
  <li>טיפ 2</li>
</ul>

<h2>שאלות נפוצות</h2>
<h3>כמה זמן לוקח...</h3>
<p>תשובה...</p>
```

## Using the API

### Python Example

```python
import requests

# Complete workflow
def process_verdict(file_path):
    base_url = "http://localhost:8000/api/v1"

    # 1. Upload
    with open(file_path, "rb") as f:
        r = requests.post(f"{base_url}/verdicts/upload", files={"file": f})
    verdict_id = r.json()["verdict_id"]
    print(f"Uploaded: Verdict ID {verdict_id}")

    # 2. Anonymize
    r = requests.post(f"{base_url}/verdicts/{verdict_id}/anonymize")
    print(f"Anonymized: Risk level {r.json()['privacy_risk_level']}")

    # 3. Analyze
    r = requests.post(f"{base_url}/articles/verdicts/{verdict_id}/analyze")
    analysis = r.json()
    print(f"Analyzed: {len(analysis['key_facts'])} facts extracted")

    # 4. Generate article
    r = requests.post(f"{base_url}/articles/generate/{verdict_id}")
    article = r.json()
    print(f"Article created: ID {article['article_id']}, Score: {article['overall_score']}")

    # 5. Get full article
    r = requests.get(f"{base_url}/articles/{article['article_id']}")
    full_article = r.json()

    return full_article

# Run it
article = process_verdict("verdict.pdf")
print(f"Title: {article['title']}")
print(f"Word count: {article['word_count']}")
print(f"Overall score: {article['overall_score']}")
```

## Statistics Endpoints

### Analysis Statistics

```bash
curl "http://localhost:8000/api/v1/articles/verdicts/statistics/analysis"
```

Response:
```json
{
  "total_analyzed": 15,
  "with_compensation": 12,
  "average_compensation": 45000.0,
  "by_legal_area": {
    "נזיקין": 8,
    "חוזים": 4,
    "דיני עבודה": 3
  }
}
```

### Article Statistics

```bash
curl "http://localhost:8000/api/v1/articles/statistics/overview"
```

Response:
```json
{
  "total": 15,
  "by_status": {
    "draft": 10,
    "ready": 3,
    "published": 2
  },
  "average_scores": {
    "content": 85.5,
    "seo": 82.3,
    "readability": 88.1,
    "eeat": 87.9,
    "overall": 85.9
  }
}
```

## Interactive Documentation

Visit **http://localhost:8000/docs** for Swagger UI with:
- All endpoints documented
- Interactive testing
- Request/response examples
- Schema definitions

## Troubleshooting

### "Verdict must be anonymized before analysis"
- Ensure you've called the anonymize endpoint first
- Check verdict status: `GET /api/v1/verdicts/{id}`

### "Verdict must be analyzed before article generation"
- Run the analyze endpoint first
- Verify status is "analyzed"

### Low article scores
- Check `quality_issues` array for specific problems
- Review the article content
- Consider re-generating with different analysis

### Article generation is slow
- Normal: generates 1500-2500 words
- Typically takes 30-60 seconds
- Consider running in background for bulk processing

## Next Phase

After Phase 4, proceed to:
- **Phase 5**: WordPress Publishing - Integrate with WordPress REST API
- **Phase 6**: Frontend Interface - Build user interface

The generated articles are ready for publishing to WordPress or other CMSs!
