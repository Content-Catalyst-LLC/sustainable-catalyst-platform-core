# Platform Core v3.37.0 — Statistical Analysis Object Model

## Objective

v3.37.0 adds a language-neutral statistical analysis object layer above the
runtime fabric.

Contract: `sc.core.statistical-analysis-object.v1`

v3.36 made R a first-class governed runtime. v3.37 defines the research objects
that describe what statistical analysis was intended, what data and variables
were used, which method was selected, how it was executed, and what results
were produced.

## First-class objects

- StatisticalVariableBinding
- StatisticalDataBinding
- StatisticalMethodSpecification
- StatisticalHypothesis
- StatisticalAnalysisPlan
- ConfidenceInterval
- StatisticalEstimate
- HypothesisTestResult
- EffectSizeResult
- ModelFitStatistic
- StatisticalDiagnostic
- StatisticalAssumptionCheck
- StatisticalMatrixResult
- StatisticalExecutionBinding
- StatisticalAnalysisResult
- StatisticalAnalysisPackage

## Research design

A `StatisticalAnalysisPlan` records:
- objective and research-question references;
- exact dataset version and variable bindings;
- variable roles and measurement scales;
- chosen statistical method;
- runtime operation;
- hypotheses and alpha;
- seed and preregistration references;
- source commit and provenance.

The method is declared by the researcher or calling workflow. Platform Core does
not autonomously choose the statistical method.

## Result semantics

A statistical result can preserve:
- parameter estimates;
- standard errors;
- test statistics;
- p-values;
- confidence intervals;
- effect sizes;
- model-fit statistics;
- diagnostics;
- assumption checks;
- matrix-valued results such as correlation matrices;
- artifacts and limitations.

A p-value or threshold result is evidence attached to the analysis. Core does
not interpret statistical significance as truth.

## Runtime execution binding

`StatisticalExecutionBinding` connects the analysis to:
- computational job;
- runtime adapter;
- runtime identity/version;
- execution environment;
- runtime operation;
- raw runtime-result reference.

The reference implementation binds to:

`adapter:sc-runtime-r`
`sc-runtime-r@1.0.0`

## R Runtime normalization

v3.37 provides deterministic normalization for all six R Runtime 1.0 operations:

- descriptive_summary
- quantile_summary
- correlation_matrix
- linear_regression
- t_test
- one_way_anova

The raw R result remains externally referenceable. Core creates governed
statistical objects from it rather than replacing the underlying runtime output.

## Future runtime neutrality

The object model is not R-specific. Later Python, Julia, Stan, gretl/hansl,
Octave and other statistical providers can normalize their outputs into the same
Core statistical objects.

This is especially important for econometric, psychometric, Bayesian,
time-series and simulation workflows.

## Product boundaries

Research Lab:
- statistical study workflows;
- diagnostics;
- model comparison;
- advanced methods.

Workbench:
- interactive analysis;
- calculators and exploratory statistical workflows.

Workspace:
- job orchestration;
- environments;
- reproducible execution.

Runtime providers:
- actual method execution.

Platform Core:
- statistical object identity;
- data/method/result lineage;
- provenance;
- portable analysis packages.

Core does not execute statistical methods, select methods, certify assumptions,
or certify statistical validity.

## Next mapped build

Platform Core v3.38.0 — Scientific Result & Artifact Registry.
