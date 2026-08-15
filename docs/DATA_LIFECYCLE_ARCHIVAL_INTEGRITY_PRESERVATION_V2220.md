# Data Lifecycle, Archival Integrity & Preservation — v2.22.0

Core v2.22.0 adds a governance plane for retention and preservation. Policies express minimum retention and archive/tombstone timing. Policy/legal holds override lifecycle actions. Preservation archives retain canonical subject references, scrubbed snapshots, SHA-256 content hashes, and SHA-256 manifests. Tombstone actions never hard-delete source records; restoration is reference-first and never silently overwrites canonical truth. Public status is aggregate only.
