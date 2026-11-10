# Scientific evidence and figure handoff

SC-RVF-01 uses each product's existing object store. Core registers research components, source snapshots, lineage and runtime contracts. Library owns content-addressed bytes. Lab owns the strict Figure Composer specification and renderer. Workbench owns research-session imports and calculation recipes. Workspace owns project artifacts and immutable publication revisions. Site Intelligence supplies attributed screening context. Research Librarian resolves canonical source identities. Decision Studio records independent review in owned rooms.

The portable specification is `schemas/source-bound-scientific-figure-spec-v1.schema.json`. Lab validates it at `POST /v1/visual-research-narrative-figure-composer/scientific-figure/render`. The response carries the canonical spec, its SHA-256, inert SVG and SVG SHA-256, renderer version, native figure reference and editable table. Hash verification establishes byte identity, not scientific validity. Pending extraction review stays pending through every adapter.

## Native adapter sequence

1. Store original source bytes and derived structured artifacts through Library's signed admin artifact API. Preserve parent artifact identities and source-specific rights. Artifact content is `GET /v1/admin/artifacts/{artifact_id}/content`; metadata is the corresponding identity route. Private reads use the configured Library bearer key. Writes retain the native timestamp/body HMAC.
2. Register dataset and visualization components under the existing Core research project. Read its bundle with `X-SC-API-Key` when public reads are disabled. Workspaces require an explicit mapping to this project identity; similar titles are not identity proof.
3. Resolve canonical sources through Librarian `POST /v1/sources/resolve` with `X-SC-RL-Key`. Promote an immutable, hashed Library-backed source snapshot through `POST /v1/core/evidence/source-snapshots/promote`. DOI metadata snapshots must never be labeled full article snapshots.
4. Render in Lab with `X-SC-Lab-Key`. A changed source or renderer creates a new Library artifact and Core component; existing publications remain pinned to their previous immutable bytes.
5. Import into an owned Workbench session with `POST /standalone/v1/research-sessions/{session_id}/scientific-figures`. Use the owner's native bearer session and the intended Workspace project identity. GET on the collection provides the owned version catalog; GET on a figure supplies a verified source preview without publication writes.
6. Workspace's native cookie-authenticated Reporting Studio handoff is `POST /v1/private-research/reporting-studio/projects/{project_id}/workbench-figures`. It requires same-origin, project ownership, source project binding and an ephemeral Workbench token. The browser token is not stored in the publication or artifact. Native report creation pins artifact, hash and source revision; exports read that saved revision.
7. Site's `GET /v1/scientific-screening/irish-soils` uses `X-SC-Intelligence-Token` and configured Library snapshot pins. Catalog availability does not establish geometry, plot accuracy or removal.
8. Decision's `POST /decision-rooms/{room_id}/scientific-readiness` requires native JWT scopes and room ownership. It resolves the registered figure through Core and Library, then records a native snapshot. A declared positive gate is not an independent reviewer decision.

Use configured service URLs only, with redirect/proxy behavior controlled by each private adapter. Never supply user-selected service targets or credentials in source artifacts. Cross-product ownership tokens and service keys are different credentials.

## Scientific boundaries

Material-specific endpoints, time windows, units and denominators remain separate. Reported plus/minus is not automatically a 95 percent confidence interval. Qualitative null findings are not numeric zero estimates. EPA cumulative stock depths overlap. National soil association data at 1:250,000 do not establish field conditions.

Workbench's protected `/standalone/v1/scientific-transport/calculate` and `/save` preserve explicit measurement timestamps, gap limits, discharge/concentration units and uncertainty assumptions in existing CalculationObjects. Transported mol or charge equivalents are not converted to atmospheric CO2 removal. Missing controls, source allocation, downstream fate, lifecycle inventory or independent review retain `NOT_QUANTIFIED`.

## Deployment and acceptance

The Pi acceptance runtime is isolated. Its protected configuration and rollback containers are operational records outside this repository. No credentials, private manuscript contents or production data belong in this document. The master acceptance issue tracks exact tested revisions, evidence and remaining gaps: https://github.com/Content-Catalyst-LLC/ucd-sustainable-development-research/issues/2

API acceptance does not substitute for browser acceptance or scientific review. The broader SC-RVF-01 experimental design, chemistry, lifecycle, legal status and full manuscript requirements require their own verified implementation and acceptance evidence; this contract does not claim them complete.

## Proposed studies and declared ledgers

Lab `POST /v1/scientific-study/plan` requires the native compute key and explicit unit IDs, blocks, groups, untreated control, seed, observation-window labels and a protocol reference. It reuses the native blocked allocation and randomization engines; source labels are simulation or conceptual. The result is a proposed schedule with pending review, not field execution or preregistration approval.

Workbench `/standalone/v1/scientific-carbon-ledger/calculate` and `/save` use native owned sessions. Each explicit accounting entry retains CO2 mass units, scope, source and method references. Storage bounds attributable mass; reversal and lifecycle domains subtract from the declared balance. Explicit covariance permits local linear propagation with a stated bound-switching limitation. Missing domains block the balance. The declared arithmetic never becomes verified removal or eligibility. Mol/charge quantities are rejected rather than converted into CO2.

Full Core CI currently contains 41 failures that also reproduce on the unmodified base commit. The master issue records the baseline comparison; this adapter contract does not declare release certification.
