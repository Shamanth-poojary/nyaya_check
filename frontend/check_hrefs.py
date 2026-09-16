import re

with open('src/app/page.tsx', 'r', encoding='utf-8') as f:
    text = f.read()

matches = re.findall(r'href="([^"]*)"', text)
for m in matches:
    print(m)
