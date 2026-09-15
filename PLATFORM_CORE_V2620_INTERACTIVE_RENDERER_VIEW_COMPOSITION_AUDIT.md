# v2.62.0 Interactive Renderer & View Composition Audit

## Governed objects
- Renderer profiles and capability declarations
- Scene-bound view compositions
- View-to-renderer assignments
- Linked-view propagation groups
- Selection/filter/viewport/layer interaction state records
- Renderer compatibility resolutions
- Immutable hash-chained composition snapshots

## Core boundary
Core stores semantic composition state and compatibility evidence. It does not draw pixels, compute layout, execute animation, hit-test browser geometry, execute GPU code, or infer truth from visual appearance.
