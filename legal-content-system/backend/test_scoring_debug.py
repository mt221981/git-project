"""Debug script to test calculate_scores directly."""

import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

# Simple imports
from app.database import get_db
from app.services.article_generator import ArticleGenerator

# Get database session
db = next(get_db())

# Get the article
from app.models.article import Article
article = db.query(Article).filter(Article.id == 1).first()

if not article:
    print("No article found with ID 1")
    sys.exit(1)

print("=" * 70)
print("Testing calculate_scores with Article ID 1")
print("=" * 70)

# Prepare article_content dictionary
article_content = {
    "title": article.title,
    "meta_description": article.meta_description,
    "content_html": article.content_html,
    "word_count": article.word_count,
    "focus_keyword": article.focus_keyword,
    "secondary_keywords": article.secondary_keywords or [],
    "faq_items": article.faq_items or [],
    "excerpt": article.excerpt
}

print(f"\nArticle content keys: {list(article_content.keys())}")
print(f"Word count: {article_content['word_count']}")
print(f"Title: {article_content['title'][:60]}...")
print(f"Focus keyword: {article_content['focus_keyword']}")

# Create generator
generator = ArticleGenerator()

# Call calculate_scores
print("\n" + "=" * 70)
print("Calling calculate_scores...")
print("=" * 70)

scores = generator.calculate_scores(article_content)

print("\n" + "=" * 70)
print("FINAL SCORES:")
print("=" * 70)
print(f"Content: {scores['content_score']}/100")
print(f"SEO: {scores['seo_score']}/100")
print(f"Readability: {scores['readability_score']}/100")
print(f"E-E-A-T: {scores['eeat_score']}/100")
print(f"Overall: {scores['overall_score']}/100")

if scores.get('quality_issues'):
    print("\nQuality Issues:")
    for issue in scores['quality_issues']:
        print(f"  - {issue}")

db.close()
