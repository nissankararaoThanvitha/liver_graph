# Manuscript compilation and Overleaf setup

## Exact settings and upload structure

Upload the repository/project root while preserving directory names and case. In Overleaf, select **XeLaTeX** as the compiler and **Paper1_Manuscript/inline_layout/manuscript_v2.tex** as the main document. Do not upload only the .tex file or flatten the figure directories. The repository-root `.latexmkrc` selects XeLaTeX for local latexmk runs; explicitly select XeLaTeX in Overleaf as well. Recompile until references resolve.

Required figure files:

```
Paper1_Results/Figure1/figure1_pipeline.png
Paper1_Results/Figure1/research_project_pipeline.pdf
Paper1_Results/Task1/task1_venn.png
Paper1_Results/Task1/task1_shared_rho_scatter.png
Paper1_Results/Task2/task2_cluster_trajectories.png
Paper1_Results/Task2/task2_heatmap.png
Paper1_Results/Task2/task2_choosing_k.png
Paper1_Results/Task3/task3_transition_comparison.png
Paper1_Results/Task4/task4_heatmap_hallmark.png
Paper1_HighConfidence/12_mechanistic_subgraph.png
```

The new pipeline PNG is the Markdown companion; LaTeX uses the vector PDF. Existing image assets are unchanged. Overleaf does not need research datasets or scripts to typeset this manuscript. References are embedded in the .tex file; no .bib file is required.

The font configuration selects Times New Roman when available and otherwise uses Times-compatible TeX Gyre Termes. There are no Windows font paths and no redistributed proprietary font files. Overleaf's primary guidance describes XeLaTeX/fontspec and available fonts: https://www.overleaf.com/learn/latex/XeLaTeX. Compiler selection: https://docs.overleaf.com/getting-started/recompiling-your-project/selecting-a-tex-live-version-and-latex-compiler.

## Root cause and correction

The earlier image macro checked `../../<asset>` and an absolute `C:/Users/DELL/liver_graph/<asset>` path, then silently rendered a text box if both checks failed. Overleaf compiles from its project root and cannot access the local Windows filesystem. Those lookup paths therefore did not match the uploaded repository layout. If only the source file was uploaded, no actual image assets could be found either.

The corrected macro directly includes repository-root-relative image paths. Missing assets now raise an explicit compilation error rather than being replaced by invented images or empty/text placeholders. All nine original image assets were present and tracked at inspection; their filename case and extensions matched the actual files. `graphicx` and the figure environments were enabled, with no draft setting suppressing images. The new pipeline adds Figure6 without renumbering or changing Figures1–5 or their captions.

## Pipeline provenance and scope

The Project Pipeline subsection follows Materials and methods in both inline-layout manuscript versions. It describes deposited GEO inputs, identifier/clinical harmonisation, supported expression transformations, Neo4j/OptimusKG integration, patient units and eligibility, association discovery, cross-sectional pattern/contrast/enrichment analyses, prioritisation and internal checks, and final resource export/audits.

Read-only sources inspected include docs/provenance/REBUILD.md, manuscript_planning/complete_workflow.md, build_graph_all.py, normalize_clinical.py, find_progression_genes.py, scripts/kg_subgraph.py, scripts/loso_validation.py and final_combined_2026-10-10/promotion_status.json. Historical source comments containing superseded counts were not used as final results. No analyses, research scripts, datasets, original plots or scientific result tables were changed.

## Validation performed

The desktop editor's built-in standalone compiler uses an isolated source directory and does not provide the repository figure tree. With silent placeholders removed, its check reports the first missing external image. This is an editor packaging limitation, not evidence that the tracked repository assets are absent. Keep the existing editor/source open; validate the full project from its root or in Overleaf with the required directories uploaded.

The complete repository-backed source was compiled successfully with the installed Tectonic0.17.0 XeTeX engine, using cached TeX resources, an explicit repository search path and a rerun. The resulting PDF had20 pages, nine original raster image objects and the new vector pipeline. Figure captions1–6 and table captions1–3 each occurred once; all13 bibliography entries resolved. The final TeX log had no undefined citations/references or overfull boxes. All six rendered figure pages were inspected. Figures3/4 panel sizes and two table-header widths were improved without changing image content, caption text or scientific table values.

The local engine reports benign Windows font/resource-probe warnings while resolving installed Times New Roman; those paths are not hard-coded in the source. The PDF was produced successfully. Overleaf itself was not accessed or remotely compiled in this task.

Validation PDF/logs and rendered pages were written only to temporary validation output and are excluded from the commit. The20-page review draft and dense existing plot labels still require final journal-size proofing before submission. Existing administrative caption notes about unassembled composites were preserved as requested: the .tex now arranges source panels, while separate composite image files have not been regenerated.

## Local compilation

From the repository root with XeLaTeX/latexmk installed:

```sh
latexmk -xelatex Paper1_Manuscript/inline_layout/manuscript_v2.tex
```

For Tectonic's XeTeX engine, pass the repository root explicitly if the main document is nested:

```sh
tectonic -X compile -Z search-path=. --reruns 1 Paper1_Manuscript/inline_layout/manuscript_v2.tex
```

Scientific content is unchanged outside the added pipeline. Existing section text, captions, numbers, clinical-label/biopsy/RLE policies, citations, references, placeholders and table entries were retained. Figures remain near their first discussion, and the new Figure6 follows its first discussion in Project Pipeline.
