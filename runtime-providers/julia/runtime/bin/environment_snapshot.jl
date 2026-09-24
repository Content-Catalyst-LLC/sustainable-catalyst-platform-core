using Pkg
Pkg.activate(joinpath(@__DIR__, ".."))
using CatalystJuliaRuntime
using JSON3
print(JSON3.write(CatalystJuliaRuntime.environment_document()))
println()
