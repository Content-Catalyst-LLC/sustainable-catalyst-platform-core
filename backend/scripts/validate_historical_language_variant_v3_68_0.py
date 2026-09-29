from app.services.historical_language_variant import (
    CONTRACT_VERSION,
    CORE_RELEASE,
    contract_document,
    reference_historical_language_variant_bundle,
)

contract = contract_document()
bundle = reference_historical_language_variant_bundle()

assert CORE_RELEASE == "3.68.0"
assert CONTRACT_VERSION == "sc.core.historical-language-script-orthography-variant.v1"
assert contract["principles"]["original_attested_form_is_preserved"] is True
assert contract["principles"]["normalization_is_a_derived_representation"] is True
assert contract["principles"]["normalization_may_replace_attested_source"] is False
assert contract["principles"]["historical_dates_may_preserve_uncertainty"] is True
assert contract["boundaries"]["core_modernizes_or_normalizes_source_text"] is False
assert contract["boundaries"]["core_rewrites_attested_source_text"] is False
assert contract["boundaries"]["core_infers_historical_periodization"] is False
assert contract["roadmap_integration"]["prepares_v3690_cross_lingual_semantic_exchange"] is True
assert contract["roadmap_integration"]["preserves_v3700_v3760_graph_neural_wave"] is True
assert contract["roadmap_integration"]["gnn_prediction_is_not_graph_fact"] is True
assert len(bundle.language_stages) == 1
assert len(bundle.script_variants) == 1
assert len(bundle.orthography_profiles) == 1
assert len(bundle.variants) == 2
assert len(bundle.normalizations) == 2
assert bundle.text_bundle.text_sources[0].content == "Publick knowledge preserves the original forme."
assert len(bundle.fingerprint()) == 64

print("PASS - Platform Core v3.68.0 Historical Language, Script, Orthography & Variant Identity")
print(f"CONTRACT={CONTRACT_VERSION}")
print(f"LANGUAGE_STAGES={len(bundle.language_stages)}")
print(f"SCRIPT_VARIANTS={len(bundle.script_variants)}")
print(f"ORTHOGRAPHY_PROFILES={len(bundle.orthography_profiles)}")
print(f"VARIANTS={len(bundle.variants)}")
print(f"NORMALIZATIONS={len(bundle.normalizations)}")
print("ORIGINAL_ATTESTED_FORM_PRESERVED=true")
print("NORMALIZATION_IS_DERIVED=true")
print("CORE_NORMALIZES_SOURCE_TEXT=false")
print("GNN_PREDICTION_IS_GRAPH_FACT=false")
