import re

html_path = r'C:\Users\hp\.gemini\antigravity\scratch\nyayacheck\landing.html'
with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

# Extract header, main, footer
header_match = re.search(r'<header[^>]*>(.*?)</header>', html, re.DOTALL)
main_match = re.search(r'<main[^>]*>(.*?)</main>', html, re.DOTALL)
footer_match = re.search(r'<footer[^>]*>(.*?)</footer>', html, re.DOTALL)

header_content = header_match.group(0) if header_match else ''
main_content = main_match.group(0) if main_match else ''
footer_content = footer_match.group(0) if footer_match else ''

def to_jsx(s):
    s = s.replace('class=', 'className=')
    s = s.replace('for=', 'htmlFor=')
    s = s.replace('<!--', '{/*').replace('-->', '*/}')
    # Fix unclosed input tags
    s = re.sub(r'<input([^>]*?)(?<!/)>', r'<input\1 />', s)
    s = re.sub(r'<img([^>]*?)(?<!/)>', r'<img\1 />', s)
    s = re.sub(r'<br([^>]*?)(?<!/)>', r'<br\1 />', s)
    s = re.sub(r'<hr([^>]*?)(?<!/)>', r'<hr\1 />', s)
    # Fix onsubmit
    s = re.sub(r'onsubmit="[^"]*"', 'onSubmit={(e) => { e.preventDefault(); alert("Deployment inquiry registered. The Legal Metrology Liaison team will contact your department within 24 hours."); }}', s)
    return s

jsx_header = to_jsx(header_content)
jsx_main = to_jsx(main_content)
jsx_footer = to_jsx(footer_content)

# Add Officer Login link to navigation in header
jsx_header = jsx_header.replace(
    'href="#faq">FAQ</a></nav>',
    'href="#faq">FAQ</a><a className="font-body-sm text-body-sm text-on-surface-variant hover:text-on-surface transition-colors py-2" href="/login">Officer Login</a></nav>'
)
jsx_header = jsx_header.replace('href="#request-access"', 'href="/inspector/new-scan"')
jsx_header = jsx_header.replace('href="#"', 'href="/"')

# Add link to inspection suite and admin dashboard
jsx_main = jsx_main.replace('href="#request-access"', 'href="/inspector/new-scan"')
jsx_main = jsx_main.replace('href="#explore-protocol"', 'href="#how-it-works"')

page_content = f"""'use client';

import React from 'react';
import Link from 'next/link';

export default function LandingPage() {{
  return (
    <div className="min-h-screen bg-surface font-body-md text-on-surface antialiased flex flex-col">
      {jsx_header}
      {jsx_main}
      {jsx_footer}
    </div>
  );
}}
"""

with open('src/app/page.tsx', 'w', encoding='utf-8') as f:
    f.write(page_content)

print('src/app/page.tsx converted from Stitch landing.html successfully!')
