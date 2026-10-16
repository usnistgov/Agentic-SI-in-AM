"""Remove only the legacy SI-in-AM footer from a NIST Pages site.

Put this script in the repository root, then run:
    python remove_old_site_footer.py

The official NIST header/footer integration is retained.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
FOOTER = re.compile(r"(?is)<footer\b[^>]*>.*?</footer\s*>")
LEGACY_INDICATORS = (
    'class="footer-content"',
    "class='footer-content'",
    'class="footer-section"',
    "class='footer-section'",
    'class="footer-links"',
    "class='footer-links'",
)
NIST_JS = 'nist-header-footer.js'


def main():
    scanned = changed = removed = 0
    skipped = []
    for path in sorted(ROOT.rglob('*.html')):
        if any(part in {'.git', '.venv', 'node_modules'} for part in path.parts):
            continue
        scanned += 1
        html = path.read_text(encoding='utf-8-sig')
        matches = list(FOOTER.finditer(html))
        old = [m for m in matches if any(k in m.group(0) for k in LEGACY_INDICATORS)]
        if not old:
            if matches:
                skipped.append(str(path.relative_to(ROOT)))
            continue
        if NIST_JS not in html and 'nist-header-footer-v-2.0.js' not in html:
            print(f'WARNING: {path.relative_to(ROOT)} has no official NIST footer script; legacy footer retained.')
            continue
        for match in reversed(old):
            html = html[:match.start()] + html[match.end():]
            removed += 1
        path.write_text(html, encoding='utf-8')
        changed += 1
        print(f'UPDATED: {path.relative_to(ROOT)}')
    print(f'Checked {scanned} HTML pages; updated {changed}; removed {removed} legacy footers.')
    if skipped:
        print(f'Preserved {len(skipped)} non-legacy footer block(s) for safety.')

if __name__ == '__main__':
    main()
