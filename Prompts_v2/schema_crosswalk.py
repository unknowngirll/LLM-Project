"""
schema_crosswalk.py
===================

Bridges the LLM extraction schema to the
OATargets gold-standard columns (used for scoring).

Design principle
----------------
Keep the prompt schema RICH so the final-stage extraction (running on all
OA abstracts) produces genuinely useful output. Only collapse to the gold
vocabulary at SCORING time, via the maps below. This keeps the two project
goals separate:
    * Goal A (final use):  rich extraction on un-annotated abstracts
    * Goal B (evaluation): score the 5 "scoreable" fields against gold

Scoreable fields (model is judged on these):
    target            <-> Gene
    manipulation      <-> Effect on gene product  (+ Type, derivable)
    oa_induction      <-> simpleModel
    outcome           <-> Susceptibility observed
    species           <-> Species

Extraction-only fields (useful, NOT scored): tissue_specificity,
genetic_detail, drug_detail, evidence_snippet.
"""


# 1. OUTCOME  (the critical one — directions are equivalent, not reversed)

# Model reports OA-severity direction; gold reports it as "Susceptibility
# observed". These are the SAME concept in different words:
#   knockout that REDUCES damage -> outcome "Decreased" -> gold "Protective"
OUTCOME_TO_GOLD = {
    "Increased":  "Detrimental",
    "Decreased":  "Protective",
    "No Change":  "No effect",
    "Not stated": None,
}
# reverse, for convenience
GOLD_SUSCEPTIBILITY = {"Detrimental", "Protective", "No effect"}


# 2. MANIPULATION  (model's 8 categories -> gold "Effect on gene product")

# NOTE: gold splits Global/Conditional/Inducible KO all into "Removal".
# Abstracts usually cannot distinguish those, so for SCORING we collapse
# them. The fine-grained label is still emitted by the model and kept for
# the final extraction output — it is just not scored against gold.
MANIPULATION_TO_GOLD_EFFECT = {
    "Global KO":            "Removal",
    "Conditional KO":       "Removal",
    "Inducible KO":         "Removal",
    "Heterozygous KO":      "Haploinsufficiency",  # gold uses this term
    "Knock-In / Mutation":  "Mutation",
    "Overexpression":       "Overexpression",
    "RNAi":                 "Knockdown",
    "Pharmacological":      "Inhibition",  # most common; see note below
}
# Gold "Type" is derivable from manipulation: genetic vs exogenous
MANIPULATION_TO_GOLD_TYPE = {
    "Global KO":            "Genetic",
    "Conditional KO":       "Genetic",
    "Inducible KO":         "Genetic",
    "Heterozygous KO":      "Genetic",
    "Knock-In / Mutation":  "Genetic",
    "Overexpression":       "Genetic",   # can be either; refine if viral
    "RNAi":                 "Exogenous",
    "Pharmacological":      "Exogenous",
}
# Pharmacological is messy in gold: a drug can be an inhibitor OR an
# activator OR a recombinant protein. For scoring, treat the manipulation
# match at the coarser "Type" level (Genetic vs Exogenous) as the robust
# signal, and treat the Effect-level match as a secondary, looser metric.


# 3. OA INDUCTION  (model's 5 categories -> gold "simpleModel", 7 values)

OA_INDUCTION_TO_GOLD = {
    "Surgical":     "Surgical",
    "Chemical":     {"MIA", "Protease"},   # gold separates these two
    "Mechanical":   "Exercise",            # closest gold bucket
    "Spontaneous":  "Ageing",              # gold's spontaneous/aging bucket
    "Transgenic":   "Genetic",             # OA from the genetic lesion itself
    "Not stated":   None,
}
# Because gold splits Chemical into MIA vs Protease (and abstracts may not
# specify which), score "Chemical" as correct if gold is EITHER MIA or
# Protease. High Fat Diet exists in gold but has no clean model-side label;
# decide with supervisor whether to add a "Metabolic" category to the prompt.


# 4. SPECIES  (near-identical, just normalise plural/case)

SPECIES_TO_GOLD = {
    "mice": "Mouse", "mouse": "Mouse",
    "rats": "Rat", "rat": "Rat",
    "rabbits": "Rabbit", "rabbit": "Rabbit",
    "guinea pigs": "Guinea pig", "guinea pig": "Guinea pig",
    "dogs": "Dog", "dog": "Dog",
    "pigs": "Pig", "pig": "Pig",
}


# Helper functions used at scoring time

def norm_gene(g):
    """Genes compared case-insensitively (model: Adamts5, gold: ADAMTS5)."""
    return (g or "").strip().upper()

def map_outcome(model_outcome):
    return OUTCOME_TO_GOLD.get((model_outcome or "").strip())

def map_species(model_species):
    return SPECIES_TO_GOLD.get((model_species or "").strip().lower(), (model_species or "").strip())

def map_induction(model_induction):
    return OA_INDUCTION_TO_GOLD.get((model_induction or "").strip())

def induction_matches(model_induction, gold_simplemodel):
    target = map_induction(model_induction)
    if target is None:
        return False
    if isinstance(target, set):
        return gold_simplemodel in target
    return gold_simplemodel == target

def derive_inferred_effect(manipulation, outcome):
    """
    Reproduce the gold 'Inferred gene effect' rule so the model does NOT
    have to infer it (keeps RULE 1: no-inference intact).

    Logic: a loss-of-function manipulation that makes OA worse implies the
    gene is protective; a gain-of-function that makes OA worse implies the
    gene is detrimental, etc.
    """
    loss = {"Global KO", "Conditional KO", "Inducible KO",
            "Heterozygous KO", "RNAi", "Pharmacological"}  # pharm usually inhibits
    gain = {"Overexpression", "Knock-In / Mutation"}
    if outcome == "No Change":
        return "No effect"
    if manipulation in loss:
        return {"Increased": "Protective", "Decreased": "Detrimental"}.get(outcome)
    if manipulation in gain:
        return {"Increased": "Detrimental", "Decreased": "Protective"}.get(outcome)
    return None  # ambiguous (e.g. pharmacological activator) -> handle separately
