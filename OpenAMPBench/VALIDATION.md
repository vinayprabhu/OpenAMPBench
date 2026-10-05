# Validation record

- All 14 generated HTML pages passed internal link and asset checks.
- Temporary input checks passed for automatic notebook discovery, nested folders, filenames with spaces, local images, relative notebook links, saved Plotly JSON and preserving Luxar/Zarr dotfiles. Those temporary fixtures are not included in the deliverable.
- A notebook containing a deliberately failing Python cell rendered from its saved outputs without executing the cell.
- Browser checks passed at widths of 390, 768 and 1440 pixels across the homepage, a project, the notebook directory, a rendered notebook, a figure page and the publishing guide. No document-width overflow was found.
- Notebook table output, directory filtering, code folding, on-demand 3D loading, drag rotation and unloading passed in headless Chromium 134 using software WebGL. No uncaught page JavaScript errors were recorded.
- Screenshots of the homepage, notebook, figure and mobile homepage were visually reviewed.
- The complete site occupies approximately 5.2 MB before archive compression, including its shared Plotly JavaScript bundle.
- A live Pages deployment was not verified. The workflow follows GitHub's documented build/artifact/deploy pattern.
- Luxar metadata and URL construction are supported. No research Luxar scene was supplied, so scene rendering and the final host's CORS/range behaviour still require checking after a real scene is attached.
- Browser-side widgets depending on external JavaScript or a Python backend are not universally supported; see the publishing guide for supported export patterns.
