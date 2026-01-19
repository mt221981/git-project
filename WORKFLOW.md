# תיעוד תהליך העבודה - מערכת ליצירת תכנים משפטיים

## סקירה כללית

מערכת אוטומטית להמרת פסקי דין ישראליים למאמרים מותאמי SEO לפרסום באתרים משפטיים.

## ארכיטקטורה

### Backend (FastAPI + Python)
- **Framework**: FastAPI
- **Database**: SQLite with SQLAlchemy ORM
- **AI Engine**: Anthropic Claude API
- **Port**: 8000

### Frontend (React + TypeScript)
- **Framework**: React 18 + Vite
- **State Management**: React Query
- **Styling**: Tailwind CSS
- **Port**: 3003

## תהליך העבודה המלא

### שלב 1: העלאת פסק דין
**מטרה**: העלאה והכנה ראשונית של הקובץ

1. המשתמש מעלה קובץ PDF של פסק דין דרך הממשק
2. המערכת:
   - יוצרת hash ייחודי לקובץ למניעת כפילויות
   - שומרת את הקובץ ב-`storage/verdicts/`
   - יוצרת רשומה ב-DB עם סטטוס `new`

**קבצים קשורים**:
- `frontend/src/pages/Dashboard.tsx` - ממשק העלאה
- `backend/app/routers/verdicts.py` - endpoint העלאה
- `backend/app/services/verdict_service.py` - לוגיקת העלאה

### שלב 2: חילוץ טקסט (Extraction)
**מטרה**: המרת PDF לטקסט עברי נקי

1. המערכת מעבדת את קובץ ה-PDF:
   - שימוש ב-PyPDF2/pdfplumber לחילוץ
   - ניקוי רווחים מיותרים
   - זיהוי כותרות ופסקאות
   - שמירת מבנה הטקסט המקורי

2. הטקסט הנקי נשמר ב-`cleaned_text`
3. סטטוס מתעדכן ל-`extracted`

**קבצים קשורים**:
- `backend/app/services/file_processor.py` - חילוץ והמרת PDF

### שלב 3: אנונימיזציה (Anonymization)
**מטרה**: הסרת פרטים מזהים מהטקסט

1. Claude API מנתח את הטקסט ומזהה:
   - שמות פרטיים ומשפחתיים
   - מספרי תעודת זהות
   - כתובות וטלפונים
   - אימיילים ופרטים מזהים אחרים

2. מחליף כל פרט בתחליף עקבי:
   - `"יוסי כהן"` → `"התובע"`
   - `"רחוב הרצל 123"` → `"רחוב [X] מספר [Y]"`
   - שמירה על עקביות לאורך כל הטקסט

3. יוצר דוח מפורט של השינויים:
   ```json
   {
     "type": "name",
     "original": "דוד לוי",
     "replacement": "הנתבע",
     "risk_level": "medium"
   }
   ```

4. מעריך רמת סיכון לפרטיות:
   - `LOW` - בטוח לפרסום
   - `MEDIUM` - דורש בדיקה
   - `HIGH` - דורש בדיקה ידנית חובה

5. הטקסט המאונונם נשמר ב-`anonymized_text`
6. סטטוס מתעדכן ל-`anonymized`

**קבצים קשורים**:
- `backend/app/services/anonymizer.py` - לוגיקת אנונימיזציה
- `backend/app/services/anonymization_service.py` - ניהול תהליך
- `backend/app/services/prompts.py` - prompts לאנונימיזציה

**Prompts**:
- `ANONYMIZATION_SYSTEM_PROMPT` - הוראות למערכת AI
- `ANONYMIZATION_USER_PROMPT` - תבנית לבקשת אנונימיזציה

### שלב 4: ניתוח משפטי (Legal Analysis)
**מטרה**: חילוץ תובנות משפטיות מובנות

Claude API מנתח את פסק הדין ומחלץ:

1. **עובדות מהותיות** (`key_facts`):
   - רקע התיק
   - אירועים מרכזיים
   - טענות הצדדים

2. **שאלות משפטיות** (`legal_questions`):
   - הסוגיות המשפטיות שנדונו
   - שאלות עקרוניות

3. **עקרונות משפטיים** (`legal_principles`):
   - כללים משפטיים שנקבעו
   - פרשנויות לחוקים
   - תקדימים חדשים

4. **חוקים רלוונטיים** (`relevant_laws`):
   - סעיפי חוק שצוטטו
   - תקנות וחוקי עזר

5. **תקדימים** (`precedents_cited`):
   - פסיקות קודמות שהוזכרו
   - מספרי תיקים והפניות

6. **פיצויים** (אם רלוונטי):
   - `compensation_amount` - סכום כולל
   - `compensation_breakdown` - פירוט הפיצויים

7. **תובנות מעשיות** (`practical_insights`):
   - לקחים למעשה
   - המלצות לציבור
   - מה ללמוד מהפסיקה

כל הנתונים נשמרים כ-JSON מובנה ב-DB.
סטטוס מתעדכן ל-`analyzed`.

**קבצים קשורים**:
- `backend/app/services/verdict_analyzer.py` - לוגיקת ניתוח
- `backend/app/services/analysis_service.py` - ניהול תהליך
- `backend/app/services/prompts.py` - prompts לניתוח
- `backend/app/models/verdict.py` - מודל הנתונים

**Prompts**:
- `VERDICT_ANALYSIS_SYSTEM_PROMPT` - הוראות למומחה משפטי AI
- `VERDICT_ANALYSIS_USER_PROMPT` - תבנית לבקשת ניתוח

### שלב 5: יצירת מאמר (Article Generation)
**מטרה**: המרה למאמר SEO מלא ומותאם

1. **תוכן המאמר**:
   Claude מייצר מאמר מקצועי הכולל:
   - כותרת משיכה (`title`)
   - תקציר מעניין (`excerpt`)
   - תוכן HTML מלא וזורם (`content_html`)
   - מבנה הירכי עם H2/H3

2. **אופטימיזציית SEO**:
   - `focus_keyword` - מילת מפתח ראשית
   - `secondary_keywords` - מילות מפתח משניות (5-7)
   - `long_tail_keywords` - ביטויים ארוכים (3-5)
   - `meta_title` - כותרת עד 70 תווים
   - `meta_description` - תיאור עד 160 תווים
   - `slug` - URL ייחודי

3. **תוכן מורחב**:
   - `faq_items` - שאלות ותשובות נפוצות (5-7)
   - `common_mistakes` - טעויות נפוצות שיש להימנע מהן
   - `tags` - תגיות לסיווג

4. **קישורים אוטומטיים**:
   LinkEnhancementService מוסיף:
   - קישורים פנימיים למאמרים קשורים (עד 5)
   - קישורים חיצוניים למקורות מהימנים (עד 3)
   - עוגנים (anchors) טבעיים בטקסט

5. **Schema Markup**:
   יצירת JSON-LD ל-Google:
   - `schema_article` - Article schema
   - `schema_faq` - FAQPage schema

6. **איכות וציונים**:
   המערכת מחשבת ציוני איכות (0-100):
   - `content_score` - איכות תוכן
   - `seo_score` - אופטימיזציית SEO
   - `readability_score` - קריאות
   - `eeat_score` - מומחיות, מהימנות, סמכות
   - `overall_score` - ציון כולל

7. **מטא-דאטה**:
   - `word_count` - מספר מילים
   - `reading_time_minutes` - זמן קריאה משוער
   - `category_primary` - קטגוריה ראשית
   - `categories_secondary` - קטגוריות משניות
   - `featured_image_prompt` - prompt ליצירת תמונה
   - `featured_image_alt` - טקסט חלופי לתמונה

המאמר נשמר ב-DB עם סטטוס `draft`.
סטטוס הפסק דין מתעדכן ל-`article_created`.

**קבצים קשורים**:
- `backend/app/services/article_generator.py` - יצירת תוכן
- `backend/app/services/article_service.py` - ניהול מאמרים
- `backend/app/services/quality_checker.py` - בדיקת איכות
- `backend/app/services/link_enhancement.py` - הוספת קישורים
- `backend/app/models/article.py` - מודל נתונים

**Prompts**:
- `ARTICLE_GENERATION_SYSTEM_PROMPT` - הוראות לכותב תוכן
- `ARTICLE_GENERATION_USER_PROMPT` - תבנית ליצירת מאמר
- `SCHEMA_GENERATION_PROMPT` - יצירת schema markup

### שלב 6: בדיקה ועריכה
**מטרה**: ווידוא איכות לפני פרסום

המשתמש רואה במערכת:
- תצוגה מקדימה של המאמר
- כל הציונים והמטריקות
- רשימת בעיות איכות (אם יש)
- הצעות לשיפור

פעולות אפשריות:
1. **עריכה ידנית** - שינוי כל שדה במאמר
2. **יצירה מחדש** - הרצת תהליך מחדש
3. **אישור** - שינוי סטטוס ל-`ready`

**קבצים קשורים**:
- `frontend/src/pages/ArticlesListEnhanced.tsx` - רשימת מאמרים
- `frontend/src/pages/PublishingDashboard.tsx` - ניהול פרסום

### שלב 7: פרסום ל-WordPress (אופציונלי)
**מטרה**: העלאה אוטומטית לאתר

1. הגדרת אתר WordPress:
   - URL
   - Application Password
   - הגדרות קטגוריות

2. פרסום מאמר:
   - יצירת פוסט ב-WordPress
   - העלאת קטגוריות ותגיות
   - הגדרת מטא-דאטה SEO
   - שמירת קישור למאמר המפורסם

3. מעקב:
   - `publish_status` מתעדכן ל-`published`
   - `wordpress_post_id` - מזהה הפוסט
   - `wordpress_url` - URL המאמר המפורסם
   - `published_at` - תאריך פרסום

**קבצים קשורים**:
- `backend/app/routers/wordpress.py` - endpoints ל-WordPress
- `backend/app/models/wordpress_site.py` - מודל אתר

## זרימת נתונים

```
PDF Upload
    ↓
[new] Verdict
    ↓
Text Extraction → [extracted]
    ↓
Anonymization → [anonymized]
    ↓
Legal Analysis → [analyzed]
    ↓
Article Generation → [article_created]
    ↓
Quality Check → [draft] Article
    ↓
User Review → [ready]
    ↓
WordPress Publish → [published]
```

## סטטוסים של פסק דין

| Status | תיאור | פעולה הבאה |
|--------|-------|-----------|
| `new` | נוצר אך לא עובד | חילוץ טקסט |
| `extracted` | טקסט חולץ | אנונימיזציה |
| `anonymizing` | בתהליך אנונימיזציה | המתן |
| `anonymized` | הושלמה אנונימיזציה | ניתוח משפטי |
| `analyzing` | בתהליך ניתוח | המתן |
| `analyzed` | הושלם ניתוח | יצירת מאמר |
| `article_created` | מאמר נוצר | עריכה/פרסום |
| `failed` | נכשל | בדיקת שגיאה |

## סטטוסים של מאמר

| Status | תיאור |
|--------|-------|
| `draft` | טיוטה, דורש בדיקה |
| `pending_review` | ממתין לבדיקת מערכת |
| `ready` | מאושר לפרסום |
| `published` | פורסם ב-WordPress |
| `failed` | נכשל בפרסום |

## API Endpoints עיקריים

### Verdicts
- `POST /api/v1/verdicts/upload` - העלאת PDF
- `GET /api/v1/verdicts/` - רשימת פסקי דין
- `GET /api/v1/verdicts/{id}` - פרטי פסק דין
- `POST /api/v1/verdicts/{id}/anonymize` - אנונימיזציה
- `POST /api/v1/verdicts/{id}/reprocess` - עיבוד מחדש מלא
- `GET /api/v1/verdicts/statistics/overview` - סטטיסטיקות

### Articles
- `POST /api/v1/articles/verdicts/{id}/analyze` - ניתוח פסק דין
- `POST /api/v1/articles/generate/{id}` - יצירת מאמר
- `GET /api/v1/articles/` - רשימת מאמרים
- `GET /api/v1/articles/{id}` - פרטי מאמר
- `GET /api/v1/articles/by-verdict/{id}` - מאמר לפי פסק דין
- `GET /api/v1/articles/statistics/overview` - סטטיסטיקות

### WordPress
- `POST /api/v1/wordpress/sites` - הוספת אתר
- `GET /api/v1/wordpress/sites` - רשימת אתרים
- `POST /api/v1/wordpress/articles/{id}/publish` - פרסום מאמר

## מדריך להרצה

### Backend
```bash
cd legal-content-system/backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd legal-content-system/frontend
npm install
npm run dev -- --port 3003
```

### Build Frontend
```bash
cd legal-content-system/frontend
npm run build
```

## משתני סביבה נדרשים

```env
# Backend (.env)
ANTHROPIC_API_KEY=your_api_key_here
DATABASE_URL=sqlite:///./legal_content.db
DEBUG=true
ALLOWED_ORIGINS=http://localhost:3003

# Frontend (.env)
VITE_API_URL=http://localhost:8000
```

## מבנה תיקיות

```
legal-content-system/
├── backend/
│   ├── app/
│   │   ├── routers/          # API endpoints
│   │   ├── services/         # Business logic
│   │   ├── models/           # Database models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── utils/            # Utilities
│   │   ├── main.py           # FastAPI app
│   │   ├── config.py         # Configuration
│   │   └── database.py       # DB setup
│   ├── storage/              # Uploaded files
│   │   └── verdicts/         # PDF files
│   └── legal_content.db      # SQLite database
│
└── frontend/
    ├── src/
    │   ├── pages/            # React pages
    │   ├── components/       # React components
    │   ├── api/              # API client
    │   └── main.tsx          # Entry point
    └── dist/                 # Built files

```

## ציוני איכות - מדדים

### Content Score (ציון תוכן)
- עומק התוכן והמידע
- מקוריות וייחודיות
- קישורים פנימיים וחיצוניים
- **ממוצע במערכת: 98.8/100** ⭐

### SEO Score (ציון SEO)
- שימוש במילות מפתח
- אורך תוכן (800+ מילים)
- כותרות ותגי H2/H3
- מטא-דאטה
- **ממוצע במערכת: 76.3/100**

### Readability Score (ציון קריאות)
- מבנה פסקאות
- אורך משפטים
- שימוש ברשימות
- זרימת הטקסט
- **ממוצע במערכת: 95.5/100** ⭐

### E-E-A-T Score (מומחיות, ניסיון, סמכותיות, מהימנות)
- ציטוט מקורות
- שימוש בטרמינולוגיה מקצועית
- הפניות לחוקים ותקדימים
- FAQ מקיף
- **ממוצע במערכת: 86.9/100**

### Overall Score (ציון כולל)
- ממוצע משוקלל של כל הציונים
- **ממוצע במערכת: 88.6/100** ⭐

## טיפול בשגיאות

### Verdict Failed
כאשר פסק דין נכשל:
1. `status` משתנה ל-`failed`
2. `review_notes` מכיל הסבר השגיאה
3. ניתן ללחוץ "רענן סטטוס" או "עבד מחדש"

### שגיאות נפוצות
- **PDF לא קריא**: הקובץ מוצפן או לא תקין
- **שגיאת API**: בעיה בקריאה ל-Claude API (מפתח, מכסה)
- **שגיאת DB**: בעיית unique constraint או קונקרנטיות

### Retry Logic
המערכת מנסה מחדש אוטומטית במקרים מסוימים:
- שגיאות רשת זמניות
- Rate limit של API
- שגיאות parsing קלות

## Performance

### Backend
- זמן תגובה API: <100ms (endpoints רגילים)
- זמן אנונימיזציה: ~30-60 שניות
- זמן ניתוח: ~45-90 שניות
- זמן יצירת מאמר: ~60-120 שניות
- **תהליך מלא**: ~3-5 דקות

### Frontend
- Bundle size: 383 KB (115 KB gzipped)
- Build time: ~1.5 שניות
- First Load: <2 שניות

### Database
- SQLite עם indexes מיטביים
- 6 טבלאות ראשיות
- ~1.4 MB לכל 6 פסקי דין

## אבטחה

### Anonymization
- זיהוי אוטומטי של פרטים מזהים
- החלפה עקבית בכל הטקסט
- הערכת רמת סיכון
- אופציה לבדיקה ידנית

### API Security
- CORS מוגדר לפי allowed_origins
- Application passwords ל-WordPress
- אין חשיפת API keys בקוד

### Data Privacy
- קבצי PDF בנפרד בתיקייה מוגנת
- DB מקומי (SQLite)
- אין שמירת נתונים ב-cloud

## תחזוקה

### Logs
- Backend logs מודפסים לקונסול
- שגיאות נשמרות ב-`review_notes`
- פרטי debugging ב-prints

### Backup
- גיבוי של `legal_content.db`
- גיבוי של תיקיית `storage/`

### Updates
- עדכון dependencies: `pip install -r requirements.txt`
- עדכון frontend: `npm install`

## שאלות נפוצות

**שאלה**: כמה זמן לוקח לעבד פסק דין?
**תשובה**: בממוצע 3-5 דקות לתהליך מלא (אנונימיזציה + ניתוח + מאמר).

**שאלה**: מה קורה אם התהליך נכשל באמצע?
**תשובה**: הפסק דין יישאר עם הסטטוס האחרון המוצלח, ותוכל להריץ שוב מאותו שלב או מההתחלה.

**שאלה**: האם אפשר לערוך את המאמר שנוצר?
**תשובה**: כן! כל שדה במאמר ניתן לעריכה ידנית לפני הפרסום.

**שאלה**: איך משפרים את ציוני האיכות?
**תשובה**: ניתן להריץ מחדש את היצירה, לערוך את המאמר ידנית, או להתאים את ה-prompts.

**שאלה**: מה עושים עם פסק דין שנכשל באנונימיזציה?
**תשובה**: בודקים את `review_notes`, ואז מריצים שוב עם "עבד מחדש מההתחלה".

## תרומה ופיתוח

### הוספת פיצ'רים
1. Backend: הוסף service חדש ב-`app/services/`
2. API: הוסף endpoint ב-`app/routers/`
3. Frontend: הוסף component או page ב-`src/`

### Testing
- Backend: `pytest` (כשנכתבו טסטים)
- Frontend: `npm test` (כשנכתבו טסטים)
- Manual: השתמש ב-dashboard לבדיקות E2E

## Support

לדיווח על באגים או בקשות לפיצ'רים - צור issue ב-GitHub.

---

**גרסה**: 1.0
**עדכון אחרון**: ינואר 2026
**מחבר**: Legal Content System
