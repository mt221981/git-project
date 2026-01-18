"""Simple test for article generation without full app dependencies."""

import sys
import os
from pathlib import Path

# Load .env file
from dotenv import load_dotenv
load_dotenv()

# Check API key
api_key = os.getenv('ANTHROPIC_API_KEY')
if not api_key or api_key == 'your-key-here':
    print("Error: ANTHROPIC_API_KEY not set in .env file")
    sys.exit(1)

# Import only what we need
from anthropic import Anthropic

# Simple quality checker
def quick_quality_check(content_html, title, meta_description, focus_keyword):
    """Quick quality assessment."""
    import re

    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', content_html)
    words = text.split()
    word_count = len(words)

    # Count H2 and H3
    h2_count = len(re.findall(r'<h2[^>]*>', content_html))
    h3_count = len(re.findall(r'<h3[^>]*>', content_html))

    # Count paragraphs and lists
    paragraph_count = len(re.findall(r'<p[^>]*>', content_html))
    list_count = len(re.findall(r'<ul[^>]*>', content_html)) + len(re.findall(r'<ol[^>]*>', content_html))

    # Calculate keyword density
    keyword_lower = focus_keyword.lower()
    text_lower = text.lower()
    keyword_count = text_lower.count(keyword_lower)
    keyword_density = (keyword_count / word_count * 100) if word_count > 0 else 0

    # Count sentences
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
    sentence_count = len(sentences)
    avg_sentence_length = sum(len(s.split()) for s in sentences) / sentence_count if sentence_count > 0 else 0

    # Count legal citations (simple pattern)
    citation_count = len(re.findall(r'סעיף \d+', text))
    precedent_count = len(re.findall(r'ע"[אעדבר] \d+', text))

    # Check disclaimer
    has_disclaimer = 'disclaimer' in content_html.lower() or 'הבהרה' in text

    print(f"\nQuick Quality Assessment:")
    print(f"  Word count: {word_count} (target: 1800+)")
    print(f"  H2 headings: {h2_count} (target: 7-8)")
    print(f"  H3 headings: {h3_count} (target: 10-12)")
    print(f"  Paragraphs: {paragraph_count}")
    print(f"  Lists: {list_count} (target: 5-6)")
    print(f"  Keyword density: {keyword_density:.2f}% (target: 1.0-1.2%)")
    print(f"  Avg sentence length: {avg_sentence_length:.1f} words (target: 15-18)")
    print(f"  Legal citations: {citation_count} (target: 6-8)")
    print(f"  Precedents: {precedent_count} (target: 2-3)")
    print(f"  Has disclaimer: {has_disclaimer}")

    # Estimate scores
    content_score = min(100, (word_count / 18) + (h2_count * 10) + (h3_count * 5))
    seo_score = 50 if 0.5 <= keyword_density <= 2.5 else 0
    seo_score += 30 if 50 <= len(title) <= 60 else 0
    seo_score += 20 if 150 <= len(meta_description) <= 155 else 0

    readability_score = min(100, 100 - abs(avg_sentence_length - 16) * 5)
    eeat_score = min(100, citation_count * 12 + precedent_count * 15 + (25 if has_disclaimer else 0))

    overall = (content_score * 0.3 + seo_score * 0.3 + readability_score * 0.2 + eeat_score * 0.2)

    print(f"\nEstimated Scores:")
    print(f"  Content: {content_score:.1f}/100")
    print(f"  SEO: {seo_score:.1f}/100")
    print(f"  Readability: {readability_score:.1f}/100")
    print(f"  E-E-A-T: {eeat_score:.1f}/100")
    print(f"  Overall: {overall:.1f}/100")

    return overall


# Test with the improved system prompt
IMPROVED_SYSTEM_PROMPT = """אתה עורך דין ישראלי מנוסה ומומחה בכתיבת תוכן משפטי SEO-אופטימלי ברמה הגבוהה ביותר.

## דרישות מחמירות:
1. אורך: 1800-2200 מילים (לא פחות!)
2. ציטוטים חוקיים: לפחות 6-8 ציטוטים לסעיפי חוק
3. תקדימים: לפחות 2-3 תקדימים עם שמות תיקים
4. מונחים משפטיים: לפחות 12 מונחים מקצועיים
5. H2: 7-8 כותרות
6. H3: 10-12 כותרות (רובן ב-FAQ)
7. FAQ: 8-10 שאלות ותשובות
8. רשימות: לפחות 5-6 רשימות
9. משפטים קצרים: ממוצע 15-18 מילים
10. צפיפות מילות מפתח: 1.0-1.2%

החזר JSON בלבד!"""

# Sample verdict
sample_verdict = {
    "case_number": "12345-01-20",
    "court_name": "בית המשפט המחוזי בתל אביב-יפו",
    "judge_name": "יצחק גרוס",
    "verdict_date": "2021-03-15",
    "legal_area": "דיני עבודה",
    "summary": "התובע פוטר ללא הודעה מוקדמת ותבע פיצויים. בית המשפט קבע כי הפיטורים שלא כדין וחייב תשלום 120,000 ש\"ח."
}

print("=" * 70)
print("Testing Improved Article Generation Prompts")
print("=" * 70)

try:
    import json
    import re
    client = Anthropic(api_key=api_key)

    user_prompt = f"""צור מאמר משפטי מקצועי על פסק הדין הבא:
{json.dumps(sample_verdict, ensure_ascii=False, indent=2)}

דרישות:
- 1800-2200 מילים
- 7-8 H2, 10-12 H3
- 8-10 FAQ
- 6-8 ציטוטי חוק
- 2-3 תקדימים
- צפיפות מילות מפתח: 1.0-1.2%

החזר JSON עם: title, meta_description, focus_keyword, content_html"""

    print("\nGenerating article...")
    print("(This may take 30-60 seconds...)\n")

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=16384,
        temperature=0.7,
        system=IMPROVED_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}]
    )

    # Parse response
    response_text = response.content[0].text

    # Try to extract JSON
    json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
    if json_match:
        article_json = json.loads(json_match.group())

        title = article_json.get('title', '')
        meta_desc = article_json.get('meta_description', '')
        keyword = article_json.get('focus_keyword', '')
        content = article_json.get('content_html', '')

        print(f"Title: {title}")
        print(f"Meta: {meta_desc}")
        print(f"Keyword: {keyword}")

        overall_score = quick_quality_check(content, title, meta_desc, keyword)

        print("\n" + "=" * 70)
        if overall_score >= 95:
            print("SUCCESS! Article achieved target score of 95+")
        elif overall_score >= 90:
            print("VERY GOOD! Article scored 90+ (close to target)")
        elif overall_score >= 80:
            print("GOOD! Article scored 80+ (needs minor improvements)")
        else:
            print("NEEDS WORK! Article needs improvements")
        print("=" * 70)

    else:
        print("Error: Could not find JSON in response")
        print(f"Response preview: {response_text[:500]}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
