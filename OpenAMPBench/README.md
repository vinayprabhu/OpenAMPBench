# OpenAMPBench

A small GitHub Pages website for SPEAR, ZAMPA, VAMPIRE, AMPversity, pAMPerclip and DAMP. The six project descriptions reflect the supplied AMR research plan; they do not assert completed experiments or validated outcomes.

## Start here

1. Keep this source at the root of `vinayprabhu/OpenAMPBench`, including `.github/`.
2. `site.json` is configured for `https://github.com/vinayprabhu/OpenAMPBench` and `https://vinayprabhu.github.io/OpenAMPBench/`.
3. **Settings → Pages** should show **GitHub Actions** as the source.
4. Push to `main`. Actions builds, checks and publishes the site.

The project repository is served at `https://vinayprabhu.github.io/OpenAMPBench/`. Generated links are relative, so project pages, notebooks and figures work under this subpath.

## Daily use

| Add this | Where | What happens |
|---|---|---|
| A saved notebook | `notebooks/**/*.ipynb` | Rendered, downloadable, automatically indexed |
| A project notebook | `notebooks/damp/`, etc. | Also appears on that project's page |
| A standalone interactive figure | `visualizations/slug/index.html` | Gets a dedicated, on-demand viewer page |
| Figure metadata | `visualizations/slug/meta.json` | Sets project, title, caption and viewer type |
| A Luxar scene reference | `meta.json` with `kind: luxar`, `scene_url` | Uses Luxar's hosted viewer against the public scene |
| A Markdown note | `content/*.md` | Rendered and indexed under Notes |
| A paper, dataset or repository link | `projects.json` → `links` | Appears on the corresponding project page |

**No navigation files to update when adding notebooks.** Notebook metadata is optional. Root-level notebooks appear under General; project folders or `metadata.openamps.project` assign a project. The homepage links to the complete automatically generated directory and shows counts on project rows. It features one notebook and one figure rather than becoming a long feed.

## Local preview

```text
python -m pip install -r requirements.txt
python scripts/build.py
python scripts/check_site.py
python -m http.server 8000 --directory _site
```

Open `http://localhost:8000`. `_site/` is generated and ignored by Git. Run the build again after edits; the preview does not watch files automatically.

## Design

White background, dark text, serif headings, fine rules and a compact research index. No decorative animation, gradients, card grid, external font request or analytics. The notebook layout uses Jupyter's nbconvert renderer, with a shared stylesheet for headings, tables and code. Quarto and PyData Sphinx were considered as scientific publishing references; this implementation uses a lightweight Python build and does not copy their theme code.

## Included demonstrations

- One DAMP notebook with explicitly synthetic comparison values.
- One working Plotly 3D scatter with 240 synthetic points, rotation, hover, group toggles and camera controls.
- Regenerate them with `python scripts/make_demo.py` if needed.
- Delete those two source folders when your own content is ready, then rebuild. Empty sections remain valid.

There is no supplied biological dataset or Luxar research scene in this package. Luxar integration is implemented using the documented hosted-viewer URL, with local or externally hosted compiled stores. Live deployment and the user's actual scenes still need testing against their chosen host.

## Publishing behaviour and limits

- Notebook code is **never executed** during publication. Save the outputs you want readers to see.
- Jupyter HTML, text, images, Markdown, equations and saved Plotly JSON are rendered. Widget state and assets are necessary for browser-side widgets; live Python callbacks require a separate application.
- Review rich outputs before publishing: they are trusted HTML and can include JavaScript.
- Each 3D view loads only after a click; the directory never instantiates all the scenes. An Unload control removes the iframe.
- Luxar needs HTTPS, CORS, and byte-range support for ZIP stores. Zarr metadata dotfiles are preserved and the generated root includes `.nojekyll`.
- Keep very large data outside Pages and reference it. The build fails above conservative 95 MiB/file or 950 MiB/site budgets. These are starter guardrails, not exact GitHub service limits.
- Colab links appear once `site.json.repository` is configured; local downloads work without that setting.
- The workflow builds pull requests without deploying. Pushes to the default branch deploy after Pages has been enabled.

The [publishing guide](content/publishing.md) contains metadata examples, Luxar instructions, a Colab staging recipe, and primary-source references. The guide is also rendered on the site.

## Files to edit

- `site.json`: identity and repository settings.
- `projects.json`: questions, plans, intended outputs, related projects and resource URLs.
- `assets/site.css`: visual design.
- `templates/`: page structure.
- `scripts/build.py`: discovery, rendering and indexing.
- `scripts/check_site.py`: internal-link checks.

Generated Python site code and templates are provided for reuse under the MIT license. That does not relicense imported notebooks, data, publications or the third-party libraries they use. Consult their original terms when adding content.
