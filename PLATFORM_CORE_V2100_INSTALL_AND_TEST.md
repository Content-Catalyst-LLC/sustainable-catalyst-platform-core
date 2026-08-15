# Platform Core v2.10.0 Install and Test

Run the release deploy/validation script from the release bundle. The validator applies migrations through `0013`, runs all deterministic tests, verifies the operational facility registry, then performs syntax/static checks. External provider availability remains non-blocking.

## R1 promotion repair

If an earlier v2.10.0 run stopped after `PASS - v2.10.0 release contract` with `AssertionError: 2.10.0`, use the R1 repaired bundle. The failure was in the post-validation promotion script, not the facility registry or migration. R1 corrects the manifest-version assertion, current installer syntax target, and inherited reliability-test filename before GitHub promotion resumes.
