# Sustainable Catalyst Stan Runtime v1.0.0

Runtime ID: `sc-runtime-stan`  
Adapter ID: `adapter:sc-runtime-stan`  
Core contract: `sc.core.stan-runtime.v1`  
Native runtime: CmdStan 2.36.0

The provider exposes bounded, governed Stan operations:
`compile_model`, `sample`, `optimize`, `variational`, and `diagnose`.

The provider does not expose a shell, package installation, include directives,
external C++ extensions, filesystem paths supplied by callers, or arbitrary
process execution. Stan model text is treated as a governed domain model and is
compiled inside provider-managed directories.

v1 intentionally supports one chain per invocation. Multi-chain orchestration
belongs to Workspace / the execution host and can be added in a later runtime
release without weakening the security boundary.
