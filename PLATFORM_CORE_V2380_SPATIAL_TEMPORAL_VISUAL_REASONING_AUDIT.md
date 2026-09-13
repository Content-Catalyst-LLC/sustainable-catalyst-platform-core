# v2.38.0 Spatial & Temporal Visual Reasoning Audit

- Governed spatial-temporal scene model.
- GeoJSON feature semantics with CRS/SRID metadata.
- Events and intervals with strict temporal ordering.
- Trajectories and ordered trajectory points.
- Provenance-required change observations.
- Saved map/timeline/time-slider views.
- Renderer-neutral visualization contract.
- Explicit Site Intelligence/Lab/Workbench runtime handoffs.
- Core does not perform CRS reprojection, spatial joins, routing, raster processing, remote sensing, arbitrary temporal model execution, or truth promotion.
- Migration `0042` description is bounded by the production `VARCHAR(300)` ledger contract.
- True v2.37.0.2 → v2.38.0 upgrade simulation passed with only `0042` newly applied and `pending=[]`.
- Streamlined release-critical gate: 100/100 passing.
