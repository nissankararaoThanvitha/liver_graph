"""Build the shareable HTML page of PAPER2_PROGRESS_REPORT.md.

Converts the generated Markdown report (so numbers come from the same source) into
Paper2_Results/report_page/index.html. Diagram images are referenced by their
Paper2_Results-relative paths and published alongside the page.

    python Paper2_Results/code/build_report_page.py
"""
import re
from pathlib import Path

import markdown

RES = Path(__file__).resolve().parents[1]
OUT = RES / "report_page"
OUT.mkdir(exist_ok=True)

md_text = (RES / "PAPER2_PROGRESS_REPORT.md").read_text(encoding="utf-8")
title_line, _, body_md = md_text.partition("\n")
subtitle = re.search(r"^\*(.+?)\*\s*$", body_md, re.M)
body_md = body_md.replace(subtitle.group(0), "", 1) if subtitle else body_md

html = markdown.markdown(body_md, extensions=["tables", "sane_lists"])
# figures: images get a light plate so the white PNGs read well in dark mode
html = re.sub(r'<p><img alt="([^"]*)" src="([^"]+)"\s*/?></p>',
              r'<figure class="plate"><img alt="\1 diagram" src="\2" loading="lazy"><figcaption>\1</figcaption></figure>', html)
html = re.sub(r"<table>", '<div class="tablewrap"><table>', html)
html = html.replace("</table>", "</table></div>")
# section anchors for the contents list
toc = []


def anchor(m):
    text = re.sub("<[^>]+>", "", m.group(1))
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    toc.append((slug, text))
    return f'<h2 id="{slug}">{m.group(1)}</h2>'


html = re.sub(r"<h2>(.*?)</h2>", anchor, html)
toc_html = "".join(f'<li><a href="#{s}">{t}</a></li>' for s, t in toc)

page = f"""<title>Paper 2 Progress Report</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Libre+Franklin:wght@600;800&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&family=JetBrains+Mono:wght@400;600&display=swap">
<style>
/* Layout: one reading column with a sticky contents rail on wide screens; colours borrow from H&E-stained liver histology (hematoxylin violet, eosin pink). */
:root {{
  --bg: #f7f7fa; --surface: #ffffff; --fg: #1d1b2b; --muted: #5c5a70; --rule: #dcdbe6;
  --accent: #4b3f8f; --eosin: #b8456f; --plate: #ffffff; --chip: #ecebf5;
  --f-display: "Libre Franklin", "Helvetica Neue", Arial, sans-serif;
  --f-body: "Source Serif 4", Georgia, "Times New Roman", serif;
  --f-mono: "JetBrains Mono", ui-monospace, Consolas, monospace;
}}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{
  --bg: #15141d; --surface: #1d1c28; --fg: #e9e8f2; --muted: #a6a4ba; --rule: #34324a;
  --accent: #a99cf0; --eosin: #e48aac; --plate: #f4f4f7; --chip: #2a2840; color-scheme: dark }} }}
:root[data-theme="dark"] {{
  --bg: #15141d; --surface: #1d1c28; --fg: #e9e8f2; --muted: #a6a4ba; --rule: #34324a;
  --accent: #a99cf0; --eosin: #e48aac; --plate: #f4f4f7; --chip: #2a2840; color-scheme: dark }}
body {{ background: var(--bg); color: var(--fg); font: 17px/1.6 var(--f-body);
  padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px)); }}
.wrap {{ max-width: 1120px; margin: 0 auto; padding-block: 40px 72px; display: grid; grid-template-columns: 220px minmax(0, 1fr); gap: 48px; }}
header {{ grid-column: 1 / -1; display: grid; gap: 12px; }}
.eyebrow {{ font: 600 12px/1 var(--f-display); letter-spacing: .14em; text-transform: uppercase; color: var(--eosin); }}
h1 {{ font: 800 clamp(30px, 5vw, 46px)/1.08 var(--f-display); margin: 0; text-wrap: balance; letter-spacing: -.01em; }}
.sub {{ color: var(--muted); margin: 0; max-width: 62ch; }}
.stages {{ display: flex; gap: 4px; margin-top: 8px; max-width: 420px; }}
.stages span {{ flex: 1; font: 600 11px/1 var(--f-mono); padding: 6px 0; text-align: center; border-radius: 3px; color: #fff; }}
nav {{ position: sticky; top: calc(env(safe-area-inset-top, 0px) + 24px); align-self: start; }}
nav p {{ font: 600 12px/1 var(--f-display); letter-spacing: .12em; text-transform: uppercase; color: var(--muted); margin: 0 0 12px; }}
nav ol {{ list-style: none; padding: 0; margin: 0; display: grid; gap: 8px; font: 14px/1.35 var(--f-display); }}
nav a {{ color: var(--fg); text-decoration: none; border-left: 2px solid var(--rule); padding-left: 10px; display: block; }}
nav a:hover, nav a:focus-visible {{ border-color: var(--accent); color: var(--accent); outline: none; }}
main {{ min-width: 0; }}
main > * {{ max-width: 72ch; }}
main > figure, main > .tablewrap {{ max-width: 100%; }}
h2 {{ font: 800 24px/1.2 var(--f-display); margin: 56px 0 14px; padding-top: 18px; border-top: 1px solid var(--rule); text-wrap: balance; scroll-margin-top: 20px; }}
h2:first-of-type {{ margin-top: 0; }}
strong {{ font-weight: 600; }}
a {{ color: var(--accent); }}
code {{ font: 0.86em var(--f-mono); background: var(--chip); padding: 1px 5px; border-radius: 3px; overflow-wrap: anywhere; }}
ul, ol {{ padding-left: 1.3em; }}
li + li {{ margin-top: 6px; }}
hr {{ border: 0; height: 0; margin: 8px 0; }}
.tablewrap {{ overflow-x: auto; margin: 16px 0 20px; border: 1px solid var(--rule); border-radius: 6px; background: var(--surface); }}
table {{ border-collapse: collapse; width: 100%; font: 14px/1.4 var(--f-display); font-variant-numeric: tabular-nums; }}
th {{ text-align: left; font-weight: 600; color: var(--muted); font-size: 12px; letter-spacing: .04em; text-transform: uppercase; padding: 10px 12px; border-bottom: 1px solid var(--rule); white-space: nowrap; }}
td {{ padding: 9px 12px; border-bottom: 1px solid var(--rule); vertical-align: top; }}
tr:last-child td {{ border-bottom: 0; }}
figure.plate {{ margin: 20px 0 28px; background: var(--plate); border: 1px solid var(--rule); border-radius: 8px; padding: 10px; }}
figure.plate img {{ display: block; width: 100%; height: auto; max-width: 100%; }}
figcaption {{ font: 12px/1.3 var(--f-display); color: #5c5a70; padding: 8px 4px 0; letter-spacing: .04em; text-transform: uppercase; }}
footer {{ grid-column: 1 / -1; color: var(--muted); font: 13px/1.5 var(--f-display); border-top: 1px solid var(--rule); padding-top: 16px; }}
@media (max-width: 860px) {{
  .wrap {{ grid-template-columns: minmax(0, 1fr); gap: 28px; padding-block: 28px 56px; }}
  nav {{ position: static; }}
  nav ol {{ grid-template-columns: repeat(auto-fill, minmax(170px, 1fr)); }}
  body {{ font-size: 16px; }}
}}
@media (prefers-reduced-motion: no-preference) {{ html {{ scroll-behavior: smooth; }} }}
</style>

<div class="wrap">
  <header>
    <div class="eyebrow">Paper 2 · Knowledge-graph drug repurposing</div>
    <h1>{title_line.lstrip('# ').strip()}</h1>
    <p class="sub">{subtitle.group(1) if subtitle else ''} Outputs are repurposing hypotheses, not treatments.</p>
    <div class="stages" aria-label="Fibrosis stages F0 to F4">
      <span style="background:#8d86b8">F0</span><span style="background:#7468a8">F1</span><span style="background:#7b5296">F2</span><span style="background:#94467f">F3</span><span style="background:#b8456f">F4</span>
    </div>
  </header>
  <nav aria-label="Contents"><p>Contents</p><ol>{toc_html}</ol></nav>
  <main>
{html}
  </main>
  <footer>Generated from <code>Paper2_Results/PAPER2_PROGRESS_REPORT.md</code>. Every number is read from the Task 1–7 output files and checked by an independent audit script.</footer>
</div>
"""
(OUT / "index.html").write_text(page, encoding="utf-8")
imgs = sorted(set(re.findall(r'src="([^"]+\.png)"', html)))
print("\n".join(imgs))
