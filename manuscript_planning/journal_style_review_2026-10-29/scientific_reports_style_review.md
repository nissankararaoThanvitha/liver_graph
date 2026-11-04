# Scientific Reports: targeted writing-style review

Reviewed 29 October 2026. Scope: a purposive sample of three published original-research Articles, using their accessible full-text Introduction, methods, results, discussion and figure-caption sections. This is a writing/structure review, not a systematic literature review or endorsement of every scientific claim in these articles. No manuscript edits made.

## Verified journal guidance

https://www.nature.com/srep/author-instructions/submission-guidelines

The journal publishes Articles and Registered Reports. The completed retrospective computational project fits the Article format. The guidance recommends concision rather than a strict universal page limit: ideally at most 11 typeset pages; main text at most 4,500 words excluding abstract, Methods, references and legends; unstructured abstract at most 200 words; title at most 20 words; at most eight main display items. A commonly suitable order is Introduction, Results with subheadings, Discussion without subheadings, Methods, but the body has no universal mandatory structure. Supplementary Information is supplied separately, preferably as a combined PDF; editable Word preparation is compatible with subsequently producing that PDF. Published typeset pagination is not equivalent to draft single-column pagination.

## Observed models

| Article | Observed writing/organisation | Transfer to this manuscript |
|---|---|---|
| Wang ZY et al. (2021), Single-cell and bulk transcriptomics of the liver reveals potential targets of NASH with fibrosis. https://doi.org/10.1038/s41598-021-98806-y | Clinical/biological problem leads to a specific resolution gap and study objective. Introduction–Results–Discussion–Methods. Results organise cell profiling, communication, regulons and comparative evidence into topical subsections with multi-panel figures; complete regulon lists are referred to supplementary tables. | Prefer a biological findings narrative and keep complete lists outside the main text. The study contains single-cell and cross-species evidence that our project does not; do not borrow its mechanistic strength. |
| Feng J et al. (2025), Machine learning-based integration reveals reliable biomarkers and potential mechanisms of NASH progression to fibrosis. https://doi.org/10.1038/s41598-025-97670-4 | Introduction–Materials and methods–Results–Discussion–Conclusion. Results follow gene discovery, module interpretation, model development and biological context, using lettered figure panels and supplementary gene/model tables. | Supports grouped figure-led presentation, but is a diagnostic-model paper. Our candidate scores and LOSO refits do not establish analogous diagnostic performance. Do not adopt causal language merely because it appears in a published enrichment interpretation. |
| Wang L et al. (2025), From biomedical knowledge graph construction to semantic querying: a comprehensive approach. https://doi.org/10.1038/s41598-025-93334-5 | Separate Related work, Methods and Experiments sections, with explicit models, equations, baselines and ablation comparisons; workflow figure introduces the technical approach. | Demonstrates accepted structural flexibility. Use a clear KG schema/provenance description, but do not frame this project as a new graph-query algorithm or claim benchmark superiority without tests. |

## Proposed writing choices (editorial recommendations, not journal requirements)

- Frame the paper as a multi-cohort cross-sectional transcriptomic study with KG contextualisation and gene prioritisation.
- Introduction: approximately four focused paragraphs, progressing from clinical importance to prior work, unresolved integration question and precise objective. A separate long Related work section is optional; integrate essential comparisons to meet the mentor's length target.
- Results: explain resource and analysis populations; cross-study associations; stage-profile clusters; stage contrasts and functional context; prioritisation and internal robustness. Use descriptive finding-oriented headings and nearby figure references.
- Each Results paragraph should supply the question, key quantitative finding, figure/table pointer and bounded implication. Omit repeated implementation details and exhaustive gene lists.
- Discussion: synthesise the major biological patterns, relate them to selected literature, identify practical resource value, and explain clinical-label uncertainty, covariates, cross-sectional design and missing independent/functional validation. Avoid repeating every numerical result.
- Methods: retain patient handling, identifier/expression processing, statistical families, selection rules and validation design sufficiently for reproduction. Supplement lengthy rules and diagnostics without hiding material analytical decisions.
- Main figures combine evidence for a scientific question; move complete shortlist, detailed enrichment, stability diagnostics and the large annotation network to separate Supplementary Information.
- Keep the mentor's 9–10-page goal, but achieve it through selection and synthesis rather than tiny type or omission of uncertainty. Final page count depends on layout and does not guarantee journal acceptance.

## Evidence boundary

Three papers do not establish universal journal practice. Observed layouts support choices, while the journal guidance establishes requirements/recommendations. Historical disease terminology, treatment claims and publication wording require independent updating before reuse. No findings, analyses, performance measures or biological mechanisms from these papers are transferred to our project.
