# v2.58.0 Causal-Predictive Integration Audit

**Migration:** `0062` (additive, migration description <= 300 characters).

**New persistence families:** `predictive_causal_studies`, `predictive_causal_variable_bindings`, `predictive_intervention_scenarios`, `predictive_counterfactual_forecasts`, `predictive_causal_effect_evidence`, `predictive_causal_evaluations`, `predictive_causal_handoffs`, and `predictive_causal_packages`.

The study layer enforces shared project lineage between the predictive model and causal graph. Variable bindings enforce graph/model ownership for causal variables, predictive targets, and predictive features. Optional references to interventions, identifications, and estimates must belong to the same causal graph.

Core records external evidence and reproducibility state only. It does not infer causal graphs, identify or estimate effects, execute counterfactuals, simulate interventions, rank decisions, or automatically intervene.
