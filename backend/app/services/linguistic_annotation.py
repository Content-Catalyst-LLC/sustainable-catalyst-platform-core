from __future__ import annotations

from collections import defaultdict
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from .computational_runtime_objects import canonical_sha256
from .multilingual_text_language import (
    MultilingualTextLanguageBundle,
    _content_sha256,
    reference_multilingual_text_language_bundle,
)

CORE_RELEASE = "3.66.0"
CONTRACT_VERSION = "sc.core.linguistic-annotation-provenance.v1"


class AnnotationMethod(str, Enum):
    manual = "manual"
    editorial = "editorial"
    imported = "imported"
    model_assisted = "model-assisted"
    pipeline = "pipeline"


class AnnotationReviewState(str, Enum):
    unreviewed = "unreviewed"
    reviewed = "reviewed"
    accepted = "accepted"
    rejected = "rejected"


class TokenKind(str, Enum):
    word = "word"
    punctuation = "punctuation"
    number = "number"
    symbol = "symbol"
    whitespace = "whitespace"
    other = "other"


class UniversalPartOfSpeech(str, Enum):
    ADJ = "ADJ"
    ADP = "ADP"
    ADV = "ADV"
    AUX = "AUX"
    CCONJ = "CCONJ"
    DET = "DET"
    INTJ = "INTJ"
    NOUN = "NOUN"
    NUM = "NUM"
    PART = "PART"
    PRON = "PRON"
    PROPN = "PROPN"
    PUNCT = "PUNCT"
    SCONJ = "SCONJ"
    SYM = "SYM"
    VERB = "VERB"
    X = "X"


def _unique(values: list[str], label: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{label} must be unique")


def _resolve_text_unit(bundle: MultilingualTextLanguageBundle, text_unit_ref: str):
    for unit in bundle.text_units:
        if unit.text_unit_id == text_unit_ref:
            return unit
    return None


class AnnotationProvenanceRecord(BaseModel):
    provenance_id: str = Field(min_length=2, max_length=500)
    source_text_ref: str = Field(min_length=2, max_length=500)
    source_content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    method: AnnotationMethod
    produced_by_ref: str = Field(min_length=2, max_length=1000)
    tool_ref: str | None = Field(default=None, max_length=1000)
    tool_version: str | None = Field(default=None, max_length=240)
    model_ref: str | None = Field(default=None, max_length=1000)
    model_version: str | None = Field(default=None, max_length=240)
    annotation_scheme: str | None = Field(default=None, max_length=500)
    created_at: str | None = Field(default=None, max_length=80)
    review_state: AnnotationReviewState = AnnotationReviewState.unreviewed
    reviewer_ref: str | None = Field(default=None, max_length=1000)
    review_note: str | None = Field(default=None, max_length=2000)
    model_output_is_advisory: Literal[True] = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_provenance(self):
        if self.method == AnnotationMethod.model_assisted and not self.model_ref:
            raise ValueError("model-assisted annotation provenance requires model_ref")
        if self.model_version and not self.model_ref:
            raise ValueError("model_version requires model_ref")
        if self.tool_version and not self.tool_ref:
            raise ValueError("tool_version requires tool_ref")
        if self.review_state != AnnotationReviewState.unreviewed and not self.reviewer_ref:
            raise ValueError("reviewed annotation provenance requires reviewer_ref")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class TokenRecord(BaseModel):
    token_id: str = Field(min_length=2, max_length=500)
    tokenization_ref: str = Field(min_length=2, max_length=500)
    text_unit_ref: str = Field(min_length=2, max_length=500)
    sequence: int = Field(ge=0)
    char_start: int = Field(ge=0)
    char_end: int = Field(gt=0)
    surface: str = Field(min_length=1)
    surface_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    token_kind: TokenKind = TokenKind.word
    language_ref: str = Field(min_length=2, max_length=500)
    script_ref: str = Field(min_length=2, max_length=500)
    provenance_ref: str = Field(min_length=2, max_length=500)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_token(self):
        if self.char_end <= self.char_start:
            raise ValueError("token char_end must be greater than char_start")
        if self.surface_sha256 != _content_sha256(self.surface):
            raise ValueError("token surface_sha256 must match UTF-8 surface")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class TokenizationRecord(BaseModel):
    tokenization_id: str = Field(min_length=2, max_length=500)
    text_unit_ref: str = Field(min_length=2, max_length=500)
    token_refs: list[str] = Field(min_length=1)
    scheme: str = Field(min_length=1, max_length=500)
    complete: bool = True
    provenance_ref: str = Field(min_length=2, max_length=500)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_tokenization(self):
        _unique(self.token_refs, "tokenization token_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class MorphemeRecord(BaseModel):
    morpheme_id: str = Field(min_length=2, max_length=500)
    token_ref: str = Field(min_length=2, max_length=500)
    sequence: int = Field(ge=0)
    char_start: int = Field(ge=0)
    char_end: int = Field(gt=0)
    surface: str = Field(min_length=1)
    surface_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    morpheme_type: str = Field(min_length=1, max_length=120)
    gloss: str | None = Field(default=None, max_length=500)
    provenance_ref: str = Field(min_length=2, max_length=500)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_morpheme(self):
        if self.char_end <= self.char_start:
            raise ValueError("morpheme char_end must be greater than char_start")
        if self.surface_sha256 != _content_sha256(self.surface):
            raise ValueError("morpheme surface_sha256 must match UTF-8 surface")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class MorphologicalAnnotation(BaseModel):
    annotation_id: str = Field(min_length=2, max_length=500)
    token_ref: str = Field(min_length=2, max_length=500)
    lemma: str | None = Field(default=None, max_length=1000)
    features: dict[str, str] = Field(default_factory=dict)
    morpheme_refs: list[str] = Field(default_factory=list)
    provenance_ref: str = Field(min_length=2, max_length=500)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_morphology(self):
        if self.lemma is None and not self.features and not self.morpheme_refs:
            raise ValueError("morphological annotation requires lemma, features, or morpheme_refs")
        _unique(self.morpheme_refs, "morphological annotation morpheme_refs")
        if any(not str(k).strip() or not str(v).strip() for k, v in self.features.items()):
            raise ValueError("morphological feature names and values must be non-empty")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class PartOfSpeechAnnotation(BaseModel):
    annotation_id: str = Field(min_length=2, max_length=500)
    token_ref: str = Field(min_length=2, max_length=500)
    upos: UniversalPartOfSpeech | None = None
    xpos: str | None = Field(default=None, max_length=120)
    tagset: str = Field(min_length=1, max_length=500)
    provenance_ref: str = Field(min_length=2, max_length=500)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_pos(self):
        if self.upos is None and not self.xpos:
            raise ValueError("POS annotation requires upos or xpos")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class DependencyRelation(BaseModel):
    relation_id: str = Field(min_length=2, max_length=500)
    parse_ref: str = Field(min_length=2, max_length=500)
    dependent_token_ref: str = Field(min_length=2, max_length=500)
    head_token_ref: str | None = Field(default=None, max_length=500)
    relation: str = Field(min_length=1, max_length=120)
    enhanced: bool = False
    provenance_ref: str = Field(min_length=2, max_length=500)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_relation(self):
        if self.head_token_ref == self.dependent_token_ref:
            raise ValueError("dependency relation cannot self-reference")
        if self.head_token_ref is None and self.relation != "root":
            raise ValueError("dependency relation without head must use relation='root'")
        if self.head_token_ref is not None and self.relation == "root":
            raise ValueError("root dependency relation cannot have a head token")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class DependencyParseRecord(BaseModel):
    parse_id: str = Field(min_length=2, max_length=500)
    tokenization_ref: str = Field(min_length=2, max_length=500)
    relation_refs: list[str] = Field(min_length=1)
    scheme: str = Field(min_length=1, max_length=500)
    complete: bool = True
    provenance_ref: str = Field(min_length=2, max_length=500)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_parse(self):
        _unique(self.relation_refs, "dependency parse relation_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ConstituencyNode(BaseModel):
    node_id: str = Field(min_length=2, max_length=500)
    parse_ref: str = Field(min_length=2, max_length=500)
    label: str = Field(min_length=1, max_length=120)
    child_node_refs: list[str] = Field(default_factory=list)
    token_refs: list[str] = Field(default_factory=list)
    provenance_ref: str = Field(min_length=2, max_length=500)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_node(self):
        _unique(self.child_node_refs, "constituency child_node_refs")
        _unique(self.token_refs, "constituency token_refs")
        if self.node_id in self.child_node_refs:
            raise ValueError("constituency node cannot be its own child")
        if not self.child_node_refs and not self.token_refs:
            raise ValueError("constituency node must reference child nodes or tokens")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class ConstituencyParseRecord(BaseModel):
    parse_id: str = Field(min_length=2, max_length=500)
    tokenization_ref: str = Field(min_length=2, max_length=500)
    root_node_ref: str = Field(min_length=2, max_length=500)
    node_refs: list[str] = Field(min_length=1)
    scheme: str = Field(min_length=1, max_length=500)
    complete: bool = True
    provenance_ref: str = Field(min_length=2, max_length=500)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_parse(self):
        _unique(self.node_refs, "constituency parse node_refs")
        if self.root_node_ref not in self.node_refs:
            raise ValueError("constituency root_node_ref must appear in node_refs")
        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


class LinguisticAnnotationBundle(BaseModel):
    text_bundle: MultilingualTextLanguageBundle
    provenance_records: list[AnnotationProvenanceRecord] = Field(min_length=1)
    tokenizations: list[TokenizationRecord] = Field(min_length=1)
    tokens: list[TokenRecord] = Field(min_length=1)
    morphemes: list[MorphemeRecord] = Field(default_factory=list)
    morphology_annotations: list[MorphologicalAnnotation] = Field(default_factory=list)
    pos_annotations: list[PartOfSpeechAnnotation] = Field(default_factory=list)
    dependency_parses: list[DependencyParseRecord] = Field(default_factory=list)
    dependency_relations: list[DependencyRelation] = Field(default_factory=list)
    constituency_parses: list[ConstituencyParseRecord] = Field(default_factory=list)
    constituency_nodes: list[ConstituencyNode] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_bundle(self):
        collections: list[tuple[list[str], str]] = [
            ([x.provenance_id for x in self.provenance_records], "annotation provenance ids"),
            ([x.tokenization_id for x in self.tokenizations], "tokenization ids"),
            ([x.token_id for x in self.tokens], "token ids"),
            ([x.morpheme_id for x in self.morphemes], "morpheme ids"),
            ([x.annotation_id for x in self.morphology_annotations], "morphology annotation ids"),
            ([x.annotation_id for x in self.pos_annotations], "POS annotation ids"),
            ([x.parse_id for x in self.dependency_parses], "dependency parse ids"),
            ([x.relation_id for x in self.dependency_relations], "dependency relation ids"),
            ([x.parse_id for x in self.constituency_parses], "constituency parse ids"),
            ([x.node_id for x in self.constituency_nodes], "constituency node ids"),
        ]
        for values, label in collections:
            _unique(values, label)

        source_map = {x.text_source_id: x for x in self.text_bundle.text_sources}
        unit_map = {x.text_unit_id: x for x in self.text_bundle.text_units}
        language_ids = {x.language_id for x in self.text_bundle.languages}
        script_ids = {x.script_id for x in self.text_bundle.scripts}
        provenance_map = {x.provenance_id: x for x in self.provenance_records}
        tokenization_map = {x.tokenization_id: x for x in self.tokenizations}
        token_map = {x.token_id: x for x in self.tokens}
        morpheme_map = {x.morpheme_id: x for x in self.morphemes}
        dependency_parse_map = {x.parse_id: x for x in self.dependency_parses}
        dependency_relation_map = {x.relation_id: x for x in self.dependency_relations}
        constituency_parse_map = {x.parse_id: x for x in self.constituency_parses}
        constituency_node_map = {x.node_id: x for x in self.constituency_nodes}

        for provenance in self.provenance_records:
            source = source_map.get(provenance.source_text_ref)
            if source is None:
                raise ValueError("annotation provenance source_text_ref must resolve")
            if provenance.source_content_sha256 != source.content_sha256:
                raise ValueError("annotation provenance source_content_sha256 must match canonical source")

        for token in self.tokens:
            tokenization = tokenization_map.get(token.tokenization_ref)
            if tokenization is None:
                raise ValueError("token tokenization_ref must resolve")
            unit = unit_map.get(token.text_unit_ref)
            if unit is None:
                raise ValueError("token text_unit_ref must resolve")
            if tokenization.text_unit_ref != token.text_unit_ref:
                raise ValueError("token and tokenization must target the same text unit")
            if token.provenance_ref not in provenance_map:
                raise ValueError("token provenance_ref must resolve")
            if token.language_ref not in language_ids:
                raise ValueError("token language_ref must resolve")
            if token.script_ref not in script_ids:
                raise ValueError("token script_ref must resolve")
            if token.char_end > len(unit.content):
                raise ValueError("token character range exceeds text unit")
            if unit.content[token.char_start:token.char_end] != token.surface:
                raise ValueError("token surface must equal canonical text-unit character slice")

        for tokenization in self.tokenizations:
            if tokenization.text_unit_ref not in unit_map:
                raise ValueError("tokenization text_unit_ref must resolve")
            if tokenization.provenance_ref not in provenance_map:
                raise ValueError("tokenization provenance_ref must resolve")
            members: list[TokenRecord] = []
            for ref in tokenization.token_refs:
                token = token_map.get(ref)
                if token is None:
                    raise ValueError("tokenization token_ref must resolve")
                if token.tokenization_ref != tokenization.tokenization_id:
                    raise ValueError("tokenization member token must point back to tokenization")
                members.append(token)
            sequences = [x.sequence for x in members]
            _unique([str(x) for x in sequences], "token sequences within tokenization")
            ordered = sorted(members, key=lambda x: (x.char_start, x.char_end, x.sequence))
            for left, right in zip(ordered, ordered[1:]):
                if right.char_start < left.char_end:
                    raise ValueError("tokens within one tokenization may not overlap")
            if tokenization.complete and ordered:
                expected = list(range(len(ordered)))
                observed = sorted(x.sequence for x in ordered)
                if observed != expected:
                    raise ValueError("complete tokenization requires contiguous zero-based token sequence")

        for morpheme in self.morphemes:
            token = token_map.get(morpheme.token_ref)
            if token is None:
                raise ValueError("morpheme token_ref must resolve")
            if morpheme.provenance_ref not in provenance_map:
                raise ValueError("morpheme provenance_ref must resolve")
            if morpheme.char_end > len(token.surface):
                raise ValueError("morpheme character range exceeds token surface")
            if token.surface[morpheme.char_start:morpheme.char_end] != morpheme.surface:
                raise ValueError("morpheme surface must equal parent-token character slice")

        for annotation in self.morphology_annotations:
            if annotation.token_ref not in token_map:
                raise ValueError("morphology token_ref must resolve")
            if annotation.provenance_ref not in provenance_map:
                raise ValueError("morphology provenance_ref must resolve")
            for ref in annotation.morpheme_refs:
                morpheme = morpheme_map.get(ref)
                if morpheme is None:
                    raise ValueError("morphology morpheme_ref must resolve")
                if morpheme.token_ref != annotation.token_ref:
                    raise ValueError("morphology morpheme must belong to annotation token")

        for annotation in self.pos_annotations:
            if annotation.token_ref not in token_map:
                raise ValueError("POS token_ref must resolve")
            if annotation.provenance_ref not in provenance_map:
                raise ValueError("POS provenance_ref must resolve")

        for relation in self.dependency_relations:
            parse = dependency_parse_map.get(relation.parse_ref)
            if parse is None:
                raise ValueError("dependency relation parse_ref must resolve")
            dependent = token_map.get(relation.dependent_token_ref)
            if dependent is None:
                raise ValueError("dependency dependent_token_ref must resolve")
            if dependent.tokenization_ref != parse.tokenization_ref:
                raise ValueError("dependency dependent token must belong to parse tokenization")
            if relation.head_token_ref is not None:
                head = token_map.get(relation.head_token_ref)
                if head is None:
                    raise ValueError("dependency head_token_ref must resolve")
                if head.tokenization_ref != parse.tokenization_ref:
                    raise ValueError("dependency head token must belong to parse tokenization")
            if relation.provenance_ref not in provenance_map:
                raise ValueError("dependency relation provenance_ref must resolve")

        for parse in self.dependency_parses:
            tokenization = tokenization_map.get(parse.tokenization_ref)
            if tokenization is None:
                raise ValueError("dependency parse tokenization_ref must resolve")
            if parse.provenance_ref not in provenance_map:
                raise ValueError("dependency parse provenance_ref must resolve")
            relations: list[DependencyRelation] = []
            for ref in parse.relation_refs:
                relation = dependency_relation_map.get(ref)
                if relation is None:
                    raise ValueError("dependency parse relation_ref must resolve")
                if relation.parse_ref != parse.parse_id:
                    raise ValueError("dependency relation must point back to parse")
                relations.append(relation)
            if parse.complete:
                dependents = [x.dependent_token_ref for x in relations]
                _unique(dependents, "complete dependency parse dependent tokens")
                if set(dependents) != set(tokenization.token_refs):
                    raise ValueError("complete dependency parse must assign one relation to every token")
                roots = [x for x in relations if x.head_token_ref is None]
                if len(roots) != 1:
                    raise ValueError("complete dependency parse requires exactly one root")
                parent = {x.dependent_token_ref: x.head_token_ref for x in relations}
                for token_ref in parent:
                    seen: set[str] = set()
                    cursor: str | None = token_ref
                    while cursor is not None:
                        if cursor in seen:
                            raise ValueError("dependency parse may not contain cycles")
                        seen.add(cursor)
                        cursor = parent.get(cursor)

        for node in self.constituency_nodes:
            parse = constituency_parse_map.get(node.parse_ref)
            if parse is None:
                raise ValueError("constituency node parse_ref must resolve")
            if node.provenance_ref not in provenance_map:
                raise ValueError("constituency node provenance_ref must resolve")
            tokenization = tokenization_map.get(parse.tokenization_ref)
            if tokenization is None:
                raise ValueError("constituency parse tokenization_ref must resolve")
            for ref in node.token_refs:
                token = token_map.get(ref)
                if token is None:
                    raise ValueError("constituency node token_ref must resolve")
                if token.tokenization_ref != parse.tokenization_ref:
                    raise ValueError("constituency token must belong to parse tokenization")
            for ref in node.child_node_refs:
                child = constituency_node_map.get(ref)
                if child is None:
                    raise ValueError("constituency child_node_ref must resolve")
                if child.parse_ref != node.parse_ref:
                    raise ValueError("constituency child must belong to same parse")

        for parse in self.constituency_parses:
            if parse.tokenization_ref not in tokenization_map:
                raise ValueError("constituency parse tokenization_ref must resolve")
            if parse.provenance_ref not in provenance_map:
                raise ValueError("constituency parse provenance_ref must resolve")
            for ref in parse.node_refs:
                node = constituency_node_map.get(ref)
                if node is None:
                    raise ValueError("constituency parse node_ref must resolve")
                if node.parse_ref != parse.parse_id:
                    raise ValueError("constituency node must point back to parse")
            if parse.root_node_ref not in constituency_node_map:
                raise ValueError("constituency root_node_ref must resolve")

            state: dict[str, int] = defaultdict(int)

            def visit(node_ref: str) -> None:
                if state[node_ref] == 1:
                    raise ValueError("constituency parse may not contain cycles")
                if state[node_ref] == 2:
                    return
                state[node_ref] = 1
                node = constituency_node_map[node_ref]
                for child_ref in node.child_node_refs:
                    visit(child_ref)
                state[node_ref] = 2

            visit(parse.root_node_ref)
            if parse.complete and set(state) != set(parse.node_refs):
                raise ValueError("complete constituency parse requires all nodes reachable from root")

        return self

    def fingerprint(self) -> str:
        return canonical_sha256(self)


def reference_linguistic_annotation_bundle() -> LinguisticAnnotationBundle:
    text_bundle = reference_multilingual_text_language_bundle()
    source = text_bundle.text_sources[0]
    unit = text_bundle.text_units[0]

    human_prov = AnnotationProvenanceRecord(
        provenance_id="annotation-provenance:reference:editorial",
        source_text_ref=source.text_source_id,
        source_content_sha256=source.content_sha256,
        method=AnnotationMethod.editorial,
        produced_by_ref="actor:sustainable-catalyst-reference-editor",
        tool_ref="tool:reference-annotation-workbench",
        tool_version="1.0",
        annotation_scheme="sc-reference-tokenization-v1",
        created_at="2026-09-29T00:15:00-05:00",
        review_state=AnnotationReviewState.accepted,
        reviewer_ref="actor:sustainable-catalyst-reference-reviewer",
    )
    model_prov = AnnotationProvenanceRecord(
        provenance_id="annotation-provenance:reference:model-assisted",
        source_text_ref=source.text_source_id,
        source_content_sha256=source.content_sha256,
        method=AnnotationMethod.model_assisted,
        produced_by_ref="analysis-run:reference-linguistic-annotation",
        tool_ref="runtime:external-nlp-reference",
        tool_version="1.0",
        model_ref="model:reference-multilingual-parser",
        model_version="2026.09",
        annotation_scheme="Universal Dependencies-compatible reference fixture",
        created_at="2026-09-29T00:16:00-05:00",
        review_state=AnnotationReviewState.accepted,
        reviewer_ref="actor:sustainable-catalyst-reference-reviewer",
        review_note="Reference fixture only; model output remains provenance-bearing rather than authoritative.",
    )

    tokenization_id = "tokenization:multilingual-reference-note:v1"
    specs = [
        ("water", "Water", TokenKind.word, "language:en", "script:Latn"),
        ("han-water", "水", TokenKind.word, "language:zh", "script:Hani"),
        ("systems", "systems", TokenKind.word, "language:en", "script:Latn"),
        ("period", ".", TokenKind.punctuation, "language:mul", "script:Zyyy"),
    ]
    tokens: list[TokenRecord] = []
    cursor = 0
    for seq, (slug, surface, kind, lang, script) in enumerate(specs):
        start = unit.content.index(surface, cursor)
        end = start + len(surface)
        tokens.append(
            TokenRecord(
                token_id=f"token:reference:{slug}",
                tokenization_ref=tokenization_id,
                text_unit_ref=unit.text_unit_id,
                sequence=seq,
                char_start=start,
                char_end=end,
                surface=surface,
                surface_sha256=_content_sha256(surface),
                token_kind=kind,
                language_ref=lang,
                script_ref=script,
                provenance_ref=human_prov.provenance_id,
            )
        )
        cursor = end

    tokenization = TokenizationRecord(
        tokenization_id=tokenization_id,
        text_unit_ref=unit.text_unit_id,
        token_refs=[x.token_id for x in tokens],
        scheme="sc-reference-surface-tokenization-v1",
        complete=True,
        provenance_ref=human_prov.provenance_id,
    )

    systems = next(x for x in tokens if x.token_id.endswith(":systems"))
    morphemes = [
        MorphemeRecord(
            morpheme_id="morpheme:reference:systems:stem",
            token_ref=systems.token_id,
            sequence=0,
            char_start=0,
            char_end=6,
            surface="system",
            surface_sha256=_content_sha256("system"),
            morpheme_type="stem",
            provenance_ref=model_prov.provenance_id,
        ),
        MorphemeRecord(
            morpheme_id="morpheme:reference:systems:plural",
            token_ref=systems.token_id,
            sequence=1,
            char_start=6,
            char_end=7,
            surface="s",
            surface_sha256=_content_sha256("s"),
            morpheme_type="suffix",
            gloss="PL",
            provenance_ref=model_prov.provenance_id,
        ),
    ]

    morphology = [
        MorphologicalAnnotation(
            annotation_id="morphology:reference:water",
            token_ref=tokens[0].token_id,
            lemma="water",
            features={"Number": "Sing"},
            provenance_ref=model_prov.provenance_id,
            confidence=0.99,
        ),
        MorphologicalAnnotation(
            annotation_id="morphology:reference:han-water",
            token_ref=tokens[1].token_id,
            lemma="水",
            provenance_ref=model_prov.provenance_id,
            confidence=0.99,
        ),
        MorphologicalAnnotation(
            annotation_id="morphology:reference:systems",
            token_ref=systems.token_id,
            lemma="system",
            features={"Number": "Plur"},
            morpheme_refs=[x.morpheme_id for x in morphemes],
            provenance_ref=model_prov.provenance_id,
            confidence=0.99,
        ),
    ]

    pos = [
        PartOfSpeechAnnotation(annotation_id="pos:reference:water", token_ref=tokens[0].token_id, upos=UniversalPartOfSpeech.NOUN, tagset="Universal POS", provenance_ref=model_prov.provenance_id, confidence=0.99),
        PartOfSpeechAnnotation(annotation_id="pos:reference:han-water", token_ref=tokens[1].token_id, upos=UniversalPartOfSpeech.NOUN, tagset="Universal POS", provenance_ref=model_prov.provenance_id, confidence=0.99),
        PartOfSpeechAnnotation(annotation_id="pos:reference:systems", token_ref=tokens[2].token_id, upos=UniversalPartOfSpeech.NOUN, tagset="Universal POS", provenance_ref=model_prov.provenance_id, confidence=0.99),
        PartOfSpeechAnnotation(annotation_id="pos:reference:period", token_ref=tokens[3].token_id, upos=UniversalPartOfSpeech.PUNCT, tagset="Universal POS", provenance_ref=model_prov.provenance_id, confidence=1.0),
    ]

    dep_parse_id = "dependency-parse:reference:v1"
    dep_specs = [
        ("systems-root", tokens[2].token_id, None, "root"),
        ("water-compound", tokens[0].token_id, tokens[2].token_id, "compound"),
        ("han-compound", tokens[1].token_id, tokens[2].token_id, "compound"),
        ("period-punct", tokens[3].token_id, tokens[2].token_id, "punct"),
    ]
    dep_relations = [
        DependencyRelation(
            relation_id=f"dependency:reference:{slug}",
            parse_ref=dep_parse_id,
            dependent_token_ref=dependent,
            head_token_ref=head,
            relation=relation,
            provenance_ref=model_prov.provenance_id,
            confidence=0.98,
        )
        for slug, dependent, head, relation in dep_specs
    ]
    dep_parse = DependencyParseRecord(
        parse_id=dep_parse_id,
        tokenization_ref=tokenization_id,
        relation_refs=[x.relation_id for x in dep_relations],
        scheme="Universal Dependencies-compatible reference fixture",
        complete=True,
        provenance_ref=model_prov.provenance_id,
    )

    con_parse_id = "constituency-parse:reference:v1"
    con_nodes = [
        ConstituencyNode(
            node_id="constituency-node:reference:root",
            parse_ref=con_parse_id,
            label="S",
            child_node_refs=["constituency-node:reference:np", "constituency-node:reference:punct"],
            provenance_ref=model_prov.provenance_id,
        ),
        ConstituencyNode(
            node_id="constituency-node:reference:np",
            parse_ref=con_parse_id,
            label="NP",
            token_refs=[tokens[0].token_id, tokens[1].token_id, tokens[2].token_id],
            provenance_ref=model_prov.provenance_id,
        ),
        ConstituencyNode(
            node_id="constituency-node:reference:punct",
            parse_ref=con_parse_id,
            label="PUNCT",
            token_refs=[tokens[3].token_id],
            provenance_ref=model_prov.provenance_id,
        ),
    ]
    con_parse = ConstituencyParseRecord(
        parse_id=con_parse_id,
        tokenization_ref=tokenization_id,
        root_node_ref=con_nodes[0].node_id,
        node_refs=[x.node_id for x in con_nodes],
        scheme="reference-constituency-v1",
        complete=True,
        provenance_ref=model_prov.provenance_id,
    )

    return LinguisticAnnotationBundle(
        text_bundle=text_bundle,
        provenance_records=[human_prov, model_prov],
        tokenizations=[tokenization],
        tokens=tokens,
        morphemes=morphemes,
        morphology_annotations=morphology,
        pos_annotations=pos,
        dependency_parses=[dep_parse],
        dependency_relations=dep_relations,
        constituency_parses=[con_parse],
        constituency_nodes=con_nodes,
        metadata={
            "purpose": "Platform Core v3.66.0 linguistic annotation provenance reference",
            "canonical_text_contract": "sc.core.multilingual-text-language-object.v1",
            "translation_alignment_objects_deferred_to": "v3.67.0",
        },
    )


def contract_document() -> dict[str, Any]:
    ref = reference_linguistic_annotation_bundle()
    return {
        "ok": True,
        "release": CORE_RELEASE,
        "contract": CONTRACT_VERSION,
        "extends_contract": "sc.core.multilingual-text-language-object.v1",
        "object_types": [
            "AnnotationProvenanceRecord",
            "TokenizationRecord",
            "TokenRecord",
            "MorphemeRecord",
            "MorphologicalAnnotation",
            "PartOfSpeechAnnotation",
            "DependencyParseRecord",
            "DependencyRelation",
            "ConstituencyParseRecord",
            "ConstituencyNode",
            "LinguisticAnnotationBundle",
        ],
        "principles": {
            "canonical_source_text_is_immutable": True,
            "linguistic_annotations_are_derived_objects": True,
            "annotations_may_not_rewrite_source_text": True,
            "source_character_offsets_are_preserved": True,
            "machine_annotations_are_advisory": True,
            "human_review_state_is_preserved": True,
            "alternative_annotation_layers_may_coexist": True,
            "annotation_provenance_is_required": True,
        },
        "capabilities": {
            "tokenization_layers": True,
            "exact_token_source_binding": True,
            "morpheme_segmentation": True,
            "lemma_and_morphological_features": True,
            "universal_and_language_specific_pos": True,
            "dependency_syntax": True,
            "constituency_syntax": True,
            "human_model_annotation_distinction": True,
            "annotation_review_state": True,
            "deterministic_object_fingerprints": True,
        },
        "roadmap_integration": {
            "extends_v3650_multilingual_text_language_model": True,
            "prepares_v3670_translation_transliteration_parallel_alignment": True,
            "prepares_v3680_historical_language_script_variant_identity": True,
            "prepares_v3690_cross_lingual_semantic_exchange": True,
            "preserves_v3700_v3760_graph_neural_wave": True,
        },
        "boundaries": {
            "core_tokenizes_text": False,
            "core_performs_morphological_analysis": False,
            "core_assigns_pos_tags": False,
            "core_parses_dependency_syntax": False,
            "core_parses_constituency_syntax": False,
            "core_resolves_annotation_disagreement": False,
            "core_promotes_model_annotation_to_truth": False,
            "core_translates_text": False,
            "core_rewrites_canonical_source_text": False,
        },
        "reference": {
            "text_source_id": ref.text_bundle.text_sources[0].text_source_id,
            "tokenization_id": ref.tokenizations[0].tokenization_id,
            "token_count": len(ref.tokens),
            "morpheme_count": len(ref.morphemes),
            "morphology_annotation_count": len(ref.morphology_annotations),
            "pos_annotation_count": len(ref.pos_annotations),
            "dependency_relation_count": len(ref.dependency_relations),
            "constituency_node_count": len(ref.constituency_nodes),
            "bundle_fingerprint_sha256": ref.fingerprint(),
        },
    }
