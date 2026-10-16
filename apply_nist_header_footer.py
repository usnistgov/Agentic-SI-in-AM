"""Add the official NIST header and footer to all site HTML files.
Run from the root of your cloned Agentic-SI-in-AM repository:
    python apply_nist_header_footer.py
Safe to run repeatedly. No pip dependencies.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
CSS = 'https://pages.nist.gov/nist-header-footer/css/nist-combined.css'
JS = 'https://pages.nist.gov/nist-header-footer/js/nist-header-footer.js'
MARKER = '<!-- Official NIST site-wide header and footer -->'
INCLUDE = (f'    {MARKER}\n'
           f'    <link rel="stylesheet" href="{CSS}">\n'
           f'    <script src="{JS}" type="text/javascript" defer="defer"></script>\n')

modified=[]
skipped=[]
for path in sorted(ROOT.rglob('*.html')):
    if any(p in ('.git', 'node_modules', '.venv', 'vendor') for p in path.relative_to(ROOT).parts):
        continue
    raw=path.read_bytes()
    try:
        content=raw.decode('utf-8-sig')
    except UnicodeDecodeError:
        print('WARNING: non UTF-8 HTML:',path.relative_to(ROOT))
        continue
    if CSS in content and JS in content:
        skipped.append(path)
        continue
    if not re.search(r'</head\s*>',content,re.I) or not re.search(r'<body\b',content,re.I):
        print('WARNING: no HTML head/body:',path.relative_to(ROOT))
        continue
    # If one directive already exists, do not insert duplicate links.
    fragments=[MARKER+'\n']
    if CSS not in content:
        fragments.append(f'    <link rel="stylesheet" href="{CSS}">\n')
    if JS not in content:
        fragments.append(f'    <script src="{JS}" type="text/javascript" defer="defer"></script>\n')
    content,n=re.subn(r'(?i)</head\s*>',lambda m:''.join('    '+p if p==MARKER+'\n' else p for p in fragments)+m.group(0),content,count=1)
    if n!=1:
        print('WARNING: could not inject:',path.relative_to(ROOT));continue
    # Keep original line-ending convention.
    if b'\r\n' in raw:
        content=content.replace('\r\n','\n').replace('\n','\r\n')
    path.write_bytes(content.encode('utf-8'))
    modified.append(path)

print(f'Added official NIST header/footer to {len(modified)} HTML files; {len(skipped)} already configured.')
for path in modified:
    print('  ', path.relative_to(ROOT))
