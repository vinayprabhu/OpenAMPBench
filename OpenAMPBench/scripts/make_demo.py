"""Regenerate the small synthetic examples. Does not require AMP data or a GPU."""
from pathlib import Path
import json
import random

import nbformat as nbf
import plotly.graph_objects as go

ROOT = Path(__file__).resolve().parents[1]
rng = random.Random(17)
groups = [(-2.5, 0.5, 1.0, "#276557"), (1.8, 2.0, -0.8, "#a77535"), (1.3, -2.1, 1.0, "#526e99")]
fig = go.Figure()
for index, (cx, cy, cz, color) in enumerate(groups):
    points = [(rng.gauss(cx, .68), rng.gauss(cy, .8), rng.gauss(cz, .62)) for _ in range(80)]
    fig.add_trace(go.Scatter3d(x=[p[0] for p in points], y=[p[1] for p in points], z=[p[2] for p in points], mode="markers", name=f"Synthetic group {index + 1}", text=[f"Demo point {index*80+i+1:03d}" for i in range(80)], hovertemplate="%{text}<br>x=%{x:.2f}<br>y=%{y:.2f}<br>z=%{z:.2f}<extra>%{fullData.name}</extra>", marker=dict(size=4, color=color, opacity=.83)))
fig.update_layout(template="plotly_white", autosize=True, margin=dict(l=0,r=0,b=0,t=30), font=dict(family="Arial",size=13,color="#17272c"), legend=dict(orientation="h",x=0,y=1.02), scene=dict(xaxis_title="Coordinate 1",yaxis_title="Coordinate 2",zaxis_title="Coordinate 3",aspectmode="data",camera=dict(eye=dict(x=1.5,y=1.5,z=.9))))
folder = ROOT / "visualizations" / "embedding-demo"
folder.mkdir(parents=True, exist_ok=True)
fragment = fig.to_html(full_html=False, include_plotlyjs="../../assets/plotly.min.js", default_height="calc(100vh - 60px)", config={"responsive": True,"displaylogo": False,"scrollZoom": False})
html = '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Synthetic 3D embedding</title><style>body{margin:0;background:#fff;font-family:Arial,sans-serif}p{margin:4px 18px;font-size:13px;color:#58656a}</style></head><body>'+fragment+'<p>Drag to rotate. Use the toolbar to zoom, pan or reset the camera. Synthetic data.</p></body></html>'
(folder / "index.html").write_text(html,encoding="utf-8")
(folder / "meta.json").write_text(json.dumps(dict(title="A three-dimensional embedding",description="A small, synthetic point cloud demonstrating rotation, hover and group selection.",project="damp",kind="html",example=True,format_label="3D / Plotly",caption="240 synthetic points across three groups. Axes are arbitrary coordinates, not measured peptide properties. No embedding model was used.",load_note="Rotate, inspect individual points and toggle groups in the legend.",notebook_url="notebooks/view/damp/reading-predictions.html"),indent=2))

nb = nbf.v4.new_notebook()
nb.metadata = {"kernelspec":{"display_name":"Python 3","language":"python","name":"python3"},"language_info":{"name":"python","version":"3.12"},"openamps":{"title":"Reading a prediction table","description":"A worked example of comparing model outputs, using synthetic values.","project":"damp","example":True}}
code = '''from statistics import mean

# Synthetic values for a publishing demonstration, not measured MICs.
records = [
    {"id": "demo-01", "model_a": 0.81, "model_b": 0.78},
    {"id": "demo-02", "model_a": 0.74, "model_b": 0.32},
    {"id": "demo-03", "model_a": 0.29, "model_b": 0.41},
    {"id": "demo-04", "model_a": 0.92, "model_b": 0.87},
]
for row in records:
    row["gap"] = abs(row["model_a"] - row["model_b"])

print(f"Mean absolute gap: {mean(row['gap'] for row in records):.3f}")'''
nb.cells = [nbf.v4.new_markdown_cell("# Reading a prediction table\n\nThis example shows how a notebook becomes part of the research record. All values below are **synthetic**. They demonstrate formatting and model comparison, not biological findings.\n\n## 1. Start with aligned records\n\nCompare the same candidates across models before calculating disagreement."), nbf.v4.new_code_cell(code, execution_count=1, outputs=[nbf.v4.new_output("stream",name="stdout",text="Mean absolute gap: 0.155\n")]), nbf.v4.new_markdown_cell("## 2. Inspect individual disagreements\n\nAn average can conceal the cases worth inspecting. In this toy table, `demo-02` has the largest gap."), nbf.v4.new_code_cell('from IPython.display import HTML, display\n\nrows = "".join(\n    f"<tr><td>{r[\'id\']}</td><td>{r[\'model_a\']:.2f}</td>"\n    f"<td>{r[\'model_b\']:.2f}</td><td>{r[\'gap\']:.2f}</td></tr>"\n    for r in records\n)\ndisplay(HTML("<table><thead><tr><th>Candidate</th><th>Model A</th>"\n             "<th>Model B</th><th>Absolute gap</th></tr></thead>"\n             f"<tbody>{rows}</tbody></table>"))', execution_count=2, outputs=[nbf.v4.new_output("display_data",data={"text/html":"<table><thead><tr><th>Candidate</th><th>Model A</th><th>Model B</th><th>Absolute gap</th></tr></thead><tbody><tr><td>demo-01</td><td>0.81</td><td>0.78</td><td>0.03</td></tr><tr><td>demo-02</td><td>0.74</td><td>0.32</td><td>0.42</td></tr><tr><td>demo-03</td><td>0.29</td><td>0.41</td><td>0.12</td></tr><tr><td>demo-04</td><td>0.92</td><td>0.87</td><td>0.05</td></tr></tbody></table>","text/plain":"Four synthetic records"})]), nbf.v4.new_markdown_cell("## 3. What this comparison cannot tell us\n\nDisagreement does not identify the more accurate model. A biological evaluation needs comparable endpoints, units, bacterial strains and independent measurements.\n\nFor MIC comparisons, specify the concentration units and assay context; for classifiers, check whether the scores are calibrated before interpreting their differences.\n\n## 4. Publish a 3D view\n\nThe Figures section contains a companion synthetic point cloud. Each figure is a separate page, so the site can host many views without loading all of them together.")]
path = ROOT / "notebooks" / "damp" / "reading-predictions.ipynb"
path.parent.mkdir(parents=True,exist_ok=True)
nbf.write(nb,path)
print("Wrote synthetic notebook and 3D figure.")
