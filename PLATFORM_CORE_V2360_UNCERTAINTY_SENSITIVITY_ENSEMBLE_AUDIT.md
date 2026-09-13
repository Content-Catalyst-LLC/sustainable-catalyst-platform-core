# Platform Core v2.36.0 Audit

## Implemented

- migration `0039`;
- seven governed uncertainty/sensitivity/ensemble tables;
- internal and public-safe APIs;
- new sensitivity/ensemble visual kinds and renderer compatibility rules;
- SDK and WordPress status surfaces;
- validation guards preventing Core-attributed sensitivity/statistic calculations.

## Validation

Dedicated v2.36 suite: 8/8 passing.
Release-critical dependency gate: 73/73 passing.
Fresh migration: `0039` applied with `pending: []`.

## Boundaries

No Monte Carlo execution, sensitivity calculation, ensemble aggregation, distribution fitting, automatic probability inference, automatic ranking, or truth promotion by Core.
