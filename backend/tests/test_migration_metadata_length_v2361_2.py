from app.migrations import MIGRATIONS
from app.models import SchemaMigration


def test_all_migration_descriptions_fit_production_storage_contract():
    max_len = SchemaMigration.__table__.c.description.type.length
    assert max_len == 300
    violations = [(version, len(description)) for version, description in MIGRATIONS if len(description) > max_len]
    assert violations == [], f"migration descriptions exceed VARCHAR({max_len}): {violations}"


def test_migration_0040_metadata_is_repair_safe():
    description = dict(MIGRATIONS)["0040"]
    assert len(description) <= 300
    assert "uncertainty compute runtime" in description.lower()
    assert "preserves the v2.36 production schema" in description.lower()
