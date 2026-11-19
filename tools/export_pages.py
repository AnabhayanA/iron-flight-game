#!/usr/bin/env python3
"""Build the static Iron Flight GitHub Pages demo in docs/.

Run from the repository root: python tools/export_pages.py
The Flask app remains unchanged. This exports only the files used at runtime.
"""
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "app"
DEST = ROOT / "docs"
TEMPLATE = SOURCE / "templates" / "index.html"
STATIC = SOURCE / "static"

CSS = ("style.css", "flight-theme.css", "jarvis.css")
JS = ("armor-model.js", "game.js", "flight.js", "jarvis.js", "combat-upgrades.js")
ARMOR = Path("models/wire-reference-bulk-v001/runtime")
ASSETS = ("hover.png", "fire.png", "anchors.json")

def main():
    html = TEMPLATE.read_text(encoding="utf-8")
    # Convert all Flask url_for() static-file references to ordinary relative URLs.
    pattern = re.compile(r"""{{\s*url_for\(\s*['\"]static['\"]\s*,\s*filename\s*=\s*['\"]([^'\"]+)['\"]\s*\)\s*}}""")
    html, count = pattern.subn(lambda match: "static/" + match.group(1), html)
    if count < 8 or "url_for(" in html:
        raise RuntimeError("Template references changed; review Flask static URLs before publishing.")
    # Update only the static export's footer.
    html = html.replace("FLASK + JAVASCRIPT CANVAS", "GITHUB PAGES DEMO + JAVASCRIPT CANVAS")
    DEST.mkdir(exist_ok=True)
    (DEST / "index.html").write_text(html, encoding="utf-8")
    (DEST / ".nojekyll").touch()
    for folder, filenames in (("css", CSS), ("js", JS)):
        for filename in filenames:
            source = STATIC / folder / filename
            target = DEST / "static" / folder / filename
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
    for filename in ASSETS:
        source = STATIC / ARMOR / filename
        target = DEST / "static" / ARMOR / filename
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    print(f"Exported {count} Flask static references to {DEST.relative_to(ROOT)}/")
    print("GitHub Pages: Settings → Pages → Deploy from branch → main → /docs")

if __name__ == "__main__":
    main()
