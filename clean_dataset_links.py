"""Remove unapproved/personal dataset links in a static NIST Pages repository.
Run from the repository root: python clean_dataset_links.py
Uses Python standard library only. Does not delete dataset descriptions or data files.
"""
from pathlib import Path
from urllib.parse import urlparse, unquote
from html import unescape, escape
import re, json

ROOT = Path(__file__).resolve().parent
ANCHOR = re.compile(r'<a\b(?P<attrs>[^>]*)>(?P<body>.*?)</a\s*>', re.I | re.S)
HREF = re.compile(r'\bhref\s*=\s*([\"\'])(.*?)\1', re.I | re.S)
TAG = re.compile(r'<[^>]*>')
PERSONAL_ACCOUNTS = {'nowrin0102'}
# Dataset download links are held until an officially reviewed NIST dataset page is available.
DATASET_REPOS = {'am-dataset-for-genai', 'am-dataset-for-ai'}
PENDING = 'Dataset access pending NIST review and publication'
CHANGES = []


def clean_text(s):
    return ' '.join(unescape(TAG.sub('', s)).split())


def is_disallowed_dataset_link(href):
    url = urlparse(unescape(href))
    if url.netloc.lower() not in {'github.com', 'www.github.com', 'raw.githubusercontent.com'}:
        return False
    parts = [unquote(p).lower() for p in url.path.strip('/').split('/')]
    if not parts: return False
    if parts[0] in PERSONAL_ACCOUNTS:
        return True
    if len(parts) >= 2 and parts[1] in DATASET_REPOS:
        return True
    return False


def is_local_broken(href, file):
    h = unescape(href).strip()
    u = urlparse(h)
    if not h or h.startswith(('#', 'mailto:', 'tel:', 'javascript:', 'data:')):
        return False
    if u.scheme or u.netloc:
        return False
    path = unquote(u.path)
    if not path:
        return False
    if path.startswith('/'):
        # Within this specific NIST Pages project; do not rewrite external absolute paths.
        prefix = '/Agentic-SI-in-AM/'
        if not path.startswith(prefix):
            return False
        target = ROOT / path[len(prefix):]
    else:
        target = file.parent / path
    if target.is_dir(): target = target / 'index.html'
    return not target.exists()


def edit_html(file):
    original = file.read_text(encoding='utf-8-sig', errors='replace')
    details = []
    is_data_page = file.name.lower() in {'dataset_1.html', 'datasets.html'} or 'dataset' in file.parts

    def replace(m):
        hm = HREF.search(m.group('attrs'))
        if not hm: return m.group(0)
        href = hm.group(2)
        label = clean_text(m.group('body'))
        if is_disallowed_dataset_link(href):
            details.append({'kind': 'personal-github' if 'nowrin0102' in href.lower() else 'unreviewed-dataset-repository', 'label': label, 'url': href})
            # Plain-text indication rather than a dead link or clickable-looking button.
            return '<span class="nist-dataset-pending">' + escape(PENDING) + '</span>'
        if is_local_broken(href, file):
            details.append({'kind': 'broken-local-link', 'label': label, 'url': href})
            return '<span class="nist-link-unavailable">' + escape(label or 'Unavailable resource') + ' (link unavailable)</span>'
        return m.group(0)

    updated = ANCHOR.sub(replace, original)
    if is_data_page and any(d['kind'] in {'personal-github', 'unreviewed-dataset-repository'} for d in details):
        note = ('<p class="nist-dataset-review-notice" role="note">'
                'Dataset download links are withheld pending NIST dataset review, '
                'registration, and publication. Descriptions are informational only.'
                '</p>')
        # Inject after body opening; harmless across templates.
        if 'nist-dataset-review-notice' not in updated:
            updated = re.sub(r'(<body\b[^>]*>)', r'\1\n' + note, updated, count=1, flags=re.I)
    if updated != original:
        file.write_text(updated, encoding='utf-8')
    for d in details: CHANGES.append({'page': str(file.relative_to(ROOT)).replace('\\','/'), **d})


def main():
    pages = sorted(p for p in ROOT.rglob('*.html') if '.git' not in p.parts)
    for p in pages: edit_html(p)
    report = {'html_files_checked': len(pages), 'changes': CHANGES,
              'counts': {k: sum(x['kind'] == k for x in CHANGES) for k in sorted({x['kind'] for x in CHANGES})},
              'policy': 'Dataset links must not target personal GitHub or unreviewed repositories; add approved NIST publication URLs only after review.'}
    (ROOT / 'DATASET-LINK-AUDIT.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    print('HTML pages checked:', len(pages))
    print('Removed/replaced links:', len(CHANGES))
    print('Breakdown:', report['counts'])
    print('Report: DATASET-LINK-AUDIT.json')

if __name__ == '__main__': main()
