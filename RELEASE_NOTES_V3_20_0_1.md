# Platform Core v3.20.0.1
## Investigation Workspace Schema, Release Identity & Runtime Validation Repair

Repairs v3.20.0 deployment verification by creating the six investigation-workspace tables idempotently, adding a repair migration ledger entry, aligning backend/WordPress release identity, validating routes internally under the existing API authentication policy, and using the public health endpoint for WordPress online-state display.
