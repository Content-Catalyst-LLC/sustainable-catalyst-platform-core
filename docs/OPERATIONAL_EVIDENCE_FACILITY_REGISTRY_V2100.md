# Operational Evidence & Facility Registry — Core v2.10.0

Core v2.10.0 separates stable facility identity from dated observations about operational condition. A new report does not erase prior evidence, and operational, damage, access, service, capacity, and supply dimensions are not collapsed into one synthetic status.

## Stable facility identity
Facilities can carry a Core entity link, source-specific identifiers, ISO3 country scope, administrative/locality context, coordinates or geometry, visibility, and metadata. Exact source-identifier namespace/value pairs support deterministic deduplication.

## Dated evidence observations
Each observation can preserve publisher, source and connector references, source-record ID and URL, evidence class, geographic scope, methodology, confidence, services, constraints, details, and provenance.

## Initial facility vocabulary
Hospital, clinic, health center, school, university, shelter, water facility, power facility, crossing, port, airport, communications facility, food distribution, warehouse, and other.

## Truth rules
- Missing evidence does not imply normal operation.
- Conflicting reports remain visible in history.
- Different status dimensions remain distinct.
- Public surfaces expose only records marked public.
- External provider uptime does not block Core promotion.
