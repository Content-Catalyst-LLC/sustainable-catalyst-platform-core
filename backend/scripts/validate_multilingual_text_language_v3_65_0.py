from app.services.multilingual_text_language import (
    CONTRACT_VERSION,
    CORE_RELEASE,
    contract_document,
    reference_multilingual_text_language_bundle,
)

contract = contract_document()
bundle = reference_multilingual_text_language_bundle()
source = bundle.text_sources[0]

assert CORE_RELEASE == "3.65.0"
assert CONTRACT_VERSION == "sc.core.multilingual-text-language-object.v1"
assert contract["principles"]["original_language_is_canonical"] is True
assert contract["principles"]["translation_is_a_derived_representation"] is True
assert contract["principles"]["translation_may_replace_original"] is False
assert contract["capabilities"]["mixed_language_span_bindings"] is True
assert contract["roadmap_integration"]["prepares_v3660_linguistic_annotation_morphology_syntax"] is True
assert contract["roadmap_integration"]["prepares_v3670_translation_transliteration_parallel_alignment"] is True
assert contract["boundaries"]["core_translates_text"] is False
assert contract["boundaries"]["core_rewrites_canonical_source_text"] is False
assert contract["boundaries"]["core_treats_model_language_assignment_as_authoritative"] is False
assert source.original_language_is_canonical is True
assert source.translation_substitution_allowed is False
assert len(bundle.language_spans) == 3
assert len(bundle.fingerprint()) == 64
print("PASS - Platform Core v3.65.0 Multilingual Text & Language Object Model")
print(f"CONTRACT={CONTRACT_VERSION}")
print(f"TEXT_SOURCE={source.text_source_id}")
print(f"LANGUAGES={','.join(x.bcp47_tag for x in bundle.languages)}")
print(f"SCRIPTS={','.join(x.iso_15924_code for x in bundle.scripts)}")
print("ORIGINAL_LANGUAGE_CANONICAL=true")
print("TRANSLATION_SUBSTITUTION_ALLOWED=false")
