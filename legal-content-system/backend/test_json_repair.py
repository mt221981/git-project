"""Test json_repair functions."""

from app.utils.json_repair import extract_from_markdown, safe_parse_json

# Test with markdown block
test = '''```json
{
  "title": "test title",
  "content": "test content"
}
```'''

print('Input:')
print(repr(test[:100]))
print()

print('After extract_from_markdown:')
result = extract_from_markdown(test)
print(repr(result[:100] if result else result))
print()

print('After safe_parse_json:')
parsed = safe_parse_json(test)
print(parsed)
