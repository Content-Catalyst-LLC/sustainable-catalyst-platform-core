# Platform Core v3.36.0 Audit

PASS criteria:
- legacy Catalyst Analytics R identity remains traceable;
- canonical runtime is `sc-runtime-r@1.0.0`;
- adapter is `adapter:sc-runtime-r`;
- runtime registry contains registered/active R runtime;
- six initial capabilities are allowlisted;
- migration is non-destructive;
- duplicate legacy/canonical execution is disabled;
- runtime provider, not Core, executes R;
- arbitrary R source is disabled;
- package installation from jobs is disabled;
- capability resolution remains candidate-discovery-only;
- Research Lab / Workbench / Workspace boundaries are preserved;
- no database migration is introduced.
