# Platform Core v2.31.0 — System Maps

System Maps build on the v2.29 visual reasoning object model and v2.30 visualization specification/renderer registry. Core stores governed map semantics: explicit boundaries, domains, visual-element memberships, saved views, and structural validation. It can compile a system map to an immutable v2.30 visualization specification.

## Boundaries
Core records included, excluded, contextual, and interface boundaries. Boundaries are explicit claims about scope; Core does not infer them.

## Domains and memberships
Domains group existing visual-reasoning elements. Membership is constrained to elements within the same system map.

## Views
Saved views capture lens, filters, highlights, and layout intent without storing renderer coordinates.

## Architecture boundary
Core does not execute layout, render images, infer causal loops, or promote map structure to truth. Those remain external/product-specific capabilities.
