# Platform Core v3.39.0 — Runtime Data Interchange

## Objective

v3.39.0 defines the language-neutral data exchange contract for moving governed
research data between Sustainable Catalyst runtimes.

Contract: `sc.core.runtime-data-interchange.v1`

The release establishes canonical schemas, type mappings, runtime interchange
profiles, format negotiation, conversion specifications, transfer verification,
and a bridge into the v3.38 Scientific Result & Artifact Registry.

## First-class objects

- DataFieldSchema
- DataInterchangeSchema
- RuntimeTypeMapping
- RuntimeInterchangeProfile
- DataInterchangeArtifact
- DataInterchangeNegotiationRequest
- DataInterchangeNegotiationResult
- DataInterchangeConversionSpec
- DataInterchangeVerification
- DataInterchangeTransfer
- RuntimeDataInterchangeBundle

## Canonical type system

The interchange layer includes runtime-neutral scalar types for booleans,
signed/unsigned integers, floating point, decimal, strings, binary data,
dates/times/timestamps/durations, categorical data and unknown/opaque cases.

Schemas are shape-aware and can represent scalars, vectors, matrices, tables,
tensors, records, collections and opaque payloads.

## Formats

The contract recognizes:
- JSON
- CSV
- Arrow IPC file
- Arrow IPC stream
- Parquet
- NumPy NPY/NPZ
- Feather
- text/binary/other

Arrow and Parquet are first-class contract formats because they are important
for future zero-copy/columnar workflows. v3.39 does not falsely claim that the
current R or Julia providers already expose native Arrow/Parquet support.

## Runtime profiles

A runtime interchange profile declares:
- exact runtime identity/version;
- readable formats;
- writable formats;
- supported data shapes;
- native-to-canonical type mappings;
- maximum supported rank;
- provider-specific metadata.

The reference profiles reflect currently implemented capabilities:

`sc-runtime-r@1.0.0`
- JSON
- CSV
- scalar/vector/matrix/table

`catalyst-julia-runtime@0.3.0`
- JSON
- scalar/vector/matrix/table

## Candidate discovery, not autonomous selection

Core computes compatible interchange-format candidates but does not choose one.

The reference R→Julia request prefers:
Arrow IPC → Parquet → JSON

Because current registered provider profiles overlap only on JSON, Core returns:

`candidate_formats = ["json"]`

and:

`selected_format = null`

The calling research workflow remains responsible for the choice.

## Conversion and verification

`DataInterchangeConversionSpec` records:
- source and target formats;
- source and target runtimes;
- converter/job/environment identity;
- loss policy;
- null/categorical/timestamp policies.

`DataInterchangeVerification` records:
- source/target schema fingerprints;
- row and column preservation;
- type compatibility;
- null and categorical semantics;
- numerical tolerance;
- verification job provenance.

A transfer cannot be marked completed unless verification passed or completed
with an explicit warning.

## Scientific registry bridge

Every interchange artifact can be projected into a v3.38
`ScientificArtifactRef` while preserving:
- content SHA-256;
- URI;
- media type;
- logical data identity;
- schema fingerprint;
- producing runtime identity.

The source interchange object remains authoritative.

## Reference cross-runtime proof

v3.39 includes a reference transfer:

`sc-runtime-r@1.0.0 → catalyst-julia-runtime@0.3.0`

using an identical two-column JSON table with canonical float64 fields. The
reference proves logical identity and schema/content preservation; it does not
claim that Core itself moved or converted the bytes.

## Product boundaries

Platform Core owns:
- canonical interchange schemas/types;
- runtime compatibility profiles;
- candidate format discovery;
- conversion specifications;
- transfer lineage;
- verification objects;
- scientific artifact bridge.

Workspace or runtime providers execute actual conversions/transfers.

Core does not:
- autonomously select a format;
- execute conversions itself;
- claim semantic equivalence without verification;
- claim provider support that is not registered;
- certify scientific validity.

## Next mapped build

Platform Core v3.40.0 — Cross-Runtime Research Workflow.
