# Publishing notebooks and figures

The site is a static research record. Python builds the pages; GitHub Pages serves them. Experiments run in your notebook environment, including Colab. Publishing reads the outputs already saved in each notebook.

## Add a notebook

1. Save a `.ipynb` file with its outputs in `notebooks/` and commit it.
2. GitHub Actions discovers it, renders it, and adds it to the notebook directory and homepage links.
3. Put it inside a project folder, such as `notebooks/damp/`, to associate it automatically with that project. Files at the root appear under General.

Project folder names are `spear`, `zampa`, `vampire`, `ampversity`, `pamperclip` and `damp`. Nested folders and filenames with spaces work. Notebook titles come from the first Markdown heading, falling back to the filename. Existing files appear in the directory without editing a navigation file.

For a description, project override or explicit title, add optional notebook metadata:

```json
"openamps": {
  "title": "Agreement across model families",
  "description": "Comparing predictions on a shared sequence panel.",
  "project": "damp"
}
```

In Colab or Python, metadata can be added after saving:

```python
from pathlib import Path
import nbformat

LOCAL_PROJECT = Path.cwd()  # Launch from your repository root.
path = LOCAL_PROJECT / "notebooks/damp/comparison.ipynb"
nb = nbformat.read(path, as_version=4)
nb.metadata["openamps"] = {
    "project": "damp",
    "title": "Agreement across model families",
    "description": "Comparing predictions on a shared sequence panel.",
}
nbformat.write(nb, path)
```

Keep figures and other local notebook assets beside the notebook or under `notebooks/`. Relative assets are copied. Relative links to other `.ipynb` files become links to their rendered pages. Paths outside the notebook tree need a public URL or an explicit link to the generated site location.

Code folding, saved tables, images, equations and rich HTML outputs are supported by Jupyter's nbconvert renderer. Saved Plotly JSON outputs are converted to interactive HTML and use a single locally served JavaScript bundle. Generic HTML outputs can retain their original external dependencies. JavaScript-only widgets need saved widget state and their renderer assets; Python callbacks, a running kernel, or a localhost server will not run on GitHub Pages. Export those views as standalone HTML or deploy their application separately.

Only publish notebooks and HTML outputs you trust and have reviewed for public sharing. Outputs can contain both data and executable JavaScript. Hidden files and `.ipynb_checkpoints` are excluded. The website does not run notebook code at build time.

## Add an interactive figure

Put a self-contained HTML export and its assets inside `visualizations/my-figure/`, with the entry point named `index.html`. The folder is discovered automatically. An optional `meta.json` gives it a useful title and project:

```json
{
  "title": "Peptide representation space",
  "description": "A three-dimensional view of the reference set.",
  "project": "ampversity",
  "kind": "html",
  "caption": "State the source data, embedding method and relevant limitations."
}
```

For Plotly, export a portable file from your own notebook:

```python
from pathlib import Path

LOCAL_PROJECT = Path.cwd()
target = LOCAL_PROJECT / "visualizations/my-figure/index.html"
target.parent.mkdir(parents=True, exist_ok=True)
fig.write_html(target, include_plotlyjs=True, full_html=True)
```

Every figure gets a dedicated page, an explicit Load button, a separate-window link and fullscreen support where available. Unload releases the iframe. No WebGL scene is loaded on the gallery page.

## Add a Luxar scene

Luxar's browser viewer reads compiled `.luxar.zarr` directories or `.luxar.zarr.zip` stores. A notebook display backed by a local server is not a publishable scene URL.

For a small scene, put the complete compiled directory under `visualizations/my-luxar/scene.luxar.zarr/`. Keep its Zarr metadata and index files, including dotfiles. Create `visualizations/my-luxar/meta.json`:

```json
{
  "title": "Peptide embedding in Luxar",
  "description": "An interactive view of the reference embeddings.",
  "project": "ampversity",
  "kind": "luxar",
  "scene_url": "visualizations/my-luxar/scene.luxar.zarr/",
  "caption": "Add the dataset version, dimensionality-reduction method and point count."
}
```

For a larger scene, set `scene_url` to its full public HTTPS URL in object storage. The site constructs a link to the hosted Luxar viewer with the scene URL encoded in `?src=`. The data host must allow cross-origin reads from `https://luxarviewer.dev`. ZIP stores additionally need HTTP byte-range support and appropriate exposed response headers. Validate the deployed scene in a browser before announcing it.

Luxar's `export` command creates a local/offline viewer package with a Python launcher. Do not assume that dropping that package onto a static host makes it a published scene. This integration uses the documented hosted-viewer route instead.

For a different hosted viewer, use `"kind": "external"` and `"viewer_url": "https://your-viewer.example/..."`. That host must allow iframe embedding; the separate-window link remains available if it does not.

This starter's working 3D demonstration uses Plotly and synthetic data. No research Luxar scene was supplied with the project brief.

## Pages and larger data

GitHub Pages has a 1 GB published-site limit and a soft 100 GB monthly bandwidth limit. Keep source data and very large 3D scenes in suitable object storage or a dataset repository, with provenance and citation links here. The build uses a conservative 950 MiB total limit and 95 MiB single-file limit to catch accidental large uploads early. A DOI archive is useful for citation, but test its CORS and range support before using it as a live viewer backend.

## Add notes and project resources

Drop Markdown into `content/`; it appears under Notes. A matching `filename.meta.json` can set `title`, `description` and `project`. Use descriptive filenames; `content/index.md` is reserved for the generated directory. Put note assets beside the Markdown file. Links between notes should use their generated `.html` filenames.

Edit `projects.json` to change a project's plan or add resources. Each project's `links` accepts entries like `{"title": "Dataset release", "url": "https://..."}`. Add real repository, paper and dataset URLs when available. No publication status or research result is inferred from the presence of a page.

## Publish on GitHub Pages

1. The source belongs at the root of `vinayprabhu/OpenAMPBench`, including `.github/workflows/pages.yml`.
2. `site.json` sets the repository, default branch `main`, and site URL `https://vinayprabhu.github.io/OpenAMPBench/`.
3. In repository Settings, select **Pages → Build and deployment → Source: GitHub Actions**.
4. Commit and push to `main`. The Actions tab shows the build and deployment.
5. The published address is `https://vinayprabhu.github.io/OpenAMPBench/`.

The build job has read-only repository access. Only the deployment job gets Pages and identity-token permissions, and it runs only for a push to the default branch or a manual run on that branch. Pull requests build and check without deploying. Enable Actions for the repository if your account requires it.

## Preview locally or in Colab

Install the dependencies from `requirements.txt`, then run `scripts/build.py`. From a terminal:

```text
python -m pip install -r requirements.txt
python scripts/build.py
python scripts/check_site.py
python -m http.server 8000 --directory _site
```

Open `http://localhost:8000` in your browser. After editing source files, run the build again. The `_site/` directory is generated, so changes made directly there are replaced on the next build.

For Colab with a mounted project directory:

```python
from pathlib import Path
import shutil
import subprocess
import sys

GOOGLE_DRIVE_PROJECT = Path("/content/drive/MyDrive/OpenAMPBench")
LOCAL_PROJECT = Path("/content/openampbench_site")

# One staged copy; no repeated tiny-file builds against mounted Drive.
shutil.copytree(
    GOOGLE_DRIVE_PROJECT,
    LOCAL_PROJECT,
    dirs_exist_ok=True,
    ignore=shutil.ignore_patterns(".git", "_site", ".build-cache", ".venv"),
)
subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
               cwd=LOCAL_PROJECT, check=True)
subprocess.run([sys.executable, "scripts/build.py"], cwd=LOCAL_PROJECT, check=True)
subprocess.run([sys.executable, "scripts/check_site.py"], cwd=LOCAL_PROJECT, check=True)

# Optional single archive write-back after the build completes.
archive = shutil.make_archive("/content/openampbench-preview", "zip", LOCAL_PROJECT / "_site")
shutil.copy2(archive, GOOGLE_DRIVE_PROJECT / "openampbench-preview.zip")
```

Notebook rendering is cached on local disk and in GitHub Actions. The cache key includes notebook contents, path, site settings, templates, renderer versions and build code. No research inference is performed by the publishing workflow.

## Design and implementation references

The visual direction borrows the restraint of scientific documentation, with a custom small stylesheet and Jupyter's standard HTML renderer. Quarto and the PyData Sphinx Theme were considered; no theme code was copied. This version uses Python throughout its build process and has no Node build step.

- [Jupyter nbconvert](https://nbconvert.readthedocs.io/en/latest/usage.html)
- [PyData Sphinx Theme](https://pydata-sphinx-theme.readthedocs.io/en/stable/)
- [Quarto document listings](https://quarto.org/docs/websites/website-listings.html)
- [Luxar: sharing and hosting](https://github.com/royerlab/luxar#sharing-and-hosting-a-scene)
- [GitHub Pages limits](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits)
- [GitHub Pages custom workflows](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)
