# v2.61.0 Visual Runtime Audit

- Contract: `sc.visual-runtime.scene.v1`
- Migration: `0065`
- Core stores semantic scene graph and interaction state.
- Core does not perform layout, SVG/Canvas/WebGL rendering, animation, GPU execution, hit testing, or visual truth inference.
- Scene snapshots are immutable, revisioned, SHA-256 content hashed, and hash chained.
