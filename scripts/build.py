"""Build a static research site. Reads saved notebooks; never executes cells."""
from __future__ import annotations

import argparse
import copy
import hashlib
import html
import json
import os
import re
import shutil
from importlib.metadata import version
from pathlib import Path
from urllib.parse import quote, urlparse

import markdown
import nbformat
import plotly.io as pio
from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape
from nbconvert import HTMLExporter
from plotly.offline import get_plotlyjs

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "_site"
CACHE = ROOT / ".build-cache"


def read_json(path: Path, default=None):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def public_files(folder: Path, keep_zarr_metadata=False):
    if not folder.exists():
        return []
    paths = []
    for path in sorted(folder.rglob("*")):
        allowed = {".zattrs", ".zarray", ".zgroup", ".zmetadata", ".luxar-index.json"} if keep_zarr_metadata else set()
        if any((part.startswith(".") and part not in allowed) or part == "__pycache__" for part in path.relative_to(folder).parts):
            continue
        if path.is_symlink():
            raise ValueError(f"Symlinks are not published: {path}")
        if path.is_file():
            paths.append(path)
    return paths


def title_from_markdown(text: str, fallback: str) -> str:
    match = re.search(r"^#\s+(.+?)\s*#*\s*$", text, flags=re.M)
    return match.group(1) if match else fallback


def safe_url(value: str, label: str, allow_relative=True) -> str:
    parts = urlparse(value)
    if parts.scheme and parts.scheme != "https":
        raise ValueError(f"{label}: expected an HTTPS URL")
    if value.startswith("//") or (not allow_relative and not parts.netloc):
        raise ValueError(f"{label}: expected an absolute HTTPS URL")
    return value


def build():
    site = read_json(ROOT / "site.json")
    projects = read_json(ROOT / "projects.json")
    project_map = {p["id"]: p for p in projects}
    if len(project_map) != len(projects):
        raise ValueError("Duplicate project id")
    for p in projects:
        if not re.fullmatch(r"[a-z0-9-]+", p["id"]):
            raise ValueError(f"Invalid project id: {p['id']}")
        for link in p["links"]:
            safe_url(link["url"], "Project resource", allow_relative=False)
    for field in ("repository", "url"):
        if site.get(field):
            safe_url(site[field], field, allow_relative=False)
    if site.get("repository") and not re.fullmatch(r"https://github.com/[\w.-]+/[\w.-]+/?", site["repository"]):
        raise ValueError("repository must be https://github.com/OWNER/REPO")
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    CACHE.mkdir(exist_ok=True)
    shutil.copytree(ROOT / "assets", OUT / "assets")
    (OUT / ".nojekyll").touch()
    (OUT / "assets" / "plotly.min.js").write_text(get_plotlyjs(), encoding="utf-8")
    env = Environment(loader=FileSystemLoader(ROOT / "templates"), autoescape=select_autoescape(["html"]), undefined=StrictUndefined)
    base = dict(site=site, projects=projects, project_map=project_map)

    def context(output: str, **kwargs):
        root = "../" * len(Path(output).parent.parts)
        canonical_url = site.get("url", "").rstrip("/") + "/" + quote(Path(output).as_posix(), safe="/") if site.get("url") else ""
        return {**base, "root": root, "canonical_url": canonical_url, "description": "", **kwargs}

    def write_page(output: str, template: str, **kwargs):
        target = OUT / output
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(env.get_template(template).render(**context(output, **kwargs)), encoding="utf-8")

    def project_info(raw: str):
        key = str(raw).lower()
        if key != "general" and key not in project_map:
            raise ValueError(f"Unknown project {raw!r}; use a projects.json id or 'general'.")
        return key, project_map[key]["name"] if key != "general" else "General"

    notebooks = []
    source_notebooks = []
    notebook_paths = public_files(ROOT / "notebooks")
    for path in notebook_paths:
        relative = path.relative_to(ROOT / "notebooks")
        if path.suffix != ".ipynb":
            target = OUT / "notebooks" / "view" / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
            continue
        notebook = nbformat.read(path, as_version=4)
        nbformat.validate(notebook)
        meta = notebook.metadata.get("openamps", {})
        inferred = relative.parts[0].lower() if len(relative.parts) > 1 else "general"
        inferred = inferred if inferred in project_map else "general"
        project, name = project_info(meta.get("project", inferred))
        first_md = "\n".join(c.source for c in notebook.cells if c.cell_type == "markdown")
        title = meta.get("title") or title_from_markdown(first_md, path.stem.replace("_", " ").replace("-", " "))
        out_path = "notebooks/view/" + relative.with_suffix(".html").as_posix()
        download = quote(path.name)
        colab = ""
        if site.get("repository"):
            owner_repo = site["repository"].removeprefix("https://github.com/").rstrip("/")
            colab = f"https://colab.research.google.com/github/{owner_repo}/blob/{quote(site['branch'], safe='')}/notebooks/{quote(relative.as_posix())}"
        item = dict(title=title, project=project, project_name=name, description=meta.get("description", "Saved code, outputs and analysis."), example=bool(meta.get("example", False)), url=quote(out_path), download=download, colab_url=colab)
        notebooks.append(item)
        source_notebooks.append((path, notebook, item, out_path))

    figures = []
    viz_root = ROOT / "visualizations"
    for path in public_files(viz_root, keep_zarr_metadata=True):
        target = OUT / "visualizations" / path.relative_to(viz_root)
        if not (path.name == "meta.json" and len(path.relative_to(viz_root).parts) == 2):
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
    for folder in sorted(viz_root.iterdir()) if viz_root.exists() else []:
        if not folder.is_dir() or folder.name.startswith("."):
            continue
        if not re.fullmatch(r"[a-zA-Z0-9_-]+", folder.name):
            raise ValueError(f"Figure directory needs a simple URL-safe name: {folder.name}")
        meta = read_json(folder / "meta.json", {})
        if not meta and not (folder / "index.html").exists():
            continue
        project, name = project_info(meta.get("project", "general"))
        kind = meta.get("kind", "html")
        if kind not in ("html", "luxar", "external"):
            raise ValueError(f"Unknown figure kind {kind}")
        src, scene = "", ""
        if kind == "html":
            if not (folder / "index.html").exists():
                raise ValueError(f"Missing {folder / 'index.html'}")
            src = f"../visualizations/{folder.name}/index.html"
        elif kind == "external":
            src = safe_url(meta["viewer_url"], "viewer_url", allow_relative=False)
        else:
            raw_scene = safe_url(meta["scene_url"], "scene_url")
            if urlparse(raw_scene).scheme:
                scene = raw_scene
            else:
                rel = Path(raw_scene)
                if rel.is_absolute() or ".." in rel.parts or not (ROOT / rel).exists():
                    raise ValueError("Local scene_url must exist under visualizations/ and be repository-relative.")
                if rel.parts[0] != "visualizations":
                    raise ValueError("Local Luxar scenes belong under visualizations/.")
                scene = "../" + quote(rel.as_posix())
            if urlparse(scene).scheme:
                src = "https://luxarviewer.dev/?src=" + quote(scene, safe="") + "&theme=light"
        notebook_url = meta.get("notebook_url", "")
        if notebook_url and notebook_url not in {n["url"] for n in notebooks}:
            raise ValueError(f"Unknown notebook_url: {notebook_url}")
        figures.append(dict(title=meta.get("title", folder.name.replace("-", " ")), description=meta.get("description", "Interactive scientific figure."), project=project, project_name=name, example=bool(meta.get("example", False)), url=f"figures/{folder.name}.html", kind=kind, src=src, scene=scene, caption=meta.get("caption", ""), format_label=meta.get("format_label", "3D / WebGL" if kind == "luxar" else "Interactive HTML"), load_note=meta.get("load_note", "Loads only when requested. Use the viewer controls to explore."), notebook_url=notebook_url))

    notes = []
    for path in public_files(ROOT / "content"):
        if path.suffix != ".md":
            continue
        relative = path.relative_to(ROOT / "content")
        meta = read_json(path.with_suffix(".meta.json"), {})
        project, name = project_info(meta.get("project", "general"))
        body = path.read_text(encoding="utf-8")
        output = "notes/" + relative.with_suffix(".html").as_posix()
        if output == "notes/index.html":
            raise ValueError("content/index.md is reserved; use a descriptive filename.")
        item = dict(title=meta.get("title", title_from_markdown(body, path.stem)), project=project, project_name=name, description=meta.get("description", "Research notes and methods."), example=False, url=quote(output))
        notes.append(item)
        write_page(output, "note.html", title=item["title"], description=item["description"], section="notes", note=item, body=markdown.markdown(body, extensions=["extra", "toc"]))
    for path in public_files(ROOT / "content"):
        if path.suffix != ".md" and not path.name.endswith(".meta.json"):
            target = OUT / "notes" / path.relative_to(ROOT / "content")
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)

    notebooks.sort(key=lambda n: (n["example"], n["title"].casefold()))
    figures.sort(key=lambda n: (n["example"], n["title"].casefold()))
    notes.sort(key=lambda n: n["title"].casefold())
    for p in projects:
        p["notebooks"] = [n for n in notebooks if n["project"] == p["id"]]
        p["figures"] = [n for n in figures if n["project"] == p["id"]]
        p["notes"] = [n for n in notes if n["project"] == p["id"]]
        write_page(f"projects/{p['id']}.html", "project.html", title=p["name"], description=p["summary"], section="projects", project=p)

    exporter = HTMLExporter(template_name="lab")
    exporter.exclude_input_prompt = True
    exporter.exclude_output_prompt = True
    exporter.embed_images = False
    signature = b"".join(p.read_bytes() for p in sorted((ROOT / "templates").glob("*.html")))
    signature += Path(__file__).read_bytes() + json.dumps(site, sort_keys=True).encode()
    signature += "|".join(version(p) for p in ("nbconvert", "nbformat", "plotly")).encode()
    converted = 0
    for path, nb, item, output in source_notebooks:
        target = OUT / output
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target.with_suffix(".ipynb"))
        key = hashlib.sha256(signature + path.read_bytes() + output.encode() + json.dumps(item, sort_keys=True).encode()).hexdigest()
        cached = CACHE / f"{key}.html"
        if cached.exists():
            shutil.copy2(cached, target)
            continue
        nb = copy.deepcopy(nb)
        # Avoid a repeated title when the first Markdown cell starts with the notebook title.
        if nb.cells and nb.cells[0].cell_type == "markdown":
            nb.cells[0].source = re.sub(r"\A\s*#\s+" + re.escape(item["title"]) + r"\s*(?:\n|$)", "", nb.cells[0].source, count=1)
        ctx = context(output, title=item["title"], description=item["description"], section="notebooks", notebook=item)
        plotly_used = False
        for cell in nb.cells:
            for obj in cell.get("outputs", []):
                data = obj.get("data", {})
                if "application/vnd.plotly.v1+json" in data:
                    fig = pio.from_json(json.dumps(data["application/vnd.plotly.v1+json"]), skip_invalid=False)
                    fragment = pio.to_html(fig, full_html=False, include_plotlyjs=False, config={"responsive": True, "displaylogo": False})
                    data["text/html"] = fragment
                    plotly_used = True
        document, _ = exporter.from_notebook_node(nb, resources={"metadata": {"path": str(path.parent)}})
        soup = BeautifulSoup(document, "html.parser")
        soup.title.string = item["title"] + " · " + site["title"]
        soup.body["class"] = ["notebook-page"]
        for anchor in soup.select('a[href]'):
            href = anchor.get("href", "")
            if not urlparse(href).scheme and not href.startswith("#"):
                anchor["href"] = re.sub(r"\.ipynb(?=$|[?#])", ".html", href)
        main = soup.body.find("main")
        if main is None:
            main = soup.new_tag("main")
            for child in list(soup.body.contents):
                main.append(child.extract())
            soup.body.append(main)
        main["class"] = ["shell"]
        main["id"] = "main"
        notebook_content = soup.new_tag("div", id="notebook-content")
        for child in list(main.contents):
            notebook_content.append(child.extract())
        main.append(BeautifulSoup(env.get_template("notebook-heading.html").render(**ctx), "html.parser"))
        main.append(notebook_content)
        soup.body.insert(0, BeautifulSoup(env.get_template("header.html").render(**ctx), "html.parser"))
        soup.body.append(BeautifulSoup(env.get_template("footer.html").render(**ctx), "html.parser"))
        extra_head = f'<meta name="description" content="{html.escape(item["description"], quote=True)}"><link rel="icon" href="{ctx["root"]}assets/favicon.svg"><link rel="stylesheet" href="{ctx["root"]}assets/site.css"><script defer src="{ctx["root"]}assets/site.js"></script>'
        if ctx["canonical_url"]:
            extra_head += f'<link rel="canonical" href="{html.escape(ctx["canonical_url"], quote=True)}">'
        if plotly_used:
            extra_head += f'<script src="{ctx["root"]}assets/plotly.min.js"></script>'
        soup.head.append(BeautifulSoup(extra_head, "html.parser"))
        result = str(soup)
        target.write_text(result, encoding="utf-8")
        cached.write_text(result, encoding="utf-8")
        converted += 1

    write_page("index.html", "index.html", title="Research programme", section="projects", notebooks=notebooks, figures=figures)
    for section, title, entries, description in [
        ("notebooks", "Computational notebooks", notebooks, "Code, saved outputs and analysis across the research programme."),
        ("figures", "Interactive figures", figures, "Explore the data in three dimensions, one figure at a time."),
        ("notes", "Notes & methods", notes, "Methods, research notes and instructions for contributing to the record.")]:
        write_page(f"{section}/index.html", "directory.html", title=title, description=description, section=section, entries=entries)
    for figure in figures:
        write_page(figure["url"], "figure.html", title=figure["title"], description=figure["description"], section="figures", figure=figure)
    total = sum(p.stat().st_size for p in OUT.rglob("*") if p.is_file())
    oversized = [str(p.relative_to(OUT)) for p in OUT.rglob("*") if p.is_file() and p.stat().st_size > 95 * 1024**2]
    if oversized or total > 950 * 1024**2:
        raise ValueError(f"Site exceeds the conservative Pages budget. Host large scenes externally. Oversized files: {oversized}")
    manifest = dict(projects=len(projects), notebooks=len(notebooks), figures=len(figures), notes=len(notes), notebook_conversions=converted, bytes=total)
    (OUT / "build-manifest.json").write_text(json.dumps(manifest, indent=2))
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    build()
