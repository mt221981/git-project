"""LinkEnhancementService - Adds SEO-optimized links to article content."""

import re
from typing import Dict, List
from bs4 import BeautifulSoup


class LinkEnhancementService:
    """Service to enhance articles with internal and external links."""

    # Internal link mapping: term -> URL slug
    # IMPORTANT: This system handles ONLY tort law (נזיקין) and insurance (ביטוח)
    # DO NOT add links for family law, divorce, criminal, or other unrelated areas
    INTERNAL_LINKS = {
        # Core tort/insurance terms
        "נזיקין": "/נזיקין",
        "נזקים": "/נזיקין",
        "נזק גוף": "/נזק-גוף",
        "פיצויים": "/פיצויים",
        "תביעת פיצויים": "/פיצויים",
        "רשלנות": "/רשלנות",
        # Insurance
        "ביטוח": "/ביטוח",
        "ביטוח רכב": "/ביטוח-רכב",
        "פוליסת ביטוח": "/ביטוח",
        "תגמולי ביטוח": "/ביטוח",
        # Accidents
        "תאונות דרכים": "/תאונות-דרכים",
        "תאונת דרכים": "/תאונות-דרכים",
        "תאונה": "/תאונות-דרכים",
        "תאונת עבודה": "/תאונות-עבודה",
        # Medical
        "רשלנות רפואית": "/רשלנות-רפואית",
        # Property
        "נזקי רכוש": "/נזקי-רכוש",
    }

    # External link patterns: (pattern, URL, title)
    EXTERNAL_PATTERNS = [
        (r"סעיף \d+", "https://www.nevo.co.il", "נבו - המאגר המשפטי הישראלי"),
        (r"פקודת", "https://www.nevo.co.il", "נבו - פקודות ודינים"),
        (r"חוק", "https://www.nevo.co.il", "נבו - חוקי ישראל"),
    ]

    def enhance_with_links(
        self,
        content_html: str,
        focus_keyword: str = None,
        secondary_keywords: List[str] = None,
        max_internal: int = 5,
        max_external: int = 3
    ) -> str:
        """
        Add internal and external links to article content.

        Args:
            content_html: Original HTML content
            focus_keyword: Primary keyword (not linked to avoid over-optimization)
            secondary_keywords: Secondary keywords to potentially link
            max_internal: Maximum internal links to add
            max_external: Maximum external links to add

        Returns:
            Enhanced HTML with links added
        """
        print(f"[LinkEnhancement] enhance_with_links called, HTML length: {len(content_html)}")
        soup = BeautifulSoup(content_html, 'html.parser')

        # Track what we've linked to avoid duplicates
        linked_internal = set()
        linked_external = set()

        internal_count = 0
        external_count = 0

        paragraphs = soup.find_all('p')
        print(f"[LinkEnhancement] Found {len(paragraphs)} paragraphs")

        # Process all paragraphs
        for p in paragraphs:
            if internal_count >= max_internal and external_count >= max_external:
                break

            text = p.get_text()

            # Add internal links
            if internal_count < max_internal:
                for term, url in self.INTERNAL_LINKS.items():
                    if term in text and url not in linked_internal:
                        # Don't link the focus keyword (avoid over-optimization)
                        if focus_keyword and term in focus_keyword:
                            continue

                        # Replace first occurrence with link
                        new_html = p.decode_contents()
                        new_html = re.sub(
                            f'(?<!>)({re.escape(term)})(?!<)',
                            f'<a href="{url}">{term}</a>',
                            new_html,
                            count=1,
                            flags=re.IGNORECASE
                        )

                        if new_html != p.decode_contents():
                            p.clear()
                            p.append(BeautifulSoup(new_html, 'html.parser'))
                            linked_internal.add(url)
                            internal_count += 1

                            if internal_count >= max_internal:
                                break

            # Add external links
            if external_count < max_external:
                for pattern, url, title in self.EXTERNAL_PATTERNS:
                    if re.search(pattern, text) and url not in linked_external:
                        # Find the match
                        match = re.search(pattern, text)
                        if match:
                            matched_text = match.group(0)
                            new_html = p.decode_contents()
                            new_html = re.sub(
                                f'({re.escape(matched_text)})',
                                f'<a href="{url}" target="_blank" rel="noopener noreferrer" title="{title}">{matched_text}</a>',
                                new_html,
                                count=1
                            )

                            if new_html != p.decode_contents():
                                p.clear()
                                p.append(BeautifulSoup(new_html, 'html.parser'))
                                linked_external.add(url)
                                external_count += 1

                                if external_count >= max_external:
                                    break

        # Return enhanced HTML
        return str(soup)

    def get_stats(self, content_html: str) -> Dict[str, int]:
        """Get link statistics from content."""
        soup = BeautifulSoup(content_html, 'html.parser')
        links = soup.find_all('a')

        internal = len([l for l in links if not l.get('href', '').startswith('http')])
        external = len([l for l in links if l.get('href', '').startswith('http')])

        return {
            "total_links": len(links),
            "internal_links": internal,
            "external_links": external
        }
