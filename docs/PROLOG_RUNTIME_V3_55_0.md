# Platform Core v3.55.0 — Prolog Logic & Constraint Runtime

Contract: `sc.core.prolog-runtime.v1`

Canonical provider: `sc-runtime-prolog` / `adapter:sc-runtime-prolog`, SWI-Prolog 9.0.4, service port 18104.

The initial runtime is designed for bounded logic and constraint workloads: relation reachability, bounded relation paths, transitive closure, contradiction scans, temporal-consistency checks, and graph coloring. The caller supplies structured facts and parameters, not Prolog source. The provider generates the Prolog program internally and retains it with stdout/stderr and result artifacts for provenance.

Core does not infer facts, certify truth, or choose investigative conclusions. It governs the runtime identity, environment, security policy, job contracts, artifacts, and reproducibility.
