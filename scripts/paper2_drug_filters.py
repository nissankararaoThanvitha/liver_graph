"""
paper2_drug_filters.py
----------------------
One definition of "is this entity actually a therapeutic?", shared by every
task that needs it.

WHY THIS MODULE EXISTS
The rule lived inside Task 4 alone, so Task 3 counted a gene as "druggable"
when its only drug was zinc chloride, ATP or an unnamed ChEMBL accession. A
reviewer found it on 13 October: 174 of the 958 drug-connected progression
genes -- 18% -- reach a flagged entity and nothing else.

Two tasks asking the same question with two different answers is the failure
this module prevents. Task 3 and Task 4 now import from here, so the rule
cannot drift between them.

TWO SEPARATE JUDGEMENTS, DELIBERATELY KEPT APART
  pharmacokinetic   is the EDGE about treating the gene, or about the liver
                    metabolising the drug? That is a property of the action.
  non-therapeutic   is the ENTITY a medicine at all? That is a property of
                    the drug, and it is what Task 3 was missing.

An edge is useful evidence only when both pass.

THE RULE IS A HEURISTIC AND IT IS NOT APOLOGISED FOR
Molecule type and clinical phase were recovered from OptimusKG and DO NOT
discriminate: ZINC ACETATE and ZINC CHLORIDE are `Small molecule`, `max_phase
4.0`, `is_approved True`, because they genuinely are approved small molecules.
A filter built on those fields flags one drug where the name rule flags
seventy. So names are used, the rule marks rather than deletes, and both the
filtered and unfiltered figures are reported wherever it matters.
"""

import re

# Edge-level: the action describes metabolism or transport, not treatment.
PHARMACOKINETIC = {"ENZYME", "TRANSPORTER", "CARRIER", "SUBSTRATE"}

# Entity-level: names that are minerals, nutrients, cofactors or solvents.
# Incomplete by construction; it marks, it does not delete.
NON_THERAPEUTIC = re.compile(
    r"\b(ZINC|CALCIUM|MAGNESIUM|POTASSIUM|SODIUM|FERROUS|FERRIC|COPPER|"
    r"MANGANESE|SELENIUM|CHROMIUM|IODIDE|PHOSPHATE|CARBONATE|CITRATE|"
    r"CHLORIDE|SULFATE|SULPHATE|ACETATE|GLUCONATE|OXIDE|HYDROXIDE)\b"
    r"|^(ALCOHOL|WATER|OXYGEN|NITROGEN|GLYCEROL|UREA|GLUCOSE|SUCROSE|"
    r"DEXTROSE|LACTOSE|STARCH)$"
    r"|\b(VITAMIN|ASCORBIC ACID|CHOLECALCIFEROL|ERGOCALCIFEROL|TOCOPHEROL|"
    r"RETINOL|THIAMINE|RIBOFLAVIN|NIACIN|PYRIDOXAL|PYRIDOXINE|FOLIC ACID|"
    r"CYANOCOBALAMIN|BIOTIN|PANTOTHEN)\b"
    r"|^(ADENOSINE TRIPHOSPHATE|GLUTAMIC ACID|ASPARTIC ACID|GLYCINE|ALANINE|"
    r"SERINE|CYSTEINE|TAURINE|CREATINE|CHOLINE|INOSITOL)\b"
    r"|NICOTINAMIDE ADENINE DINUCLEOTIDE|DINUCLEOTIDE|FLAVIN|"
    r"COENZYME|HEME|HEMIN", re.I)

UNNAMED = re.compile(r"^CHEMBL\d+$")

# A drug whose target set is this far inside a flagged drug's target set is
# treated as the same entity under another accession.
DUPLICATE_OVERLAP = 0.95
DUPLICATE_MIN_TARGETS = 5


def flag_entities(names_by_id, targets_by_id):
    """Which drug ids are probably not therapeutics.

    names_by_id    {drug_id: name}
    targets_by_id  {drug_id: set of gene ids}  -- used for the duplicate rule

    Returns {drug_id: {"flag_name", "flag_unnamed", "flag_duplicate",
                       "non_therapeutic"}}.

    The duplicate rule exists because CHEMBL1201279 shares all 126 of its
    targets with ZINC ACETATE: the same thing under another accession, which no
    name rule can catch.
    """
    by_name, by_unnamed = {}, {}
    for did, name in names_by_id.items():
        n = "" if name is None else str(name)
        by_name[did] = bool(NON_THERAPEUTIC.search(n))
        by_unnamed[did] = bool(UNNAMED.match(n))

    flagged_sets = [targets_by_id[d] for d, f in by_name.items()
                    if f and d in targets_by_id]

    out = {}
    for did in names_by_id:
        s = targets_by_id.get(did)
        dup = False
        if s and len(s) >= DUPLICATE_MIN_TARGETS and not by_name[did]:
            dup = any(len(s & f) / len(s) >= DUPLICATE_OVERLAP
                      for f in flagged_sets)
        out[did] = {"flag_name": by_name[did],
                    "flag_unnamed": by_unnamed[did],
                    "flag_duplicate": dup,
                    "non_therapeutic": by_name[did] or by_unnamed[did] or dup}
    return out
