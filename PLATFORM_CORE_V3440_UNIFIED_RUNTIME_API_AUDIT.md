# Platform Core v3.44.0 Audit

PASS criteria:
- runtime catalog identities are unique and content-fingerprinted;
- R and Julia catalog entries preserve governed versions/adapters;
- product profiles explicitly scope actions, runtimes and operations;
- Workspace, Research Lab and Workbench profiles are contract-ready;
- candidate discovery never binds a runtime automatically;
- explicit bindings are validated against product/runtime capabilities;
- unavailable runtimes are excluded from resolution;
- invocation requires exact request/resolution/profile/catalog fingerprints;
- invocation requires computational job, environment package and security decision;
- invocation dispatch owner remains Workspace/execution host;
- completion receipts bind exact invocation/runtime/host identity;
- failed receipts require an error identity;
- bundle validates product/profile/request/resolution/invocation/receipt lineage;
- scientific artifact projection validates against v3.38;
- Core does not claim separate product repositories were modified;
- Core does not autonomously select runtimes or dispatch execution;
- no database migration is introduced.
