from app.services.linguistic_annotation import (
    CONTRACT_VERSION,
    CORE_RELEASE,
    contract_document,
    reference_linguistic_annotation_bundle,
)

contract = contract_document()
bundle = reference_linguistic_annotation_bundle()

assert CORE_RELEASE == "3.66.0"
assert CONTRACT_VERSION == "sc.core.linguistic-annotation-provenance.v1"
assert contract["extends_contract"] == "sc.core.multilingual-text-language-object.v1"
assert contract["principles"]["canonical_source_text_is_immutable"] is True
assert contract["principles"]["linguistic_annotations_are_derived_objects"] is True
assert contract["principles"]["machine_annotations_are_advisory"] is True
assert contract["capabilities"]["exact_token_source_binding"] is True
assert contract["capabilities"]["dependency_syntax"] is True
assert contract["capabilities"]["constituency_syntax"] is True
assert contract["boundaries"]["core_tokenizes_text"] is False
assert contract["boundaries"]["core_performs_morphological_analysis"] is False
assert contract["boundaries"]["core_assigns_pos_tags"] is False
assert contract["boundaries"]["core_parses_dependency_syntax"] is False
assert contract["boundaries"]["core_parses_constituency_syntax"] is False
assert contract["boundaries"]["core_promotes_model_annotation_to_truth"] is False
assert contract["roadmap_integration"]["prepares_v3670_translation_transliteration_parallel_alignment"] is True
assert contract["roadmap_integration"]["preserves_v3700_v3760_graph_neural_wave"] is True
assert len(bundle.tokens) == 4
assert len(bundle.morphemes) == 2
assert len(bundle.dependency_relations) == 4
assert len(bundle.constituency_nodes) == 3
assert len(bundle.fingerprint()) == 64

print("PASS - Platform Core v3.66.0 Linguistic Annotation, Token, Morphology & Syntax Provenance")
print(f"CONTRACT={CONTRACT_VERSION}")
print(f"TEXT_SOURCE={bundle.text_bundle.text_sources[0].text_source_id}")
print(f"TOKENIZATION={bundle.tokenizations[0].tokenization_id}")
print(f"TOKENS={len(bundle.tokens)}")
print(f"MORPHEMES={len(bundle.morphemes)}")
print(f"DEPENDENCY_RELATIONS={len(bundle.dependency_relations)}")
print(f"CONSTITUENCY_NODES={len(bundle.constituency_nodes)}")
print("MACHINE_ANNOTATIONS_ADVISORY=true")
print("CORE_EXECUTES_NLP=false")
