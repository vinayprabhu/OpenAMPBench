"""Check generated internal links and asset paths without accessing the network."""
from pathlib import Path
from urllib.parse import unquote, urlsplit
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1] / "_site"


def check_site():
    problems = []
    pages = sorted(ROOT.rglob("*.html"))
    if not pages:
        raise SystemExit("Build the site first: python scripts/build.py")
    for page in pages:
        soup = BeautifulSoup(page.read_text(encoding="utf-8"), "html.parser")
        if not soup.title:
            problems.append(f"{page.relative_to(ROOT)}: missing title")
        for node, attr in [(n, attr) for attr in ("href", "src", "data-src", "data-scene") for n in soup.select(f"[{attr}]")]:
            url = node.get(attr, "")
            parsed = urlsplit(url)
            if not url or parsed.scheme or parsed.netloc or url.startswith("#"):
                continue
            if url.startswith("/"):
                problems.append(f"{page.relative_to(ROOT)}: root-relative URL breaks project Pages: {url}")
                continue
            target = (page.parent / unquote(parsed.path)).resolve()
            if not target.is_relative_to(ROOT.resolve()) or not target.exists():
                problems.append(f"{page.relative_to(ROOT)}: missing local target {url}")
    if problems:
        raise SystemExit("\n".join(problems))
    print(f"Checked {len(pages)} HTML pages: internal links and assets resolve.")


if __name__ == "__main__":
    check_site()
