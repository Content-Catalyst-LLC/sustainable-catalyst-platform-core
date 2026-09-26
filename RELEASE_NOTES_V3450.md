# Platform Core v3.45.0 — Runtime Fabric Production Certification

## Objective

v3.45.0 adds the formal certification layer for the runtime fabric assembled
through v3.22–v3.44.

Contract: `sc.core.runtime-fabric-production-certification.v1`

The release converts runtime readiness from an informal deployment impression
into an explicit evidence model with blocker, required and advisory gates.

## Certification domains

The production plan covers:

- release identity and production Git tag;
- Platform Core health;
- unified runtime API contract integrity;
- R provider registration;
- Julia provider registration;
- unified runtime catalog;
- runtime security governance;
- reproducible environment verification;
- R→Julia data interchange verification;
- cross-runtime workflow verification;
- reproduction comparison;
- Workspace / Research Lab / Workbench Core-side runtime profiles;
- Scientific Artifact Registry packaging.

## First-class objects

- ProductionCertificationCriterion
- ProductionCertificationEvidence
- ProductionCriterionResult
- RuntimeProviderCertification
- ProductRuntimeProfileCertification
- RuntimeFabricCertificationPlan
- RuntimeFabricCertificationAssessment
- RuntimeFabricProductionCertificate

## Gate semantics

Criteria are classified as:

- `blocker`: any failure prevents certification;
- `required`: failure prevents certification but is reported separately from a
  hard runtime blocker;
- `advisory`: failure produces `certified-with-warnings`.

Assessment states are:

- `certified`
- `certified-with-warnings`
- `not-certified`
- `incomplete`

## Provider certification

The reference certification covers the current canonical providers:

- `sc-runtime-r@1.0.0`
- `catalyst-julia-runtime@0.3.0`

Provider certification preserves runtime identity, adapter identity, required
operations and evidence references.

## Product integration certification

v3.45 certifies the Core-side runtime profiles introduced in v3.44 for:

- Workspace
- Research Lab
- Workbench

This is intentionally **not** a claim that the separate product repositories
have already been wired to consume the unified runtime API. Product repository
integration remains a follow-on product task.

## Reference certificate versus live certification

The built-in reference certificate is a deterministic contract proof. It is
used by tests and the Core API to prove the certification model itself.

It is not live production evidence.

The deployment verifier supplies the actual production evidence by checking:

- deployed release version;
- exact production Git tag;
- live health endpoint;
- live unified runtime contract/catalog/profile endpoints;
- live R and Julia adapter registration;
- live v3.43 security reference;
- live v3.41 environment verification;
- live v3.39 interchange verification;
- live v3.40 workflow verification;
- live v3.42 reproduction equivalence;
- live v3.44 reference integration.

The deployment does not finish successfully unless those production gates pass.

## Scientific Registry bridge

A runtime-fabric production certificate can be projected into the v3.38
Scientific Artifact Registry. The certificate fingerprint becomes its content
hash.

## Boundaries

Platform Core certifies its runtime-fabric contracts and collected production
evidence.

It does not:

- certify scientific truth or methodological validity;
- autonomously select runtimes;
- execute runtime jobs itself;
- claim external product repository integration without product-side changes;
- turn the built-in reference certificate into live production evidence.

## Next mapped build

Platform Core v3.46.0 — Stan Runtime.
