# Sustainable Catalyst gretl/hansl Runtime v1.0.0

Runtime ID: `sc-runtime-gretl`  
Adapter ID: `adapter:sc-runtime-gretl`  
Core contract: `sc.core.gretl-hansl-runtime.v1`  
Native runtime: gretl 2023c (`2023c-2.1build3` on Ubuntu 24.04)

The provider exposes bounded econometric operations:
OLS, robust OLS, binary logit, binary probit, descriptive summaries, and
correlation matrices.

The provider generates hansl scripts internally from validated identifiers and
numeric datasets. It does not accept arbitrary hansl source, shell commands,
runtime package installation, or caller-selected filesystem paths.
