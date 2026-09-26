# Sustainable Catalyst Haskell Runtime v1.0.0

Runtime ID: `sc-runtime-haskell`  
Adapter ID: `adapter:sc-runtime-haskell`  
Core contract: `sc.core.haskell-runtime.v1`  
Native runtime: GHC 9.4.7 (`9.4.7-3` on Ubuntu 24.04)

The v1 provider exposes bounded exact/discrete operations: GCD, LCM, rational
reduction, factorial, Fibonacci, binomial coefficients, integer powers, and
graph reachability. The provider generates Haskell source internally from
validated integer inputs and executes it with `runghc`. Arbitrary Haskell
source, shell execution, package installation and caller-selected filesystem
paths are not exposed.
