# -*- coding: utf-8 -*-
"""Builds the Paper 1 manuscript as a Word document.

Every number in the Results comes from the committed Paper1_Results outputs
(the four README.txt files and their CSVs), not from memory, so the draft
cannot drift from the analysis. Sections the mentor said she will write
herself -- Discussion and Conclusion -- are left as marked placeholders
rather than ghost-written.
"""
import os
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

ROOT = r"C:\Users\nissa\OneDrive\Desktop\liver_kg"
FIG = os.path.join(ROOT, "Paper1_Results")
OUTDIR = os.path.join(ROOT, "Paper1_Manuscript")
os.makedirs(OUTDIR, exist_ok=True)
OUT = os.path.join(OUTDIR, "Paper1_draft_v1.docx")

doc = Document()

# ------------------------------------------------------------- page setup
sec = doc.sections[0]
sec.page_width, sec.page_height = Inches(8.27), Inches(11.69)      # A4
for m in ("top_margin", "bottom_margin", "left_margin", "right_margin"):
    setattr(sec, m, Inches(1.0))

# continuous line numbers -- makes it far easier for a supervisor to comment
ln = OxmlElement("w:lnNumType")
ln.set(qn("w:countBy"), "1")
ln.set(qn("w:restart"), "continuous")
ln.set(qn("w:distance"), "360")
sec._sectPr.append(ln)

normal = doc.styles["Normal"]
normal.font.name = "Times New Roman"
normal.font.size = Pt(11)
normal._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
pf = normal.paragraph_format
pf.line_spacing_rule = WD_LINE_SPACING.DOUBLE
pf.space_after = Pt(0)

for name, size in (("Heading 1", 13), ("Heading 2", 11.5), ("Heading 3", 11)):
    st = doc.styles[name]
    st.font.name = "Times New Roman"
    st.font.size = Pt(size)
    st.font.bold = True
    st.font.color.rgb = RGBColor(0, 0, 0)
    st.paragraph_format.space_before = Pt(12)
    st.paragraph_format.space_after = Pt(4)
    st.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE


def para(text="", style=None, align=None, italic=False, bold=False,
         size=None, space_after=None, single=False):
    p = doc.add_paragraph(style=style)
    if text:
        r = p.add_run(text)
        r.italic, r.bold = italic, bold
        if size:
            r.font.size = Pt(size)
    if align is not None:
        p.alignment = align
    if single:
        p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
    if space_after is not None:
        p.paragraph_format.space_after = Pt(space_after)
    return p


def body(text):
    return para(text, align=WD_ALIGN_PARAGRAPH.JUSTIFY)


def todo(text):
    """A placeholder the author must act on -- visually unmistakable."""
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(6)
    r = p.add_run("[ " + text + " ]")
    r.bold = True
    r.font.color.rgb = RGBColor(0xB0, 0x30, 0x00)
    r.font.size = Pt(10)
    return p


def figure(relpath, legend_title, legend_body, width_in=6.0):
    path = os.path.join(FIG, relpath)
    if not os.path.exists(path):
        todo("MISSING FIGURE FILE: " + relpath)
        return
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
    p.add_run().add_picture(path, width=Inches(width_in))
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    cap.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
    cap.paragraph_format.space_after = Pt(12)
    r = cap.add_run(legend_title)
    r.bold = True
    r.font.size = Pt(9.5)
    r2 = cap.add_run(" " + legend_body)
    r2.font.size = Pt(9.5)


def table(headers, rows, caption_title, caption_body, widths=None):
    cap = doc.add_paragraph()
    cap.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
    cap.paragraph_format.space_before = Pt(10)
    cap.paragraph_format.space_after = Pt(4)
    r = cap.add_run(caption_title)
    r.bold = True
    r.font.size = Pt(9.5)
    r2 = cap.add_run(" " + caption_body)
    r2.font.size = Pt(9.5)

    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    t.autofit = True
    for i, h in enumerate(headers):
        c = t.rows[0].cells[i]
        c.text = ""
        pr = c.paragraphs[0]
        pr.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
        run = pr.add_run(str(h))
        run.bold = True
        run.font.size = Pt(9)
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            pr = cells[i].paragraphs[0]
            pr.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
            run = pr.add_run(str(v))
            run.font.size = Pt(9)
    if widths:
        for r_ in t.rows:
            for i, w in enumerate(widths):
                r_.cells[i].width = Inches(w)
    doc.add_paragraph().paragraph_format.space_after = Pt(6)
    return t


# ============================================================ TITLE BLOCK
para("A cross-study knowledge graph of 1,085 human liver biopsies resolves "
     "fibrosis progression into stage-specific gene programmes",
     align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=14, single=True,
     space_after=10)

para("[Author list to be completed]", align=WD_ALIGN_PARAGRAPH.CENTER,
     italic=True, size=11, single=True, space_after=2)
para("[Affiliations to be completed]", align=WD_ALIGN_PARAGRAPH.CENTER,
     italic=True, size=10, single=True, space_after=2)
para("[Corresponding author and e-mail to be completed]",
     align=WD_ALIGN_PARAGRAPH.CENTER, italic=True, size=10, single=True,
     space_after=10)

todo("DRAFT v1. Written from the committed outputs in Paper1_Results. "
     "Discussion and Conclusion are deliberately left blank for the supervisor. "
     "References are not yet inserted; citation markers read [REF]. "
     "Line numbering is on to make commenting easier.")

# ================================================================ ABSTRACT
doc.add_heading("Abstract", level=1)
body(
    "Fibrosis stage is the strongest predictor of liver-related outcome in "
    "metabolic dysfunction-associated steatotic liver disease, yet the "
    "molecular events that separate one stage from the next remain poorly "
    "resolved [REF]. Individual transcriptomic cohorts are small, stage "
    "distributions are uneven, and each study records severity on its own "
    "scale, so findings have been difficult to compare or combine. Here we "
    "assembled eight public human liver transcriptome studies comprising "
    "1,085 biopsies from 1,027 patients into a single property graph of "
    "126,244 nodes and 35,091,066 relationships, in which per-sample "
    "measurement and curated biological knowledge are queryable together. "
    "Gene identifiers were mapped to one canonical namespace and clinical "
    "labels were harmonised onto two explicitly separate ladders: fibrosis "
    "stage F0-F4, and disease group from control through NAFL to NASH. "
    "Correlating expression with ladder position within each study and "
    "combining across studies, rather than pooling patients, identified "
    "4,692 progression-associated genes, of which 1,953 tracked fibrosis "
    "only, 1,047 inflammation only and 1,692 both. Clustering the 3,645 "
    "fibrosis-associated genes by the shape of their F0-F4 curve resolved "
    "five reproducible trajectories, including an early immune activation "
    "programme and a late matrix-remodelling programme. Testing every stage "
    "transition at patient level under a power-matched design showed that "
    "the transition into cirrhosis, F3 to F4, carries by far the largest "
    "transcriptional change: a median of 311 substantially changing genes "
    "against 0-2 for earlier transitions, with effect sizes roughly twice "
    "as large. Enrichment against the 14,794 genes eligible for cross-study "
    "analysis assigned distinct biology to each group: loss of xenobiotic, "
    "fatty-acid and bile-acid metabolism among down-regulated genes, and "
    "extracellular matrix formation, epithelial-mesenchymal transition and "
    "TNF-NF-kB signalling among genes shared by both ladders. The resulting "
    "stage-resolved map provides a reproducible foundation for staging "
    "models and for therapeutic target prioritisation.")

para()
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
r = p.add_run("Keywords: ")
r.bold = True
p.add_run("liver fibrosis; MASLD/NAFLD; disease progression; knowledge "
          "graph; transcriptomics; cross-study integration; stage transition")

# ============================================================ INTRODUCTION
doc.add_heading("1. Introduction", level=1)

body(
    "Metabolic dysfunction-associated steatotic liver disease affects a "
    "substantial fraction of the adult population worldwide and is now a "
    "leading indication for liver transplantation [REF]. Its clinical course "
    "is governed less by the presence of steatosis than by the degree of "
    "fibrosis: among all histological features scored on biopsy, fibrosis "
    "stage is the feature most consistently associated with liver-related "
    "morbidity and mortality [REF]. Staging therefore sits at the centre of "
    "both prognosis and trial eligibility. It nonetheless still depends on "
    "needle biopsy, an invasive procedure subject to sampling variability "
    "and inter-observer disagreement, and one that returns a single ordinal "
    "label rather than any account of the molecular processes that carried "
    "the tissue from one stage to the next [REF].")

body(
    "Transcriptomic profiling of staged biopsies offers a route to that "
    "account, and many such cohorts are now public. In practice, however, "
    "they have proved difficult to use collectively. Individual studies "
    "enrol tens to a few hundred patients, and advanced stages are "
    "systematically under-represented because patients with cirrhosis are "
    "biopsied less often. Each cohort differs in sequencing platform, depth "
    "and centre, so absolute expression values are not comparable across "
    "studies. Severity is recorded on study-specific scales, with the same "
    "biological state written variously as \"4\", \"F4\" or a free-text "
    "description, so a naive query against a merged table silently returns "
    "an incomplete group rather than an error. Analyses that pool patients "
    "across cohorts without addressing these differences risk reporting "
    "cohort structure as biology.")

body(
    "Knowledge graphs have become a common substrate for integrating "
    "heterogeneous biomedical evidence, linking genes to diseases, pathways, "
    "phenotypes and drugs in a single queryable structure [REF]. Existing "
    "resources of this kind are, however, built almost entirely from curated "
    "literature assertions: they encode what is already known about a gene, "
    "but contain no patient-level measurement, and therefore cannot by "
    "themselves say how a gene behaves as a particular disease advances. "
    "Conversely, differential-expression analyses produce exactly that "
    "measurement but discard the surrounding biological context. The two "
    "halves are rarely held in the same structure.")

body(
    "This study was designed around that gap, and differs from previous work "
    "in several respects that we consider essential rather than incidental. "
    "First, measurement and curated knowledge are placed in one graph, so "
    "that a gene's behaviour across 1,085 biopsies and its established "
    "pathway, disease and drug associations are reachable in a single query; "
    "the patient-derived edges linking genes to fibrosis and inflammation "
    "are themselves a contribution to the graph rather than an import from "
    "an existing database. Second, both the gene axis and the patient axis "
    "are harmonised, and every clinical translation is additive, leaving the "
    "original study-specific fields untouched so that each mapping remains "
    "auditable. Third, fibrosis and inflammation are treated as two separate "
    "ladders rather than one severity score, because they are scored "
    "separately by pathologists, differ in reversibility, and dissociate in "
    "real patients: 40 patients in this cohort have steatohepatitis at "
    "fibrosis stage 0, a state that is invisible on the fibrosis ladder "
    "alone. Fourth, genes are selected by agreement across independent "
    "studies rather than by pooling patients, so that a gene behaving "
    "atypically in a single cohort cannot enter the result. Fifth, "
    "enrichment is tested against the genes actually eligible for "
    "cross-study analysis rather than the whole genome, which materially "
    "changes which terms reach significance. Finally, each result is "
    "reported with the stability or power analysis that bounds it, so that "
    "the distinction between what the data support and what they merely "
    "suggest is visible in the output itself.")

body(
    "We report here the construction of that resource and four analyses "
    "built on it: the division of progression-associated genes into "
    "fibrosis-specific, inflammation-specific and shared programmes; the "
    "shapes those genes trace across stages F0 to F4; the stage transition "
    "at which the largest transcriptional change occurs; and the biological "
    "processes enriched in each group. Together these define a "
    "stage-resolved molecular map of fibrosis progression, intended both as "
    "a basis for staging models and as the evidence layer for downstream "
    "therapeutic target prioritisation.")

# ================================================================= RESULTS
doc.add_heading("2. Results", level=1)

doc.add_heading("2.1 A harmonised eight-study resource linking measurement to "
                "curated knowledge", level=2)
body(
    "We assembled eight public human liver transcriptome studies "
    "(Table 1), together comprising 1,085 samples from 1,027 patients; the "
    "difference reflects 58 patients in GSE193066 who were biopsied twice. "
    "Expression files were converted to a common long format, and gene "
    "identifiers from all studies were mapped to canonical Ensembl "
    "identifiers, yielding 53,993 genes. Because studies differ in platform "
    "and depth, expression was standardised per gene within each study "
    "(value_z); this within-study standardisation is what makes the eight "
    "cohorts comparable at all, and all subsequent analyses use it.")
body(
    "Clinical labels were harmonised onto two ladders. Fibrosis stage was "
    "recorded as \"0\"-\"4\" in four studies, \"F0\"-\"F4\" in another, and "
    "in one case as free text; disease state was recorded with four "
    "different vocabularies. Harmonised fibrosis_stage and disease_group "
    "fields were added alongside, never replacing, the original values, so "
    "that every translation remains auditable. Where a label could not be "
    "established with confidence it was left blank rather than inferred: "
    "one apparently informative field in GSE193066 was tested and rejected "
    "because the group it produced was more fibrotic yet expressed less "
    "COL1A1 than its comparator, contradicting that study's own staging and "
    "the direction seen in every other cohort. After harmonisation, 668 "
    "samples carry a fibrosis stage (F0 152, F1 168, F2 186, F3 127, F4 35) "
    "and the imbalance at F4 is carried explicitly through every subsequent "
    "analysis.")
body(
    "The harmonised data were loaded into a Neo4j property graph of 126,244 "
    "nodes and 35,091,066 relationships (Figure 1). Sample-to-gene "
    "EXPRESSES edges constitute 32,471,042 of these and represent "
    "measurement; curated nodes and edges for diseases, pathways, "
    "biological processes, phenotypes and drugs were attached from "
    "OptimusKG, restricted to associations with an evidence score of at "
    "least 0.1 to prevent the weakest literature co-mentions from "
    "connecting everything to everything. Each gene node additionally "
    "records n_datasets, the number of studies in which it was measured; "
    "39,199 genes are absent from at least one study and 10,621 appear in "
    "exactly one, so this field is required before any cross-gene "
    "comparison.")

figure("Figure1/figure1_pipeline.png",
       "Figure 1. Study design and analysis pipeline.",
       "Eight public GEO liver transcriptome studies were parsed to a common "
       "long format, harmonised on both the gene axis (identifier mapping to "
       "Ensembl) and the patient axis (fibrosis stage, disease group, patient "
       "identity), standardised within study, and loaded into a Neo4j property "
       "graph together with a curated knowledge layer. Progression-associated "
       "genes were identified by per-study Spearman correlation against each "
       "ladder, combined across studies, and then analysed in four steps "
       "corresponding to Sections 2.2-2.5. Counts shown are the final values "
       "reported in this paper.", width_in=6.0)

table(
    ["Study", "Samples", "Patients", "Fibrosis staged", "Disease labelled"],
    [["GSE126848", 57, 57, "no", "yes"],
     ["GSE130970", 78, 78, "yes", "derived"],
     ["GSE135251", 216, 216, "yes", "yes"],
     ["GSE162694", 143, 143, "yes", "yes"],
     ["GSE167523", 98, 98, "no", "yes"],
     ["GSE193066", 164, 106, "yes", "no"],
     ["GSE240729", 67, 67, "yes", "no"],
     ["GSE269412", 262, 262, "no", "no"],
     ["Total", 1085, 1027, "668 samples", "-"]],
    "Table 1. Studies included.",
    "Patients differ from samples only in GSE193066, where 58 patients were "
    "biopsied twice; repeat biopsies are collapsed to one observation per "
    "patient before any statistical test. \"derived\" indicates diagnosis "
    "reconstructed from the study's own Kleiner component scores using the "
    "standard NASH-CRN definition, flagged in the data and removable with a "
    "single filter.",
    widths=[1.5, 1.0, 1.0, 1.3, 1.3])

doc.add_heading("2.2 Progression-associated genes separate into "
                "fibrosis-specific, inflammation-specific and shared "
                "programmes", level=2)
body(
    "For each gene we computed Spearman correlations against ladder position "
    "within each study separately, then combined the per-study coefficients "
    "by their median and the per-study p-values by Fisher's method. Genes "
    "were retained only when the false-discovery rate was below 0.05 and "
    "every study in which the gene was testable agreed on the direction of "
    "effect. This requirement is deliberately strict: a gene that rises "
    "convincingly in one cohort but is flat in the others is excluded, "
    "because such behaviour is more readily explained by cohort composition "
    "than by disease biology. Repeat biopsies were collapsed to one "
    "observation per patient before testing, so that the 58 twice-biopsied "
    "patients in GSE193066 could not receive double weight.")
body(
    "This procedure identified 4,692 progression-associated genes. "
    "Partitioning them by ladder (Table 2) showed that 1,953 genes (41.6%) "
    "tracked fibrosis only, 1,047 (22.3%) tracked inflammation only, and "
    "1,692 (36.1%) tracked both. The shared group is strikingly coherent in "
    "direction: 1,335 genes rise on both ladders and 356 fall on both, while "
    "a single gene (GPD1) moves in opposite directions. Across shared genes "
    "the two correlation coefficients agree closely (Spearman rho = 0.725, "
    "p = 2.9e-276), although this figure is inflated by the separation "
    "between the up and down clouds; computed within direction the agreement "
    "is more modest but still clear (rho = 0.453 among rising genes, "
    "rho = 0.354 among falling genes).")
body(
    "The genes most strongly associated with fibrosis stage include NALCN "
    "(rho = 0.580), STMN2 (0.574), LAMC3 (0.538), CCL20 (0.526), IL32 "
    "(0.522) and THBS2 (0.514), each of which also tracks inflammation. The "
    "most strongly negative associations are dominated by hepatocyte "
    "metabolic and sinusoidal genes, among them CLEC4M, ANXA10 and OAT. "
    "That the positive end is populated by matrix and immune genes while "
    "the negative end is populated by differentiated hepatocyte functions "
    "is the expected signature of progressive fibrosis, and provides a "
    "first check that the harmonisation has not distorted direction.")

figure("Task1/task1_venn.png",
       "Figure 2. Overlap between the two progression ladders.",
       "Genes significantly associated with fibrosis stage and with disease "
       "group, showing the fibrosis-only, inflammation-only and shared "
       "partitions used throughout this paper.", width_in=3.9)

figure("Task1/task1_shared_rho_scatter.png",
       "Figure 3. Agreement between ladders among shared genes.",
       "Fibrosis correlation plotted against inflammation correlation for the "
       "1,692 shared genes. The two clouds correspond to concordantly rising "
       "and concordantly falling genes; only one gene is discordant.",
       width_in=3.9)

table(
    ["Group", "Genes", "% of 4,692", "Rising", "Falling"],
    [["Fibrosis only", "1,953", "41.6", "1,301", "652"],
     ["Inflammation only", "1,047", "22.3", "597", "450"],
     ["Shared", "1,692", "36.1", "1,335", "356"],
     ["Total", "4,692", "100.0", "3,233", "1,458"]],
    "Table 2. Progression-associated genes by ladder and direction.",
    "Rising indicates expression increasing with severity. One shared gene "
    "(GPD1) is discordant between ladders and is excluded from the rising and "
    "falling columns.",
    widths=[1.7, 1.0, 1.1, 1.0, 1.0])

doc.add_heading("2.3 Fibrosis-associated genes follow five reproducible "
                "trajectories across F0-F4", level=2)
body(
    "To ask how fibrosis-associated genes behave across stages rather than "
    "merely whether they correlate with stage, we took the 3,645 genes "
    "associated with fibrosis (fibrosis-only plus shared), computed their "
    "mean expression at each stage from the 668 staged samples, and "
    "z-scored each gene across its own five stage means so that genes would "
    "group by the shape of their curve rather than its amplitude. K-means "
    "clustering was applied for k = 3 to 8 and the number of clusters chosen "
    "by stability rather than by silhouette score alone: for each k we "
    "reclustered 50 random 80% subsets of genes and 50 patient-level "
    "bootstraps, and selected the largest k whose gene-subsample adjusted "
    "Rand index remained at or above 0.95, giving k = 5. Clusters were named "
    "only after clustering, from their average curves; no gene was assigned "
    "to a pattern by hand.")
body(
    "The five trajectories are an early increase beginning at F0-F1 and "
    "continuing (927 genes), a late increase largest at F3-F4 (1,514 genes), "
    "an early rise followed by a plateau (197 genes), a mid decrease largest "
    "at F1-F2 (309 genes), and a late decrease largest at F3-F4 (698 genes). "
    "Representative members are SAE1, LAIR1 and CD52 for the early increase; "
    "SLC51B, CCN2 and KRT23 for the late increase; ANLN, ASPM and RRM2 for "
    "the early rise and plateau; and SLC27A2, ADH6 and PDK4 for the late "
    "decrease.")
body(
    "The shapes themselves are robust. Across 100 patient bootstraps each "
    "shape was recovered with a median correlation of 0.97 to 0.997 to the "
    "original, and re-estimating stage profiles with study included as a "
    "covariate produced per-gene profiles correlating at 0.998 with the "
    "plain stage means, so the shapes are not an artefact of which studies "
    "contributed to which stage. The membership of individual genes is less "
    "certain: under bootstrap, genes move most often between the three "
    "increasing clusters, which differ only in timing. We therefore report a "
    "per-gene membership confidence and recommend that statements about "
    "specific genes within a cluster be restricted to high-confidence "
    "members, of which the late-increase and late-decrease clusters have "
    "large stable cores (841 and 423 genes) while the early-increase cluster "
    "has only 47.")
body(
    "One cluster was renamed as a direct consequence of the next analysis. "
    "Cluster 3 was initially described as rising to F3 and then reversing, "
    "on the basis of its stage means. Patient-level testing of the F3-F4 "
    "transition (Section 2.4) found no significant decrease for any of its "
    "197 genes, so the apparent reversal is not supported and the cluster is "
    "described here as an early rise followed by a plateau. Its core "
    "members are cell-cycle genes, consistent with a proliferative response "
    "that stops increasing rather than one that reverses.")

figure("Task2/task2_cluster_means.png",
       "Figure 4. The five fibrosis trajectory shapes.",
       "Mean standardised expression of each cluster at fibrosis stages F0 to "
       "F4. Cluster names were assigned after clustering from these curves.",
       width_in=5.4)

figure("Task2/task2_heatmap.png",
       "Figure 5. Stage profiles of all 3,645 fibrosis-associated genes.",
       "Genes in rows, grouped by cluster; stages F0-F4 in columns. Values "
       "are mean standardised expression per stage.", width_in=4.0)

figure("Task2/task2_choosing_k.png",
       "Figure 6. Choice of cluster number.",
       "Silhouette score, gene-subsample stability and patient-bootstrap "
       "stability for k = 3 to 8. k = 5 is the largest k retaining a "
       "gene-subsample adjusted Rand index of at least 0.95.", width_in=6.0)

doc.add_heading("2.4 The largest transcriptional change occurs at the "
                "transition into cirrhosis", level=2)
body(
    "Stage means describe where genes sit, not whether the difference "
    "between adjacent stages is real. We therefore tested every one of the "
    "3,645 fibrosis-associated genes at each of the four transitions "
    "(F0-F1, F1-F2, F2-F3, F3-F4) at patient level, fitting value_z as a "
    "function of stage with study included as a covariate so that stages are "
    "compared within study and differences in stage composition between "
    "studies cannot create an apparent change. Patients contribute once: "
    "repeat biopsies at the same stage were averaged, and for the 24 "
    "patients biopsied on both sides of a transition one sample was retained "
    "at random under a fixed seed. Genes were called substantially changing "
    "at a false-discovery rate below 0.05 together with an absolute "
    "standardised effect of at least 0.2.")
body(
    "On the full data the four transitions appear broadly similar, with "
    "1,165, 1,175, 1,117 and 936 substantially changing genes respectively "
    "(Table 3). This comparison is, however, confounded by sample size: the "
    "F3-F4 transition rests on only 34 patients with cirrhosis. We "
    "therefore refitted every transition 50 times on an identical "
    "study-balanced design of 30 patients per stage, equalising statistical "
    "power across all four. Under this design the ordering changes "
    "decisively: the median number of substantially changing genes is 0 at "
    "F0-F1, 0 at F1-F2 and 2 at F2-F3, against 311 at F3-F4. The typical "
    "effect size shows the same pattern, with a median absolute "
    "standardised effect of 0.378 at F3-F4 against 0.188 to 0.221 earlier.")
body(
    "The two views are complementary rather than contradictory. Earlier "
    "transitions involve many small and consistent changes that are "
    "detectable only with large samples; the transition into cirrhosis "
    "involves fewer but much larger ones. Direction also shifts across the "
    "disease course: the first transition is almost entirely composed of "
    "increases (1,135 rising against 30 falling), whereas decreases appear "
    "in quantity from F1-F2 onward (528 falling). Among the genes changing "
    "most sharply at F3-F4 are STC1, KRT23, MMP7 and PLVAP, while CYP2E1, "
    "SLC22A1 and CMBL fall, a pattern consistent with matrix remodelling and "
    "ductular reaction replacing hepatocyte metabolic capacity.")

figure("Task3/task3_transition_comparison.png",
       "Figure 7. Comparison of the four stage transitions.",
       "Numbers of substantially changing genes on the full data, the same "
       "counts under the power-matched design of 30 patients per stage, and "
       "the distribution of effect sizes. Equalising power isolates F3-F4 as "
       "the transition carrying the largest transcriptional change.",
       width_in=6.3)

table(
    ["Transition", "Patients (a / b)", "Substantial genes", "Rising",
     "Falling", "Median |effect|", "Power-matched median"],
    [["F0 - F1", "152 / 166", "1,165", "1,135", "30", "0.188", "0"],
     ["F1 - F2", "160 / 165", "1,175", "647", "528", "0.189", "0"],
     ["F2 - F3", "165 / 109", "1,117", "906", "211", "0.221", "2"],
     ["F3 - F4", "118 / 34", "936", "865", "71", "0.378", "311"]],
    "Table 3. Transcriptional change at each fibrosis stage transition.",
    "Substantial genes are those with false-discovery rate below 0.05 and an "
    "absolute standardised effect of at least 0.2, from a model including "
    "study as a covariate. The power-matched column gives the median across "
    "50 refits on a fixed study-balanced design of 30 patients per stage.",
    widths=[0.9, 1.1, 1.05, 0.65, 0.65, 0.9, 1.05])

doc.add_heading("2.5 Each programme carries distinct biology", level=2)
body(
    "Gene sets were tested for over-representation of GO Biological Process, "
    "KEGG, Reactome and Hallmark terms, each group separately and never all "
    "4,692 genes together. The background was the 14,794 genes eligible for "
    "the cross-study analysis, that is, those measured in every study, "
    "rather than the whole genome; using the full genome would overstate "
    "enrichment for any term whose members are preferentially well measured, "
    "and this choice materially changes which terms reach significance.")
body(
    "The resulting assignments are biologically coherent. Genes rising with "
    "fibrosis only are enriched for immune cell activation, including "
    "myeloid and T-cell programmes, IL6-JAK-STAT3 signalling and "
    "inflammatory response. Genes falling with fibrosis only are enriched "
    "for xenobiotic, fatty-acid and bile-acid metabolism and for peroxisomal "
    "function, representing the progressive loss of normal hepatocyte "
    "metabolism. Genes rising on both ladders give the strongest signal of "
    "any group and describe the core fibrogenic programme: extracellular "
    "matrix and collagen formation, epithelial-mesenchymal transition, "
    "TNF-NF-kB signalling, apoptosis, p53 and angiogenesis. Genes falling on "
    "both ladders are enriched for amino-acid and organic-acid catabolism "
    "and coagulation. The inflammation-only groups are notably weak, with "
    "only interferon-alpha response and G2/M reaching significance among "
    "rising genes and nothing at all among falling genes, indicating that "
    "most interpretable inflammatory biology in these data is shared with "
    "the fibrosis ladder rather than specific to inflammation.")
body(
    "Mapping enrichment onto the trajectory clusters orders this biology in "
    "time. The early-increase cluster is enriched for adaptive immunity, "
    "T-cell activation and interferon-gamma response, so immune activation "
    "is already established at the earliest stage transition. The "
    "late-increase cluster is enriched for epithelial-mesenchymal "
    "transition, matrix organisation, cell migration, hypoxia and "
    "TGF-beta signalling, indicating that scarring accelerates late. The "
    "early-rise-then-plateau cluster is dominated by cell-cycle terms "
    "(E2F targets, G2/M checkpoint, chromosome segregation). The "
    "late-decrease cluster recapitulates metabolic failure, with bile-acid, "
    "fatty-acid and xenobiotic metabolism and peroxisomal terms. The "
    "mid-decrease cluster yields few terms and no clear theme. Repeating "
    "every cluster analysis using only high-confidence cluster members "
    "confirmed the late-increase, early-rise and late-decrease conclusions, "
    "partially confirmed the early-increase cluster at the level of immune "
    "activation, and left the mid-decrease cluster uninterpretable; "
    "statements in this paper are restricted accordingly.")

figure("Task4/task4_heatmap_hallmark.png",
       "Figure 8. Hallmark process enrichment across groups and clusters.",
       "All significantly enriched Hallmark processes (false-discovery rate "
       "below 0.05) by gene group and trajectory cluster, tested against the "
       "14,794-gene eligible background.", width_in=5.6)

table(
    ["Group", "Genes", "GO BP", "KEGG", "Reactome", "Hallmark"],
    [["Fibrosis only, rising", "1,301", 234, 35, 18, 7],
     ["Fibrosis only, falling", "652", 106, 26, 33, 8],
     ["Inflammation only, rising", "597", 2, 1, 30, 2],
     ["Inflammation only, falling", "450", 0, 0, 0, 0],
     ["Shared, rising", "1,335", 446, 27, 71, 30],
     ["Shared, falling", "356", 62, 22, 19, 5],
     ["C1 early increase", "927", 348, 47, 50, 15],
     ["C2 late increase", "1,514", 542, 20, 48, 21],
     ["C3 early rise, plateau", "197", 85, 3, 29, 3],
     ["C4 mid decrease", "309", 5, 1, 2, 2],
     ["C5 late decrease", "698", 159, 35, 38, 7]],
    "Table 4. Significantly enriched terms per group.",
    "Counts of terms at false-discovery rate below 0.05 in each database, "
    "tested against the 14,794-gene eligible background with gene sets "
    "restricted to 10-500 background genes.",
    widths=[1.9, 0.8, 0.8, 0.7, 0.9, 0.9])

# ============================================================== DISCUSSION
doc.add_heading("3. Discussion", level=1)
todo("TO BE WRITTEN BY THE SUPERVISOR, as agreed. Material available to draw "
     "on: the ordering of immune activation before matrix remodelling; the "
     "F3-F4 result and what it implies for staging models and trial "
     "endpoints; the dissociation of the two ladders and the 40 patients "
     "with NASH at fibrosis stage 0; and the handover of these gene sets to "
     "the drug-prioritisation analysis.")

doc.add_heading("4. Conclusion", level=1)
todo("TO BE WRITTEN BY THE SUPERVISOR, as agreed.")

# ================================================================= METHODS
doc.add_heading("5. Methods", level=1)

doc.add_heading("5.1 Data sources", level=2)
body(
    "Eight human liver transcriptome studies were obtained from the Gene "
    "Expression Omnibus: GSE126848 (57 samples), GSE130970 (78), GSE135251 "
    "(216), GSE162694 (143), GSE167523 (98), GSE193066 (164), GSE240729 "
    "(67) and GSE269412 (262), giving 1,085 samples from 1,027 patients. For "
    "each study both the supplementary expression files and the series "
    "matrix were retrieved, the latter providing per-sample clinical "
    "characteristics. No new human data were generated; all analyses use "
    "existing public data, so no sample-size calculation or randomisation "
    "applies and the available sample size is reported as a constraint "
    "rather than a design choice.")

doc.add_heading("5.2 Expression parsing", level=2)
body(
    "Supplementary expression files differ in layout between studies. Each "
    "was parsed into a single long-format table with columns for dataset, "
    "sample key, raw gene identifier, identifier type, value and unit. "
    "Measured values of zero were retained throughout. This is a "
    "consequential choice: a zero recorded by the assay is evidence that a "
    "gene was not detected in that biopsy, and discarding such values "
    "removes precisely the switching-on behaviour that distinguishes stages. "
    "Retaining them added approximately 9.1 million measurements and 514 "
    "additional progression genes relative to an earlier run in which they "
    "were dropped.")

doc.add_heading("5.3 Gene identifier harmonisation", level=2)
body(
    "Every gene identifier was translated to a canonical Ensembl gene "
    "identifier with version suffixes removed, using the HGNC complete set "
    "as the dictionary. Mapping was performed on the unique identifiers of "
    "each dataset and then joined back to the measurement table, rather than "
    "row by row. Identifiers that failed to map were written to a separate "
    "report rather than silently discarded. Rows corresponding to "
    "pseudoautosomal duplicates (_PAR_Y) were removed, and where two raw "
    "identifiers collapsed onto a single Ensembl identifier their values "
    "were summed. This produced 53,993 genes.")

doc.add_heading("5.4 Sample crosswalk", level=2)
body(
    "Expression files label their columns differently from the GEO sample "
    "accessions used in the series matrices, so a per-study rule was derived "
    "to map each expression column to its GSM accession. Rules were not "
    "trusted blindly: each was applied and then verified against the sample "
    "keys actually present in the expression files, and the per-study match "
    "rate was reported, so that a rule correct for the first few samples but "
    "wrong for the rest would be detected rather than produce a partially "
    "connected graph.")

doc.add_heading("5.5 Clinical label harmonisation", level=2)
body(
    "Clinical severity was recorded on study-specific scales. Four studies "
    "recorded fibrosis as \"0\" to \"4\", one as \"F0\" to \"F4\", and one "
    "used a free-text description for normal histology; disease state was "
    "recorded with four distinct vocabularies. Harmonised fields "
    "(fibrosis_stage as an integer 0-4; disease_group as control, obese, "
    "NAFL, NASH or NAFLD) were added alongside the original *_raw fields, "
    "which were never modified, so that every translation remains "
    "auditable. Patient identity and biopsy number were also derived, "
    "because the 164 samples of GSE193066 come from 106 patients, 58 of "
    "whom were biopsied twice. For GSE162694 the diagnosis encoded in "
    "sample titles was recovered after cross-checking against the recorded "
    "fibrosis stage for all 143 samples. For GSE130970, which states no "
    "diagnosis but reports full Kleiner component scores, diagnosis was "
    "derived using the standard NASH-CRN definition (steatosis 0 as "
    "control; ballooning at least 1 as NASH; steatosis of at least 1 with no "
    "ballooning as NAFL) and flagged as derived so that it can be excluded "
    "with a single filter. Four studies were deliberately left unlabelled "
    "where no defensible join existed; one candidate field in GSE193066 was "
    "tested and rejected because the groups it produced contradicted that "
    "study's own fibrosis staging.")

doc.add_heading("5.6 Expression standardisation", level=2)
body(
    "Because studies differ in platform, depth and centre, raw values are "
    "not comparable across cohorts. Expression was therefore standardised "
    "per gene within each study (value_z), so that a value expresses how far "
    "a sample sits from that study's own mean for that gene. All downstream "
    "analyses use value_z.")

doc.add_heading("5.7 Graph construction", level=2)
body(
    "The harmonised measurements were written as Neo4j-ready CSVs and loaded "
    "into a Neo4j property graph with uniqueness constraints created before "
    "loading. The graph contains 126,244 nodes (Gene 53,993; Disease 36,044; "
    "BioProcess 12,203; Drug 12,025; Phenotype 8,666; Pathway 2,220; Sample "
    "1,085; Dataset 8) and 35,091,066 relationships. Sample-gene EXPRESSES "
    "edges account for 32,471,042 of these. No gene filter was applied at "
    "load time; instead each Gene node records n_datasets, the number of "
    "studies in which it was measured, so that filtering decisions are made "
    "at query time and remain visible in the analysis rather than being "
    "fixed in the data.")

doc.add_heading("5.8 Knowledge layer", level=2)
body(
    "Curated biological knowledge was attached from OptimusKG, which "
    "identifies genes by Ensembl identifier and so joins directly to the "
    "measurement layer (50,725 of 53,993 genes match, 94%). Gene-disease "
    "associations were restricted to an evidence score of at least 0.1 and "
    "the score was stored on every edge, so queries may tighten the "
    "threshold without reloading; without this restriction the resource "
    "contributes over nine million gene-disease links with a median score of "
    "0.026, connecting a third of the genome to NAFLD and leaving the graph "
    "too densely connected to support inference. Drug-gene edges retain "
    "their reported mode of action. Drug-drug interaction, anatomy-gene and "
    "environmental exposure slices were excluded as not relevant to disease "
    "mechanism.")

doc.add_heading("5.9 Identification of progression-associated genes", level=2)
body(
    "Two ladders were analysed separately: fibrosis stage (0 to 4) and "
    "disease group (control, NAFL, NASH, coded 0 to 2). Only genes measured "
    "in all eight studies were tested. Within each study, each gene's "
    "value_z was correlated with ladder position by Spearman's rho, chosen "
    "because stages are ordered ranks whose spacing is not meaningful. "
    "Studies contributing fewer than 25 labelled patients for an axis were "
    "skipped for that axis, and a gene had to be testable in at least three "
    "studies. Per-study coefficients were combined by their median and "
    "per-study p-values by Fisher's method, with Benjamini-Hochberg "
    "correction. Genes were retained at a false-discovery rate below 0.05 "
    "and only when every study in which they were testable agreed on the "
    "direction of effect. Samples were collapsed to one observation per "
    "patient per study before any statistic was computed. Combining "
    "per-study results rather than pooling patients is deliberate: pooling "
    "allows a gene that behaves atypically in one cohort to dominate, "
    "whereas requiring cross-study agreement makes cohort-specific "
    "behaviour a reason for exclusion.")

doc.add_heading("5.10 Assignment to progression groups", level=2)
body(
    "Genes significant on the fibrosis ladder only, on the disease ladder "
    "only, or on both were assigned to the fibrosis-only, inflammation-only "
    "and shared groups respectively, and each group was further split by the "
    "sign of its median correlation. Agreement between ladders among shared "
    "genes was quantified by Spearman correlation of the two coefficients, "
    "computed overall and separately within the rising and falling subsets, "
    "the latter being the more conservative estimate.")

doc.add_heading("5.11 Trajectory clustering", level=2)
body(
    "The 3,645 fibrosis-associated genes (fibrosis-only plus shared) were "
    "summarised by their mean value_z at each fibrosis stage, computed from "
    "the 668 staged samples. Each gene's five stage means were z-scored "
    "across stages so that clustering would respond to curve shape rather "
    "than amplitude. K-means was run with 50 random initialisations for "
    "k = 3 to 8. The number of clusters was selected by stability: for each "
    "k, 50 random 80% subsets of genes and 50 patient-level bootstraps "
    "(resampling patients within study, with replacement, and recomputing "
    "stage means) were reclustered and compared to the full-data solution by "
    "adjusted Rand index. The largest k retaining a gene-subsample index of "
    "at least 0.95 was chosen, giving k = 5; silhouette score alone would "
    "have favoured k = 3, which visibly merges distinct shapes. Clusters "
    "were named after clustering from their average curves. A per-gene "
    "membership confidence was recorded as the fraction of 100 bootstraps in "
    "which the gene remained in its assigned cluster, and the sensitivity of "
    "the solution to study composition was assessed by re-estimating stage "
    "profiles from a model including study as a covariate.")

doc.add_heading("5.12 Stage transition analysis", level=2)
body(
    "For each fibrosis-associated gene and each adjacent-stage transition, "
    "value_z was modelled as a function of stage with study as a covariate, "
    "fitted only on patients at the two stages concerned, so that stages are "
    "compared within study; studies lacking either stage were excluded from "
    "that transition. Patients contribute once: repeat biopsies at the same "
    "stage were averaged (28 patients) and, for patients biopsied on either "
    "side of a transition (24 patients), one sample was retained at random "
    "under a fixed seed. Coefficients were tested by t-test with "
    "Benjamini-Hochberg correction within each transition, and a gene was "
    "called substantially changing at a false-discovery rate below 0.05 "
    "together with an absolute coefficient of at least 0.2 standard "
    "deviations. Because the number of patients differs sharply between "
    "transitions, and F4 in particular is represented by only 34 patients, "
    "every transition was additionally refitted 50 times on an identical "
    "study-balanced design of 30 patients per stage, equalising power across "
    "transitions.")

doc.add_heading("5.13 Pathway enrichment", level=2)
body(
    "Over-representation was tested for GO Biological Process, KEGG, "
    "Reactome and Hallmark gene sets (MSigDB v2024.1, human symbols) using "
    "one-sided hypergeometric tests with Benjamini-Hochberg correction "
    "within each group and database, calling terms significant below a "
    "false-discovery rate of 0.05. The background was the 14,794 genes "
    "eligible for the cross-study analysis, not the whole genome; every gene "
    "set was first restricted to these genes and retained only if 10 to 500 "
    "of them remained, leaving 4,853 GO BP, 183 KEGG, 1,279 Reactome and 50 "
    "Hallmark sets. Each group was tested separately. Cluster analyses were "
    "repeated using only genes with a bootstrap membership confidence of at "
    "least 0.8, and conclusions are reported only where they survive that "
    "check.")

doc.add_heading("5.14 Software and availability", level=2)
body(
    "Analyses were performed in Python using pandas, NumPy, SciPy, "
    "scikit-learn and gseapy, with the graph held in Neo4j. All analysis "
    "code, the per-step rationale and the complete result tables are "
    "available in the project repository; each analysis directory carries a "
    "README recording its method, its chosen thresholds and its limitations.")
todo("Insert the repository URL or data-availability statement required by "
     "the target journal, and confirm package versions.")

# ============================================================= LIMITATIONS
doc.add_heading("6. Limitations", level=1)
body(
    "Four limitations bound the interpretation of these results and are "
    "stated here rather than left to inference. First, the genes analysed in "
    "Sections 2.3 to 2.5 were selected because they correlate with fibrosis "
    "stage in these same data, so absolute counts of significant genes are "
    "inflated by selection; comparisons between transitions remain fair "
    "because all four use the same gene set, but the counts themselves "
    "should not be read as unbiased estimates. Second, stage F4 is "
    "represented by only 34 to 35 patients, and although the power-matched "
    "design addresses the resulting imbalance in statistical power, "
    "estimates for the F3-F4 transition remain the least precise in the "
    "study. Third, cluster membership for individual genes is less stable "
    "than the cluster shapes, particularly among the three increasing "
    "clusters, which is why per-gene membership confidence is reported and "
    "gene-level claims are restricted to high-confidence members. Fourth, "
    "demographic coverage is partial: age and sex are recorded by five of "
    "the eight studies and only three of those also stage fibrosis, so any "
    "analysis combining stage with age or sex rests on 385 samples rather "
    "than the full cohort, and every output file carries its own sample "
    "count so that this limit remains visible.")

# ============================================================== REFERENCES
doc.add_heading("References", level=1)
todo("To be inserted. Citation markers in the text read [REF] and mark the "
     "places where a reference is required: disease burden and "
     "transplantation; fibrosis stage as the dominant prognostic feature; "
     "biopsy sampling variability and inter-observer agreement; and "
     "biomedical knowledge graphs. Format according to the target journal.")

doc.save(OUT)
print("wrote", OUT)
