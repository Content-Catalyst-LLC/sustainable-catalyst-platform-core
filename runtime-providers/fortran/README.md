# Sustainable Catalyst Fortran Runtime v1.0.0

Runtime ID: `sc-runtime-fortran`  
Adapter ID: `adapter:sc-runtime-fortran`  
Core contract: `sc.core.fortran-runtime.v1`  
Compiler: GNU Fortran 13.3.0 (`gfortran-13` package `13.3.0-6ubuntu2~24.04.1` on Ubuntu 24.04 amd64)

The provider exposes bounded scientific/HPC kernels for dot products, matrix multiplication, numerical integration, finite differences, a reference RK4 step, and a one-dimensional explicit heat-equation step.

All Fortran source is generated internally from validated numeric inputs. The API does not accept arbitrary Fortran source, shell commands, runtime package installation, or caller-selected filesystem paths. Compilation is provider-managed with bounded flags and the compiled executable is transient.
