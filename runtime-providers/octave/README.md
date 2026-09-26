# Sustainable Catalyst Octave Runtime v1.0.0

Runtime ID: `sc-runtime-octave`  
Adapter ID: `adapter:sc-runtime-octave`  
Core contract: `sc.core.octave-runtime.v1`  
Native runtime: GNU Octave 8.4.0

The v1 provider exposes bounded numerical operations only:
matrix multiplication, linear solving, eigenvalue analysis, SVD, FFT, and
polynomial roots.

It does not accept arbitrary Octave source, shell commands, package
installation requests, or caller-selected filesystem paths.
