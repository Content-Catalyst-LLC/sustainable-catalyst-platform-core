# Sustainable Catalyst C/C++ Runtime v1.0.0

Runtime: `sc-runtime-cpp`  
Adapter: `adapter:sc-runtime-cpp`  
Core contract: `sc.core.c-cpp-runtime.v1`

The provider exposes bounded native-engineering kernels across two managed language profiles:
C11 and C++17. Structured requests are validated by the provider, source is generated internally,
compiled with pinned GCC/G++, executed as a transient native binary, and returned as governed results
and artifacts. Arbitrary caller C/C++ source, shell commands, package installation, and caller-controlled
filesystem paths are not accepted.
