# Platform Core v3.45.0 Audit

PASS criteria:
- release identity is a blocker gate;
- health is a blocker gate;
- R and Julia providers are blocker-gated;
- unified runtime API contract is blocker-gated;
- catalog/security/environment/interchange/workflow/reproduction evidence is explicit;
- production criteria have unique identities;
- evidence has unique identities and stable fingerprints;
- missing or invalid required evidence cannot certify the fabric;
- missing/uncertified required providers block certification;
- missing/not-ready required Core product profiles prevent certification;
- advisory failures produce certified-with-warnings only;
- production certificate requires a certifiable assessment;
- reference certificate is explicitly not live production evidence;
- deployment verifier is the source of live production evidence;
- external product repository integration is explicitly outside certificate scope;
- scientific validity remains outside certification scope;
- Scientific Artifact Registry bridge is valid;
- no database migration is introduced.
