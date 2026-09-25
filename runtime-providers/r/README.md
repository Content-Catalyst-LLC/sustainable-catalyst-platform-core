# Sustainable Catalyst R Runtime v1.0.0

Canonical runtime: `sc-runtime-r`
Adapter: `adapter:sc-runtime-r`
Default endpoint: `127.0.0.1:18094`

This provider migrates the former Catalyst Analytics R execution role into the
Platform Core runtime fabric.

Allowlisted base-R operations:
- descriptive_summary
- quantile_summary
- correlation_matrix
- linear_regression
- t_test
- one_way_anova

No arbitrary R source, shell execution, or package installation is permitted
through job payloads.
