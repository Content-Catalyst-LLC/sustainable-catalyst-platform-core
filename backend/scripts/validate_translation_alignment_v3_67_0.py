from app.services.translation_alignment import (
    CONTRACT_VERSION,
    CORE_RELEASE,
    contract_document,
    reference_translation_alignment_bundle,
)

contract = contract_document()
bundle = reference_translation_alignment_bundle()

assert CORE_RELEASE == "3.67.0"
assert CONTRACT_VERSION == "sc.core.translation-transliteration-alignment.v1"
assert contract["extends_contracts"] == [
    "sc.core.multilingual-text-language-object.v1",
    "sc.core.linguistic-annotation-provenance.v1",
]
assert contract["principles"]["original_language_remains_canonical"] is True
assert contract["principles"]["translation_is_a_derived_representation"] is True
assert contract["principles"]["transliteration_is_a_derived_representation"] is True
assert contract["principles"]["translation_disagreement_is_preserved"] is True
assert contract["principles"]["machine_derivations_are_advisory"] is True
assert contract["boundaries"]["core_translates_text"] is False
assert contract["boundaries"]["core_transliterates_text"] is False
assert contract["boundaries"]["core_infers_parallel_alignment"] is False
assert contract["boundaries"]["core_selects_best_translation"] is False
assert contract["roadmap_integration"]["preserves_v3700_v3760_graph_neural_wave"] is True
assert contract["roadmap_integration"]["gnn_prediction_is_not_graph_fact"] is True
assert len(bundle.representations) == 3
assert len(bundle.alignments) == 7
assert len(bundle.variant_sets) == 1
assert len(bundle.fingerprint()) == 64

print("PASS - Platform Core v3.67.0 Translation, Transliteration & Parallel-Text Alignment Objects")
print(f"CONTRACT={CONTRACT_VERSION}")
print(f"CANONICAL_SOURCE={bundle.annotation_bundle.text_bundle.text_sources[0].text_source_id}")
print(f"REPRESENTATIONS={len(bundle.representations)}")
print(f"ALIGNMENTS={len(bundle.alignments)}")
print(f"VARIANT_SETS={len(bundle.variant_sets)}")
print("ORIGINAL_LANGUAGE_CANONICAL=true")
print("TRANSLATION_DISAGREEMENT_PRESERVED=true")
print("MACHINE_DERIVATIONS_ADVISORY=true")
print("CORE_EXECUTES_TRANSLATION=false")
print("GNN_PREDICTION_IS_GRAPH_FACT=false")
