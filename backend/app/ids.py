from __future__ import annotations

import re
import unicodedata

ID_PATTERN = re.compile(r"^sc:([a-z0-9-]+):([a-z0-9-]+)$")
TOKEN_PATTERN = re.compile(r"^[a-z0-9-]+$")


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_value).strip("-").lower()
    slug = re.sub(r"-{2,}", "-", slug)
    if not slug:
        raise ValueError("Could not produce a non-empty slug.")
    return slug


def build_entity_id(entity_type: str, slug: str) -> str:
    entity_type = slugify(entity_type)
    slug = slugify(slug)
    return f"sc:{entity_type}:{slug}"


def validate_entity_id(value: str) -> tuple[str, str]:
    match = ID_PATTERN.fullmatch(value)
    if not match:
        raise ValueError(
            "Entity ID must use sc:<entity-type>:<slug> with lowercase letters, "
            "numbers, and hyphens."
        )
    return match.group(1), match.group(2)


def validate_token(value: str, label: str = "value") -> str:
    if not TOKEN_PATTERN.fullmatch(value):
        raise ValueError(
            f"{label} must contain only lowercase letters, numbers, and hyphens."
        )
    return value
