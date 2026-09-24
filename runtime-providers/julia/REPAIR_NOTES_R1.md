# Catalyst Julia Runtime v0.3.0 R1

The original v0.3.0 push path stopped on macOS before commit/push/tag because
the global Python installation did not include pytest.

R1 removes that external dependency entirely. The static validator now uses
only the Python standard library to discover and execute the five adapter
tests, then validates JSON contracts, shell syntax, and release markers.

The Julia runtime implementation, Core adapter contract, deployment script,
and provider behavior are unchanged.
